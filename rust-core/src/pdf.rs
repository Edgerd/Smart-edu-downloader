// PDF 书签与校验（lopdf）
use lopdf::{Dictionary, Object, ObjectId, StringFormat};
use serde_json::Value;
use std::collections::BTreeMap;

fn title_obj(title: &str) -> Object {
    Object::String(title.as_bytes().to_vec(), StringFormat::Literal)
}

pub fn add_bookmarks(pdf_path: &str, chapters: &Value) -> Result<(), String> {
    let chapters = match chapters.as_array() {
        Some(a) if !a.is_empty() => a,
        _ => {
            crate::logging::log("INFO", "书签章节列表为空，跳过添加");
            return Ok(());
        }
    };
    let mut doc = lopdf::Document::load(pdf_path).map_err(|e| format!("打开PDF失败: {}", e))?;
    let page_count = doc.get_pages().len() as i64;
    let mut toc: Vec<(i64, String, i64)> = Vec::new();
    build_toc(chapters, 1, page_count, &mut toc);
    if toc.is_empty() {
        crate::logging::log("WARNING", "没有有效的书签条目可添加");
        return Ok(());
    }
    set_outline(&mut doc, &toc)?;
    doc.save(pdf_path).map_err(|e| format!("保存PDF失败: {}", e))?;
    crate::logging::log("SUCCESS", &format!("已添加 {} 个书签到 PDF", toc.len()));
    Ok(())
}

fn build_toc(chapters: &[Value], level: i64, page_count: i64, toc: &mut Vec<(i64, String, i64)>) {
    if level > 20 {
        return;
    }
    for ch in chapters {
        let title = ch.get("title").and_then(|v| v.as_str()).unwrap_or("未命名").to_string();
        let page = ch.get("page_index").and_then(|v| v.as_i64());
        if let Some(p) = page {
            if p >= 1 && p <= page_count {
                toc.push((level, title, p));
            } else {
                crate::logging::log("WARNING", &format!("章节 \"{}\" 页码 {} 超出范围", title, p));
            }
        }
        if let Some(children) = ch.get("children").and_then(|v| v.as_array()) {
            build_toc(children, level + 1, page_count, toc);
        }
    }
}

// 构建 PDF outline（书签树）
fn set_outline(doc: &mut lopdf::Document, toc: &[(i64, String, i64)]) -> Result<(), String> {
    // 页对象号映射：按文档顺序
    let pages: Vec<ObjectId> = doc.get_pages().values().copied().collect();

    struct Item {
        level: i64,
        title: String,
        page_ref: ObjectId,
        parent: ObjectId,
        id: ObjectId,
    }
    // 根 outline
    let outlines_id = doc.add_object(Object::Dictionary(Dictionary::from_iter([(
        b"Type".to_vec(),
        Object::Name("Outlines".into()),
    )])));
    let mut items: Vec<Item> = Vec::new();
    let mut stack: Vec<(i64, ObjectId)> = Vec::new(); // (level, outline_id)
    stack.push((0, outlines_id));

    for (level, title, page) in toc.iter() {
        while stack.len() > 1 && stack.last().unwrap().0 >= *level {
            stack.pop();
        }
        let parent = stack.last().unwrap().1;
        let page_ref = pages.get((*page - 1) as usize).copied().ok_or("页码越界")?;
        let d = Dictionary::from_iter([
            (b"Title".to_vec(), title_obj(title)),
            (b"Parent".to_vec(), Object::Reference(parent)),
            (
                b"Dest".to_vec(),
                Object::Array(vec![
                    Object::Reference(page_ref),
                    Object::Name("XYZ".into()),
                    Object::Null,
                    Object::Null,
                    Object::Null,
                ]),
            ),
        ]);
        let id = doc.add_object(Object::Dictionary(d));
        items.push(Item {
            level: *level,
            title: title.clone(),
            page_ref,
            parent,
            id,
        });
        stack.push((*level, id));
    }

    // 互相写 Prev/Next/First/Last/Count
    let children_map: BTreeMap<ObjectId, Vec<ObjectId>> = {
        let mut m: BTreeMap<ObjectId, Vec<ObjectId>> = BTreeMap::new();
        for it in &items {
            m.entry(it.parent).or_default().push(it.id);
        }
        m
    };
    for it in &items {
        let siblings = &children_map[&it.parent];
        let pos = siblings.iter().position(|x| *x == it.id).unwrap();
        let mut d = Dictionary::from_iter([
            (b"Title".to_vec(), title_obj(&it.title)),
            (b"Parent".to_vec(), Object::Reference(it.parent)),
            (
                b"Dest".to_vec(),
                Object::Array(vec![
                    Object::Reference(it.page_ref),
                    Object::Name("XYZ".into()),
                    Object::Null,
                    Object::Null,
                    Object::Null,
                ]),
            ),
        ]);
        if let Some(next) = siblings.get(pos + 1) {
            d.set("Next", Object::Reference(*next));
        }
        if pos > 0 {
            d.set("Prev", Object::Reference(siblings[pos - 1]));
        }
        if children_map.contains_key(&it.id) {
            let kids = &children_map[&it.id];
            d.set("First", Object::Reference(kids[0]));
            d.set("Last", Object::Reference(*kids.last().unwrap()));
            d.set("Count", Object::Integer(count_descendants(&children_map, it.id)));
        }
        doc.set_object(it.id, Object::Dictionary(d));
    }
    // 根 outlines
    let top: Vec<ObjectId> = children_map.get(&outlines_id).cloned().unwrap_or_default();
    let mut root = Dictionary::from_iter([(b"Type".to_vec(), Object::Name("Outlines".into()))]);
    if !top.is_empty() {
        root.set("First", Object::Reference(top[0]));
        root.set("Last", Object::Reference(*top.last().unwrap()));
        root.set("Count", Object::Integer(count_descendants(&children_map, outlines_id)));
    }
    doc.set_object(outlines_id, Object::Dictionary(root));

    // Catalog 挂载
    let root_ref = doc
        .trailer
        .get(b"Root")
        .ok()
        .and_then(|o| match o {
            Object::Reference(r) => Some(*r),
            _ => None,
        });
    if let Some(cid) = root_ref {
        if let Ok(mut catalog) = doc.get_object_mut(cid) {
            if let Object::Dictionary(d) = &mut *catalog {
                d.set("Outlines", Object::Reference(outlines_id));
            }
        }
    }
    Ok(())
}

fn count_descendants(map: &BTreeMap<lopdf::ObjectId, Vec<lopdf::ObjectId>>, id: lopdf::ObjectId) -> i64 {
    let mut total = 0i64;
    if let Some(kids) = map.get(&id) {
        for k in kids {
            total += 1 + count_descendants(map, *k);
        }
    }
    total
}

pub fn verify_pdf(path: &str) -> Result<bool, String> {
    match lopdf::Document::load(path) {
        Ok(doc) => {
            let pages = doc.get_pages().len();
            Ok(pages > 0)
        }
        Err(_) => Ok(false),
    }
}
