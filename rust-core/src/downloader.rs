// 下载管理：队列 + 工作线程 + 断点续传 + 备用 CDN + 限速 + 校验
use crate::history;
use crate::http::HTTP;
use crate::naming;
use crate::parser;
use crate::paths;
use crate::settings;
use crate::urlfixer;
use once_cell::sync::Lazy;
use serde_json::{json, Value};
use std::io::{Read, Write};
use std::path::Path;
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::Mutex;
use std::time::{Duration, Instant};

pub const BUILTIN_ALLOWED_DOMAINS: &[&str] = &[
    "smartedu.cn",
    "ykt.cbern.com.cn",
    "c1.ykt.cbern.com.cn",
    "r1-ndr-private.ykt.cbern.com.cn",
    "s-file-1.ykt.cbern.com.cn",
];

#[derive(Clone)]
pub struct Task {
    pub task_id: String,
    pub url: String,
    pub save_path: String,
    pub title: Option<String>,
    pub chapters: Value,
    pub status: String, // pending downloading paused completed failed cancelled
    pub downloaded_size: u64,
    pub total_size: u64,
    pub speed: f64,
    pub error: Option<String>,
}

static TASKS: Lazy<Mutex<Vec<Task>>> = Lazy::new(|| Mutex::new(Vec::new()));
static CANCEL_FLAGS: Lazy<Mutex<std::collections::HashMap<String, std::sync::Arc<AtomicBool>>>> =
    Lazy::new(|| Mutex::new(std::collections::HashMap::new()));
static RUNNING: AtomicUsize = AtomicUsize::new(0);
static WAKE: Lazy<std::sync::Condvar> = Lazy::new(std::sync::Condvar::new);
static WORKER_STARTED: AtomicBool = AtomicBool::new(false);

pub fn is_url_allowed(url: &str) -> bool {
    if settings::get("allow_any_domain_download").as_bool().unwrap_or(true) {
        return true;
    }
    let host = host_of(url).to_lowercase();
    let mut allowed: Vec<String> = BUILTIN_ALLOWED_DOMAINS.iter().map(|s| s.to_string()).collect();
    if let Some(arr) = settings::get("custom_allowed_domains").as_array() {
        for d in arr {
            if let Some(s) = d.as_str() {
                allowed.push(s.to_lowercase());
            }
        }
    }
    allowed.iter().any(|d| host == *d || host.ends_with(&format!(".{}", d)) || host.ends_with(d))
}

fn host_of(url: &str) -> String {
    let rest = url.split("://").nth(1).unwrap_or(url);
    rest.split('/').next().unwrap_or("").to_string()
}

fn load_persisted() {
    let mut tasks = TASKS.lock().unwrap();
    if !tasks.is_empty() {
        return;
    }
    if let Ok(text) = std::fs::read_to_string(paths::download_tasks_file()) {
        if let Ok(arr) = serde_json::from_str::<Value>(&text) {
            if let Some(list) = arr.as_array() {
                for t in list {
                    let status = t.get("status").and_then(|v| v.as_str()).unwrap_or("pending").to_string();
                    let status = if status == "downloading" || status == "pending" { "pending".to_string() } else { status };
                    tasks.push(Task {
                        task_id: t.get("task_id").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                        url: t.get("url").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                        save_path: t.get("save_path").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                        title: t.get("title").and_then(|v| v.as_str()).map(|s| s.to_string()),
                        chapters: t.get("chapters").cloned().unwrap_or(json!([])),
                        status,
                        downloaded_size: t.get("downloaded_size").and_then(|v| v.as_u64()).unwrap_or(0),
                        total_size: t.get("total_size").and_then(|v| v.as_u64()).unwrap_or(0),
                        speed: 0.0,
                        error: None,
                    });
                }
            }
        }
    }
}

fn persist() {
    let tasks = TASKS.lock().unwrap();
    let arr: Vec<Value> = tasks
        .iter()
        .map(|t| {
            json!({
                "task_id": t.task_id,
                "url": t.url,
                "save_path": t.save_path,
                "title": t.title,
                "chapters": t.chapters,
                "status": t.status,
                "downloaded_size": t.downloaded_size,
                "total_size": t.total_size,
                "speed": t.speed,
                "error": t.error,
            })
        })
        .collect();
    let _ = std::fs::create_dir_all(paths::cache_dir());
    let _ = std::fs::write(paths::download_tasks_file(), serde_json::to_string_pretty(&arr).unwrap_or_default());
}

