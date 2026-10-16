// 资源库：扁平化 + 缓存(7天) + 搜索
use crate::fetcher;
use crate::paths;
use crate::settings;
use once_cell::sync::Lazy;
use serde_json::{json, Value};
use std::sync::Mutex;

pub const CACHE_EXPIRE_DAYS: i64 = 7;

static RESOURCE_LIST: Lazy<Mutex<Option<Value>>> = Lazy::new(|| Mutex::new(None));
static FLAT_CACHE: Lazy<Mutex<Option<Vec<Value>>>> = Lazy::new(|| Mutex::new(None));

pub const KNOWN_PUBLISHERS: &[&str] = &[
    "冀教版", "人教版", "北师大版", "苏教版", "湘教版", "鲁教版", "沪科版", "浙教版", "华师大版", "沪教版", "教科版", "粤教版", "中图版", "地图版", "外研版", "译林版", "仁爱版", "科普版", "鲁科版", "川教版", "鄂教版", "粤沪版", "粤科技版", "青岛版", "沪粤版", "大象版", "西师大版", "语文版", "长春版", "河大版", "冀少版", "济南版", "沪科技版", "苏科版", "苏少版", "浙人版", "沪外版", "沪外教版", "湘少版", "湘美版", "湘科版", "湘文艺版", "沪教牛津版", "鲁美版", "鲁文艺版", "鲁外版", "粤教花城版", "粤教育版", "粤音版", "粤美版", "粤外版", "粤教科版", "鄂科版", "鄂美版", "鄂外版", "鄂音版", "鄂文艺版", "鄂教科版", "川科版", "川美版", "川外版", "川音版", "川文艺版", "川教科版", "辽教版", "辽科版", "辽美版", "辽外版", "辽音版", "辽文艺版", "辽教科版", "辽海版", "辽师大版", "闽教版", "闽科版", "闽美版", "闽外版", "闽音版", "闽文艺版", "闽教科版", "赣教版", "赣科版", "赣美版", "赣外版", "赣音版", "赣文艺版", "赣教科版",
];

const SUBJECT_WORDS: &[&str] = &["语文", "数学", "英语", "科学", "道德与法治", "音乐", "美术", "体育", "信息科技", "信息技术"];
const GRADE_WORDS: &[&str] = &["一年级", "二年级", "三年级", "四年级", "五年级", "六年级", "七年级", "八年级", "九年级", "高一", "高二", "高三", "十年级", "十一年级", "十二年级"];

pub fn resource_url(content_id: &str, resource_type: &str) -> String {
    format!("https://basic.smartedu.cn/tchMaterial/detail?contentType={}&contentId={}&catalogType=tchMaterial&subCatalog=tchMaterial", resource_type, content_id)
}

pub fn get_resource_list(force_refresh: bool) -> Result<Value, String> {
    let mut g = RESOURCE_LIST.lock().unwrap();
    if !force_refresh {
        if let Some(v) = g.as_ref() {
            return Ok(v.clone());
        }
        // 文件缓存 7 天
        if let Ok(cached) = load_file_cache() {
            *g = Some(cached.clone());
            *FLAT_CACHE.lock().unwrap() = None;
            return Ok(cached);
        }
    }
    let list = fetcher::fetch_book_list()?;
    save_file_cache(&list);
    *g = Some(list.clone());
    *FLAT_CACHE.lock().unwrap() = None;
    Ok(list)
}

fn load_file_cache() -> Result<Value, String> {
    let meta_path = paths::cache_meta_file();
    let meta = std::fs::read_to_string(&meta_path).map_err(|_| "无缓存".to_string())?;
    let meta: Value = serde_json::from_str(&meta).map_err(|_| "缓存损坏".to_string())?;
    let saved = meta.get("saved_at").and_then(|v| v.as_i64()).ok_or("缓存损坏")?;
    let age = chrono::Utc::now().timestamp() - saved;
    if age > CACHE_EXPIRE_DAYS * 86400 {
        return Err("缓存过期".into());
    }
    let data = std::fs::read_to_string(paths::resource_list_file()).map_err(|_| "无缓存".to_string())?;
    serde_json::from_str(&data).map_err(|_| "缓存损坏".into())
}

fn save_file_cache(list: &Value) {
    let _ = std::fs::create_dir_all(paths::cache_dir());
    let _ = std::fs::write(paths::resource_list_file(), serde_json::to_string(list).unwrap_or_default());
    let meta = json!({"saved_at": chrono::Utc::now().timestamp()});
    let _ = std::fs::write(paths::cache_meta_file(), serde_json::to_string(&meta).unwrap_or_default());
}

pub fn clear_cache() {
    *RESOURCE_LIST.lock().unwrap() = None;
    *FLAT_CACHE.lock().unwrap() = None;
    let _ = std::fs::remove_file(paths::resource_list_file());
    let _ = std::fs::remove_file(paths::cache_meta_file());
}

pub fn cache_info() -> Value {
    let meta_path = paths::cache_meta_file();
    let saved_at = std::fs::read_to_string(&meta_path)
        .ok()
        .and_then(|s| serde_json::from_str::<Value>(&s).ok())
        .and_then(|v| v.get("saved_at").and_then(|x| x.as_i64()));
    json!({
        "exists": saved_at.is_some(),
        "saved_at": saved_at,
        "expire_days": CACHE_EXPIRE_DAYS,
    })
}

fn flat_resources() -> Vec<Value> {
    let mut fc = FLAT_CACHE.lock().unwrap();
    if let Some(v) = fc.as_ref() {
        return v.clone();
    }
    let list = RESOURCE_LIST.lock().unwrap().clone();
    let list = match list {
        Some(l) => l,
        None => return Vec::new(),
    };
    let mut out = Vec::new();
    flatten(&list, None, None, "", 0, &mut out);
    *fc = Some(out.clone());
    out
}

