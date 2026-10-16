// URL 修复与解析：与 1.x URLFixer 保持一致
use regex::Regex;
use once_cell::sync::Lazy;

pub const SUPPORTED_DOMAINS: &[&str] = &[
    "basic.smartedu.cn",
    "www.smartedu.cn",
    "smartedu.cn",
    "s-file-1.ykt.cbern.com.cn",
    "r1-ndr-private.ykt.cbern.com.cn",
    "c1.ykt.cbern.com.cn",
];

static P_CONTENT_ID: Lazy<Vec<Regex>> = Lazy::new(|| {
    vec![
        Regex::new(r"contentId=([a-f0-9\-]{36})").unwrap(),
        Regex::new(r"contentId=([a-zA-Z0-9\-]+)").unwrap(),
        Regex::new(r"/([a-f0-9\-]{36})").unwrap(),
        Regex::new(r"id=([a-f0-9\-]{36})").unwrap(),
        Regex::new(r"resourceId=([a-f0-9\-]{36})").unwrap(),
    ]
});
static P_CONTENT_TYPE: Lazy<Vec<Regex>> = Lazy::new(|| {
    vec![
        Regex::new(r"contentType=([a-zA-Z_]+)").unwrap(),
        Regex::new(r"type=([a-zA-Z_]+)").unwrap(),
    ]
});

pub fn fix_url(url: &str) -> String {
    if url.is_empty() {
        return url.to_string();
    }
    let mut u = url.trim().to_string();
    while u.contains("//") && !u.contains("://") {
        u = u.replace("//", "/");
    }
    if u.contains("://") {
        let p = u.find("://").unwrap() + 3;
        let rest = u[p..].replace("//", "/");
        u = format!("{}{}", &u[..p], rest);
    }
    u = u.replace(' ', "").replace('\n', "").replace('\r', "").replace('\t', "");
    if !u.starts_with("http://") && !u.starts_with("https://") {
        u = format!("https://{}", u);
    }
    if u.starts_with("http://") {
        u = format!("https://{}", &u[7..]);
    }
    // 域名归一
    if let Some(rest_start) = u.find("://").map(|i| i + 3) {
        let rest = &u[rest_start..];
        let host_end = rest.find('/').unwrap_or(rest.len());
        let mut host = rest[..host_end].to_lowercase();
        let path_query = &rest[host_end..];
        if host.starts_with("www.") {
            host = host[4..].to_string();
        }
        let mapping: &[(&str, &str)] = &[("smart-edu.cn", "smartedu.cn"), ("edu.cn", "basic.smartedu.cn")];
        for (old, new) in mapping {
            if host.ends_with(old) && !host.ends_with(new) {
                host = host.replace(old, new);
                break;
            }
        }
        u = format!("https://{}{}", host, path_query);
    }
    // 特殊格式处理
    if !(u.contains("s-file-1.ykt.cbern.com.cn") && u.contains("/edu_product/")) {
        if !u.contains("contentId") && u.contains("tchMaterial/detail") {
            if let Some(m) = Regex::new(r"/([a-f0-9\-]{36})(?:[/?]|$)").unwrap().find(&u) {
                let cid = m.as_str().trim_start_matches('/').trim_end_matches(['/', '?']).to_string();
                if u.contains('?') {
                    let (base, q) = u.split_once('?').unwrap();
                    u = format!("{}?contentId={}&{}", base, cid, q);
                } else {
                    u = format!("{}?contentId={}", u, cid);
                }
            }
        }
        if u.contains("/zxx/ndrv2/resources/tch_material/details/") {
            if let Some(m) = Regex::new(r"/details/([a-f0-9\-]{36})").unwrap().find(&u) {
                let cid = &m.as_str()["/details/".len()..];
                u = format!(
                    "https://basic.smartedu.cn/tchMaterial/detail?contentId={}&catalogType=tchMaterial&subCatalog=tchMaterial",
                    cid
                );
            }
        }
    }
    if (u.contains("thematic_course") || u.contains("contentType=thematic_course")) && !u.contains("contentType") {
        u = if u.contains('?') { format!("{}&contentType=thematic_course", u) } else { format!("{}?contentType=thematic_course", u) };
    }
    if u.contains("syncClassroom/basicWork") && !u.contains("contentType") {
        u = if u.contains('?') { format!("{}&contentType=basic_work", u) } else { format!("{}?contentType=basic_work", u) };
    }
    if u.contains("tchMaterial/detail") {
        if !u.contains("catalogType") {
            u = if u.contains('?') { format!("{}&catalogType=tchMaterial", u) } else { format!("{}?catalogType=tchMaterial", u) };
        }
        if !u.contains("subCatalog") {
            u = format!("{}&subCatalog=tchMaterial", u);
        }
    }
    u
}

pub fn extract_content_id(url: &str) -> Option<String> {
    for re in P_CONTENT_ID.iter() {
        if let Some(m) = re.captures(url) {
            return Some(m[1].to_string());
        }
    }
    // query 兜底
    if let Some(qi) = url.find('?') {
        for pair in url[qi + 1..].split('&') {
            let mut it = pair.splitn(2, '=');
            if it.next() == Some("contentId") {
                if let Some(v) = it.next() {
                    return Some(v.to_string());
                }
            }
        }
    }
    None
}

pub fn extract_content_type(url: &str) -> String {
    for re in P_CONTENT_TYPE.iter() {
        if let Some(m) = re.captures(url) {
            return m[1].to_string();
        }
    }
    if url.contains("thematic_course") {
        return "thematic_course".into();
    }
    if url.contains("syncClassroom/basicWork") {
        return "basic_work".into();
    }
    "assets_document".into()
}

pub fn is_valid_smartedu_url(url: &str) -> bool {
    if url.is_empty() {
        return false;
    }
    let lower = url.to_lowercase();
    SUPPORTED_DOMAINS.iter().any(|d| lower.contains(d))
}
