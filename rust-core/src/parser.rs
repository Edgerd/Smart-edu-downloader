// 资源解析：URL -> (resource_url, title, chapters, cover_url)
use crate::fetcher;
use crate::http::HTTP;
use crate::urlfixer;
use serde_json::{json, Value};

#[derive(Default, Clone, serde::Serialize)]
pub struct ParseResult {
    pub resource_url: Option<String>,
    pub title: Option<String>,
    pub chapters: Value,
    pub cover_url: Option<String>,
    pub error: Option<String>,
}

pub fn parse(url: &str, bookmarks: bool) -> ParseResult {
    let mut res = ParseResult::default();
    let url = urlfixer::fix_url(url);
    let content_id = match urlfixer::extract_content_id(&url) {
        Some(c) => c,
        None => {
            res.error = Some("未找到 contentId 参数".into());
            return res;
        }
    };
    let content_type = urlfixer::extract_content_type(&url);
    crate::logging::log("DEBUG", &format!("contentId: {}, contentType: {}", content_id, content_type));
    let data = match fetcher::fetch_resource_data(&content_id, &content_type, &url) {
        Some(d) => d,
        None => {
            res.error = Some("获取资源详情失败".into());
            return res;
        }
    };
    res.title = data.get("title").and_then(|v| v.as_str()).map(|s| s.to_string());
    res.cover_url = extract_cover_url(&data);
    let ti_items = data.get("ti_items").and_then(|v| v.as_array()).cloned().unwrap_or_default();
    let token = HTTP.token();
    match extract_resource_url(&ti_items, token.as_deref()) {
        Some(ru) => res.resource_url = Some(ru),
        None => {
            if content_type == "thematic_course" {
                if let Some(resources) = fetcher::fetch_thematic_course_resources(&content_id) {
                    if let Some(arr) = resources.as_array() {
                        for resource in arr {
                            if resource.get("resource_type_code").and_then(|v| v.as_str()) == Some("assets_document") {
                                let items = resource.get("ti_items").and_then(|v| v.as_array()).cloned().unwrap_or_default();
                                if let Some(ru) = extract_resource_url(&items, token.as_deref()) {
                                    res.resource_url = Some(ru);
                                    break;
                                }
                            }
                        }
                    }
                }
            }
            if res.resource_url.is_none() {
                res.error = Some("未找到资源下载链接".into());
                return res;
            }
        }
    }
    if bookmarks {
        res.chapters = extract_chapters(&data);
    }
    res
}

pub fn extract_resource_url(ti_items: &[Value], token: Option<&str>) -> Option<String> {
    for item in ti_items {
        if item.get("ti_is_source_file").and_then(|v| v.as_bool()).unwrap_or(false) {
            if let Some(storage) = item.get("ti_storage").and_then(|v| v.as_str()) {
                let base = if token.is_some() {
                    "https://r1-ndr-private.ykt.cbern.com.cn"
                } else {
                    "https://c1.ykt.cbern.com.cn"
                };
                return Some(storage.replace("cs_path:${ref-path}", base));
            }
            for u in item.get("ti_storages").and_then(|v| v.as_array()).cloned().unwrap_or_default() {
                let s = match u.as_str() {
                    Some(s) if !s.is_empty() => s.to_string(),
                    _ => continue,
                };
                if token.is_none() {
                    // 无 token 时替换为公共 CDN
                    if let Ok(re) = regex::Regex::new(r"^https?://[^/]*ykt\.cbern\.com\.cn/(.+)$") {
                        if let Some(c) = re.captures(&s) {
                            return Some(format!("https://c1.ykt.cbern.com.cn/{}", &c[1]));
                        }
                    }
                }
                return Some(s);
            }
        }
    }
    None
}

