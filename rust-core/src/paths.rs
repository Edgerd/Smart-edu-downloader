// 运行时路径管理
use once_cell::sync::OnceCell;
use std::path::PathBuf;
use std::sync::Mutex;

static DATA_DIR: OnceCell<PathBuf> = OnceCell::new();
static DOWNLOAD_DIR: Mutex<Option<String>> = Mutex::new(None);

pub fn init(data_dir: &str) {
    let p = PathBuf::from(data_dir);
    let _ = std::fs::create_dir_all(p.join("cache"));
    let _ = std::fs::create_dir_all(p.join("settings"));
    let _ = std::fs::create_dir_all(p.join("logs"));
    let _ = DATA_DIR.set(p);
}

pub fn data_dir() -> PathBuf {
    DATA_DIR
        .get()
        .cloned()
        .unwrap_or_else(|| std::env::temp_dir().join("Smart-edu-downloader-2.0"))
}

pub fn settings_file() -> PathBuf {
    data_dir().join("settings").join("settings.json")
}
pub fn cache_dir() -> PathBuf {
    data_dir().join("cache")
}
pub fn resource_list_file() -> PathBuf {
    cache_dir().join("resource_list.json")
}
pub fn cache_meta_file() -> PathBuf {
    cache_dir().join("cache_meta.json")
}
pub fn search_history_file() -> PathBuf {
    cache_dir().join("search_history.json")
}
pub fn download_tasks_file() -> PathBuf {
    cache_dir().join("download_tasks.json")
}
pub fn download_history_file() -> PathBuf {
    cache_dir().join("download_history.json")
}
pub fn logs_dir() -> PathBuf {
    data_dir().join("logs")
}

pub fn set_download_dir(dir: &str) {
    *DOWNLOAD_DIR.lock().unwrap() = Some(dir.to_string());
}
pub fn download_dir() -> String {
    let guard = DOWNLOAD_DIR.lock().unwrap();
    if let Some(d) = guard.as_ref() {
        return d.clone();
    }
    drop(guard);
    // 默认: 系统下载目录/教材下载
    let dl = system_downloads_dir().join("教材下载");
    let _ = std::fs::create_dir_all(&dl);
    dl.to_string_lossy().to_string()
}

pub fn system_downloads_dir() -> PathBuf {
    // XDG 优先，其次 USERPROFILE，再退到家目录
    if let Ok(v) = std::env::var("XDG_DOWNLOAD_DIR") {
        if !v.is_empty() {
            return PathBuf::from(v);
        }
    }
    let home = std::env::var("USERPROFILE")
        .or_else(|_| std::env::var("HOME"))
        .unwrap_or_else(|_| ".".to_string());
    PathBuf::from(home).join("Downloads")
}
