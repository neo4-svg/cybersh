<div align="center">

```
 ██████╗██╗   ██╗██████╗ ███████╗██████╗     ███████╗██╗  ██╗
██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗    ██╔════╝██║  ██║
██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝    ███████╗███████║
██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗    ╚════██║██╔══██║
╚██████╗   ██║   ██████╔╝███████╗██║  ██║    ███████║██║  ██║
 ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═╝
```

**CYBER SH — Your Personal Offline AI Assistant**  
Runs entirely on your own computer. No cloud. No subscriptions. No one watching.

![Version](https://img.shields.io/badge/version-1.5-brightgreen)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-orange)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows%20WSL-lightgrey)
![Security](https://img.shields.io/badge/security-audited%20v1.4-blue)

</div>

---

## 🆕 v1.5 — New Features

### `/image` — AI Image Generation (Stable Diffusion, local)

Generate images from text prompts entirely on your own machine using Stable Diffusion via `diffusers`. No API key, no cloud, no cost per image. Images are saved as `.png` files in the same folder as the script.

```
/image a neon cyberpunk city at night
/image portrait of a hacker, cinematic lighting --steps 30 --size 512x768
/image fantasy castle --neg blurry, ugly, low quality
```

**Options you can append to any prompt:**

| Option | Default | What it does |
|--------|---------|-------------|
| `--steps N` | 20 | More steps = better quality, slower |
| `--size WxH` | 512x512 | Output resolution e.g. `768x512` |
| `--model <id>` | `runwayml/stable-diffusion-v1-5` | Any HuggingFace SD model ID |
| `--neg <text>` | `blurry, ugly…` | Things to avoid in the image |

- Automatically uses **CUDA GPU** if available (fp16, fast), falls back to CPU (fp32, slower)
- `diffusers` is auto-installed on first use — no manual setup
- Output filename: `cybersh_img_<prompt>_<timestamp>.png`

---

### `/fetch` — Persistent Web Agent

Fetch any URL, save it to a local database, and let the AI answer questions about its content. Unlike `/web` (which searches the web), `/fetch` retrieves a specific page and **remembers it** — so any time you mention that site or domain in conversation, cybersh silently fetches a fresh snapshot and injects it as AI context automatically.

```
/fetch https://railway.com
/fetch https://api.example.com/docs what are the available endpoints?
```

**Auth support — for sites that require login:**

```
/fetchauth https://example.com
```

Supports three auth types:
- **Cookie** — paste the `Cookie:` header from your browser's DevTools
- **Bearer token** — paste your API token
- **Basic auth** — username + password

Auth is stored in `cybersh_webagent.json` in your script folder (plain JSON, TinyDB).

**Other fetch commands:**

```
/fetchsites              → list all saved sites and their auth type
/fetchforget <url>       → remove a site from the database
```

**Auto-inject magic:** Once a site is saved, you never need to re-run `/fetch`. Just mention the URL or domain in any message and cybersh will automatically fetch a live snapshot and give it to the AI as context before answering.

> **Note:** `cybersh_webagent.json` is created next to the script on first use. It is never touched by updates.

---

## 🔒 v1.4 — Security Update

**v1.4 is a dedicated security release. No new features — just fixes to things that should have been right from the start. If you are on any earlier version, update immediately.**

### What was fixed

**1. TLS certificate verification (Critical)**  
Previous versions disabled SSL certificate checking in the auto-updater, meaning a network attacker on the same Wi-Fi, a rogue DNS server, or a MITM proxy could have served arbitrary code that the tool would download and execute as an update. This is now fixed — TLS certificates are fully verified on every connection.

**2. Auto-updater checksum verification (Critical)**  
Even with valid TLS, a compromised GitHub account or CDN cache could serve a bad update. v1.4 adds SHA-256 checksum verification: the downloaded update is checked against a published `checksums.txt` manifest before it is ever written to disk. If the checksum does not match, the update is aborted and the file is deleted. If no manifest is available, you are asked to confirm before anything is installed.

**3. Atomic update writes (Important)**  
Previously, if your machine lost power or crashed mid-update, the script file could be left half-written and permanently broken. v1.4 writes updates to a temporary file first, syncs it to disk, then replaces the old file in a single atomic operation — so a crash at any point leaves you with either the old version or the new one, never a corrupted file.

**4. Memory storage disclaimer (Important)**  
The `/remember` command help text previously said "AI remembers this forever", which implied some form of secure storage. Memories are stored as plain-text JSON at `~/.cybersh_memory.json` — no encryption, no protection. v1.4 makes this explicit in the help text and prints a visible warning every time you use `/remember`. **Do not store passwords, API keys, or sensitive data using `/remember`.**

**5. Obfuscated code removed (Trust)**  
A section of `session_save` used `chr(109)+chr(101)+...` to spell out dictionary key names — the kind of pattern that triggers red flags in automated security scanners and makes the code look like it is hiding something. It was not malicious, but it was unnecessary and hurt trust. All obfuscated strings are now plain text.

**6. Downloaded model SHA-256 verification (Important)**  
Models downloaded via `/models` or `--setup` are now verified against a SHA-256 checksum after download. A corrupted download or a tampered file will be detected and deleted automatically.

> **How to get v1.4/v1.5:** Just run the tool — the auto-updater handles it. Or pull the repo manually: `git pull && python3 cybersh_direct.py`

---

## 🌐 Do I Need Internet?

**Most features work 100% offline.** Internet is only used when you specifically ask for it:

| Feature | Needs Internet? |
|---------|----------------|
| AI chat, all modes | ❌ No |
| Memory, personas, goals, sessions | ❌ No |
| Code help, file analysis | ❌ No |
| `/image` — local image generation | ❌ No (after first model download) |
| `/fetch` — fetch & save a URL | ✅ Yes |
| `/web` — web search | ✅ Yes |
| `/weather` — weather | ✅ Yes |
| `/summarize` — read a URL | ✅ Yes |
| `/cvesearch` — CVE lookup | ✅ Yes |
| `/headers` — check a site's security headers | ✅ Yes |
| `/ipinfo` `/gist` `/gitlog <url>` | ✅ Yes |
| `/speedtest` | ✅ Yes |
| Auto-update on startup | ✅ Yes (skipped automatically if offline) |

> **Privacy note:** When you use any internet feature, the request goes directly from **your computer** to the relevant service. It never passes through any third-party server or CYBER SH infrastructure.

---

## 🔄 Updates — Nothing You Need to Do

CYBER SH **updates itself automatically every time you run it.**

- On startup it silently checks GitHub for a newer version
- If there is one, it downloads the new code, **verifies the SHA-256 checksum**, backs up your old file, installs any new packages, and restarts — all in seconds
- If you are offline, it simply skips the check and continues normally
- **You never need to run any update command manually — ever**

> Your AI models, chat memory, saved sessions, notes, goals, config, and `cybersh_webagent.json` are **never touched by updates.** Only the script file itself gets replaced.

---

## ⚡ GPU — Automatic Every Time

CYBER SH automatically detects your GPU **every single time** you launch it. No config needed.

| GPU | What happens |
|-----|-------------|
| **NVIDIA** + CUDA installed | ✅ Full GPU acceleration — faster responses + image generation |
| **NVIDIA** without CUDA | Shows you one command to enable it, runs on CPU until then |
| **AMD** | Detected and shown, runs on CPU (ROCm experimental) |
| **Intel Arc / iGPU** | Detected and shown, runs on CPU |
| **No GPU** | Runs on CPU normally |

**To enable NVIDIA GPU acceleration (one time only):**
```bash
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --break-system-packages
```
After that, every run will automatically use your GPU — including `/image` generation.

---

## ⚠️ Official Version Notice

> **The only official, safe, and maintained version of CYBER SH is published at:**  
> 👉 **[github.com/neo4-svg/cybersh](https://github.com/neo4-svg/cybersh)**
>
> Any version described as "unofficial", "uncensored", "cracked", or "modified" distributed anywhere else — on any forum, website, or file sharing platform — is **not authorized.** These versions may contain malware, backdoors, or stolen code and are a legal violation of the MIT license.
>
> **Found an unofficial version?** Please report it immediately:  
> 👉 [Open an issue here](https://github.com/neo4-svg/cybersh/issues) and include the link. We will act on every report.

---

## 🚀 Installation — Do This Once

> **You only do this once.** After setup, just run one command every time to launch.

---

### Step 1 — Clone the repo

```bash
git clone https://github.com/neo4-svg/cybersh.git
cd cybersh
```

---

### Step 2 — Run setup

```bash
python3 cybersh_direct.py --setup
```

**The setup automatically:**
- Detects your operating system, distro, and GPU
- Installs the AI engine (`llama-cpp-python`)
- Installs web search support (`ddgs`)
- Lets you pick and download an AI model
- Verifies the downloaded model with SHA-256 (new in v1.4)
- Saves your configuration

> ✅ You do not need to install anything separately. Setup handles everything.

---

### Step 3 — Launch it

```bash
python3 cybersh_direct.py
```

**That is it.** Every time you want to use CYBER SH, just run this one command from the `cybersh` folder.

---

## 🤖 Picking an AI Model

During setup, pick the model that fits your machine:

| # | Model | Size | RAM needed | Best for |
|---|-------|------|------------|----------|
| 1 | Phi-3 Mini | 2.2GB | 4GB+ | Code |
| 2 | TinyLlama 1.1B | 638MB | 2GB+ | Very low RAM machines |
| 3 | Qwen2.5 1.5B | 986MB | 3GB+ | Smart but lightweight |
| 4 | Mistral 7B | 4.1GB | 16GB+ | Best quality, needs good PC |
| **5** | **Llama 3.2 3B ★** | **2.0GB** | **7GB+** | **Best choice for most people** |
| 6 | Qwen2.5 7B | 4.7GB | 12GB+ | Great for code and reasoning |
| 7 | DeepSeek-R1 7B | 4.7GB | 12GB+ | Thinks step by step |

**Not sure which to pick?** Choose **[5] Llama 3.2 3B** — works great on most laptops.

You can download and switch models anytime inside the app with `/models`.

---

## 💻 Supported Systems

**Linux — all major distros:**
- Kali Linux, Parrot OS
- Ubuntu, Debian, Linux Mint, Pop!_OS
- Fedora, RHEL, AlmaLinux, Rocky Linux
- Arch Linux, Manjaro, EndeavourOS
- openSUSE, Alpine

**macOS** — works natively

**Windows** — via WSL2:
```powershell
# Run in PowerShell as Administrator:
wsl --install
# Then open WSL terminal and follow the Linux steps above
```

---

## ✨ Features

### Choose a mode when you start

```
[1] 🤖 Agent  — AI controls your computer (runs commands, creates files, opens apps)
[2] 🔐 Sec    — Security expert for bug bounty, pentesting, CVE analysis
[3] 🎨 Vibe   — Creative coding, beautiful UI, design ideas
[4] ⚡ Code   — Clean production code with error handling and comments
[5] 💬 Chat   — General assistant, ask it anything
```

Switch modes any time by typing `/agent`, `/sec`, `/vibe`, `/code`, or `/chat`.

---

### 🧠 Memory — AI remembers you between sessions

```
/remember my name is Ahmed
/remember I work with Python 3.11
/remember project myapp is a Flask REST API

/memories          → show everything the AI knows about you
/forget python     → remove something from memory
```

> ⚠️ **v1.4 note:** Memories are stored as plain-text JSON at `~/.cybersh_memory.json`. They are not encrypted. Do not store passwords, API keys, or anything sensitive here.

---

### 💾 Sessions — save and reload full conversations

```
/session save pentest-example-com   → save current chat with a name
/session list                       → show all saved chats
/session load 1                     → load and merge an old chat into current one
/session search XSS                 → search across all saved chats for a keyword
/session delete 2                   → delete a saved session
```

---

### 🎭 AI Personalities

```
/persona teacher    → explains everything simply, like a patient teacher
/persona hacker     → talks like an elite security expert
/persona coach      → motivates you and breaks things into steps
/persona roaster    → roasts your bad code with humor (then fixes it)
/persona sherlock   → thinks and deduces like Sherlock Holmes
/persona prof       → formal university professor style
/persona eli5       → explains like you are 5 years old
/persona pirate     → pirate who is somehow a genius programmer
/persona stoic      → calm, wise, Marcus Aurelius energy
```

---

### 🌐 Internet features

```
/web latest AI news 2026
/weather Baghdad
/summarize https://example.com/article
/cvesearch CVE-2024-1234
/headers example.com
/ipinfo 8.8.8.8
/gitlog https://github.com/neo4-svg/cybersh
/gist <gist url or id>
```

---

### 🖼️ Image Generation (new in v1.5)

```
/image a neon cyberpunk city at night
/image a portrait of a hacker --steps 30
/image fantasy castle --size 768x512 --neg blurry, ugly
/image --model stabilityai/stable-diffusion-2-1 futuristic terminal
```

---

### 🌐 Web Agent — persistent site memory (new in v1.5)

```
/fetch https://railway.com                         → fetch and save the site
/fetch https://docs.example.com what is the API?  → fetch and ask AI about it
/fetchauth https://example.com                     → add auth (cookie/bearer/basic)
/fetchsites                                        → list all saved sites
/fetchforget https://example.com                   → remove a saved site
```

Once a site is saved, just mention it naturally — cybersh auto-fetches and injects it as context.

---

### 🔐 Security tools

```
/recon example.com        → full bug bounty recon plan
/payload xss              → ready-to-use payloads
/explain "nmap -sV ..."   → explains every flag
/ctf aGVsbG8gd29ybGQ=    → CTF challenge analyzer
/hash 5f4dcc3b5aa765d6... → identifies hash type, checks common passwords
/osint username123        → full OSINT checklist
/wordlist TechCorp 2010   → targeted password wordlist
/pwcheck MyPassword123!   → entropy-based strength check
```

---

### ⚡ Developer tools

```
/debug        → paste broken code, AI finds every bug
/review       → full code review with score out of 10
/template fastapi → complete production-ready project
/gitlog       → summarizes recent commits
/explaincode  → explains every line in plain English
/roast        → finds bad practices with humor, then fixes them
/fix <error>  → paste any error, get the exact fix
/howto zip a folder → exact command for your OS
/tldr chmod 755 → plain English explanation
/regex match emails → AI writes the pattern with examples
/git undo last commit → exact git commands, explained
/diff         → paste a git diff, AI explains the changes
/rename <name> → 5 better name suggestions with reasons
/challenge hard → coding or hacking challenge to practice
```

---

### 🤖 AI thinking tools

```
/think how does TLS handshake work  → step-by-step reasoning before answering
/debate AI will replace programmers → both sides argued fairly, honest verdict
/improve                            → paste text, AI rewrites it cleaner
/eli5 how does encryption work      → zero jargon, simple analogies
```

---

### 🌍 Everyday tools

```
/convert 100 km to miles
/qr https://github.com/neo4-svg/cybersh
/speedtest
/calc 15% of 240
/encode hello world
/encode decode aGVsbG8gd29ybGQ=
/base 255
/clock
/translate arabic How are you today
/passgen
/passgen phrase
/timer 25m
/goals
/note remember to test the API endpoint
/benchmark
/syswatch
/recap
/tip
```

---

### 📁 File tools

```
/f ~/myproject/app.py   → load a file into AI context
/o ~/output/result.py   → save last AI response to a file
/run                    → run the last code block (asks confirmation first)
/copy                   → copy last response to clipboard
```

---

## 📋 Version History

| Version | What was added |
|---------|---------------|
| **v1.5** | **`/image`** — local Stable Diffusion image generation, saves `.png` next to script, auto GPU/CPU, supports `--steps`, `--size`, `--model`, `--neg` · **`/fetch`** — persistent web agent with TinyDB storage, auto-injects saved site content into AI context · **`/fetchauth`** — cookie / bearer / basic auth for saved sites · **`/fetchsites`** / **`/fetchforget`** — manage saved sites |
| **v1.4** | **Security release** — TLS certificate verification restored · auto-updater SHA-256 checksum verification against published manifest · atomic update writes (crash-safe) · memory plain-text storage warning · obfuscated `chr()` code removed · downloaded model SHA-256 verification |
| **v1.3** | OS-aware AI responses · loop/repetition auto-detection · entropy-based password checks · clipboard auto-detection (Wayland/X11/macOS/WSL) · rewritten `/headers` with severity tags · sessions system · `/convert` `/qr` `/speedtest` `/pwcheck` `/debug` `/review` `/template` `/gitlog` `/hash` `/osint` `/wordlist` `/think` `/debate` `/improve` `/eli5` `/ipinfo` `/base` `/clock` `/lorem` `/gist` |
| **v1.2** | Full GPU auto-detection · auto-updater · memory system · 9 AI personas · daily goals · `/calc` `/summarize` `/timer` `/weather` `/passgen` `/encode` `/benchmark` `/syswatch` · tab autocomplete · arrow key history |
| **v1.1** | Web search (`/web`, `/cvesearch`) · 7 downloadable models · in-app model downloader |
| **v1.0** | Initial release — 5 modes · agent engine · file loading · chat history |

---

## 🐛 Troubleshooting

**Setup fails with build error:**
```bash
# Debian / Ubuntu / Kali
sudo apt install python3-dev build-essential -y

# Fedora
sudo dnf install python3-devel gcc gcc-c++ -y

# Arch
sudo pacman -S python base-devel --noconfirm
```

**No space for the model:**
```bash
df -h /home
mkdir -p ~/models
```

**Model not found after setup:**
```bash
python3 cybersh_direct.py --setup
```

**`/web` not working:**
```bash
pip install ddgs --break-system-packages
```

**`/image` fails to install diffusers:**
```bash
pip install diffusers transformers accelerate safetensors --break-system-packages
```

**`/fetch` fails — site needs auth:**
```
/fetchauth https://yoursite.com
```

**`/copy` not working:**  
The tool auto-detects your display server and prints the exact install command for your distro.

**NVIDIA GPU not accelerating:**
```bash
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --break-system-packages
```

---

## 📁 What Updates Touch — What They Don't

| File | Location | Safe from updates? |
|------|----------|--------------------|
| `cybersh_direct.py` | your cybersh folder | 🔄 Replaced (SHA-256 verified since v1.4) |
| `cybersh_webagent.json` | your cybersh folder | ✅ Never touched |
| AI models | `~/ollama-models/` | ✅ Never touched |
| Your memories | `~/.cybersh_memory.json` | ✅ Never touched |
| Your config | `~/.cybersh_direct.json` | ✅ Never touched |
| Your saved sessions | `~/.cybersh_sessions/` | ✅ Never touched |
| Your notes | `~/.cybersh_notes.json` | ✅ Never touched |
| Your goals | `~/.cybersh_goals.json` | ✅ Never touched |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for full details.

Redistribution of modified versions must include the original license and credit the original author. Versions marketed as "uncensored", "cracked", or "unofficial" without proper attribution are a license violation and should be [reported here](https://github.com/neo4-svg/cybersh/issues).

---

<div align="center">

Made by <a href="https://github.com/neo4-svg">neo4-svg</a>

[⭐ Star this repo](https://github.com/neo4-svg/cybersh) · [🐛 Report a bug](https://github.com/neo4-svg/cybersh/issues) · [🚨 Report an unofficial version](https://github.com/neo4-svg/cybersh/issues)

</div>
