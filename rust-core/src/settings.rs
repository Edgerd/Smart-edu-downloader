// 设置存储：JSON 文件，键名与 1.x 保持一致
use crate::paths;
use once_cell::sync::Lazy;
use serde_json::{json, Map, Value};
use std::collections::BTreeMap;
use std::sync::Mutex;

fn defaults() -> Value {
    json!({
        "show_tips_switch": true,
        "launch_count": 0,
        "auto_recover_tasks": true,
        "minimize_to_tray": false,
        "tray_notifications": false,
        "tray_show_progress": false,
        "sound_enabled": true,
        "download_complete_sound": true,
        "show_startup_time": false,
        "auto_clean_temp": true,
        "download_dir": "",
        "ask_download_dir": false,
        "open_folder_after_download": false,
        "max_concurrent_downloads": 5,
        "download_threads": 10,
        "speed_limit": 0,
        "retry_count": 3,
        "retry_interval": 5,
        "connect_timeout": 30,
        "read_timeout": 60,
        "auto_rename_duplicates": true,
        "file_naming_rule": "default",
        "include_chapter_info": false,
        "include_timestamp": false,
        "auto_categorize": false,
        "categorize_rule": "by_subject",
        "resume_download": true,
        "resume_threshold": 10,
        "auto_delete_failed": false,
        "auto_verify": false,
        "retry_on_verify_fail": false,
        "language": "zh_CN",
        "theme_mode": "system",
        "theme_seed_color": "#1277DD",
        "dynamic_color": false,
        "first_run": true,
        "proxy_enabled": false,
        "proxy_type": "http",
        "proxy_host": "",
        "proxy_port": "",
        "proxy_username": "",
        "proxy_password": "",
        "ssl_verify": true,
        "cache_enabled": true,
        "cache_size_limit": 500,
        "log_retention_days": 7,
        "api_timeout": 30,
        "api_retry_count": 3,
        "log_level": "INFO",
        "debug_mode": true,
        "auto_export_config": false,
        "access_token": "",
        "auto_save_token": true,
        "history_retention": "7d",
        "auto_clear_history": true,
        "privacy_protection": false,
        "safe_download_mode": false,
        "allow_any_domain_download": true,
        "confirm_non_whitelist_download": true,
        "custom_allowed_domains": [],
        "search_mode": "approximate",
        "search_suggestions_enabled": true,
        "search_max_results": 100,
        "search_smart_repair": true,
        "clipboard_monitor_enabled": true
    })
}

static STORE: Lazy<Mutex<Option<BTreeMap<String, Value>>>> = Lazy::new(|| Mutex::new(None));

fn load() -> BTreeMap<String, Value> {
    let mut g = STORE.lock().unwrap();
    if g.is_none() {
        let mut map: BTreeMap<String, Value> = defaults()
            .as_object()
            .unwrap()
            .iter()
            .map(|(k, v)| (k.clone(), v.clone()))
            .collect();
        if let Ok(text) = std::fs::read_to_string(paths::settings_file()) {
            if let Ok(Value::Object(saved)) = serde_json::from_str::<Value>(&text) {
                for (k, v) in saved {
                    map.insert(k, v);
                }
            }
        }
        *g = Some(map);
    }
    g.as_ref().unwrap().clone()
}

fn save(map: &BTreeMap<String, Value>) {
    let obj: Map<String, Value> = map.iter().map(|(k, v)| (k.clone(), v.clone())).collect();
    let path = paths::settings_file();
    let _ = std::fs::create_dir_all(path.parent().unwrap());
    if let Ok(text) = serde_json::to_string_pretty(&Value::Object(obj)) {
        let _ = std::fs::write(path, text);
    }
}

pub fn get_all() -> Value {
    let map = load();
    let mut obj = Map::new();
    for (k, v) in map {
        // download_dir 为空时返回默认值
        obj.insert(k.clone(), v.clone());
    }
    let dd = obj.get("download_dir").and_then(|v| v.as_str()).unwrap_or("");
    if dd.is_empty() {
        obj.insert("download_dir".into(), Value::String(paths::download_dir()));
    }
    Value::Object(obj)
}

pub fn get(key: &str) -> Value {
    let map = load();
    map.get(key).cloned().unwrap_or(Value::Null)
}

pub fn set(key: &str, value: Value) {
    let mut g = STORE.lock().unwrap();
    let map = g.get_or_insert_with(load);
    map.insert(key.to_string(), value.clone());
    save(map);
    if key == "download_dir" {
        if let Some(s) = value.as_str() {
            paths::set_download_dir(s);
        }
    }
}