pub fn add_task(url: &str, title: Option<&str>, chapters: Value, save_path: Option<&str>) -> Result<String, String> {
    load_persisted();
    if !is_url_allowed(url) {
        return Err(format!("URL 不在允许的域名白名单中: {}", url));
    }
    let mut tasks = TASKS.lock().unwrap();
    if tasks.len() >= 500 {
        return Err("下载队列已满（最多 500 个任务）".into());
    }
    let task_id = format!("task_{}", chrono::Local::now().timestamp_nanos_opt().unwrap_or_else(|| rand::random()));
    let final_path = match save_path {
        Some(p) if !p.is_empty() => p.to_string(),
        _ => {
            let mut dir = paths::download_dir();
            if settings::get("auto_categorize").as_bool().unwrap_or(false) {
                let rule = settings::get("categorize_rule").as_str().unwrap_or(naming::CAT_BY_SUBJECT).to_string();
                dir = naming::categorized_path(&dir, &rule, title);
            }
            let filename = naming::generate_filename(
                settings::get("file_naming_rule").as_str().unwrap_or("default"),
                title,
                settings::get("include_timestamp").as_bool().unwrap_or(false),
            );
            Path::new(&dir).join(filename).to_string_lossy().to_string()
        }
    };
    if let Some(parent) = Path::new(&final_path).parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    let task = Task {
        task_id: task_id.clone(),
        url: url.to_string(),
        save_path: final_path,
        title: title.map(|s| s.to_string()),
        chapters,
        status: "pending".into(),
        downloaded_size: 0,
        total_size: 0,
        speed: 0.0,
        error: None,
    };
    tasks.push(task);
    drop(tasks);
    persist();
    ensure_worker();
    WAKE.notify_all();
    Ok(task_id)
}

pub fn pause_task(task_id: &str) {
    set_cancel(task_id);
    let mut tasks = TASKS.lock().unwrap();
    if let Some(t) = tasks.iter_mut().find(|t| t.task_id == task_id) {
        if t.status == "pending" || t.status == "downloading" {
            t.status = "paused".into();
        }
    }
    drop(tasks);
    persist();
}

pub fn cancel_task(task_id: &str) {
    set_cancel(task_id);
    let mut tasks = TASKS.lock().unwrap();
    if let Some(t) = tasks.iter_mut().find(|t| t.task_id == task_id) {
        if t.status == "pending" || t.status == "downloading" {
            t.status = "cancelled".into();
        }
    }
    drop(tasks);
    persist();
}

pub fn remove_task(task_id: &str) {
    set_cancel(task_id);
    let mut tasks = TASKS.lock().unwrap();
    tasks.retain(|t| t.task_id != task_id);
    drop(tasks);
    persist();
}

pub fn retry_task(task_id: &str) {
    let mut tasks = TASKS.lock().unwrap();
    if let Some(t) = tasks.iter_mut().find(|t| t.task_id == task_id) {
        if t.status == "downloading" || t.status == "pending" {
            return;
        }
        t.status = "pending".into();
        t.downloaded_size = 0;
        t.error = None;
    }
    drop(tasks);
    persist();
    ensure_worker();
    WAKE.notify_all();
}

pub fn clear_all_tasks() {
    {
        let flags = CANCEL_FLAGS.lock().unwrap();
        for (_, f) in flags.iter() {
            f.store(true, Ordering::SeqCst);
        }
    }
    let mut tasks = TASKS.lock().unwrap();
    tasks.clear();
    drop(tasks);
    persist();
}

fn set_cancel(task_id: &str) {
    let mut flags = CANCEL_FLAGS.lock().unwrap();
    flags.entry(task_id.to_string()).or_insert_with(|| std::sync::Arc::new(AtomicBool::new(true)));
    if let Some(f) = flags.get(task_id) {
        f.store(true, Ordering::SeqCst);
    }
}

fn is_cancelled(task_id: &str) -> bool {
    let flags = CANCEL_FLAGS.lock().unwrap();
    flags.get(task_id).map(|f| f.load(Ordering::SeqCst)).unwrap_or(false)
}