pub fn extract_cover_url(data: &Value) -> Option<String> {
    if let Some(slide1) = data
        .get("custom_properties")
        .and_then(|c| c.get("preview"))
        .and_then(|p| p.get("Slide1"))
        .and_then(|v| v.as_str())
    {
        return Some(slide1.to_string());
    }
    if let Some(items) = data.get("ti_items").and_then(|v| v.as_array()) {
        for item in items {
            if item.get("ti_file_flag").and_then(|v| v.as_str()) == Some("cover") {
                if let Some(s) = item.get("ti_storage").and_then(|v| v.as_str()) {
                    return Some(s.to_string());
                }
                for u in item.get("ti_storages").and_then(|v| v.as_array()).cloned().unwrap_or_default() {
                    if let Some(s) = u.as_str() {
                        if !s.is_empty() {
                            return Some(s.to_string());
                        }
                    }
                }
            }
        }
    }
    None
}

pub fn extract_chapters(data: &Value) -> Value {
    crate::logging::log("STEP", "开始获取书签信息...");
    let ti_items = data.get("ti_items").and_then(|v| v.as_array()).cloned().unwrap_or_default();
    let mut mapping_url: Option<String> = None;
    for item in &ti_items {
        if item.get("ti_file_flag").and_then(|v| v.as_str()) == Some("ebook_mapping") {
            if let Some(s) = item.get("ti_storage").and_then(|v| v.as_str()) {
                mapping_url = Some(s.replace("cs_path:${ref-path}", "https://r1-ndr-private.ykt.cbern.com.cn"));
            } else {
                for u in item.get("ti_storages").and_then(|v| v.as_array()).cloned().unwrap_or_default() {
                    if let Some(s) = u.as_str() {
                        if !s.is_empty() {
                            mapping_url = Some(s.to_string());
                            break;
                        }
                    }
                }
            }
            break;
        }
    }
    let map_data = match mapping_url.and_then(|u| fetcher::fetch_mapping_data(&u)) {
        Some(m) => m,
        None => return json!([]),
    };
    let ebook_id = map_data.get("ebook_id").and_then(|v| v.as_str()).map(|s| s.to_string());
    let mut page_map: Vec<(String, i64)> = Vec::new();
    if let Some(mappings) = map_data.get("mappings").and_then(|v| v.as_array()) {
        for m in mappings {
            let node = m.get("node_id").and_then(|v| v.as_str()).unwrap_or("").to_string();
            let page = m.get("page_number").and_then(|v| v.as_i64()).unwrap_or(1);
            if !node.is_empty() {
                page_map.push((node, page));
            }
        }
    }
    let mut chapters = json!([]);
    if let Some(eid) = ebook_id {
        if let Some(tree) = fetcher::fetch_tree_data(&eid) {
            let nodes: Vec<Value> = if tree.is_array() {
                tree.as_array().unwrap().clone()
            } else if let Some(c) = tree.get("child_nodes").and_then(|v| v.as_array()) {
                c.clone()
            } else {
                Vec::new()
            };
            chapters = process_tree(&nodes, &page_map, 0);
        }
    }
    if chapters.as_array().map(|a| a.is_empty()).unwrap_or(true) {
        // 备选：页码映射
        page_map.sort_by_key(|(_, p)| *p);
        let arr: Vec<Value> = page_map
            .iter()
            .enumerate()
            .map(|(i, (_, p))| json!({"title": format!("第 {} 节 (P{})", i + 1, p), "page_index": p}))
            .collect();
        chapters = json!(arr);
    }
    chapters
}

fn process_tree(nodes: &[Value], page_map: &[(String, i64)], depth: usize) -> Value {
    if depth >= 50 {
        return json!([]);
    }
    let result: Vec<Value> = nodes
        .iter()
        .map(|node| {
            let id = node.get("id").and_then(|v| v.as_str()).unwrap_or("");
            let page = page_map.iter().find(|(n, _)| n == id).map(|(_, p)| *p);
            let mut item = json!({
                "title": node.get("title").and_then(|v| v.as_str()).unwrap_or(""),
                "page_index": page,
            });
            if let Some(children) = node.get("child_nodes").and_then(|v| v.as_array()) {
                item["children"] = process_tree(children, page_map, depth + 1);
            }
            item
        })
        .collect();
    json!(result)
}
