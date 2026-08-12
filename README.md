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

![Version](https://img.shields.io/badge/version-1.9-brightgreen)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-orange)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)
![Security](https://img.shields.io/badge/security-audited%20v1.4-blue)

</div>

---

## 🆕 v1.9 — Smarter Agent, Fewer Errors

v1.9 is focused on one thing: making `/agent` actually reliable in a real project instead of just capable in a demo. Several of these are fixes for real bugs, not just new features.

### 🧠 The agent now knows its actual environment, not just its OS

Before, the agent only knew which Linux distro it was on. That's not enough to avoid errors — the single most common avoidable mistake was assuming `python` exists when a system only has `python3`. The agent's environment context now includes the exact Python command to use, the real shell, the current working directory, and whether it's inside a git repo, and it's told to use those facts exactly instead of guessing.

### 🔍 `grep_files` and `list_dir` — the agent can finally explore before it edits

Two new read-only tools, no approval needed:
```
ACTION: grep_files | <regex> | <path>   → search file CONTENTS, not just names
ACTION: list_dir | <path>               → directory tree, so it can orient itself
```
Previously the agent could only find files by name (`search_files`), never by what's actually inside them — so it was editing code somewhat blind. The agent system prompt now explicitly tells it to orient with these before touching anything, and to always `read_file` a section before `edit_file`-ing it.

### 🛡️ `edit_file` now refuses ambiguous matches

If the text you're asking it to replace appears more than once in a file, `edit_file` used to silently patch the *first* occurrence — possibly the wrong one. It now refuses and asks for more surrounding context, the same exact-match discipline Claude Code's own edit tool uses.

### 👀 Real diff preview before you approve an edit

Approving an `edit_file` action now shows an actual colorized unified diff (green additions, red removals) instead of just a filename. `create_file` shows the new content and warns if it's about to overwrite something that already exists.

### 💾 Automatic backups + `/undo`

Every `create_file`, `edit_file`, and `delete_file` the agent performs now snapshots the file first to `~/.cybersh_backups/`. If it gets something wrong, `/undo` restores the file to exactly how it was before that change — including bringing back a file the agent just deleted.

### ✅ Instant syntax checking after every write

Right after the agent writes a `.py` or `.json` file, it's automatically checked (`py_compile` / JSON parse) and any error is fed straight back into the same tool result — so a broken edit surfaces immediately instead of the agent finding out three steps later.

### 🔁 Loop detection

If the agent issues the exact same action twice in a row — a classic sign it's stuck re-running something that already failed the same way — it now gets an explicit nudge to stop repeating itself and actually read what went wrong, instead of quietly burning iterations.

### 🐛 Fixed: tool results were being cut to 150 characters

This was a real bug. Every tool result — command output, file contents, error messages — was being truncated to 150 characters before being fed back to the agent. Long error messages were getting cut off mid-sentence, so the agent was often working from incomplete information and making worse decisions as a result. The limit is now 3000 characters with a clear "truncated" marker if it's still not enough.

### 📄 `CYBERSH.md` — project-specific context, automatically

Drop a `CYBERSH.md` (or `.cybersh.md`) file in your project root and its contents get automatically injected into every mode's system prompt — the same idea as Claude Code's `CLAUDE.md`. Use it for build/test commands, coding conventions, or anything else the AI should always know about that specific project.

```
# CYBERSH.md
This project uses pytest. Run `make test` before considering any change done.
Follow the existing snake_case naming — don't introduce camelCase.
```

### 🎯 Do exactly what was asked

The agent system prompt now explicitly instructs the model to do exactly what was requested — no unrequested extra features, files, or "improvements" — and to ask one short clarifying question if a request is genuinely ambiguous about *what* to build, rather than guessing and going off in the wrong direction.

### ⏱️ More room to actually finish multi-step tasks

`max_agent_iters` default raised from 6 to 12. Real coding tasks (explore → read → edit → test → fix → re-test) burn through iterations fast; 6 often wasn't enough to finish before the loop cut off.

---

## 🆕 v1.8 — Context Safety, Model Switching & Regenerate

### 🛡️ Automatic context management

The #1 way local llama.cpp chat sessions crash is a long conversation silently overflowing the model's context window (`Requested tokens exceed context window`). v1.8 tracks a running token estimate for the live conversation and, once it gets close to the budget, automatically drops the oldest turns (keeping the system prompt and your most recent exchanges) instead of hitting that wall. This applies in both normal chat and the agent tool-calling loop, which is the fastest way to burn through context. Toggle with `auto_trim_context` in your config; check current usage anytime with `/context`.

### 🔁 `/model` — hot-swap models without restarting

List every `.gguf` in `~/ollama-models` and switch the active chat model on the fly:

```
/model                  → list available models, shows which is active
/model 2                → switch to the 2nd model in the list
/model qwen             → switch by (partial) filename match
/model ~/path/to.gguf   → switch to any file path
```

`/models` (download new models) now also loads the model immediately after downloading instead of telling you to restart.

### ↻ `/regen` — redo the last response

Didn't like the last answer? `/regen` drops it and asks again with the same context — standard in every other chat tool, now here too.

### 🗜️ `/compact` — smart context compaction

Rather than just dropping old turns, `/compact` has the AI summarize everything except your most recent exchange into a short briefing, then replaces the old history with that summary — same idea as Claude Code's `/compact`. Frees up real context budget without losing the thread of the conversation.

### 📤 `/export` — save the conversation to a file

```
/export        → Markdown file in the current directory
/export html   → styled HTML file instead
```

### 🖥️ Browser-based GUI

A real GUI, no extra dependencies — stdlib `http.server` only, runs entirely on `127.0.0.1`, no cloud involved:

```
python cybersh_direct.py --gui
python cybersh_direct.py --gui --port 8421   # if 8420 is taken
```

Opens automatically in your browser: mode switcher (Chat/Sec/Code/Vibe), a model dropdown that hot-swaps via `/model` under the hood, live streaming responses, context-usage bar, and one-click Regen/Compact/Export/Clear. Agent mode's tool execution + approval prompts are terminal-only by design — a real confirm dialog before destructive actions matters more than convenience there, so run the plain REPL and use `/agent` for that.

---

## 🆕 v1.7 — Performance & Coding Update

### ⚡ Direct-to-GGUF prompt caching

The chat model, the RAG embedder, and the vision model now each get an in-RAM `LlamaCache` attached directly to the loaded `.gguf` instance. Any prompt that shares a prefix with a previous turn — your system prompt, injected RAG context, ongoing conversation history — no longer has to be re-evaluated from scratch. The cache lives on the model object itself in memory, not on disk, so there's no extra file and nothing to clean up. Configurable via `prompt_cache_enabled` / `prompt_cache_mb` in your config (default: on, 256MB per model).

### 📚 RAG index now served from RAM

`/rag` used to re-read `~/.cybersh_rag/index.json` off disk on every single search or ask. It's now cached in memory and only re-read if the file actually changes on disk, so a `/rag` session runs fast after the first hit instead of hitting the filesystem every query.

### 💪 Sharper `/code` mode

The `/code` system prompt was rewritten to think like a principal engineer: it defaults to complete, runnable files instead of fragments, reasons through edge cases and concurrency up front, calls out security and performance issues unprompted, and states real tradeoffs instead of silently picking a side.

### 📄 File-aware dev commands

`/review`, `/debug`, `/testgen`, `/docstring`, and `/complexity` now accept a file path directly — point them at a real file on disk and they read it straight in, instead of requiring you to copy-paste code every time.

```
/review app.py
/testgen src/parser.py
/complexity ~/scripts/scraper.py
```

### 🪟 Native Windows fixes

Downloads (`/models`, `--setup`, `/see setup`) previously shelled out to `wget`, which isn't installed by default on Windows — this silently broke model downloads on a stock Windows machine. v1.7 replaces it with a pure-Python downloader (stdlib `urllib`, works identically everywhere) and wires in the SHA-256 verification that already existed but was never actually being called. ANSI colors are now explicitly enabled on `cmd.exe` via the Windows console API, so you get real colors instead of raw escape codes on terminals that don't already support VT100.

---

## 🆕 v1.6 — Agent Tools, Vision, RAG & Plugins

### 🤖 Real agent tool-calling loop

`/agent` mode can now actually act: it issues `ACTION:` blocks (`run_command`, `create_file`, `edit_file`, `delete_file`, `open_app`, `search_files`, `read_file`, `make_dir`, `web_search`, `rag_search`), destructive ones wait for your approval, and read-only results are fed straight back to the model automatically so it can chain steps without you repeating yourself.

### 👁️ `/see` — local vision

Point cybersh at an image and ask a question about it, entirely offline via a local multimodal `.gguf` model (LLaVA / Phi-3 vision). Run `/see setup` once to configure the vision model + mmproj pair.

```
/see screenshot.png what does this error mean?
```

### 📚 `/rag` — local retrieval over your own files

Index any file or folder into a local, offline knowledge base and ask questions grounded in it — no cloud, nothing leaves your machine.

```
/rag index ~/notes
/rag ask what did I write about the auth flow?
/rag list
/rag clear
```

### 🔌 Plugin system with hot-reload

Drop a `.py` file in `~/.cybersh_plugins/` (or `./cybersh_plugins/` next to the script) defining a `setup(api)` function, and it can register new slash commands and new agent-callable tools without touching core code. `/plugins list`, `/plugins reload`, `/plugins new <name>` to scaffold one.

### 📖 Rebuilt `/help`

Searchable, categorized help — `/help rag`, `/help code`, etc. — instead of one long wall of text.

---

## 🆕 v1.5 — Older Features

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

> **How to get the latest version:** Just run the tool — the auto-updater handles it. Or pull the repo manually: `git pull && python3 cybersh_direct.py`

---

## 🌐 Do I Need Internet?

**Most features work 100% offline.** Internet is only used when you specifically ask for it:

| Feature | Needs Internet? |
|---------|----------------|
| AI chat, all modes | ❌ No |
| Memory, personas, goals, sessions | ❌ No |
| Code help, file analysis | ❌ No |
| Agent mode — file/command actions | ❌ No |
| `/image` — local image generation | ❌ No (after first model download) |
| `/rag` — local retrieval | ❌ No |
| `/see` — local vision | ❌ No |
| `--gui` — browser-based GUI | ❌ No (runs on 127.0.0.1 only) |
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

> Your AI models, chat memory, saved sessions, notes, goals, config, RAG index, plugins, agent backups, and `cybersh_webagent.json` are **never touched by updates.** Only the script file itself gets replaced.

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

Or launch the browser GUI instead of the terminal:

```bash
python3 cybersh_direct.py --gui
```

**That is it.** Every time you want to use CYBER SH, just run one of these commands from the `cybersh` folder.

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

You can download and switch models anytime inside the app with `/models` (download new) or `/model` (hot-swap one already downloaded, no restart needed).

---

## 💻 Supported Systems

**Linux — all major distros:**
- Kali Linux, Parrot OS
- Ubuntu, Debian, Linux Mint, Pop!_OS
- Fedora, RHEL, AlmaLinux, Rocky Linux
- Arch Linux, Manjaro, EndeavourOS
- openSUSE, Alpine

**macOS** — works natively

**Windows** — native support since v1.7 (ANSI colors enabled on `cmd.exe`, pure-Python downloader instead of `wget`, cross-platform pip flags):
```powershell
python cybersh_direct.py --setup
```
WSL2 also still works if you prefer a Linux environment:
```powershell
wsl --install
# Then open WSL terminal and follow the Linux steps above
```

---

## ✨ Features

### Choose a mode when you start

```
[1] 🤖 Agent  — AI controls your computer (runs commands, creates/edits files, explores your codebase)
[2] 🔐 Sec    — Security expert for bug bounty, pentesting, CVE analysis
[3] 🎨 Vibe   — Creative coding, beautiful UI, design ideas
[4] ⚡ Code   — Clean production code with error handling and comments
[5] 💬 Chat   — General assistant, ask it anything
```

Switch modes any time by typing `/agent`, `/sec`, `/vibe`, `/code`, or `/chat`. Or skip the terminal entirely with `python cybersh_direct.py --gui` for a browser-based version of Chat/Sec/Code/Vibe.

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

**Managing the live conversation:**

```
/context           → see how much of the context window is in use
/compact            → AI-summarizes older history to free up context, keeps the thread
/regen              → redo the last response
/export [html]      → save the conversation to a Markdown or HTML file
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

### 🖼️ Image Generation

```
/image a neon cyberpunk city at night
/image a portrait of a hacker --steps 30
/image fantasy castle --size 768x512 --neg blurry, ugly
/image --model stabilityai/stable-diffusion-2-1 futuristic terminal
```

---

### 🌐 Web Agent — persistent site memory

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
/debug [file]        → paste or point at broken code, AI finds every bug
/review [file]        → full code review with score out of 10
/testgen [file]       → generate a pytest test suite
/docstring [file]     → add docstrings + type hints
/complexity [file]    → Big-O time/space analysis
/lint <file>          → runs a real linter if installed, AI explains findings
/profile <script.py>  → runs cProfile, AI summarizes the hotspots
/template fastapi     → complete production-ready project
/gitlog                → summarizes recent commits
/gitdiff [staged]      → reviews uncommitted changes before you commit
/commitmsg             → generates a conventional commit message from your diff
/todo [path]           → scans for TODO/FIXME/HACK markers, AI triages them
/gitignore <stack>     → generates + optionally writes a .gitignore
/license <type>        → generates + optionally writes a LICENSE file
/explaincode           → explains every line in plain English
/roast                 → finds bad practices with humor, then fixes them
/fix <error>           → paste any error, get the exact fix
/howto zip a folder    → exact command for your OS
/tldr chmod 755         → plain English explanation
/regex match emails    → AI writes the pattern with examples
/git undo last commit  → exact git commands, explained
/diff                  → paste a git diff, AI explains the changes
/rename <name>          → 5 better name suggestions with reasons
/challenge hard          → coding or hacking challenge to practice
```

`/review`, `/debug`, `/testgen`, `/docstring`, and `/complexity` all accept a file path directly (`/review app.py`) as well as pasted code.

---

### 🤖 Agent mode — AI controls your computer

```
/agent
> add input validation to the signup endpoint and write a test for it
```

**How it actually works (v1.9):** the agent orients itself first — `list_dir` and `grep_files` to understand your project — then `read_file`s the exact section it's about to touch, makes a targeted `edit_file` change (rejected automatically if the match isn't unique), and verifies its own work by running your tests or a quick syntax check via `run_command`. It works through the whole task across multiple steps on its own instead of stopping to ask permission at every turn, up to `max_agent_iters` (default 12) tool round-trips per request.

**Tools it can use:**
```
ACTION: run_command | <bash command>              (needs your approval)
ACTION: create_file | <path> | <content>           (needs your approval)
ACTION: edit_file | <path> | <old text> | <new text>  (needs your approval, unique match required)
ACTION: delete_file | <path>                        (needs your approval)
ACTION: open_app | <app>                            (needs your approval)
ACTION: make_dir | <path>                           (needs your approval)
ACTION: search_files | <glob pattern>               (read-only, runs immediately)
ACTION: grep_files | <regex> | <path>                (read-only, runs immediately)
ACTION: list_dir | <path>                            (read-only, runs immediately)
ACTION: read_file | <path>                           (read-only, runs immediately)
ACTION: web_search | <query>                         (read-only, runs immediately)
ACTION: rag_search | <query>                         (read-only, runs immediately)
```

Every approval prompt for `edit_file` shows you a real colorized diff first. Every `create_file`/`edit_file`/`delete_file` is backed up automatically — if the agent gets something wrong, `/undo` restores the file to how it was.

**Project-specific context — like Claude Code's `CLAUDE.md`:** drop a `CYBERSH.md` (or `.cybersh.md`) file in your project root and its contents are automatically read into every mode's system prompt.

```md
# CYBERSH.md
This project uses pytest. Run `make test` before considering any change done.
Follow the existing snake_case naming.
```

---

### 👁️ Vision & 📚 RAG

```
/see setup                              → configure a local vision model once
/see screenshot.png what's wrong here?   → ask about an image, fully offline

/rag index ~/notes                       → build a local knowledge base
/rag ask what did I decide about auth?   → ask a question grounded in your files
/rag list                                → see what's indexed
/rag clear                               → wipe the index
```

---

### 🖥️ Browser-based GUI

```
python cybersh_direct.py --gui
python cybersh_direct.py --gui --port 8421   # if 8420 is taken
```

Runs entirely on `127.0.0.1` with zero extra dependencies (stdlib `http.server` only). Mode switcher, model dropdown, streaming responses, a context-usage bar, and one-click Regen/Compact/Export/Clear. Agent mode's tool execution with approval prompts is intentionally terminal-only — a real confirm dialog matters more than convenience for anything that touches your filesystem.

---

### 🔌 Plugins

```
/plugins list          → show loaded plugins
/plugins reload         → hot-reload without restarting
/plugins new mytool     → scaffold a new plugin file
```

Plugins are plain `.py` files in `~/.cybersh_plugins/` (or `./cybersh_plugins/`) that define `setup(api)` to register new slash commands and agent tools — see the generated template for the exact shape.

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
/undo                   → restore the last agent-made file change (create/edit/delete)
```

---

## 📋 Version History

| Version | What was added |
|---------|---------------|
| **v1.9** | **Smarter, more reliable `/agent`** — environment context now includes the exact python binary, shell, cwd, and git status instead of just the OS · **`grep_files`** (content search) and **`list_dir`** (directory tree) so the agent can orient itself before editing · `edit_file` now refuses ambiguous (non-unique) matches · real colorized diff preview before approving an edit · **automatic backups + `/undo`** for every agent file change · instant `py_compile`/JSON syntax check right after a write · loop detection for repeated failing actions · **fixed a real bug** where tool results were truncated to 150 characters, starving the agent of the error detail it needed to self-correct (now 3000) · **`CYBERSH.md`** project-context file, auto-injected into every mode (like Claude Code's `CLAUDE.md`) · explicit "do exactly what was asked, nothing extra" instruction · `max_agent_iters` default raised 6 → 12 |
| **v1.8** | **Automatic context management** — auto-trims oldest turns once the conversation nears the model's context budget instead of crashing with a hard overflow error, in both chat and the agent loop · **`/model`** — list and hot-swap the loaded `.gguf` model without restarting · **`/regen`** — redo the last response · **`/context`** — see current context-window usage · **`/compact`** — AI-summarizes older history instead of just dropping it · **`/export [html]`** — save the conversation to a Markdown or HTML file · **`--gui`** — browser-based GUI (stdlib only, no extra deps) with mode switching, model dropdown, streaming, and one-click Regen/Compact/Export/Clear · `/models` now loads a freshly downloaded model immediately instead of requiring a restart |
| **v1.7** | **Direct-to-gguf prompt caching** — in-RAM `LlamaCache` attached straight to the loaded chat/embedder/vision models, so repeated or shared-prefix prompts skip re-evaluation · RAG index now cached in RAM instead of re-read from disk every call · rewritten `/code` system prompt (full files, edge cases, security/perf called out unprompted) · `/review` `/debug` `/testgen` `/docstring` `/complexity` now accept a file path directly · **native Windows fixes** — pure-Python downloader replaces the `wget` dependency, SHA-256 model verification actually wired in, ANSI colors enabled on `cmd.exe` |
| **v1.6** | **Agent tool-calling loop** — real `ACTION:` execution with approval gating for destructive steps · **`/see`** local vision (LLaVA/Phi-3 multimodal) · **`/rag`** local offline retrieval over your own files · plugin system with hot-reload (`/plugins`) · rebuilt searchable `/help` · `/testgen` `/docstring` `/complexity` `/gitdiff` `/commitmsg` `/todo` `/gitignore` `/license` `/lint` `/profile` |
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

**Agent keeps repeating the same failed command:**  
This should now self-correct (v1.9 loop detection) — if it still gets stuck, `/undo` any partial file changes and try rephrasing the task more specifically.

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
| Your RAG index | `~/.cybersh_rag/` | ✅ Never touched |
| Your plugins | `~/.cybersh_plugins/` | ✅ Never touched |
| Your agent file backups | `~/.cybersh_backups/` | ✅ Never touched |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for full details.

Redistribution of modified versions must include the original license and credit the original author. Versions marketed as "uncensored", "cracked", or "unofficial" without proper attribution are a license violation and should be [reported here](https://github.com/neo4-svg/cybersh/issues).

---

<div align="center">

Made by <a href="https://github.com/neo4-svg">neo4-svg</a>

[⭐ Star this repo](https://github.com/neo4-svg/cybersh) · [🐛 Report a bug](https://github.com/neo4-svg/cybersh/issues) · [🚨 Report an unofficial version](https://github.com/neo4-svg/cybersh/issues)

</div>