pub fn get_all_tasks() -> Value {
    load_persisted();
    let tasks = TASKS.lock().unwrap();
    let arr: Vec<Value> = tasks
        .iter()
        .map(|t| {
            json!({
                "task_id": t.task_id,
                "url": t.url,
                "save_path": t.save_path,
                "title": t.title,
                "status": t.status,
                "downloaded_size": t.downloaded_size,
                "total_size": t.total_size,
                "speed": t.speed,
                "error": t.error,
            })
        })
        .collect();
    json!(arr)
}

fn ensure_worker() {
    if WORKER_STARTED.swap(true, Ordering::SeqCst) {
        return;
    }
    std::thread::spawn(|| loop {
        // 取下一个 pending 任务，遵守并发限制
        let next: Option<Task> = {
            let mut tasks = TASKS.lock().unwrap();
            let max = settings::get("max_concurrent_downloads").as_u64().unwrap_or(5) as usize;
            if RUNNING.load(Ordering::SeqCst) >= max {
                None
            } else {
                tasks.iter_mut().find(|t| t.status == "pending").map(|t| {
                    t.status = "downloading".into();
                    Task {
                        task_id: t.task_id.clone(),
                        url: t.url.clone(),
                        save_path: t.save_path.clone(),
                        title: t.title.clone(),
                        chapters: t.chapters.clone(),
                        status: "downloading".into(),
                        downloaded_size: 0,
                        total_size: 0,
                        speed: 0.0,
                        error: None,
                    }
                })
            }
        };
        match next {
            Some(task) => {
                RUNNING.fetch_add(1, Ordering::SeqCst);
                let handle_task = task.clone();
                std::thread::spawn(move || {
                    download_task(&handle_task);
                    RUNNING.fetch_sub(1, Ordering::SeqCst);
                });
            }
            None => {
                // 无任务或并发满：等待唤醒或超时
                let tasks = TASKS.lock().unwrap();
                let max = settings::get("max_concurrent_downloads").as_u64().unwrap_or(5) as usize;
                let has_pending = tasks.iter().any(|t| t.status == "pending");
                drop(tasks);
                if !has_pending {
                    persist();
                    std::thread::sleep(Duration::from_secs(2));
                } else {
                    std::thread::sleep(Duration::from_millis(200));
                }
            }
        }
    });
}

fn backup_url(url: &str) -> Option<String> {
    let servers = ["c1", "s-file-1", "r1-ndr-private"];
    for s in servers {
        let domain = format!("{}.ykt.cbern.com.cn", s);
        if url.contains(&domain) {
            for alt in servers {
                let alt_domain = format!("{}.ykt.cbern.com.cn", alt);
                if alt_domain != domain {
                    return Some(url.replacen(&domain, &alt_domain, 1));
                }
            }
            break;
        }
    }
    None
}