fn flatten(dict: &Value, subject: Option<&str>, grade: Option<&str>, publisher: &str, depth: usize, out: &mut Vec<Value>) {
    if depth >= 50 {
        return;
    }
    let obj = match dict.as_object() {
        Some(o) => o,
        None => return,
    };
    for (_key, value) in obj {
        let has_title = value.get("title").map(|v| v.is_string()).unwrap_or(false)
            || value.get("name").map(|v| v.is_string()).unwrap_or(false);
        let has_id = value.get("id").is_some();
        if has_title && has_id {
            let title = value.get("title").and_then(|v| v.as_str()).filter(|s| !s.is_empty())
                .or_else(|| value.get("name").and_then(|v| v.as_str()))
                .unwrap_or("");
            let id = value.get("id").and_then(|v| v.as_str()).unwrap_or("");
            let rtc = value.get("resource_type_code").and_then(|v| v.as_str()).unwrap_or("assets_document");
            out.push(json!({
                "id": id,
                "title": title,
                "subject": subject.unwrap_or(""),
                "grade": grade.unwrap_or(""),
                "publisher": publisher,
                "url": resource_url(id, rtc),
                "cover_url": crate::parser::extract_cover_url(value),
            }));
        } else if let Some(children) = value.get("children").and_then(|c| c.as_object()) {
            if children.is_empty() {
                continue;
            }
            let mut s = subject.map(|x| x.to_string());
            let mut g = grade.map(|x| x.to_string());
            let mut p = publisher.to_string();
            let dn = value.get("display_name").and_then(|v| v.as_str()).unwrap_or("");
            if !dn.is_empty() {
                if KNOWN_PUBLISHERS.contains(&dn) || dn.ends_with("版") {
                    p = dn.to_string();
                } else if s.is_none() && SUBJECT_WORDS.iter().any(|w| dn.contains(w)) {
                    s = Some(dn.to_string());
                } else if g.is_none() && GRADE_WORDS.iter().any(|w| dn.contains(w)) {
                    g = Some(dn.to_string());
                }
            }
            flatten(&Value::Object(children.clone()), s.as_deref(), g.as_deref(), &p, depth + 1, out);
        }
    }
}

pub fn flat_public() -> Vec<Value> {
    flat_resources()
}

pub fn search(keyword: &str) -> Value {
    if keyword.trim().is_empty() {
        return json!([]);
    }
    let mode = settings::get("search_mode").as_str().unwrap_or("approximate").to_string();
    let max = settings::get("search_max_results").as_u64().unwrap_or(100) as usize;
    let kw = keyword.trim().to_string();
    let kw_lower = kw.to_lowercase();
    let mut results = Vec::new();
    for r in flat_resources() {
        let title = r.get("title").and_then(|v| v.as_str()).unwrap_or("");
        let hay = format!(
            "{} {} {} {}",
            title,
            r.get("subject").and_then(|v| v.as_str()).unwrap_or(""),
            r.get("grade").and_then(|v| v.as_str()).unwrap_or(""),
            r.get("publisher").and_then(|v| v.as_str()).unwrap_or("")
        );
        let matched = match mode.as_str() {
            "exact" => title == kw,
            "fuzzy" => {
                let t = hay.to_lowercase();
                let mut it = kw_lower.chars().peekable();
                let mut ok = true;
                for c in t.chars() {
                    if it.peek() == Some(&c) {
                        it.next();
                    }
                }
                ok && it.peek().is_none()
            }
            // approximate
            _ => hay.to_lowercase().contains(&kw_lower),
        };
        if matched {
            results.push(r);
            if results.len() >= max {
                break;
            }
        }
    }
    json!(results)
}

pub fn suggestions(partial: &str, limit: usize) -> Value {
    if partial.trim().is_empty() {
        return json!([]);
    }
    let p = partial.trim().to_lowercase();
    let out: Vec<Value> = flat_resources()
        .into_iter()
        .filter(|r| {
            r.get("title").and_then(|v| v.as_str()).unwrap_or("").to_lowercase().contains(&p)
        })
        .take(limit)
        .map(|r| json!(r.get("title").and_then(|v| v.as_str()).unwrap_or("")))
        .collect();
    json!(out)
}

// ==================== 搜索历史 ====================

fn load_search_history() -> Vec<String> {
    std::fs::read_to_string(paths::search_history_file())
        .ok()
        .and_then(|s| serde_json::from_str::<Value>(&s).ok())
        .and_then(|v| v.get("history").and_then(|h| h.as_array()).cloned())
        .map(|a| a.into_iter().filter_map(|x| x.as_str().map(|s| s.to_string())).collect())
        .unwrap_or_default()
}

fn save_search_history(list: &[String]) {
    let _ = std::fs::create_dir_all(paths::cache_dir());
    let data = json!({"history": list, "updated_at": chrono::Utc::now().to_rfc3339()});
    let _ = std::fs::write(paths::search_history_file(), serde_json::to_string(&data).unwrap_or_default());
}

pub fn add_search_history(kw: &str) {
    let kw = kw.trim().to_string();
    if kw.is_empty() {
        return;
    }
    let mut list: Vec<String> = load_search_history().into_iter().filter(|k| k != &kw).collect();
    list.insert(0, kw);
    list.truncate(20);
    save_search_history(&list);
}

pub fn get_search_history() -> Value {
    json!(load_search_history())
}

pub fn clear_search_history() {
    save_search_history(&[]);
}

pub fn remove_search_history(kw: &str) {
    let list: Vec<String> = load_search_history().into_iter().filter(|k| k != kw).collect();
    save_search_history(&list);
}
