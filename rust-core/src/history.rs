// 下载历史记录：与 1.x 文件格式兼容
use crate::paths;
use serde_json::{json, Value};

pub fn load() -> Vec<Value> {
    std::fs::read_to_string(paths::download_history_file())
        .ok()
        .and_then(|s| serde_json::from_str::<Value>(&s).ok())
        .and_then(|v| v.get("records").and_then(|r| r.as_array()).cloned())
        .unwrap_or_default()
}

fn save(records: &[Value]) {
    let _ = std::fs::create_dir_all(paths::cache_dir());
    let data = json!({
        "records": records,
        "total_count": records.len(),
        "updated_at": chrono::Local::now().to_rfc3339(),
    });
    let _ = std::fs::write(paths::download_history_file(), serde_json::to_string_pretty(&data).unwrap_or_default());
}

pub fn add_record(resource_id: &str, title: &str, filename: &str, file_size: u64, save_path: &str, download_url: &str) {
    let mut records = load();
    let record = json!({
        "resource_id": resource_id,
        "title": title,
        "filename": filename,
        "file_size": file_size,
        "save_path": save_path,
        "download_url": download_url,
        "downloaded_at": chrono::Local::now().to_rfc3339(),
    });
    if let Some(i) = records.iter().position(|r| r.get("resource_id").and_then(|v| v.as_str()) == Some(resource_id)) {
        records[i] = record;
    } else {
        records.push(record);
    }
    save(&records);
}

pub fn is_downloaded(resource_id: &str) -> bool {
    let mut records = load();
    if let Some(i) = records.iter().position(|r| r.get("resource_id").and_then(|v| v.as_str()) == Some(resource_id)) {
        let path = records[i].get("save_path").and_then(|v| v.as_str()).unwrap_or("");
        if std::path::Path::new(path).exists() {
            return true;
        }
        records.remove(i);
        save(&records);
    }
    false
}

pub fn get_record(resource_id: &str) -> Option<Value> {
    load().into_iter().find(|r| r.get("resource_id").and_then(|v| v.as_str()) == Some(resource_id))
}

pub fn remove_record(resource_id: &str) {
    let records: Vec<Value> = load().into_iter().filter(|r| r.get("resource_id").and_then(|v| v.as_str()) != Some(resource_id)).collect();
    save(&records);
}

pub fn clear() {
    save(&[]);
}
