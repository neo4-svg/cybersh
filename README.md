# CYBER SH — Full Installation Guide

## ⚠️ **IMPORTANT — UPDATES**

**Updates are NOT fixed in time.** To stay informed about the latest releases and bug fixes, **follow the X account for updates:** [@germanhack40404](https://twitter.com/germanhack40404)

**How to update:**
1. Copy the new `.py` file from the repo
2. Delete your old `cybersh_direct.py`
3. Replace it with the new version
4. **Memory & dependencies will persist** — your settings and models stay intact
5. Always check **`requirements.txt`** for any new dependencies before updating

---

## Requirements

- OS:     Linux (Kali, Ubuntu, Debian) or Windows WSL2
- Python: 3.10 or higher
- RAM:    7GB minimum, 16GB recommended
- Disk:   1GB+ free space in /home
- CPU:    Any x86_64 with AVX2 support
- Note:   Runs 100% locally — no internet needed after setup

---

## Step 1: Check Python version

```bash
python3 --version
# Need 3.10 or higher
```

## Step 2: Install build tools (Linux/WSL)

```bash
sudo apt update
sudo apt install python3-dev build-essential wget -y
```

## Step 3: Install the AI engine

```bash
pip install llama-cpp-python --break-system-packages
```

> CPU will hit 99% for 5–10 minutes during install — this is normal.
> Only happens once, never again after first install.

## Step 4: Install web search (optional but recommended)

```bash
pip install duckduckgo-search --break-system-packages
```

Enables `/web` and `/cvesearch` commands. No API key needed.

## Step 5: Verify installation

```bash
python3 -c "import llama_cpp; print('engine OK')"
# Should print: engine OK
```

## Step 6: Run setup wizard

```bash
python3 cybersh_direct.py --setup
```

The wizard will ask:
- Do you have a `.gguf` file already? (y/n)
- If no, pick a model to download (see model guide below)
- How many CPU threads (press Enter to use all)
- GPU detected automatically — CUDA install instructions shown if NVIDIA found

## Step 7: Run it

```bash
python3 cybersh_direct.py
```

---

## Model Guide — Which one to pick?

| # | Model | Size | RAM needed | Best for |
|---|-------|------|------------|----------|
| 1 | Phi-3 Mini | 2.2GB | 4GB+ | Code |
| 2 | TinyLlama 1.1B | 638MB | 2GB+ | Speed, very low RAM |
| 3 | Qwen2.5 1.5B | 986MB | 3GB+ | Smart + small |
| 4 | Mistral 7B | 4.1GB | 16GB+ | Best quality |
| 5 | **Llama 3.2 3B ★** | 2.0GB | 7GB+ | **Best all-round pick** |
| 6 | Qwen2.5 7B | 4.7GB | 12GB+ | Code & reasoning |
| 7 | DeepSeek-R1 7B | 4.7GB | 12GB+ | Step-by-step reasoning |

**7–8GB RAM → pick [5] Llama 3.2 3B**
**16GB+ RAM → pick [4] Mistral 7B or [6] Qwen2.5 7B**

Download more models anytime inside the app with `/models`.

---

## Modes — What each one does + examples

---

### 🤖 AGENT mode — AI controls your computer

Switch to it:
```
/agent
```

The AI can run commands, create files, edit files, open apps — all on your machine.
It always asks your permission before doing anything.

**Examples:**

```
create a folder called projects on my desktop
```
> AI will ask: approve creating ~/Desktop/projects? [y/N]

```
find all python files in my home folder
```
> AI searches and lists them

```
create a bash script that backs up my documents folder
```
> AI writes the script and saves it to disk

```
what is my IP address
```
> AI runs `ip a` and tells you

```
install nmap on my machine
```
> AI runs `sudo apt install nmap -y` after your approval

**Tip:** Agent mode is powerful — always read what it wants to do before pressing y.

---

### 🔐 SEC mode — Bug bounty & pentest expert

Switch to it:
```
/sec
```

Specialized for offensive security, OSINT, vulnerability research, and bug bounty hunting.
Gives real commands, not theory.

**Examples:**

```
/recon example.com
```
> Full recon plan: subdomains, ports, tech stack, wayback, dir fuzzing, API discovery

```
/payload xss
```
> List of XSS payloads: basic, encoded, polyglots, filter bypass

```
/payload sqli
```
> SQL injection payloads ready to use

```
/cvesearch CVE-2024-1234
```
> Searches the web for exploit info, gives you severity, affected versions, POC, mitigation

```
/cvesearch apache struts
```
> Finds latest known CVEs for Apache Struts

```
/explain "sqlmap -u http://target.com/page?id=1 --dbs"
```
> Explains every flag and what it does

```
how do I find hidden API endpoints on a target?
```
> Gives you tools and commands: ffuf, gobuster, katana, gau

```
write a python script to brute force login with a wordlist
```
> Writes working Python code for authorized testing

```
/web latest bug bounty writeups XSS 2026
```
> Searches the web for fresh techniques and feeds them to the AI

---

### 🎨 VIBE mode — Creative coding & UI/UX

Switch to it:
```
/vibe
```

Builds beautiful projects fast. Great for frontends, tools with style, and creative ideas.

**Examples:**

```
build a neon hacker-style terminal dashboard in Python
```
> Writes a full rich/curses dashboard with colors and panels

```
create a portfolio website with dark theme and animations
```
> Full HTML/CSS/JS in one file

```
make a beautiful login page with glassmorphism design
```
> Modern CSS with blur effects, gradients, smooth transitions

```
suggest a color scheme for a cybersecurity tool
```
> Gives you hex codes, rationale, and usage examples

```
build a pomodoro timer CLI with colored output
```
> Writes a working terminal timer with ANSI colors

```
/web best UI trends 2026
```
> Searches latest design trends and asks AI to apply them to your project

---

### ⚡ CODE mode — Clean production code

Switch to it:
```
/code
```

Writes clean, commented, production-ready Python and bash.
Always adds error handling and usage examples.

**Examples:**

```
write a port scanner in Python
```
> Clean threaded port scanner with argparse, error handling, output formatting

```
write a bash script to monitor CPU and RAM every 5 seconds
```
> Full script with colors, thresholds, and alerts

```
/f ~/myproject/app.py
What to do with it? fix all the bugs and add type hints
```
> Loads your file, fixes it, returns improved version

```
write a Python script to download all images from a webpage
```
> Uses requests + BeautifulSoup, saves files, handles errors

```
convert this bash one-liner to a proper Python script:
find . -name "*.log" -mtime +7 -delete
```
> Rewrites it cleanly with logging and dry-run flag

```
/run
```
> Executes the last code block the AI wrote (asks confirmation first)

```
/o ~/output/scanner.py
```
> Saves the last AI response to that file

---

### 💬 CHAT mode — General assistant

Switch to it:
```
/chat
```

General purpose assistant. Good for questions, explanations, summaries, writing, anything.

**Examples:**

```
explain how DNS works in simple terms
```

```
what is the difference between TCP and UDP?
```

```
summarize this article for me
/web how does quantum computing threaten encryption
```
> Searches the web then summarizes the results

```
write a professional email asking for a refund
```

```
translate this error message and tell me how to fix it:
ModuleNotFoundError: No module named 'requests'
```

```
what linux command shows open network connections?
```

---

## All Commands Reference

### Mode switching
| Command | Mode |
|---------|------|
| `/agent` | 🤖 AI controls your computer |
| `/sec` | 🔐 Bug bounty & pentest |
| `/vibe` | 🎨 Creative coding |
| `/code` | ⚡ Production code |
| `/chat` | 💬 General assistant |

### Files
| Command | What it does |
|---------|-------------|
| `/f <path>` | Load a file into AI context |
| `/o <path>` | Save last AI response to file |
| `/run` | Run the last code block (asks confirmation) |
| `/copy` | Copy last response to clipboard |

### Web & Research
| Command | What it does |
|---------|-------------|
| `/web <query>` | Search DuckDuckGo, feed results to AI |
| `/cvesearch <CVE or software>` | Search & analyze vulnerability |

### Security shortcuts
| Command | What it does |
|---------|-------------|
| `/recon <target>` | Full recon plan for bug bounty |
| `/payload <type>` | Generate payloads (xss, sqli, ssrf, lfi, rce) |
| `/explain <command>` | Explain a command step by step |

### Session
| Command | What it does |
|---------|-------------|
| `/models` | Download a new model without restarting |
| `/clear` | Wipe conversation memory |
| `/history` | Show conversation so far |
| `/temp <0.0-2.0>` | Change creativity (lower = focused, higher = creative) |
| `/info` | Show model name, size, settings |
| `/save` | Save current config |
| `/help` | Show all commands |
| `/exit` | Exit |

---

## GPU Acceleration (NVIDIA only)

```bash
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --break-system-packages
```

GPU is detected automatically on startup — no extra config needed.

---

## Windows WSL2 Setup

```powershell
# Run in PowerShell as admin:
wsl --install
```

Then open WSL terminal and follow the Linux steps from Step 1.

---

## Troubleshooting

**pip install fails:**
```bash
sudo apt install python3-dev build-essential -y
pip install llama-cpp-python --break-system-packages
```

**No space on root partition:**
```bash
df -h /home
mkdir -p ~/models
# Point setup wizard to ~/models
```

**Model not found:**
```bash
python3 cybersh_direct.py --setup
```

**`/web` not working:**
```bash
pip install duckduckgo-search --break-system-packages
```

---

## Important Notes

- Everything runs locally — nothing leaves your machine
- No API keys needed
- No internet needed after model download
- Model files stored in `~/ollama-models` by default
- Switch or download models anytime with `/models`
