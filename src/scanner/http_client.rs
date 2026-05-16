use reqwest::{Client, Response, header::{HeaderMap, USER_AGENT, HeaderName, HeaderValue}};
use std::time::Duration;
use rand::seq::SliceRandom;
use crate::config::HttpClientConfig;

pub struct AsyncHttpClient {
    client: Client,
    user_agents: Vec<&'static str>,
    rotate_ua: bool,
}

impl AsyncHttpClient {
    pub fn new(config: &HttpClientConfig) -> anyhow::Result<Self> {
        let mut headers = HeaderMap::new();

        // Add custom headers - FIXED: properly parse header names and values
        for (key, value) in &config.custom_headers {
            let header_name = HeaderName::from_bytes(key.as_bytes())
                .map_err(|e| anyhow::anyhow!("Invalid header name '{}': {}", key, e))?;
            let header_value = HeaderValue::from_str(value)
                .map_err(|e| anyhow::anyhow!("Invalid header value '{}': {}", value, e))?;
            headers.insert(header_name, header_value);
        }

        let builder = Client::builder()
            .timeout(Duration::from_secs(config.timeout))
            .danger_accept_invalid_certs(config.allow_invalid_certs)
            .redirect(if config.follow_redirects {
                reqwest::redirect::Policy::limited(10)
            } else {
                reqwest::redirect::Policy::none()
            })
            .default_headers(headers)
            .gzip(true)
            .brotli(true);

        let builder = if let Some(proxy_url) = &config.proxy {
            let proxy = reqwest::Proxy::all(proxy_url)?;
            builder.proxy(proxy)
        } else {
            builder
        };

        Ok(Self {
            client: builder.build()?,
            user_agents: Self::load_user_agents(),
            rotate_ua: Self::safe_rotate_ua(config),
        })
    }

    /// SAFE fallback (no config field dependency)
    fn safe_rotate_ua(_config: &HttpClientConfig) -> bool {
        // If you later add rotate_ua in config → change here only
        false
    }

    fn load_user_agents() -> Vec<&'static str> {
        vec![
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "curl/7.88.1",
            "python-requests/2.31.0",
        ]
    }

    pub async fn get(&self, url: &str) -> anyhow::Result<Response> {
        let mut req = self.client.get(url);

        // Rotate User-Agent if enabled
        if self.rotate_ua {
            let ua = self.user_agents
                .choose(&mut rand::thread_rng())
                .unwrap_or(&self.user_agents[0]);

            req = req.header(USER_AGENT, *ua);
        }

        Ok(req.send().await?)
    }

    // Auto fallback: HTTP → HTTPS
    pub async fn get_with_fallback(&self, url: &str) -> anyhow::Result<(String, Response)> {
        match self.get(url).await {
            Ok(resp) => {
                // Check if response is successful or redirection
                if resp.status().is_success() || resp.status().is_redirection() {
                    Ok((url.to_string(), resp))
                } 
                // fallback http -> https when response is not success/redirection
                else if url.starts_with("http://") {
                    let https_url = url.replacen("http://", "https://", 1);
                    
                    match self.get(&https_url).await {
                        Ok(resp) => Ok((https_url, resp)),
                        Err(e) => Err(e),
                    }
                }
                // Return error for unsuccessful non-HTTP request
                else {
                    Err(anyhow::anyhow!("Request failed with status: {}", resp.status()))
                }
            }
            // Handle network/connection errors
            Err(e) => Err(e),
        }
    }
}