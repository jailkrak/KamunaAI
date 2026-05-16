![Sentinel Apex](https://img.shields.io/badge/Sentinel%20Apex-Team-black.svg)
![Version](https://img.shields.io/badge/Cyber%20Scout-1.0-red.svg)

## 🛡️ PENTINEL-CYBER-SCOUT

High-Performance Cybersecurity Reconnaissance Tool written in Rust.

CyberScout is a fast, async-powered scanning tool for:
- Subdomain enumeration
- Directory brute-force scanning
- HTTP probing & status analysis
- Fast wordlist-based reconnaissance

## 🚀 Features

- ⚡ Async high-performance scanning (Tokio runtime)
- 🌐 Subdomain enumeration
- 📁 Directory brute-force scanner
- 🔁 HTTP redirect handling
- 📊 Clean terminal output with progress tracking
- 🧠 Configurable scanning engine
- 📦 Wordlist-based attack simulation
- 🧰 Modular Rust architecture

## ⚙️ Installation
```bash
git clone https://github.com/jailkrak/cyber-scout.git
cd cyber-scout
```
## ▶️ Usage
Directory brute-force scan
```bash
.\target\release\cyber_scout.exe \
--wordlist wordlists/directories.txt \
--domain https://example.com \
--dir /
```
```bash
# Sundomain Scan
.\target\release\cyber_scout.exe \
--wordlist wordlists/subdomains.txt \
--domain example.com
```

## 📄 Example Output
```bash
[+] Starting scan...
[+] Target: https://example.com
[+] Found: /admin
[+] Found: /api
[+] Found: /login
[+] Scan completed in 2.34s
```
##🧠 Configuration
Edit config/default.yaml:
```edit
concurrency: 50
timeout: 10
follow_redirects: true
colored_output: true
```
## 📁 Wordlists
```sok
wordlists/directories.txt → directory brute-force
wordlists/subdomains.txt → subdomain enumeration
```
## ⚠️ Disclaimer

This tool is for educational and authorized security testing only.

Do not use it on systems you do not own or do not have permission to test.

The author is not responsible for misuse.

## 🛠️ Tech Stack
Rust 🦀
Tokio (async runtime)
Reqwest (HTTP client)
Clap (CLI parser)
Tracing (logging)

## 📌 Author

Cybersecurity Recon Tool Project (CyberScout) - PENTINELAPEX
