// 统一 HTTP 客户端：X-ND-AUTH、token 清洗、超时、SSL 开关、代理
use once_cell::sync::Lazy;
use reqwest::blocking::Client;
use std::sync::Mutex;
use std::time::Duration;

pub struct HttpClient {
    token: Mutex<Option<String>>,
    ssl_verify: Mutex<bool>,
    client: Mutex<Client>,
}

pub static HTTP: Lazy<HttpClient> = Lazy::new(|| HttpClient::new());

impl HttpClient {
    fn new() -> Self {
        let ssl = crate::settings::get("ssl_verify").as_bool().unwrap_or(true);
        let client = build_client(ssl, 30, 60);
        HttpClient {
            token: Mutex::new(None),
            ssl_verify: Mutex::new(ssl),
            client: Mutex::new(client),
        }
    }

    pub fn set_token(&self, raw: Option<String>) {
        let clean = clean_token(raw.as_deref());
        *self.token.lock().unwrap() = clean.clone();
        crate::logging::log(
            "INFO",
            &format!(
                "Access Token {}",
                if clean.is_some() { "已设置" } else { "已清除" }
            ),
        );
    }

    pub fn token(&self) -> Option<String> {
        self.token.lock().unwrap().clone()
    }

    pub fn auth_header(&self) -> String {
        match self.token() {
            Some(t) => format!("MAC id=\"{}\",nonce=\"0\",mac=\"0\"", t),
            None => "MAC id=\"0\",nonce=\"0\",mac=\"0\"".to_string(),
        }
    }

    pub fn set_ssl_verify(&self, on: bool) {
        *self.ssl_verify.lock().unwrap() = on;
        let to = timeouts();
        *self.client.lock().unwrap() = build_client(on, to.0, to.1);
    }

    pub fn ssl_verify(&self) -> bool {
        *self.ssl_verify.lock().unwrap()
    }

    fn client(&self) -> Client {
        self.client.lock().unwrap().clone()
    }

    pub fn get(&self, url: &str) -> reqwest::Result<reqwest::blocking::Response> {
        self.client()
            .get(url)
            .header("X-ND-AUTH", self.auth_header())
            .header(
                "User-Agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Smart-edu-downloader/2.0",
            )
            .send()
    }
}

fn timeouts() -> (u64, u64) {
    let c = crate::settings::get("connect_timeout").as_u64().unwrap_or(30);
    let r = crate::settings::get("read_timeout").as_u64().unwrap_or(60);
    (c.max(1), r.max(1))
}

fn build_client(ssl_verify: bool, connect: u64, read: u64) -> Client {
    // rustls 下无法放宽密钥长度，弱证书场景交给 ssl_verify 开关降级
    Client::builder()
        .danger_accept_invalid_certs(!ssl_verify)
        .danger_accept_invalid_hostnames(!ssl_verify)
        .connect_timeout(Duration::from_secs(connect))
        .timeout(Duration::from_secs(connect + read))
        .build()
        .unwrap_or_else(|_| Client::new())
}

/// 与 1.x 一致的 token 清洗逻辑
pub fn clean_token(token: Option<&str>) -> Option<String> {
    let t = match token {
        Some(t) if !t.is_empty() => t,
        _ => return None,
    };
    let mut out = String::new();
    for c in t.chars() {
        if c.is_whitespace() || matches!(c, '"' | '\\') {
            continue;
        }
        if (32..127).contains(&(c as u32)) {
            out.push(c);
        }
    }
    if out.chars().count() > 512 {
        crate::logging::log("WARNING", "Token 长度异常，可能粘贴了 JS 代码");
        out = out.chars().take(64).collect();
    }
    if out.is_empty() {
        None
    } else {
        Some(out)
    }
}

pub fn init_from_settings() {
    let ssl = crate::settings::get("ssl_verify").as_bool().unwrap_or(true);
    HTTP.set_ssl_verify(ssl);
    // 加密 token（xor: 前缀）解密
    let enc = crate::settings::get("access_token")
        .as_str()
        .unwrap_or("")
        .to_string();
    if !enc.is_empty() {
        if let Ok(plain) = crate::crypto::decrypt(&enc) {
            if !plain.is_empty() {
                HTTP.set_token(Some(plain));
            }
        }
    }
}