fn download_task(task: &Task) {
    crate::logging::log("STEP", &format!("开始下载: {}", task.title.as_deref().unwrap_or("未命名")));
    // token 检查
    if HTTP.token().is_none() {
        crate::http::init_from_settings();
    }
    if HTTP.token().is_none() {
        set_task_error(&task.task_id, "Access Token 未配置，请在设置中填写有效的 Token");
        return;
    }
    let save_path = task.save_path.clone();
    let tmp_path = format!("{}.tmp", save_path);

    let urls: Vec<String> = {
        let mut v = vec![task.url.clone()];
        if let Some(b) = backup_url(&task.url) {
            v.push(b);
        }
        v
    };

    let mut last_error: Option<String> = None;
    let mut success = false;
    let mut bytes_final = 0u64;
    for (attempt, u) in urls.iter().enumerate() {
        if is_cancelled(&task.task_id) {
            break;
        }
        if attempt > 0 {
            crate::logging::log("INFO", &format!("主链接失败，切换到备用CDN重试 (第{}次)", attempt));
            let _ = std::fs::remove_file(&tmp_path);
        }
        match download_single(u, &save_path, &task.task_id) {
            Ok(bytes) => {
                success = true;
                bytes_final = bytes;
                break;
            }
            Err(e) => {
                last_error = Some(e);
                if is_cancelled(&task.task_id) {
                    break;
                }
            }
        }
    }

    if is_cancelled(&task.task_id) {
        let mut tasks = TASKS.lock().unwrap();
        if let Some(t) = tasks.iter_mut().find(|t| t.task_id == task.task_id) {
            t.status = "cancelled".into();
            t.speed = 0.0;
        }
        drop(tasks);
        persist();
        return;
    }
    if !success {
        let err = last_error.unwrap_or_else(|| "未知错误".into());
        crate::logging::log("ERROR", &format!("下载失败: {} - {}", task.title.as_deref().unwrap_or(""), err));
        set_task_error(&task.task_id, &err);
        return;
    }

    crate::logging::log("SUCCESS", &format!("文件下载完成 ({:.1} MB)", bytes_final as f64 / 1048576.0));

    // PDF 书签
    if let Some(arr) = task.chapters.as_array() {
        if !arr.is_empty() && save_path.to_lowercase().ends_with(".pdf") {
            crate::logging::log("STEP", "添加书签中...");
            if let Err(e) = crate::pdf::add_bookmarks(&save_path, &task.chapters) {
                crate::logging::log("WARNING", &format!("添加书签失败: {}", e));
            } else {
                crate::logging::log("SUCCESS", "书签添加完成");
            }
        }
    }

    // 校验
    let auto_verify = settings::get("auto_verify").as_bool().unwrap_or(false);
    if auto_verify && save_path.to_lowercase().ends_with(".pdf") {
        match crate::pdf::verify_pdf(&save_path) {
            Ok(true) => {}
            Ok(false) => {
                crate::logging::log("WARNING", "文件校验失败");
                if settings::get("retry_on_verify_fail").as_bool().unwrap_or(false) {
                    let _ = std::fs::remove_file(&save_path);
                    let mut tasks = TASKS.lock().unwrap();
                    if let Some(t) = tasks.iter_mut().find(|t| t.task_id == task.task_id) {
                        t.status = "pending".into();
                        t.downloaded_size = 0;
                        t.error = Some("校验失败，自动重试".into());
                    }
                    drop(tasks);
                    persist();
                    WAKE.notify_all();
                    return;
                }
                update_task_field(&task.task_id, |t| t.error = Some("文件校验失败".into()));
            }
            Err(e) => crate::logging::log("WARNING", &format!("校验出错: {}", e)),
        }
    }

    // 历史记录
    let content_id = urlfixer::extract_content_id(&task.url).unwrap_or_else(|| task.task_id.clone());
    let filename = Path::new(&save_path).file_name().map(|f| f.to_string_lossy().to_string()).unwrap_or_default();
    history::add_record(
        &content_id,
        task.title.as_deref().unwrap_or("未命名"),
        &filename,
        bytes_final,
        &save_path,
        &task.url,
    );

    {
        let mut tasks = TASKS.lock().unwrap();
        if let Some(t) = tasks.iter_mut().find(|t| t.task_id == task.task_id) {
            t.status = "completed".into();
            t.downloaded_size = bytes_final;
            t.total_size = bytes_final;
            t.speed = 0.0;
        }
    }
    persist();
    crate::logging::log("SUCCESS", &format!("任务完成: {}", task.title.as_deref().unwrap_or("未命名")));
}

fn set_task_error(task_id: &str, err: &str) {
    let mut tasks = TASKS.lock().unwrap();
    if let Some(t) = tasks.iter_mut().find(|t| t.task_id == task_id) {
        t.status = "failed".into();
        t.error = Some(err.to_string());
        t.speed = 0.0;
    }
    drop(tasks);
    persist();
}

fn update_task_field(task_id: &str, f: impl FnOnce(&mut Task)) {
    let mut tasks = TASKS.lock().unwrap();
    if let Some(t) = tasks.iter_mut().find(|t| t.task_id == task_id) {
        f(t);
    }
}

