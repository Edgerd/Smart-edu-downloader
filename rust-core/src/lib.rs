#![recursion_limit = "512"]
// FFI 入口：单一 JSON 分发接口 sed_call(method, payload) -> JSON
mod crypto;
mod downloader;
mod fetcher;
mod history;
mod http;
mod logging;
mod naming;
 mod parser;
mod paths;
mod pdf;
mod resources;
mod settings;
mod urlfixer;

use serde_json::{json, Value};
use std::ffi::{CStr, CString};
use std::os::raw::{c_char};

fn dispatch(method: &str, payload: &Value) -> Value {
    match method {
        "init" => {
            let dir = payload.get("data_dir").and_then(|v| v.as_str()).unwrap_or("");
            if !dir.is_empty() {
                paths::init(dir);
            }
            http::init_from_settings();
            json!({"ok": true})
        }
        "version" => json!({"ok": true, "version": "1.0.0"}),

        // ---------- 设置 ----------
        "get_settings" => json!({"ok": true, "data": settings::get_all()}),
        "get_setting" => json!({"ok": true, "data": settings::get(payload.get("key").and_then(|v| v.as_str()).unwrap_or(""))}),
        "set_setting" => {
            let key = payload.get("key").and_then(|v| v.as_str()).unwrap_or("");
            let value = payload.get("value").cloned().unwrap_or(Value::Null);
            settings::set(key, value.clone());
            if key == "ssl_verify" {
                http::HTTP.set_ssl_verify(value.as_bool().unwrap_or(true));
            }
            json!({"ok": true})
        }
        "set_access_token" => {
            let raw = payload.get("token").and_then(|v| v.as_str()).unwrap_or("");
            http::HTTP.set_token(Some(raw.to_string()));
            // 自动保存（加密）
            if settings::get("auto_save_token").as_bool().unwrap_or(true) {
                if raw.is_empty() {
                    settings::set("access_token", json!(""));
                } else {
                    settings::set("access_token", json!(crypto::encrypt(raw)));
                }
            }
            json!({"ok": true})
        }
        "get_access_token" => json!({"ok": true, "data": http::HTTP.token()}),

        // ---------- 解析 ----------
        "parse_url" => {
            let url = payload.get("url").and_then(|v| v.as_str()).unwrap_or("");
            let bookmarks = payload.get("bookmarks").and_then(|v| v.as_bool()).unwrap_or(true);
            let r = parser::parse(url, bookmarks);
            serde_json::to_value(&r).unwrap_or(json!({"error": "解析失败"}))
        }
        "fix_url" => json!({"ok": true, "data": urlfixer::fix_url(payload.get("url").and_then(|v| v.as_str()).unwrap_or(""))}),
        "is_valid_url" => json!({"ok": true, "data": urlfixer::is_valid_smartedu_url(payload.get("url").and_then(|v| v.as_str()).unwrap_or(""))}),

        // ---------- 资源库 ----------
        "fetch_resource_list" => {
            let force = payload.get("force_refresh").and_then(|v| v.as_bool()).unwrap_or(false);
            match resources::get_resource_list(force) {
                Ok(v) => json!({"ok": true, "data": v}),
                Err(e) => json!({"ok": false, "error": e}),
            }
        }
        "search" => {
            let kw = payload.get("keyword").and_then(|v| v.as_str()).unwrap_or("");
            resources::add_search_history(kw);
            json!({"ok": true, "data": resources::search(kw)})
        }
        "get_flat_resources" => {
            let _ = resources::get_resource_list(false);
            json!({"ok": true, "data": resources::flat_public()})
        }
        "search_only" => {
            let kw = payload.get("keyword").and_then(|v| v.as_str()).unwrap_or("");
            json!({"ok": true, "data": resources::search(kw)})
        }
        "suggest" => {
            let kw = payload.get("keyword").and_then(|v| v.as_str()).unwrap_or("");
            let limit = payload.get("limit").and_then(|v| v.as_u64()).unwrap_or(10) as usize;
            json!({"ok": true, "data": resources::suggestions(kw, limit)})
        }
        "clear_cache" => {
            resources::clear_cache();
            json!({"ok": true})
        }
        "cache_info" => json!({"ok": true, "data": resources::cache_info()}),

        // 搜索历史
        "get_search_history" => json!({"ok": true, "data": resources::get_search_history()}),
        "clear_search_history" => {
            resources::clear_search_history();
            json!({"ok": true})
        }
        "remove_search_history" => {
            let kw = payload.get("keyword").and_then(|v| v.as_str()).unwrap_or("");
            resources::remove_search_history(kw);
            json!({"ok": true})
        }

        // ---------- 下载 ----------
        "add_task" => {
            let url = payload.get("url").and_then(|v| v.as_str()).unwrap_or("");
            let title = payload.get("title").and_then(|v| v.as_str());
            let chapters = payload.get("chapters").cloned().unwrap_or(json!([]));
            let save_path = payload.get("save_path").and_then(|v| v.as_str());
            match downloader::add_task(url, title, chapters, save_path) {
                Ok(id) => json!({"ok": true, "data": id}),
                Err(e) => json!({"ok": false, "error": e}),
            }
        }
        "get_tasks" => json!({"ok": true, "data": downloader::get_all_tasks()}),
        "pause_task" => {
            downloader::pause_task(payload.get("task_id").and_then(|v| v.as_str()).unwrap_or(""));
            json!({"ok": true})
        }
        "cancel_task" => {
            downloader::cancel_task(payload.get("task_id").and_then(|v| v.as_str()).unwrap_or(""));
            json!({"ok": true})
        }
        "remove_task" => {
            downloader::remove_task(payload.get("task_id").and_then(|v| v.as_str()).unwrap_or(""));
            json!({"ok": true})
        }
        "retry_task" => {
            downloader::retry_task(payload.get("task_id").and_then(|v| v.as_str()).unwrap_or(""));
            json!({"ok": true})
        }
        "clear_all_tasks" => {
            downloader::clear_all_tasks();
            json!({"ok": true})
        }

        // ---------- 下载历史 ----------
        "get_history" => json!({"ok": true, "data": history::load()}),
        "is_downloaded" => json!({"ok": true, "data": history::is_downloaded(payload.get("resource_id").and_then(|v| v.as_str()).unwrap_or(""))}),
        "remove_history" => {
            history::remove_record(payload.get("resource_id").and_then(|v| v.as_str()).unwrap_or(""));
            json!({"ok": true})
        }
        "clear_history" => {
            history::clear();
            json!({"ok": true})
        }

        // ---------- 其他 ----------
        "get_logs" => {
            let n = payload.get("count").and_then(|v| v.as_u64()).unwrap_or(200) as usize;
            json!({"ok": true, "data": logging::last_logs(n)})
        }
        "builtin_domains" => json!({"ok": true, "data": downloader::BUILTIN_ALLOWED_DOMAINS}),
        "clear_logs" => {
            let _ = std::fs::remove_file(paths::logs_dir().join("sed.log"));
            json!({"ok": true})
        }

        _ => json!({"ok": false, "error": format!("未知方法: {}", method)}),
    }
}

#[no_mangle]
pub extern "C" fn sed_version() -> *mut c_char {
    to_ptr(json!({"version": "1.0.0"}).to_string())
}

#[no_mangle]
pub extern "C" fn sed_call(method: *const c_char, payload: *const c_char) -> *mut c_char {
    let method = unsafe { cstr(method) };
    let payload_str = unsafe { cstr(payload) };
    let payload: Value = serde_json::from_str(&payload_str).unwrap_or(json!({}));
    let result = dispatch(&method, &payload);
    to_ptr(result.to_string())
}

#[no_mangle]
pub extern "C" fn sed_free(ptr: *mut c_char) {
    if !ptr.is_null() {
        unsafe { drop(CString::from_raw(ptr)) };
    }
}

unsafe fn cstr(p: *const c_char) -> String {
    if p.is_null() {
        return String::new();
    }
    CStr::from_ptr(p).to_string_lossy().into_owned()
}

fn to_ptr(s: String) -> *mut c_char {
    CString::new(s).unwrap_or_else(|_| CString::new("{}").unwrap()).into_raw()
}
