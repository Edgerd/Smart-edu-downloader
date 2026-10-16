// 简单日志：写入 logs/sed.log + 内存环形缓冲供 UI 读取
use once_cell::sync::Lazy;
use std::io::Write;
use std::sync::Mutex;

pub static LOG_BUF: Lazy<Mutex<Vec<String>>> = Lazy::new(|| Mutex::new(Vec::new()));

pub fn log(level: &str, msg: &str) {
    let line = format!(
        "[{}] [{}] {}",
        chrono::Local::now().format("%Y-%m-%d %H:%M:%S"),
        level,
        msg
    );
    {
        let mut buf = LOG_BUF.lock().unwrap();
        if buf.len() > 2000 {
            buf.drain(0..1000);
        }
        buf.push(line.clone());
    }
    let f = crate::paths::logs_dir().join("sed.log");
    if let Ok(mut file) = std::fs::OpenOptions::new().create(true).append(true).open(f) {
        let _ = writeln!(file, "{}", line);
    }
}

pub fn last_logs(n: usize) -> Vec<String> {
    let buf = LOG_BUF.lock().unwrap();
    let start = buf.len().saturating_sub(n);
    buf[start..].to_vec()
}