fn download_single(url: &str, save_path: &str, task_id: &str) -> Result<u64, String> {
    let tmp_path = format!("{}.tmp", save_path);
    let mut start_pos: u64 = std::fs::metadata(&tmp_path).map(|m| m.len()).unwrap_or(0);
    if start_pos > 0 {
        crate::logging::log("INFO", &format!("检测到断点，从 {:.1} MB 处继续", start_pos as f64 / 1048576.0));
    }

    let client = reqwest::blocking::Client::builder()
        .danger_accept_invalid_certs(!HTTP.ssl_verify())
        .connect_timeout(Duration::from_secs(settings::get("connect_timeout").as_u64().unwrap_or(30).max(1)))
        .build()
        .map_err(|e| e.to_string())?;

    let speed_limit = settings::get("speed_limit").as_u64().unwrap_or(0);
    let speed_limit_bytes = if speed_limit > 0 { speed_limit * 1024 } else { 0 };

    let mut request = client
        .get(url)
        .header("X-ND-AUTH", HTTP.auth_header())
        .header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Smart-edu-downloader/2.0");
    if start_pos > 0 {
        request = request.header("Range", format!("bytes={}-", start_pos));
    }
    let mut resp = request.send().map_err(|e| format!("网络错误: {}", e))?;
    let status = resp.status().as_u16();
    if status == 416 && start_pos > 0 {
        // 已完整下载
        std::fs::rename(&tmp_path, save_path).map_err(|e| e.to_string())?;
        return Ok(start_pos);
    }
    if !(200..300).contains(&status) {
        return Err(format!("HTTP {}", status));
    }
    if start_pos > 0 && status != 206 {
        crate::logging::log("WARNING", "服务器未返回206，断点续传不可用，从头重新下载");
        start_pos = 0;
    }
    let total_from_header: u64 = resp
        .headers()
        .get("content-length")
        .and_then(|v| v.to_str().ok())
        .and_then(|v| v.parse().ok())
        .unwrap_or(0);
    let total_size = if start_pos > 0 { start_pos + total_from_header } else { total_from_header };

    let mut file = std::fs::OpenOptions::new()
        .create(true)
        .append(start_pos > 0)
        .write(true)
        .truncate(start_pos == 0)
        .open(&tmp_path)
        .map_err(|e| format!("打开文件失败: {}", e))?;

    let mut bytes_downloaded = start_pos;
    let mut last_report = Instant::now();
    let mut last_speed_calc = Instant::now();
    let mut last_size = bytes_downloaded;
    let mut buf = [0u8; 65536];
    loop {
        if is_cancelled(task_id) {
            update_progress(task_id, bytes_downloaded, total_size, 0.0);
            return Err("已取消".into());
        }
        let n = resp.read(&mut buf).map_err(|e| format!("读取失败: {}", e))?;
        if n == 0 {
            break;
        }
        file.write_all(&buf[..n]).map_err(|e| format!("写入失败: {}", e))?;
        bytes_downloaded += n as u64;

        if speed_limit_bytes > 0 {
            let elapsed = last_speed_calc.elapsed().as_secs_f64().max(0.001);
            let current = (bytes_downloaded - last_size) as f64 / elapsed;
            if current > speed_limit_bytes as f64 {
                let sleep = (bytes_downloaded - last_size) as f64 / speed_limit_bytes as f64 - elapsed;
                if sleep > 0.0 {
                    std::thread::sleep(Duration::from_secs_f64(sleep.min(1.0)));
                }
            }
        }
        if last_report.elapsed().as_millis() >= 100 {
            let elapsed = last_speed_calc.elapsed().as_secs_f64().max(0.001);
            let speed = (bytes_downloaded - last_size) as f64 / elapsed;
            last_size = bytes_downloaded;
            last_speed_calc = Instant::now();
            last_report = Instant::now();
            update_progress(task_id, bytes_downloaded, total_size, speed);
        }
    }
    update_progress(task_id, bytes_downloaded, total_size, 0.0);
    std::fs::rename(&tmp_path, save_path).map_err(|e| format!("重命名失败: {}", e))?;
    Ok(bytes_downloaded)
}

fn update_progress(task_id: &str, downloaded: u64, total: u64, speed: f64) {
    let mut tasks = TASKS.lock().unwrap();
    if let Some(t) = tasks.iter_mut().find(|t| t.task_id == task_id) {
        t.downloaded_size = downloaded;
        t.total_size = total;
        t.speed = speed;
    }
}

pub fn format_bytes(size: f64) -> String {
    let units = ["B", "KB", "MB", "GB", "TB"];
    let mut s = size;
    for u in units {
        if s < 1024.0 {
            return format!("{:3.1} {}", s, u);
        }
        s /= 1024.0;
    }
    format!("{:3.1} PB", s)
}

// 供 parser.rs 调用的解析门面（保持模块职责一致）
pub fn parse_url(url: &str, bookmarks: bool) -> parser::ParseResult {
    parser::parse(url, bookmarks)
}
