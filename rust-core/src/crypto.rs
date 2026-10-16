// Token 加密：沿用 1.x 的 XOR+Base64 方案（前缀 xor:）
use base64::engine::general_purpose::STANDARD as B64;
use base64::Engine;

const KEY: &[u8] = b"SED_TOKEN_KEY_2024";

pub fn encrypt(text: &str) -> String {
    let data = text.as_bytes();
    let enc: Vec<u8> = data
        .iter()
        .enumerate()
        .map(|(i, b)| b ^ KEY[i % KEY.len()])
        .collect();
    format!("xor:{}", B64.encode(enc))
}

pub fn decrypt(enc: &str) -> Result<String, String> {
    let data = enc.strip_prefix("xor:").unwrap_or(enc);
    let raw = B64
        .decode(data.trim())
        .map_err(|e| format!("base64 解码失败: {}", e))?;
    let dec: Vec<u8> = raw
        .iter()
        .enumerate()
        .map(|(i, b)| b ^ KEY[i % KEY.len()])
        .collect();
    String::from_utf8(dec).map_err(|_| "解密结果不是有效 UTF-8".to_string())
}

pub fn is_xor_format(enc: &str) -> bool {
    decrypt(enc).is_ok()
        && decrypt(enc)
            .map(|s| s.chars().all(|c| !c.is_control()))
            .unwrap_or(false)
}
