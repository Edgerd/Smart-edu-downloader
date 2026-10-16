// 文件命名与分类：与 1.x 规则一致
use chrono::Local;

pub const NAMING_DEFAULT: &str = "default";
pub const NAMING_TEXTBOOK_NAME: &str = "textbook_name";
pub const NAMING_TIMESTAMP: &str = "timestamp";
pub const NAMING_TEXTBOOK_NAME_TIMESTAMP: &str = "textbook_name_timestamp";

pub fn sanitize_filename(name: &str) -> String {
    let mut s = name.to_string();
    for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|'] {
        s = s.replace(c, "_");
    }
    if s.chars().count() > 100 {
        s = s.chars().take(100).collect();
    }
    s.trim().to_string()
}

pub fn generate_filename(rule: &str, title: Option<&str>, include_timestamp: bool) -> String {
    let ts = Local::now().format("%Y%m%d_%H%M%S").to_string();
    let name = match rule {
        NAMING_TIMESTAMP => format!("download_{}.pdf", ts),
        NAMING_TEXTBOOK_NAME_TIMESTAMP => match title {
            Some(t) if !t.is_empty() => format!("{}_{}.pdf", sanitize_filename(t), ts),
            _ => format!("download_{}.pdf", ts),
        },
        _ => match title {
            // default / textbook_name
            Some(t) if !t.is_empty() => format!("{}.pdf", sanitize_filename(t)),
            _ => format!("download_{}.pdf", Local::now().timestamp()),
        },
    };
    if include_timestamp && rule != NAMING_TIMESTAMP && rule != NAMING_TEXTBOOK_NAME_TIMESTAMP {
        let stem = name.strip_suffix(".pdf").unwrap_or(&name);
        return format!("{}_{}.pdf", stem, ts);
    }
    name
}

pub const CAT_BY_SUBJECT: &str = "by_subject";
pub const CAT_BY_GRADE: &str = "by_grade";
pub const CAT_BY_VERSION: &str = "by_version";
pub const CAT_BY_SUBJECT_AND_GRADE: &str = "by_subject_and_grade";

const SUBJECTS: &[&str] = &["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治", "美术", "音乐", "体育", "信息技术", "科学"];
const GRADES: &[&str] = &["一年级", "二年级", "三年级", "四年级", "五年级", "六年级", "七年级", "八年级", "九年级", "高一", "高二", "高三"];
const VERSIONS: &[&str] = &["人教版", "北师大版", "苏教版", "外研社版", "冀教版", "沪教版", "华师大版", "浙教版", "鲁教版", "教科版", "湘教版", "鄂教版"];

fn contains(title: &str, words: &[&str]) -> Option<String> {
    words.iter().find(|w| title.contains(**w)).map(|w| w.to_string())
}

pub fn categorized_path(base: &str, rule: &str, title: Option<&str>) -> String {
    let t = title.unwrap_or("");
    let dir = match rule {
        CAT_BY_GRADE => contains(t, GRADES).unwrap_or_else(|| "其他年级".into()),
        CAT_BY_VERSION => contains(t, VERSIONS).unwrap_or_else(|| "其他版本".into()),
        CAT_BY_SUBJECT_AND_GRADE => format!(
            "{}/{}",
            contains(t, SUBJECTS).unwrap_or_else(|| "其他科目".into()),
            contains(t, GRADES).unwrap_or_else(|| "其他年级".into())
        ),
        _ => contains(t, SUBJECTS).unwrap_or_else(|| "其他科目".into()),
    };
    let path = std::path::Path::new(base).join(dir);
    let _ = std::fs::create_dir_all(&path);
    path.to_string_lossy().to_string()
}
