// 资源获取：详情 API、课本列表、专题课程、书签
use crate::http::HTTP;
use serde_json::{json, Value};
use std::collections::BTreeMap;

pub fn fetch_json(url: &str) -> Result<Value, String> {
    let resp = HTTP
        .get(url)
        .map_err(|e| format!("网络错误: {}", e))?;
    let status = resp.status().as_u16();
    if status != 200 {
        return Err(format!("HTTP {}", status));
    }
    resp.json::<Value>().map_err(|e| format!("JSON 解析失败: {}", e))
}

pub fn fetch_resource_data(content_id: &str, content_type: &str, url: &str) -> Option<Value> {
    let api_url = if url.starts_with("https://") || url.starts_with("http://") {
        // 与 1.x 相同的 basicWork 判定
        if url.contains("/syncClassroom/basicWork/detail") {
            format!("https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/special_edu/resources/details/{}.json", content_id)
        } else {
            String::new()
        }
    } else {
        String::new()
    };
    let api_url = if !api_url.is_empty() {
        api_url
    } else if content_type == "thematic_course" {
        format!("https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/special_edu/resources/details/{}.json", content_id)
    } else {
        format!("https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/resources/tch_material/details/{}.json", content_id)
    };
    crate::logging::log("STEP", &format!("请求API: {}", api_url));
    match fetch_json(&api_url) {
        Ok(v) => Some(v),
        Err(e) => {
            crate::logging::log("WARNING", &format!("详情API请求失败: {}，尝试从资源列表获取", e));
            fetch_resource_data_from_list(content_id)
        }
    }
}

pub fn fetch_resource_data_from_list(content_id: &str) -> Option<Value> {
    crate::logging::log("STEP", &format!("从资源列表查找: {}", content_id));
    let version_url = "https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/resources/tch_material/version/data_version.json";
    let urls = fetch_json(version_url).ok()?;
    let list_urls: Vec<String> = urls
        .get("urls")
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .split(',')
        .map(|s| s.to_string())
        .filter(|s| !s.is_empty())
        .collect();
    for lu in list_urls {
        if let Ok(books) = fetch_json(&lu) {
            if let Some(arr) = books.as_array() {
                for book in arr {
                    if book.get("id").and_then(|v| v.as_str()) == Some(content_id) {
                        return Some(book.clone());
                    }
                }
            }
        }
    }
    None
}

pub fn fetch_thematic_course_resources(content_id: &str) -> Option<Value> {
    let url = format!("https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/special_edu/thematic_course/{}/resources/list.json", content_id);
    fetch_json(&url).ok()
}

pub fn fetch_mapping_data(mapping_url: &str) -> Option<Value> {
    fetch_json(mapping_url).ok()
}

pub fn fetch_tree_data(ebook_id: &str) -> Option<Value> {
    let url = format!("https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/trees/{}.json", ebook_id);
    fetch_json(&url).ok()
}

pub fn parse_hierarchy(hierarchy: &Value, depth: usize) -> BTreeMap<String, Value> {
    let mut parsed = BTreeMap::new();
    if depth >= 50 || !hierarchy.is_array() {
        return parsed;
    }
    if let Some(arr) = hierarchy.as_array() {
        for h in arr {
            if let Some(children) = h.get("children").and_then(|c| c.as_array()) {
                for ch in children {
                    let tag_id = ch.get("tag_id").and_then(|v| v.as_str()).unwrap_or("").to_string();
                    if tag_id.is_empty() {
                        continue;
                    }
                    let sub = parse_hierarchy(ch.get("hierarchies").unwrap_or(&Value::Null), depth + 1);
                    parsed.insert(
                        tag_id,
                        json!({
                            "display_name": ch.get("tag_name").and_then(|v| v.as_str()).unwrap_or(""),
                            "children": sub,
                        }),
                    );
                }
            }
        }
    }
    parsed
}

pub fn fetch_book_list() -> Result<Value, String> {
    let tags = fetch_json("https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/tags/tch_material_tag.json")?;
    let hier = tags.get("hierarchies").cloned().unwrap_or(Value::Null);
    let mut parsed: BTreeMap<String, Value> = parse_hierarchy(&hier, 0);
    let version = fetch_json("https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/resources/tch_material/version/data_version.json")?;
    let list_urls: Vec<String> = version
        .get("urls")
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .split(',')
        .map(|s| s.to_string())
        .filter(|s| !s.is_empty())
        .collect();
    for lu in list_urls {
        let books = match fetch_json(&lu) {
            Ok(v) => v,
            Err(e) => {
                crate::logging::log("ERROR", &format!("获取书籍数据失败 ({}): {}", lu, e));
                continue;
            }
        };
        if let Some(arr) = books.as_array() {
            for book in arr {
                if book.get("tag_paths").and_then(|v| v.as_array()).is_none() {
                    continue;
                }
                let tag_path = book["tag_paths"][0].as_str().unwrap_or("");
                let parts: Vec<&str> = tag_path.split('/').collect();
                if parts.len() < 2 {
                    continue;
                }
                let tag_paths = &parts[2..];
                if tag_paths.is_empty() {
                    continue;
                }
                // 顶层 key 可能带或不带前缀，与 1.x 一致用 parts[1]
                let root = match parsed.get_mut(parts[1]) {
                    Some(h) => h,
                    None => continue,
                };
                let _ = root;
                // 挂载 book（attach_book 会沿路径定位并校验第一层存在）
                attach_book(&mut parsed, parts[1], tag_paths, book);
            }
        }
    }
    Ok(serde_json::to_value(&parsed).unwrap())
}

fn attach_book(root: &mut BTreeMap<String, Value>, top: &str, tag_paths: &[&str], book: &Value) {
    let mut cur = match root.get_mut(top) {
        Some(v) => v,
        None => return,
    };
    for p in tag_paths {
        if !cur.get("children").map(|c| c.get(p).map(|v| !v.is_null()).unwrap_or(false)).unwrap_or(false) {
            return;
        }
        cur = cur.get_mut("children").unwrap().get_mut(p).unwrap();
    }
    if cur.get("children").is_none() {
        cur["children"] = json!({});
    }
    let mut b = book.clone();
    let display = b
        .get("title")
        .and_then(|v| v.as_str())
        .filter(|s| !s.is_empty())
        .or_else(|| b.get("name").and_then(|v| v.as_str()))
        .map(|s| s.to_string())
        .unwrap_or_else(|| format!("(未知电子课本 {})", b.get("id").and_then(|v| v.as_str()).unwrap_or("?")));
    b["display_name"] = json!(display);
    if b.get("resource_type_code").is_none() {
        b["resource_type_code"] = json!("assets_document");
    }
    cur["children"]
        .as_object_mut()
        .unwrap()
        .insert(b.get("id").and_then(|v| v.as_str()).unwrap_or("").to_string(), b);
}
