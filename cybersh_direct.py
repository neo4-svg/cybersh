#!/usr/bin/env python3
# version: 1.9
"""
 ██████╗██╗   ██╗██████╗ ███████╗██████╗     ███████╗██╗  ██╗
██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗    ██╔════╝██║  ██║
██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝    ███████╗███████║
██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗    ╚════██║██╔══██║
╚██████╗   ██║   ██████╔╝███████╗██║  ██║    ███████║██║  ██║
 ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═╝
  CYBER SH DIRECT — No Server · Pure Python · llama-cpp-python
"""

import sys, os, json, time, shutil, re, subprocess, threading, datetime, textwrap, argparse, glob, readline, difflib
import importlib.util
import http.server, socketserver

def _own_version() -> str:
    """Read the '# version:' header of this file so the banner never drifts out of sync."""
    try:
        with open(__file__) as f:
            for line in f:
                if line.strip().startswith("# version:"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return "?"

APP_VERSION = _own_version()

# ══════════════════════════════════════════════════════════════
#  AUTO-UPDATER
# ══════════════════════════════════════════════════════════════
REPO_RAW    = "https://raw.githubusercontent.com/neo4-svg/cybersh/main"
VERSION_URL = f"{REPO_RAW}/version.txt"
SCRIPT_URL  = f"{REPO_RAW}/cybersh_direct.py"
REQS_URL    = f"{REPO_RAW}/requirements.txt"

def _http_get(url: str, timeout: int = 10) -> str | None:
    try:
        import urllib.request, ssl
        ctx = ssl.create_default_context()  # verifies TLS certs — do not disable
        req = urllib.request.Request(url, headers={"User-Agent": "cybersh-updater/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:
        return None

def _download_file(url: str, dest: str, label: str = "") -> bool:
    """Pure-Python file downloader with a live progress bar. Used for model
    downloads instead of shelling out to `wget` — wget isn't installed by
    default on Windows, so relying on it silently broke every download
    (/models, --setup, /see setup) on a stock Windows machine."""
    import urllib.request, ssl
    label = label or os.path.basename(dest)
    tmp   = dest + ".part"
    try:
        ctx = ssl.create_default_context()  # verifies TLS certs — do not disable
        req = urllib.request.Request(url, headers={"User-Agent": "cybersh-downloader/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp, open(tmp, "wb") as out:
            total, done = int(resp.headers.get("Content-Length", 0) or 0), 0
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                done += len(chunk)
                if total:
                    pct = done * 100 // total
                    print(f"\r  {label}: {pct}%  ({done/1e6:.0f}/{total/1e6:.0f} MB)", end="", flush=True)
                else:
                    print(f"\r  {label}: {done/1e6:.0f} MB", end="", flush=True)
        print()
        os.replace(tmp, dest)
        return True
    except Exception as e:
        print(f"\n  ✗ Download failed: {e}")
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        return False

def _is_online() -> bool:
    import socket
    for host, port in [("github.com", 443), ("8.8.8.8", 53), ("1.1.1.1", 53)]:
        try:
            socket.setdefaulttimeout(3)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port)); s.close()
            return True
        except Exception:
            continue
    return False

def copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard — auto-detects Wayland/X11/macOS/WSL/termux."""
    if not text:
        return False

    os_info = _detect_os()
    system  = os_info["system"]

    # build candidate clipboard tools in priority order based on environment
    candidates = []

    if system == "Darwin":
        candidates = [["pbcopy"]]
    elif system == "Linux":
        is_wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
        is_wsl     = "microsoft" in platform_release().lower() if platform_release() else False
        if is_wsl:
            candidates = [["clip.exe"]]
        elif is_wayland:
            candidates = [["wl-copy"], ["xclip","-selection","clipboard"], ["xsel","--clipboard","--input"]]
        else:
            candidates = [["xclip","-selection","clipboard"], ["xsel","--clipboard","--input"], ["wl-copy"]]
    elif system == "Windows":
        candidates = [["clip"]]

    for cmd in candidates:
        try:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            p.communicate(text.encode(), timeout=5)
            if p.returncode == 0:
                print(f"{NEON_G}✓ Copied to clipboard! {DIM}(via {cmd[0]}){R}\n")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    # nothing worked — give the right install command for THIS distro
    pkg_mgr = os_info.get("pkg_mgr")
    install_hints = {
        "apt":    "sudo apt install wl-clipboard   # Wayland\nsudo apt install xclip         # X11",
        "dnf":    "sudo dnf install wl-clipboard   # Wayland\nsudo dnf install xclip         # X11",
        "pacman": "sudo pacman -S wl-clipboard     # Wayland\nsudo pacman -S xclip           # X11",
        "zypper": "sudo zypper install wl-clipboard\nsudo zypper install xclip",
        "apk":    "sudo apk add wl-clipboard",
        "brew":   "brew install pbcopy   # usually pre-installed on macOS",
    }
    hint = install_hints.get(pkg_mgr, "Install xclip or wl-clipboard for your distro.")
    print(f"{NEON_Y}⚠ No clipboard tool found on this system.{R}")
    print(f"{DIM}{hint}{R}\n")
    return False


def platform_release() -> str:
    """Safe wrapper for platform.release() — used to detect WSL."""
    try:
        import platform
        return platform.release()
    except Exception:
        return ""


def _detect_os() -> dict:
    import platform
    info = {
        "system":  platform.system(),
        "distro":  "",
        "pkg_mgr": None,
        "pip_flag": [],
        "is_venv": sys.prefix != sys.base_prefix,
    }
    if info["system"] == "Linux":
        os_release = {}
        for path in ("/etc/os-release", "/usr/lib/os-release"):
            try:
                with open(path) as f:
                    for line in f:
                        k, _, v = line.strip().partition("=")
                        os_release[k] = v.strip('"')
                break
            except Exception:
                pass
        distro_id = os_release.get("ID", "").lower()
        like      = os_release.get("ID_LIKE", "").lower()
        info["distro"] = os_release.get("PRETTY_NAME", distro_id)
        apt_ids    = {"debian","ubuntu","kali","parrot","linuxmint","pop","elementary","mx","zorin","raspbian"}
        dnf_ids    = {"fedora","rhel","centos","almalinux","rocky","ol","nobara"}
        pacman_ids = {"arch","manjaro","endeavouros","garuda","artix","cachyos"}
        zypper_ids = {"opensuse","suse","opensuse-leap","opensuse-tumbleweed"}
        apk_ids    = {"alpine"}
        all_ids    = {distro_id} | set(like.split())
        if   all_ids & apt_ids:    info["pkg_mgr"] = "apt"
        elif all_ids & dnf_ids:    info["pkg_mgr"] = "dnf"
        elif all_ids & pacman_ids: info["pkg_mgr"] = "pacman"
        elif all_ids & zypper_ids: info["pkg_mgr"] = "zypper"
        elif all_ids & apk_ids:    info["pkg_mgr"] = "apk"
        if not info["is_venv"]:
            info["pip_flag"] = ["--break-system-packages"]
    elif info["system"] == "Darwin":
        info["distro"] = "macOS"; info["pkg_mgr"] = "brew"
    elif info["system"] == "Windows":
        info["distro"] = "Windows"
    return info

def _install_packages(pkgs: list) -> None:
    G="\033[38;5;82m"; C="\033[38;5;51m"; Y="\033[38;5;226m"; D="\033[2m"; R2="\033[0m"
    os_info = _detect_os()
    flag    = os_info["pip_flag"]
    print(f"  {D}OS: {os_info['distro'] or os_info['system']}{R2}")
    for pkg in pkgs:
        print(f"  {C}→{R2} {pkg}", end="", flush=True)
        pip_cmd = [sys.executable, "-m", "pip", "install", pkg, "--quiet", "--upgrade"] + flag
        r = subprocess.run(pip_cmd, capture_output=True, text=True)
        if r.returncode == 0:
            print(f"\r  {G}✓{R2} {pkg}                    "); continue
        # fallback: without flag
        r2 = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg, "--quiet", "--upgrade"],
            capture_output=True, text=True)
        if r2.returncode == 0:
            print(f"\r  {G}✓{R2} {pkg}                    "); continue
        # fallback: system package manager
        pm = os_info["pkg_mgr"]
        if pm:
            pm_cmds = {
                "apt":    ["sudo","apt","install","-y",f"python3-{pkg}"],
                "dnf":    ["sudo","dnf","install","-y",f"python3-{pkg}"],
                "pacman": ["sudo","pacman","-S","--noconfirm",f"python-{pkg}"],
                "zypper": ["sudo","zypper","install","-y",f"python3-{pkg}"],
                "apk":    ["sudo","apk","add",f"py3-{pkg}"],
            }
            r3 = subprocess.run(pm_cmds[pm], capture_output=True, text=True)
            if r3.returncode == 0:
                print(f"\r  {G}✓{R2} {pkg} {D}(via {pm}){R2}              "); continue
        err = (r.stderr or "").strip().split("\n")[-1][:60]
        print(f"\r  {Y}⚠{R2} {pkg} — {D}{err}{R2}")
        print(f"    {D}Manual: pip install {pkg} --break-system-packages{R2}")

def check_and_update(force: bool = False) -> None:
    G="\033[38;5;82m"; C="\033[38;5;51m"; Y="\033[38;5;226m"
    B="\033[1m"; D="\033[2m"; R2="\033[0m"

    this_file = os.path.realpath(os.path.abspath(__file__))

    # read local version from line 2
    local_ver = "0.0.0"
    try:
        with open(this_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("# version:"):
                    local_ver = line.split(":", 1)[1].strip(); break
    except Exception:
        pass

    print(f"\n{C}🔄 Checking for updates…{R2}", end="", flush=True)

    if not force and not _is_online():
        print(f"\r{D}  ↷ No internet — skipping update check.{R2}          \n")
        return

    remote_ver = _http_get(VERSION_URL)
    if not remote_ver:
        print(f"\r{D}  ↷ Could not reach GitHub — skipping.{R2}            \n")
        return

    remote_ver = remote_ver.strip()

    def ver_tuple(v):
        try: return tuple(int(x) for x in v.split("."))
        except: return (0, 0, 0)

    if not force and ver_tuple(remote_ver) <= ver_tuple(local_ver):
        print(f"\r{G}  ✓ Up to date (v{local_ver}){R2}                          \n")
        return

    print(f"\r{Y}  ✦ Update: v{local_ver} → v{remote_ver}{R2}                    ")
    print(f"  {D}Downloading…{R2}", end="", flush=True)

    new_code = _http_get(SCRIPT_URL)
    if not new_code or len(new_code) < 1000:
        print(f"\r\033[38;5;196m  ✗ Download failed — keeping current version.{R2}\n"); return

    # validate python syntax before overwriting
    try:
        import ast as _ast; _ast.parse(new_code)
    except SyntaxError:
        print(f"\r\033[38;5;196m  ✗ Downloaded file invalid — aborting.{R2}\n"); return

    # checksum verification against published manifest
    import hashlib as _hashlib
    new_code_hash = _hashlib.sha256(new_code.encode("utf-8")).hexdigest()
    checksums_raw = _http_get(f"{REPO_RAW}/checksums.txt")
    verified = False
    if checksums_raw:
        for line in checksums_raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[1].endswith("cybersh_direct.py"):
                expected_hash = parts[0].lower()
                if expected_hash == new_code_hash:
                    verified = True
                else:
                    print(f"\r\033[38;5;196m  ✗ Checksum mismatch — aborting update for your safety.{R2}\n"
                          f"  {D}This may indicate a corrupted download or a MITM attack.{R2}\n")
                    return
                break

    if not verified:
        print(f"\r\033[38;5;226m  ⚠ No checksum manifest found — cannot verify authenticity.{R2}")
        print(f"  {D}SHA-256: {new_code_hash}{R2}")
        try:
            ans = input(f"  {Y}Install unverified update? [y/N]: {R2}").strip().lower()
        except (EOFError, KeyboardInterrupt):
            ans = "n"
        if ans != "y":
            print(f"  {D}Update cancelled.{R2}\n")
            return

    # backup
    backup = this_file + f".backup_v{local_ver}"
    try:
        import shutil as _sh; _sh.copy2(this_file, backup)
        print(f"\r  {D}Backup: {os.path.basename(backup)}{R2}                         ")
    except Exception:
        pass

    # atomic write — temp file + os.replace() prevents corruption on crash/power loss
    try:
        tmp_path = this_file + ".tmp_update"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(new_code)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, this_file)
    except PermissionError:
        print(f"\r\033[38;5;196m  ✗ Permission denied. Try: chmod +w {this_file}{R2}\n"); return
    except Exception as e:
        print(f"\r\033[38;5;196m  ✗ Write error: {e}{R2}\n"); return

    # install/update dependencies
    new_reqs = _http_get(REQS_URL)
    if new_reqs:
        pkgs = [l.strip() for l in new_reqs.splitlines()
                if l.strip() and not l.startswith("#") and not l.startswith("-")]
        if pkgs:
            print(f"  {C}📦 Installing dependencies…{R2}")
            _install_packages(pkgs)

    print(f"\n{G}{B}  ✓ Updated to v{remote_ver} — restarting!{R2}\n")
    time.sleep(1)
    # Pass --no-update so the restarted process skips the update check
    # and doesn't loop back into another update cycle.
    # Also strip --update so a manual `--update` run doesn't loop either.
    restart_args = [a for a in sys.argv[1:] if a != "--update"]
    if "--no-update" not in restart_args:
        restart_args = ["--no-update"] + restart_args
    os.execv(sys.executable, [sys.executable, this_file] + restart_args)

# ══════════════════════════════════════════════════════════════
#  ANSI
# ══════════════════════════════════════════════════════════════
R      = "\033[0m";  BOLD  = "\033[1m";  DIM   = "\033[2m"
NEON_G = "\033[38;5;82m";  NEON_C = "\033[38;5;51m"
NEON_P = "\033[38;5;201m"; NEON_Y = "\033[38;5;226m"
NEON_O = "\033[38;5;208m"; NEON_R = "\033[38;5;196m"
BOLD_C = f"\033[1m{NEON_C}"; BOLD_Y = f"\033[1m{NEON_Y}"
CLEAR  = "\033[2K\r"

def _enable_windows_ansi() -> None:
    """Native cmd.exe doesn't render ANSI escape codes unless virtual
    terminal processing is explicitly turned on. Without this, every
    NEON_*/color constant above prints as raw garbage on plain Windows
    consoles instead of an actual color."""
    if os.name != "nt":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
    except Exception:
        pass

_enable_windows_ansi()

# ══════════════════════════════════════════════════════════════
#  RICH INPUT BAR — Claude-style typing experience
# ══════════════════════════════════════════════════════════════
ALL_COMMANDS = [
    "/vibe","/sec","/code","/chat","/agent","/help","/exit","/quit",
    "/clear","/history","/temp","/info","/save","/f","/o","/run","/copy",
    "/recon","/payload","/explain","/cvesearch","/web","/models",
    "/tldr","/howto","/fix","/passgen","/encode","/syswatch",
    "/benchmark","/note","/notes","/tip",
    "/explaincode","/roast","/challenge","/recap","/translate","/weather",
    "/timer","/rename","/regex","/git","/ctf","/diff",
    "/remember","/memories","/memory","/forget",
    "/persona","/summarize","/calc","/goals","/goal",
    "/session",
    "/convert","/qr","/speedtest","/pwcheck",
    "/debug","/review","/template","/gitlog",
    "/hash","/headers","/osint","/wordlist",
    "/think","/debate","/improve","/eli5",
    "/uuid","/cheatsheet","/json","/base","/color","/slugify","/lorem",
    "/countdown","/ip","/clock","/gist","/cron","/quiz","/name","/image",
    "/fetch","/fetchauth","/fetchsites","/fetchforget",
    "/see","/rag",
    "/testgen","/docstring","/complexity","/gitdiff","/commitmsg",
    "/todo","/gitignore","/license","/lint","/profile",
    "/plugins",
    "/model","/context","/regen","/compact","/export","/undo",
    "--update","--no-update",
]

class RichInput:
    """Claude-style input bar with autocomplete, history nav, and live char count."""

    def __init__(self):
        self._setup_readline()

    def _setup_readline(self):
        try:
            readline.set_completer(self._completer)
            readline.set_completer_delims(" \t")
            readline.parse_and_bind("tab: complete")
            # history
            hist = os.path.expanduser("~/.cybersh_input_history")
            try:
                readline.read_history_file(hist)
            except FileNotFoundError:
                pass
            readline.set_history_length(500)
            import atexit
            atexit.register(readline.write_history_file, hist)
        except Exception:
            pass

    def _completer(self, text, state):
        options = [c for c in ALL_COMMANDS if c.startswith(text)]
        return options[state] if state < len(options) else None

    def read(self, prompt: str, multiline_hint: bool = True) -> str:
        """Read input with rich prompt. Returns stripped text."""
        try:
            text = input(prompt)
            return text.strip()
        except (EOFError, KeyboardInterrupt):
            raise KeyboardInterrupt

_rich_input = RichInput()

def rich_prompt(mode_color: str, icon: str, cwd: str) -> str:
    """Render the Claude-style input bar and return user input."""
    w = min(shutil.get_terminal_size((80, 24)).columns, 80)

    # top border
    sys.stdout.write(f"\n{DIM}{'─' * w}{R}\n")

    # prompt line
    prompt = f"{mode_color}{BOLD}{icon} {R}{NEON_C}[{cwd}]{R}{DIM} ▶ {R}"
    try:
        text = _rich_input.read(prompt)
    except KeyboardInterrupt:
        print()
        raise

    return text

# ══════════════════════════════════════════════════════════════
#  EXPERIMENTAL FEATURES
# ══════════════════════════════════════════════════════════════

def cmd_explain_code(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Paste a code snippet and AI explains every line."""
    if arg:
        code = arg
    else:
        print(f"{NEON_Y}Paste your code (type END on a new line when done):{R}")
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "END": break
                lines.append(line)
            except EOFError: break
        code = "\n".join(lines)
    if not code: return ""
    return ask(cfg, messages, session_msgs,
        f"Explain this code line by line in plain English. "
        f"Format each explanation as: `line` → what it does.\n\n```\n{code}\n```")

def cmd_roast(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """AI roasts your code — finds bad practices with humor."""
    code = arg
    if not code:
        print(f"{NEON_Y}Paste your code to roast (END to finish):{R}")
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "END": break
                lines.append(line)
            except EOFError: break
        code = "\n".join(lines)
    if not code: return ""
    return ask(cfg, messages, session_msgs,
        f"Roast this code like a senior dev who's seen it all. "
        f"Be funny but accurate — point out every bad practice, naming issue, "
        f"security hole, and inefficiency. Then at the end give the fixed version.\n\n```\n{code}\n```")

def cmd_challenge(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """AI gives you a coding or hacking challenge to solve."""
    level = arg.lower() if arg else "medium"
    mode  = cfg.get("mode", "chat")
    if mode == "sec":
        topic = "penetration testing or CTF"
    elif mode in ("code", "vibe"):
        topic = "programming"
    else:
        topic = "Linux or general tech"
    return ask(cfg, messages, session_msgs,
        f"Give me a {level} difficulty {topic} challenge. "
        f"Format: 1) Challenge title. 2) Description. 3) What I need to do. "
        f"4) Hints (hidden in a spoiler block using >! syntax). "
        f"5) What a correct solution looks like (also hidden). Make it fun and interesting.")

def cmd_recap(messages: list) -> None:
    """AI-style recap of this session so far."""
    w   = min(shutil.get_terminal_size((80,24)).columns, 70)
    div = f"{NEON_C}{'─'*w}{R}"
    print(f"\n{div}")
    print(f"{NEON_C}{BOLD}  📋 Session Recap{R}")
    print(div)
    count = 0
    for m in messages:
        if m["role"] == "user" and not m["content"].startswith("["):
            count += 1
            preview = textwrap.shorten(m["content"], 65)
            print(f"  {NEON_Y}{count:>2}.{R} {preview}")
    if count == 0:
        print(f"  {DIM}No messages yet.{R}")
    print(f"\n  {DIM}Total exchanges: {count}{R}")
    print(f"{div}\n")

def cmd_translate(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Translate any text to any language — single clean output, no looping."""
    if not arg:
        print(f"{NEON_Y}Usage: /translate <language> <text>")
        print(f"Example: /translate arabic Hello how are you{R}\n")
        return ""
    parts = arg.split(maxsplit=1)
    lang  = parts[0]
    text  = parts[1] if len(parts) > 1 else ""
    if not text:
        print(f"{NEON_Y}Usage: /translate <language> <text>{R}\n"); return ""

    # isolated one-shot call — does NOT pollute main conversation history,
    # which is what was causing repeated/looping translations on long chats
    isolated_messages = [
        {"role": "system", "content":
            "You are a translation engine. Output ONLY the translated text. "
            "No explanations, no notes, no repeating the original, no extra lines. "
            "One clean translation and nothing else."},
        {"role": "user", "content": f"Translate to {lang}:\n{text}"},
    ]
    w   = min(cols(), 60)
    div = f"{NEON_C}{'─'*w}{R}"
    print(f"\n{div}")
    print(f"{NEON_C}{BOLD}  🌍 Translate → {lang.title()}{R}")
    print(div + "\n")
    parts_out = []
    try:
        for token in stream_local(cfg, isolated_messages):
            sys.stdout.write(token); sys.stdout.flush()
            parts_out.append(token)
    except KeyboardInterrupt:
        print(f"\n{NEON_Y}[interrupted]{R}")
    result = "".join(parts_out).strip()
    print(f"\n\n{div}\n")
    return result

def cmd_weather_ascii(arg: str) -> None:
    """Fetch weather as ASCII art using wttr.in."""
    loc = arg.strip() or ""
    url = f"https://wttr.in/{loc}?A"
    print(f"\n{NEON_C}🌤 Fetching weather…{R}\n")
    r = subprocess.run(["curl","-s","--max-time","5", url],
                       capture_output=True, text=True)
    if r.returncode == 0 and r.stdout:
        print(r.stdout)
    else:
        print(f"{NEON_R}✗ Could not fetch weather. Check internet.{R}\n")

def cmd_timer(arg: str) -> None:
    """Countdown timer. /timer 5m or /timer 30s or /timer 1h"""
    import time as _time
    if not arg:
        print(f"{NEON_Y}Usage: /timer 30s | /timer 5m | /timer 1h{R}\n"); return
    arg = arg.strip().lower()
    try:
        if arg.endswith("h"):   secs = int(arg[:-1]) * 3600
        elif arg.endswith("m"): secs = int(arg[:-1]) * 60
        elif arg.endswith("s"): secs = int(arg[:-1])
        else:                   secs = int(arg)
    except ValueError:
        print(f"{NEON_R}✗ Invalid time. Use 30s, 5m, or 1h.{R}\n"); return

    total = secs
    print(f"\n{NEON_C}⏱  Timer: {arg}{R}  {DIM}(Ctrl+C to stop){R}\n")
    try:
        while secs > 0:
            h, rem = divmod(secs, 3600)
            m, s   = divmod(rem, 60)
            bar_w  = 30
            filled = int(bar_w * (total - secs) / total)
            bar    = f"{NEON_G}{'█'*filled}{DIM}{'░'*(bar_w-filled)}{R}"
            ts     = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
            sys.stdout.write(f"\r  {bar}  {NEON_Y}{BOLD}{ts}{R}  ")
            sys.stdout.flush()
            _time.sleep(1)
            secs -= 1
        sys.stdout.write(f"\r{CLEAR}")
        print(f"\n{NEON_G}{BOLD}  ✓ TIME'S UP! 🔔{R}\n")
        # terminal bell
        sys.stdout.write("\a"); sys.stdout.flush()
    except KeyboardInterrupt:
        sys.stdout.write(f"\r{CLEAR}")
        print(f"\n{NEON_Y}  Timer stopped.{R}\n")

def cmd_ai_rename(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """AI suggests better names for variables, functions, files."""
    if not arg:
        print(f"{NEON_Y}Usage: /rename <name>  — AI suggests better names{R}\n"); return ""
    return ask(cfg, messages, session_msgs,
        f"Suggest 5 better names for this identifier: `{arg}`\n"
        f"Consider: clarity, convention (snake_case for Python, camelCase for JS), "
        f"and what the name implies. Format as a numbered list with a one-line reason for each.")

def cmd_regex(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """AI writes a regex for you."""
    if not arg:
        print(f"{NEON_Y}Usage: /regex <describe what to match>{R}\n"); return ""
    return ask(cfg, messages, session_msgs,
        f"Write a regex pattern for: {arg}\n"
        f"Format: 1) The pattern. 2) Language-specific examples (Python, JS, grep). "
        f"3) Explanation of each part. 4) Test cases showing matches and non-matches.")

def cmd_githelp(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """AI explains or generates git commands."""
    if not arg:
        print(f"{NEON_Y}Usage: /git <what you want to do>{R}\n"); return ""
    return ask(cfg, messages, session_msgs,
        f"Git help: {arg}\n"
        f"Give the exact git command(s) to accomplish this. "
        f"If there are multiple approaches, show the safest one first. "
        f"Add a one-line warning if the command is destructive (rebase, force push, reset --hard etc).")

def cmd_ctf(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """CTF challenge helper — analyze flags, hints, encodings."""
    if not arg:
        print(f"{NEON_Y}Usage: /ctf <paste challenge text or data>{R}\n"); return ""
    return ask(cfg, messages, session_msgs,
        f"CTF challenge analysis:\n{arg}\n\n"
        f"Identify: 1) Challenge category (crypto, forensics, web, pwn, rev, misc). "
        f"2) Any encodings or ciphers present. 3) Tools to use. "
        f"4) Step-by-step approach to solve it. Don't give the flag directly — guide me.")

def cmd_diff_explain(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Paste a git diff and AI explains what changed and why it matters."""
    diff = arg
    if not diff:
        print(f"{NEON_Y}Paste your git diff (END to finish):{R}")
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "END": break
                lines.append(line)
            except EOFError: break
        diff = "\n".join(lines)
    if not diff: return ""
    return ask(cfg, messages, session_msgs,
        f"Explain this git diff in plain English:\n```diff\n{diff}\n```\n"
        f"Cover: what changed, why it might have changed, any risks or bugs introduced.")



# ══════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════
CONFIG_PATH = os.path.expanduser("~/.cybersh_direct.json")
DEFAULT_CFG = {
    "model_path":     "",
    "context":        4096,
    "temperature":    0.7,
    "max_tokens":     2048,
    "mode":           "chat",
    "history_file":   os.path.expanduser("~/.cybersh_direct_history.json"),
    "max_history":    60,
    "threads":        4,
    "max_agent_iters": 12,     # auto tool round-trips per turn (coding tasks need many steps)
    "vision_model_path": "",   # multimodal .gguf (e.g. moondream2)
    "vision_mmproj_path": "",  # matching --mmproj clip projector file
    "rag_enabled":    True,    # allow /rag commands to build a local index
    "prompt_cache_enabled": True,  # cache KV-state directly on the loaded gguf model in RAM
    "prompt_cache_mb": 256,        # RAM budget for that cache, per loaded model
    "auto_trim_context": True,     # drop oldest turns instead of crashing when context fills up
}

# well-known GGUF download links (free, official)
KNOWN_MODELS = {
    "1": {
        "name":  "Phi-3 Mini (2.2GB) — Microsoft, great for code",
        "file":  "Phi-3-mini-4k-instruct-q4.gguf",
        "url":   "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf",
    },
    "2": {
        "name":  "TinyLlama 1.1B (638MB) — fastest, lightest",
        "file":  "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "url":   "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
    },
    "3": {
        "name":  "Qwen2.5 1.5B (986MB) — smart small model",
        "file":  "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "url":   "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf",
    },
    "4": {
        "name":  "Mistral 7B (4.1GB) — powerful, best quality",
        "file":  "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "url":   "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
    },
    "5": {
        "name":  "Llama 3.2 3B (2.0GB) — Meta, smarter than TinyLlama ★ RECOMMENDED",
        "file":  "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "url":   "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
    },
    "6": {
        "name":  "Qwen2.5 7B (4.7GB) — best for code & reasoning",
        "file":  "qwen2.5-7b-instruct-q4_k_m.gguf",
        "url":   "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf",
    },
    "7": {
        "name":  "DeepSeek-R1 7B (4.7GB) — reasoning model, thinks step-by-step",
        "file":  "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
        "url":   "https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-7B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
    },
}

# SHA-256 checksums for known models. None = not yet published (warns but proceeds).
# Update these from the official model card or HuggingFace file page.
KNOWN_MODEL_SHA256: dict[str, "str | None"] = {
    "1": None,  # Phi-3 Mini   — update when checksum is published
    "2": None,  # TinyLlama
    "3": None,  # Qwen2.5 1.5B
    "4": None,  # Mistral 7B
    "5": None,  # Llama 3.2 3B
    "6": None,  # Qwen2.5 7B
    "7": None,  # DeepSeek-R1 7B
}

def _verify_model_sha256(path: str, expected, label: str) -> bool:
    """Verify downloaded model SHA-256. Returns False on mismatch (file deleted)."""
    import hashlib as _hl
    if expected is None:
        print(f"{NEON_Y}⚠  No checksum for {label} — cannot verify integrity. "
              f"Verify manually if security matters.{R}")
        return True
    print(f"{DIM}  Verifying SHA-256…{R}", end="", flush=True)
    h = _hl.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        digest = h.hexdigest()
        if digest.lower() == expected.lower():
            print(f"\r{NEON_G}✓ Checksum verified.{R}                    ")
            return True
        print(f"\r{NEON_R}✗ Checksum MISMATCH for {label}!{R}")
        print(f"  {DIM}Expected: {expected}{R}")
        print(f"  {DIM}Got:      {digest}{R}")
        print(f"  {NEON_R}Deleting potentially corrupted/tampered file.{R}")
        try:
            import os as _os; _os.remove(path)
        except Exception:
            pass
        return False
    except Exception as e:
        print(f"\r{NEON_Y}⚠  Could not read file for verification: {e}{R}")
        return True


# Known multimodal (vision) GGUF model + mmproj (clip projector) pairs.
# Both files are required — the mmproj is what actually encodes the image.
KNOWN_VISION_MODELS = {
    "1": {
        "name":        "LLaVA-Phi-3-mini (2.9GB total) — small & fast, recommended",
        "file":        "llava-phi-3-mini-int4.gguf",
        "mmproj_file": "llava-phi-3-mini-mmproj-f16.gguf",
        "url":         "https://huggingface.co/xtuner/llava-phi-3-mini-gguf/resolve/main/llava-phi-3-mini-int4.gguf",
        "mmproj_url":  "https://huggingface.co/xtuner/llava-phi-3-mini-gguf/resolve/main/llava-phi-3-mini-mmproj-f16.gguf",
        "handler":     "llava-1-5",
    },
    "2": {
        "name":        "LLaVA 1.5 7B (8.5GB total) — higher quality, slower",
        "file":        "ggml-model-q4_k.gguf",
        "mmproj_file": "mmproj-model-f16.gguf",
        "url":         "https://huggingface.co/mys/ggml_llava-v1.5-7b/resolve/main/ggml-model-q4_k.gguf",
        "mmproj_url":  "https://huggingface.co/mys/ggml_llava-v1.5-7b/resolve/main/mmproj-model-f16.gguf",
        "handler":     "llava-1-5",
    },
}

def vision_setup_wizard(cfg: dict) -> None:
    """Download and configure a vision (image-understanding) model."""
    print(f"\n{BOLD_C}{'─'*60}")
    print(f"  VISION SETUP — pick a multimodal model")
    print(f"{'─'*60}{R}\n")
    print(f"{NEON_Y}Already have a model + mmproj pair? [y/N]: {R}", end="")
    has = input().strip().lower()

    if has == "y":
        print(f"{NEON_C}Path to vision .gguf model: {R}", end="")
        mp = os.path.expanduser(input().strip())
        print(f"{NEON_C}Path to matching mmproj (clip) .gguf: {R}", end="")
        cp = os.path.expanduser(input().strip())
        if os.path.exists(mp) and os.path.exists(cp):
            cfg["vision_model_path"]  = mp
            cfg["vision_mmproj_path"] = cp
            save_cfg(cfg)
            print(f"{NEON_G}✓ Vision model configured.{R}\n")
        else:
            print(f"{NEON_R}✗ One or both files not found.{R}\n")
        return

    print(f"\n{NEON_Y}Available vision models:{R}\n")
    for k, m in KNOWN_VISION_MODELS.items():
        print(f"  {NEON_C}[{k}]{R} {m['name']}")
    print(f"\n{NEON_Y}Choose [1-{len(KNOWN_VISION_MODELS)}] or Enter to cancel: {R}", end="")
    choice = input().strip()
    if choice not in KNOWN_VISION_MODELS:
        print(f"{DIM}Cancelled.{R}\n"); return

    model  = KNOWN_VISION_MODELS[choice]
    dl_dir = os.path.expanduser("~/ollama-models")
    os.makedirs(dl_dir, exist_ok=True)
    dest_m = os.path.join(dl_dir, model["file"])
    dest_c = os.path.join(dl_dir, model["mmproj_file"])

    print(f"\n{NEON_C}Downloading model…{R}")
    ok1 = _download_file(model["url"], dest_m, label=model["file"])
    print(f"{NEON_C}Downloading mmproj (clip projector)…{R}")
    ok2 = _download_file(model["mmproj_url"], dest_c, label=model["mmproj_file"])

    if ok1 and ok2:
        ok1 = _verify_model_sha256(dest_m, model.get("sha256"), model["file"])
        ok2 = _verify_model_sha256(dest_c, model.get("mmproj_sha256"), model["mmproj_file"])

    if ok1 and ok2 and os.path.exists(dest_m) and os.path.exists(dest_c):
        cfg["vision_model_path"]  = dest_m
        cfg["vision_mmproj_path"] = dest_c
        save_cfg(cfg)
        print(f"\n{NEON_G}✓ Vision model ready! Try: /see <image_path> what's in this?{R}\n")
    else:
        print(f"{NEON_R}✗ Download failed. Re-run /see setup to try again, "
              f"or download the files manually and point to them.{R}\n")


_vision_llm_instance = None

def get_vision_llm(cfg: dict):
    """Lazily load a separate llama-cpp instance with a multimodal chat handler."""
    global _vision_llm_instance
    if _vision_llm_instance is not None:
        return _vision_llm_instance

    mp = cfg.get("vision_model_path", "").strip()
    cp = cfg.get("vision_mmproj_path", "").strip()
    if not mp or not cp or not os.path.exists(mp) or not os.path.exists(cp):
        raise RuntimeError("No vision model configured — run: /see setup")

    from llama_cpp import Llama
    from llama_cpp.llama_chat_format import Llava15ChatHandler

    print(f"{DIM}  Loading vision model (first use only)…{R}")
    handler = Llava15ChatHandler(clip_model_path=cp, verbose=False)
    n_gpu_layers = -1 if _detect_gpu()["type"] == "nvidia" else 0
    _vision_llm_instance = Llama(
        model_path   = mp,
        chat_handler = handler,
        n_ctx        = 4096,
        n_threads    = cfg.get("threads", 4),
        n_gpu_layers = n_gpu_layers,
        logits_all   = True,   # required by some llava chat handlers
        verbose      = False,
    )
    _attach_prompt_cache(_vision_llm_instance, cfg, label="vision model")
    return _vision_llm_instance

def cmd_vision(arg: str, cfg: dict) -> None:
    """/see <image_path> [question] — analyze an image with a local vision model."""
    if not arg:
        print(f"{NEON_Y}Usage: /see <image_path> [question]{R}")
        print(f"{DIM}       /see setup   — download/configure a vision model{R}\n")
        return

    if arg.strip().lower() == "setup":
        vision_setup_wizard(cfg)
        return

    parts    = arg.split(maxsplit=1)
    img_path = os.path.expanduser(parts[0])
    question = parts[1] if len(parts) > 1 else "Describe this image in detail."

    if not os.path.exists(img_path):
        print(f"{NEON_R}✗ Image not found: {img_path}{R}\n")
        return

    try:
        llm = get_vision_llm(cfg)
    except Exception as e:
        print(f"{NEON_R}✗ {e}{R}\n")
        return

    import base64, mimetypes
    mime = mimetypes.guess_type(img_path)[0] or "image/jpeg"
    with open(img_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    data_uri = f"data:{mime};base64,{b64}"

    bw = min(cols(), 62)
    print(f"\n{NEON_P}{'▓'*bw}{R}")
    print(f"{NEON_P}{BOLD}  👁  VISION{R}")
    print(f"{NEON_P}{'▓'*bw}{R}\n")

    start = time.time()
    try:
        resp = llm.create_chat_completion(
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_uri}},
                    {"type": "text", "text": question},
                ],
            }],
            max_tokens=1024,
        )
        answer = resp["choices"][0]["message"]["content"]
        print(answer)
    except Exception as e:
        print(f"{NEON_R}✗ Vision inference failed: {e}{R}\n")
        return

    elapsed = time.time() - start
    print(f"\n\n{DIM}  ⏱ {elapsed:.1f}s{R}\n")


def load_cfg() -> dict:
    cfg = DEFAULT_CFG.copy()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f: cfg.update(json.load(f))
        except: pass
    return cfg

def save_cfg(cfg: dict) -> None:
    with open(CONFIG_PATH, "w") as f: json.dump(cfg, f, indent=2)
    print(f"\n{NEON_G}✓ Config saved → {CONFIG_PATH}{R}")

# ══════════════════════════════════════════════════════════════
#  WEB SEARCH (DuckDuckGo — no API key needed)
# ══════════════════════════════════════════════════════════════
def web_search(query: str, max_results: int = 5) -> str:
    """Search DuckDuckGo and return results as text. No API key needed."""
    try:
        from ddgs import DDGS
    except ImportError:
        return (
            f"{NEON_R}✗ ddgs not installed.{R}\n"
            f"{NEON_Y}Fix:{R} pip install ddgs --break-system-packages"
        )
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(
                    f"[{r.get('title','')}]\n{r.get('href','')}\n{r.get('body','')}"
                )
        if not results:
            return "No results found."
        return "\n\n".join(results)
    except Exception as e:
        return f"Search error: {e}"

# ══════════════════════════════════════════════════════════════
#  LOCAL RAG — offline retrieval over your own files, no cloud
# ══════════════════════════════════════════════════════════════
RAG_DIR        = os.path.expanduser("~/.cybersh_rag")
RAG_INDEX_PATH = os.path.join(RAG_DIR, "index.json")
RAG_CHUNK_SIZE = 900
RAG_OVERLAP    = 150
RAG_TEXT_EXTS  = {".txt",".md",".py",".js",".ts",".json",".yaml",".yml",".log",
                  ".c",".cpp",".h",".java",".go",".rs",".sh",".conf",".cfg",".ini",".csv"}

_embed_instance = None  # separate Llama instance, lazily loaded with embedding=True

def _ensure_rag_dir() -> None:
    os.makedirs(RAG_DIR, exist_ok=True)

def get_embedder(cfg: dict):
    """Lazily load a second llama-cpp instance (same model) in embedding mode.
    Kept separate from the chat instance since llama-cpp-python needs
    embedding=True at construction time to use .embed()."""
    global _embed_instance
    if _embed_instance is not None:
        return _embed_instance
    from llama_cpp import Llama
    model_path = cfg.get("model_path","").strip()
    if not model_path or not os.path.exists(model_path):
        raise RuntimeError("No model loaded — run --setup first.")
    print(f"{DIM}  Loading embedding model (first RAG use only)…{R}")
    _embed_instance = Llama(
        model_path = model_path,
        n_ctx      = 2048,
        n_threads  = cfg.get("threads", 4),
        embedding  = True,
        verbose    = False,
    )
    _attach_prompt_cache(_embed_instance, cfg, label="RAG embedder")
    return _embed_instance

def embed_text(text: str, cfg: dict) -> list:
    """Return a single flat embedding vector for a piece of text."""
    llm = get_embedder(cfg)
    out = llm.embed(text)
    # llama-cpp-python may return a single vector or a list-of-token-vectors —
    # normalize to one mean-pooled vector either way.
    if out and isinstance(out[0], (list, tuple)):
        dim = len(out[0])
        pooled = [0.0] * dim
        for vec in out:
            for i, v in enumerate(vec):
                pooled[i] += v
        n = len(out)
        return [v / n for v in pooled]
    return list(out)

def _cosine(a: list, b: list) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x*y for x, y in zip(a, b))
    na  = sum(x*x for x in a) ** 0.5
    nb  = sum(y*y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)

def chunk_text(text: str, size: int = RAG_CHUNK_SIZE, overlap: int = RAG_OVERLAP) -> list:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks, i = [], 0
    while i < len(text):
        chunks.append(text[i:i+size])
        i += max(1, size - overlap)
    return chunks

_RAG_INDEX_CACHE  = None
_RAG_INDEX_MTIME  = None

def rag_load_index() -> list:
    """Return the RAG index, served from RAM whenever the on-disk sub-file
    hasn't changed since the last read."""
    global _RAG_INDEX_CACHE, _RAG_INDEX_MTIME
    if not os.path.exists(RAG_INDEX_PATH):
        _RAG_INDEX_CACHE, _RAG_INDEX_MTIME = [], None
        return []
    try:
        mtime = os.path.getmtime(RAG_INDEX_PATH)
        if _RAG_INDEX_CACHE is not None and mtime == _RAG_INDEX_MTIME:
            return _RAG_INDEX_CACHE
        with open(RAG_INDEX_PATH) as f:
            _RAG_INDEX_CACHE = json.load(f)
        _RAG_INDEX_MTIME = mtime
        return _RAG_INDEX_CACHE
    except Exception:
        return _RAG_INDEX_CACHE or []

def rag_save_index(index: list) -> None:
    global _RAG_INDEX_CACHE, _RAG_INDEX_MTIME
    _ensure_rag_dir()
    with open(RAG_INDEX_PATH, "w") as f:
        json.dump(index, f)
    _RAG_INDEX_CACHE = index
    _RAG_INDEX_MTIME = os.path.getmtime(RAG_INDEX_PATH)

def rag_index_path(path: str, cfg: dict) -> str:
    """Index a file or directory into the local RAG store. Returns a status string."""
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return f"✗ Not found: {path}"

    files = []
    if os.path.isdir(path):
        for root, _, fnames in os.walk(path):
            if "/.git" in root or "/node_modules" in root:
                continue
            for fn in fnames:
                if os.path.splitext(fn)[1].lower() in RAG_TEXT_EXTS:
                    files.append(os.path.join(root, fn))
    else:
        files = [path]

    if not files:
        return f"✗ No indexable text files found under {path}"

    index      = rag_load_index()
    seen_hashes = {e["hash"] for e in index}
    added, skipped = 0, 0
    import hashlib as _hl

    for fp in files[:500]:
        try:
            if os.path.getsize(fp) > 5_000_000:  # skip anything absurdly large
                skipped += 1; continue
            with open(fp, "r", errors="ignore") as f:
                content = f.read()
        except Exception:
            skipped += 1; continue

        for chunk in chunk_text(content):
            h = _hl.sha256((fp + chunk).encode()).hexdigest()
            if h in seen_hashes:
                continue
            try:
                vec = embed_text(chunk, cfg)
            except Exception as e:
                return f"✗ Embedding failed: {e}"
            index.append({"hash": h, "source": fp, "text": chunk, "embedding": vec})
            seen_hashes.add(h)
            added += 1

    rag_save_index(index)
    return f"✓ Indexed {added} new chunk(s) from {len(files)} file(s) ({skipped} skipped)."

def rag_search(query: str, cfg: dict, top_k: int = 4) -> list:
    """Return the top_k most relevant chunks for a query."""
    index = rag_load_index()
    if not index:
        return []
    try:
        qvec = embed_text(query, cfg)
    except Exception:
        return []
    scored = [(_cosine(qvec, e["embedding"]), e) for e in index]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"source": e["source"], "text": e["text"], "score": s}
            for s, e in scored[:top_k] if s > 0]

# ══════════════════════════════════════════════════════════════
#  MODES
# ══════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════
#  ENVIRONMENT CONTEXT — injected into every system prompt
# ══════════════════════════════════════════════════════════════
_ENV_CACHE = None

def get_project_context() -> str:
    """Read an optional CYBERSH.md (or .cybersh.md) in the current directory
    and feed it into the system prompt — same idea as Claude Code's
    CLAUDE.md: a place for project-specific conventions, build/test commands,
    and context the AI should always have for this project."""
    for name in ("CYBERSH.md", ".cybersh.md"):
        path = os.path.join(os.getcwd(), name)
        if os.path.isfile(path):
            try:
                with open(path, "r", errors="ignore") as f:
                    content = f.read(8000)
                if content.strip():
                    return f"\n\n[PROJECT CONTEXT from {name} — follow these project-specific " \
                           f"conventions and instructions:]\n{content.strip()}"
            except Exception:
                pass
    return ""

def get_env_context() -> str:
    """Build a short OS/environment description for the AI system prompt.
    Cached after first call since OS and cwd don't change mid-session.
    Deliberately includes the exact python binary, shell, cwd, and git
    status — these are the concrete facts that stop the model from
    guessing wrong (e.g. running `python` on a system that only has
    `python3`) instead of just naming the OS."""
    global _ENV_CACHE
    if _ENV_CACHE:
        return _ENV_CACHE

    os_info = _detect_os()
    distro  = os_info.get("distro") or os_info.get("system","Unknown")
    pkg_mgr = os_info.get("pkg_mgr")

    pkg_examples = {
        "apt":    "apt install <pkg>  (Debian/Ubuntu/Kali/Parrot)",
        "dnf":    "dnf install <pkg>  (Fedora/RHEL)",
        "pacman": "pacman -S <pkg>    (Arch/Manjaro)",
        "zypper": "zypper install <pkg> (openSUSE)",
        "apk":    "apk add <pkg>      (Alpine)",
        "brew":   "brew install <pkg> (macOS)",
    }
    pkg_line = pkg_examples.get(pkg_mgr, "")

    # which python command actually exists — the #1 avoidable "command not
    # found" error is assuming `python` when only `python3` is installed
    py_cmd = "python3" if shutil.which("python3") else ("python" if shutil.which("python") else None)
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    pip_flag = " --break-system-packages" if os_info.get("pip_flag") else ""

    shell_name = os.path.basename(os.environ.get("SHELL", "")) or ("cmd.exe" if os.name == "nt" else "unknown")

    cwd = os.getcwd()
    in_git = os.path.isdir(os.path.join(cwd, ".git")) or shutil.which("git") and subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"], cwd=cwd,
        capture_output=True, text=True, timeout=3
    ).stdout.strip() == "true"

    facts = [f"OS: {distro}", f"Shell: {shell_name}", f"CWD: {cwd}"]
    if py_cmd:
        facts.append(f"Python: run it as `{py_cmd}` (v{py_ver}) — do NOT assume `python` exists, use `{py_cmd}` explicitly")
    else:
        facts.append("Python: no python interpreter found on PATH — flag this instead of assuming one exists")
    if pkg_mgr:
        facts.append(f"Package manager: {pkg_mgr} — use '{pkg_line}'{(' with ' + pip_flag.strip()) if pip_flag else ''}, never suggest a different one")
    facts.append(f"Git repo: {'yes' if in_git else 'no'} — " + ("git commands are safe to use here" if in_git
                 else "this directory is NOT a git repo, don't assume git history/branches exist"))

    _ENV_CACHE = (
        "[SYSTEM ENVIRONMENT — concrete facts about THIS machine, use them exactly, "
        "don't guess or assume a different setup:]\n- " + "\n- ".join(facts) + "\n"
        "Always tailor shell commands, package install instructions, and file paths to "
        "these exact facts. If a command you'd normally reach for isn't confirmed above "
        "(e.g. a specific tool's presence), check with `which <tool>` before relying on it "
        "instead of assuming it's installed."
        + get_project_context()
    )
    return _ENV_CACHE

_GLOBAL_RULES = (
    "\n\n[OUTPUT RULES — always follow:]\n"
    "- Never repeat yourself or loop the same sentence/explanation more than once.\n"
    "- If you notice you are about to repeat earlier content, STOP and move on.\n"
    "- Be realistic and accurate — do not invent commands, flags, or facts that don't exist. "
    "If unsure, say so briefly instead of guessing confidently.\n"
    "- Write for BOTH beginners and professionals in the same answer: give the direct "
    "technical answer first (for pros), then one short plain-English line clarifying "
    "anything non-obvious (for beginners). Do not write two separate explanations.\n"
    "- Polish every response: no filler, no restating the question, no unnecessary caveats. "
    "Be direct, clean, and confident."
)

MODES = {
    "chat": {
        "icon": "💬", "label": "CHAT", "color": NEON_C,
        "system": "You are CYBER SH AI, a sharp helpful local AI. Be concise and direct." + _GLOBAL_RULES,
    },
    "sec": {
        "icon": "🔐", "label": "SEC", "color": NEON_G,
        "system": (
            "You are an elite offensive security expert and bug bounty hunter. "
            "Help with recon, OSINT, XSS, SQLi, SSRF, LFI, RCE, IDOR, API testing, CVE analysis. "
            "Give real working commands and Python tools. Be technical and precise."
        ) + _GLOBAL_RULES,
    },
    "vibe": {
        "icon": "🎨", "label": "VIBE", "color": NEON_P,
        "system": (
            "You are an expert vibe coder. Build beautiful impressive projects fast. "
            "Write creative elegant code, suggest UI/UX aesthetics, color schemes, animations."
        ) + _GLOBAL_RULES,
    },
    "code": {
        "icon": "⚡", "label": "CODE", "color": NEON_Y,
        "system": (
            "You are an elite, principal-level software engineer — write production-grade "
            "code a senior dev would ship straight to review with no changes requested. "
            "Rules for every answer:\n"
            "1) Default to complete, runnable files, not fragments or diffs, unless the user "
            "explicitly asks for a patch/snippet — assume they'll copy-paste and run it as-is.\n"
            "2) Think about the whole system before writing: correctness, edge cases (empty "
            "input, huge input, concurrency, network failure, malformed data), and how this "
            "code will be used and maintained six months from now.\n"
            "3) Add proper error handling and, for Python, type hints — never let an exception "
            "propagate somewhere the user can't understand it.\n"
            "4) Comment only where it adds real value (why, not what). Include a short usage "
            "example so the user can run it immediately.\n"
            "5) Call out security-relevant issues unprompted (injection, unsafe deserialization, "
            "path traversal, secrets in code, shell=True, etc.) — you are excellent at "
            "security-aware coding, not just feature coding.\n"
            "6) Flag real performance/complexity concerns (Big-O, N+1 queries, blocking I/O) "
            "when they matter for the input sizes implied by the request.\n"
            "7) Prefer clear, boring, correct code over clever code. If there's a real tradeoff "
            "(speed vs. readability, memory vs. simplicity), state it in one line instead of "
            "silently picking one."
        ) + _GLOBAL_RULES,
    },
    "agent": {
        "icon": "🤖", "label": "AGENT", "color": NEON_O,
        "system": (
            "You are CYBER SH AGENT — an autonomous coding agent controlling a Linux computer, "
            "operating the way a careful senior engineer would. "
            "When asked to do things, use ACTION BLOCKS — one per line:\n"
            "ACTION: run_command | <bash command>\n"
            "ACTION: create_file | <filepath> | <content>\n"
            "ACTION: edit_file | <filepath> | <old text> | <new text>\n"
            "ACTION: delete_file | <filepath>\n"
            "ACTION: open_app | <app>\n"
            "ACTION: search_files | <glob pattern>   (find files by name)\n"
            "ACTION: grep_files | <regex> | <path>    (search file CONTENTS — use this to find where "
            "something is defined/used before touching it)\n"
            "ACTION: list_dir | <path>                (see the project structure before editing blind)\n"
            "ACTION: read_file | <filepath>\n"
            "ACTION: make_dir | <path>\n"
            "ACTION: web_search | <query>\n"
            "ACTION: rag_search | <query>   (searches the user's indexed local knowledge base)\n"
            "\n"
            "How to work on a coding task, in order:\n"
            "1) ORIENT before you touch anything — use list_dir and grep_files to understand the "
            "project's structure and conventions. Don't guess at file layout or existing code.\n"
            "2) READ before you EDIT — always read_file the exact section you're about to change so "
            "your old-text match is byte-accurate. Never edit a file you haven't read this turn.\n"
            "3) PREFER edit_file over create_file for existing files — small, targeted, reviewable "
            "changes over full-file rewrites. Only use create_file for genuinely new files. If "
            "edit_file reports the match isn't unique, include more surrounding context and retry.\n"
            "4) VERIFY your own work — after a code change, run_command the relevant test suite, "
            "linter, or a quick syntax/import check (e.g. `python -m py_compile file.py`). If it "
            "fails, read the error, fix it, and re-run. Don't declare a task done on faith.\n"
            "5) MATCH the existing style — same indentation, naming, and patterns already used in "
            "the file, not your own preferences.\n"
            "6) WORK AUTONOMOUSLY through the whole task — chain as many ACTIONs as the task needs "
            "across your available turns without stopping to ask 'should I continue?' Only pause "
            "for the user's approval prompt (which happens automatically on side-effecting actions) "
            "or if the task is genuinely ambiguous about WHAT to build, not HOW.\n"
            "7) DO EXACTLY WHAT WAS ASKED — no more, no less. Don't add extra features, files, "
            "refactors, or 'improvements' the user didn't request. If the request is genuinely "
            "ambiguous about what to build, ask one short clarifying question before acting; if "
            "it's just ambiguous about HOW, pick the most reasonable approach and proceed.\n"
            "8) USE the [SYSTEM ENVIRONMENT] facts below exactly as given — the correct python "
            "command, package manager, shell, and cwd are already detected for you. Don't guess "
            "or assume a different setup. If you need to know whether a specific tool is installed "
            "beyond what's listed, check with `which <tool>` via run_command before relying on it.\n"
            "9) WHEN AN ACTION FAILS, read the actual error text in the tool result and fix the "
            "real cause — wrong path, wrong command name, missing flag, etc. Never re-run the exact "
            "same action expecting a different result; that wastes a turn and won't self-correct.\n"
            "\n"
            "Always explain what you're doing before each ACTION, briefly. "
            "Destructive/side-effecting actions (run_command, create_file, edit_file, delete_file, "
            "open_app, make_dir) require the user's approval each time. Read-only actions "
            "(search_files, grep_files, list_dir, read_file, web_search, rag_search) run immediately "
            "and their output is fed straight back to you automatically — you do NOT need the user "
            "to repeat themselves. Use that output to decide your next ACTION or give a final answer. "
            "Once the task is actually done and verified, stop issuing ACTIONs and give a final "
            "summary of what changed and how you confirmed it works."
        ) + _GLOBAL_RULES,
    },
}

# ══════════════════════════════════════════════════════════════
#  LLAMA CPP WRAPPER
# ══════════════════════════════════════════════════════════════
_llm_instance = None

def _attach_prompt_cache(llm, cfg: dict, label: str = "model") -> None:
    """Feed the model's computed context state directly into RAM on the
    loaded .gguf instance itself, instead of recomputing the whole prompt
    from scratch every turn. llama-cpp-python exposes this via
    Llama.set_cache(LlamaCache(...)) — it keeps recently-seen prompt
    prefixes (system prompt, RAG context, conversation history) resident in
    RAM against THIS model object, so a new turn that shares a prefix with
    a previous one only evaluates the new tail."""
    if not cfg.get("prompt_cache_enabled", True):
        return
    try:
        from llama_cpp import LlamaCache
        cache_mb = max(32, int(cfg.get("prompt_cache_mb", 256)))
        llm.set_cache(LlamaCache(capacity_bytes=cache_mb * 1024 * 1024))
        print(f"{DIM}  ⚡ In-RAM prompt cache attached to {label} ({cache_mb}MB){R}")
    except ImportError:
        pass
    except Exception:
        pass

def get_llm(cfg: dict):
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance
    try:
        from llama_cpp import Llama
    except ImportError:
        print(f"\n{NEON_R}✗ llama-cpp-python not installed!{R}")
        print(f"{NEON_Y}Fix:{R} pip install llama-cpp-python --break-system-packages")
        sys.exit(1)

    model_path = cfg.get("model_path","").strip()
    if not model_path or not os.path.exists(model_path):
        print(f"\n{NEON_R}✗ No model loaded!{R}")
        print(f"{NEON_Y}Run:{R} python3 {sys.argv[0]} --setup")
        sys.exit(1)

    size_gb = os.path.getsize(model_path) / 1e9
    print(f"\n{NEON_C}Loading {BOLD}{os.path.basename(model_path)}{R} "
          f"{DIM}({size_gb:.1f} GB)…{R}")
    print(f"{DIM}This takes 5-15 seconds on first load…{R}\n")

    # ── Auto-detect GPU every time ────────────────────────────
    n_gpu_layers = 0
    gpu_info     = _detect_gpu()

    if gpu_info["type"] == "nvidia":
        # check if llama-cpp-python was built with CUDA support
        try:
            from llama_cpp import llama_supports_gpu_offload
            cuda_ok = llama_supports_gpu_offload()
        except ImportError:
            cuda_ok = False
        except Exception:
            cuda_ok = True  # older versions don't have this fn but may work

        if cuda_ok:
            n_gpu_layers = -1  # -1 = offload ALL layers to GPU
            print(f"{NEON_G}✓ NVIDIA GPU: {gpu_info['name']} ({gpu_info['vram']}) — CUDA ON ⚡{R}\n")
        else:
            print(f"{NEON_Y}⚠ NVIDIA GPU found ({gpu_info['name']}) but CUDA not enabled.{R}")
            print(f"{DIM}  To enable: CMAKE_ARGS=\"-DGGML_CUDA=on\" pip install llama-cpp-python --force-reinstall --break-system-packages{R}")
            print(f"{DIM}  Running on CPU for now.{R}\n")

    elif gpu_info["type"] == "amd":
        print(f"{NEON_Y}⚠ AMD GPU: {gpu_info['name']} detected.{R}")
        print(f"{DIM}  ROCm support is experimental. Running on CPU.{R}")
        print(f"{DIM}  To try GPU: CMAKE_ARGS=\"-DGGML_HIPBLAS=on\" pip install llama-cpp-python --force-reinstall --break-system-packages{R}\n")

    elif gpu_info["type"] == "intel":
        print(f"{NEON_Y}⚠ Intel GPU: {gpu_info['name']} detected.{R}")
        print(f"{DIM}  Intel Arc/iGPU acceleration not yet supported. Running on CPU.{R}\n")

    else:
        print(f"{DIM}  No GPU detected — running on CPU ({cfg.get('threads',4)} threads){R}\n")

    _llm_instance = Llama(
        model_path   = model_path,
        n_ctx        = cfg["context"],
        n_threads    = cfg.get("threads", 4),
        n_gpu_layers = n_gpu_layers,
        verbose      = False,
    )
    _attach_prompt_cache(_llm_instance, cfg, label="chat model")
    print(f"{NEON_G}✓ Model ready!{R}\n")
    return _llm_instance


def _detect_gpu() -> dict:
    """Detect GPU type, name, and VRAM. Returns dict with type/name/vram."""
    info = {"type": None, "name": "Unknown", "vram": ""}

    # ── NVIDIA — nvidia-smi ───────────────────────────────────
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0 and r.stdout.strip():
            parts = r.stdout.strip().split(",")
            name  = parts[0].strip() if parts else "NVIDIA GPU"
            vram  = f"{int(parts[1].strip())//1024}GB VRAM" if len(parts) > 1 else ""
            return {"type": "nvidia", "name": name, "vram": vram}
    except Exception:
        pass

    # ── AMD — rocm-smi ───────────────────────────────────────
    try:
        r = subprocess.run(["rocm-smi", "--showproductname"],
                           capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            for line in r.stdout.splitlines():
                if "card" in line.lower() or "gpu" in line.lower() or "rx" in line.lower():
                    name = line.strip().split(":")[-1].strip() or "AMD GPU"
                    return {"type": "amd", "name": name, "vram": ""}
    except Exception:
        pass

    # ── AMD fallback — lspci ─────────────────────────────────
    try:
        r = subprocess.run(["lspci"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            for line in r.stdout.splitlines():
                ll = line.lower()
                if "amd" in ll and ("vga" in ll or "display" in ll or "3d" in ll):
                    name = line.split(":")[-1].strip()[:50]
                    return {"type": "amd", "name": name, "vram": ""}
                if "nvidia" in ll and ("vga" in ll or "display" in ll or "3d" in ll):
                    name = line.split(":")[-1].strip()[:50]
                    return {"type": "nvidia", "name": name, "vram": ""}
                if "intel" in ll and ("vga" in ll or "display" in ll or "3d" in ll):
                    name = line.split(":")[-1].strip()[:50]
                    return {"type": "intel", "name": name, "vram": ""}
    except Exception:
        pass

    # ── macOS — system_profiler ──────────────────────────────
    try:
        r = subprocess.run(
            ["system_profiler", "SPDisplaysDataType"],
            capture_output=True, text=True, timeout=8
        )
        if r.returncode == 0:
            for line in r.stdout.splitlines():
                if "Chipset Model:" in line:
                    name = line.split(":", 1)[-1].strip()
                    gpu_type = "nvidia" if "nvidia" in name.lower() \
                               else "amd" if "amd" in name.lower() \
                               else "intel" if "intel" in name.lower() \
                               else "other"
                    return {"type": gpu_type, "name": name, "vram": ""}
    except Exception:
        pass

    return info

def _estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token for English) — good enough for
    budget checks without needing to actually tokenize with the model."""
    return max(1, len(text or "") // 4)

def _messages_token_estimate(messages: list) -> int:
    return sum(_estimate_tokens(m.get("content", "")) for m in messages)

def manage_context(cfg: dict, messages: list) -> None:
    """Keep the running conversation inside the model's context window.
    llama-cpp-python hard-errors ('Requested tokens exceed context window')
    once the prompt + history + max_tokens overflows n_ctx — the single most
    common way local chat sessions crash. Instead of hitting that wall, once
    the conversation gets close to the budget this drops the oldest
    non-system turns and keeps the system prompt + most recent exchanges,
    which is what actually matters for coherence in almost every chat."""
    if not cfg.get("auto_trim_context", True):
        return
    budget  = cfg.get("context", 4096)
    reserve = cfg.get("max_tokens", 2048) + 256  # room for the reply + safety margin
    limit   = max(512, budget - reserve)

    if _messages_token_estimate(messages) <= limit:
        return

    system_msgs = [m for m in messages if m["role"] == "system"]
    convo       = [m for m in messages if m["role"] != "system"]
    original_len = len(convo)

    while len(convo) > 2 and (_messages_token_estimate(system_msgs) + _messages_token_estimate(convo)) > limit:
        convo.pop(0)

    if len(convo) < original_len:
        messages[:] = system_msgs + convo
        print(f"{DIM}  ⚙ Trimmed {original_len - len(convo)} older message(s) to stay inside "
              f"the {budget}-token context window (use /context to check usage).{R}")

def build_prompt(messages: list, model_path: str) -> str:
    """Build prompt string from messages list."""
    mp = model_path.lower()
    parts = []

    # detect model family for correct prompt format
    if "phi-3" in mp or "phi3" in mp:
        for m in messages:
            if m["role"] == "system":
                parts.append(f"<|system|>\n{m['content']}<|end|>")
            elif m["role"] == "user":
                parts.append(f"<|user|>\n{m['content']}<|end|>")
            elif m["role"] == "assistant":
                parts.append(f"<|assistant|>\n{m['content']}<|end|>")
        parts.append("<|assistant|>")

    elif "mistral" in mp or "mixtral" in mp:
        sys_content = ""
        for m in messages:
            if m["role"] == "system": sys_content = m["content"]
        conv = [m for m in messages if m["role"] != "system"]
        for i, m in enumerate(conv):
            if m["role"] == "user":
                prefix = f"[INST] {sys_content}\n" if i == 0 and sys_content else "[INST] "
                parts.append(f"{prefix}{m['content']} [/INST]")
            elif m["role"] == "assistant":
                parts.append(f"{m['content']}</s>")

    elif "qwen" in mp:
        parts.append("<|im_start|>system")
        sys_msg = next((m["content"] for m in messages if m["role"]=="system"), "You are a helpful assistant.")
        parts.append(sys_msg + "<|im_end|>")
        for m in messages:
            if m["role"] == "system": continue
            parts.append(f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>")
        parts.append("<|im_start|>assistant")

    else:
        # generic ChatML / TinyLlama
        parts.append("<|system|>")
        sys_msg = next((m["content"] for m in messages if m["role"]=="system"), "You are a helpful assistant.")
        parts.append(sys_msg)
        for m in messages:
            if m["role"] == "system": continue
            tag = "<|user|>" if m["role"] == "user" else "<|assistant|>"
            parts.append(f"{tag}\n{m['content']}")
        parts.append("<|assistant|>")

    return "\n".join(parts)

def stream_local(cfg: dict, messages: list):
    """Stream tokens from local llama-cpp model. Auto-stops on detected loops."""
    llm    = get_llm(cfg)
    prompt = build_prompt(messages, cfg["model_path"])
    stream = llm(
        prompt,
        max_tokens     = cfg.get("max_tokens", 2048),
        temperature    = cfg.get("temperature", 0.7),
        repeat_penalty = 1.3,     # discourage the model from repeating itself
        frequency_penalty = 0.3,  # extra penalty for frequently-used tokens
        stream         = True,
        stop           = ["<|user|>","<|end|>","[INST]","<|im_start|>user"],
    )

    # ── live loop detector ────────────────────────────────────
    buf          = ""           # rolling text buffer for repetition checks
    full_text    = ""
    chunk_count  = 0
    CHECK_EVERY  = 40           # check every N tokens
    WINDOW       = 200          # how much recent text to scan
    MIN_PHRASE   = 25           # minimum repeated phrase length to count as a loop

    for piece in stream:
        token = piece["choices"][0].get("text","")
        if not token:
            continue
        full_text   += token
        buf         += token
        chunk_count += 1
        yield token

        if chunk_count % CHECK_EVERY == 0 and len(full_text) > WINDOW * 2:
            recent = full_text[-WINDOW*2:]
            # check if the last WINDOW chars repeat earlier in `recent`
            tail = recent[-WINDOW:]
            head = recent[:-WINDOW]
            # look for a long common substring = loop
            if len(tail) >= MIN_PHRASE:
                probe = tail[:MIN_PHRASE]
                if probe in head:
                    # confirmed repetition — stop generation
                    yield "\n\n⚠ [stopped: repetition detected]"
                    return

# ══════════════════════════════════════════════════════════════
#  AGENT ENGINE — real tool-calling loop
# ══════════════════════════════════════════════════════════════
# TOOLS registry: single source of truth for what the agent can call.
# "confirm": True  -> user must approve (destructive / side-effecting)
# "confirm": False -> read-only, runs immediately and result is fed straight back
_IGNORE_DIRS = {".git", "node_modules", "__pycache__", "venv", ".venv", "env",
                 "dist", "build", ".idea", ".vscode", "target", ".mypy_cache", ".pytest_cache"}

def _grep_files(pattern: str, root: str, max_results: int = 50) -> str:
    """Content search across a directory tree — the tool that lets the agent
    find where something is actually used/defined, instead of guessing from
    filenames alone."""
    try:
        regex = re.compile(pattern)
    except re.error as e:
        return f"⚠ Invalid regex: {e}"
    root = os.path.expanduser(root or ".")
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _IGNORE_DIRS and not d.startswith(".")]
        for fn in sorted(filenames):
            if len(hits) >= max_results:
                return "\n".join(hits) + f"\n… ({max_results}+ matches, narrow your pattern)"
            fpath = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(fpath) > 1_000_000:
                    continue
                with open(fpath, "r", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        if regex.search(line):
                            hits.append(f"{fpath}:{i}: {line.strip()[:150]}")
                            if len(hits) >= max_results:
                                break
            except Exception:
                continue
    return "\n".join(hits) if hits else "No matches."

def _list_dir(path: str, max_depth: int = 3, max_entries: int = 200) -> str:
    """Directory tree listing — how the agent orients itself in an unfamiliar
    project before making changes, instead of editing blind."""
    root = os.path.expanduser(path or ".")
    if not os.path.isdir(root):
        return f"⚠ Not a directory: {root}"
    lines, root_depth = [], root.rstrip(os.sep).count(os.sep)
    for dirpath, dirnames, filenames in os.walk(root):
        depth = dirpath.rstrip(os.sep).count(os.sep) - root_depth
        if depth >= max_depth:
            dirnames[:] = []
            continue
        dirnames[:] = sorted(d for d in dirnames if d not in _IGNORE_DIRS and not d.startswith("."))
        indent = "  " * depth
        if dirpath != root:
            lines.append(f"{indent}{os.path.basename(dirpath)}/")
        for fn in sorted(filenames):
            if fn.startswith("."):
                continue
            lines.append(f"{indent}  {fn}")
            if len(lines) >= max_entries:
                lines.append("… (truncated)")
                return "\n".join(lines)
    return "\n".join(lines) if lines else "(empty)"

TOOLS = {
    "run_command":  {"confirm": True,  "danger": True,  "desc": "Run a shell command"},
    "create_file":  {"confirm": True,  "danger": False, "desc": "Create/overwrite a file"},
    "edit_file":    {"confirm": True,  "danger": False, "desc": "Find/replace text in a file"},
    "delete_file":  {"confirm": True,  "danger": True,  "desc": "Delete a file"},
    "open_app":     {"confirm": True,  "danger": False, "desc": "Launch an application"},
    "search_files": {"confirm": False, "danger": False, "desc": "Glob-search for files by name"},
    "grep_files":   {"confirm": False, "danger": False, "desc": "Search file contents for a pattern"},
    "list_dir":     {"confirm": False, "danger": False, "desc": "List a directory tree"},
    "read_file":    {"confirm": False, "danger": False, "desc": "Read a file's contents"},
    "make_dir":     {"confirm": True,  "danger": False, "desc": "Create a directory"},
    "web_search":   {"confirm": False, "danger": False, "desc": "Search the web"},
    "rag_search":   {"confirm": False, "danger": False, "desc": "Search your local knowledge base (/rag)"},
}

ACTION_RE = None  # built by _rebuild_action_re(), called at startup and after plugin loading

def _rebuild_action_re() -> None:
    global ACTION_RE
    ACTION_RE = re.compile(
        r"ACTION:\s*(" + "|".join(re.escape(k) for k in TOOLS) + r")\s*\|(.+?)(?=ACTION:|$)",
        re.DOTALL | re.IGNORECASE
    )

_rebuild_action_re()

MAX_AGENT_ITERS = 6  # hard cap on automatic tool-result round-trips per user turn

def parse_actions(text: str) -> list:
    actions = []
    for m in ACTION_RE.finditer(text):
        actions.append({
            "type":  m.group(1).strip().lower(),
            "parts": [p.strip() for p in m.group(2).split("|")],
        })
    return actions

def confirm_action(atype: str, parts: list) -> bool:
    if not TOOLS.get(atype, {}).get("confirm", True):
        return True  # read-only tools run without a prompt

    c = min(shutil.get_terminal_size((80,24)).columns, 60)
    print(f"\n{NEON_O}{'─'*c}")
    print(f"  🤖 AGENT ACTION")
    print(f"{'─'*c}{R}")
    labels = {
        "run_command":  (NEON_Y, "RUN",    parts[0][:70]),
        "create_file":  (NEON_G, "CREATE", parts[0]),
        "edit_file":    (NEON_C, "EDIT",   parts[0]),
        "delete_file":  (NEON_R, "DELETE", parts[0]),
        "open_app":     (NEON_P, "OPEN",   parts[0]),
        "make_dir":     (NEON_G, "MKDIR",  parts[0]),
    }
    color, label, desc = labels.get(atype, (NEON_C, "ACTION", parts[0]))
    print(f"  {color}{BOLD}[{label}]{R}  {desc}")

    if atype == "delete_file":
        print(f"  {NEON_R}{BOLD}⚠  PERMANENT DELETE{R}  {DIM}(a backup is kept — /undo can restore it){R}")

    elif atype == "create_file" and len(parts) > 1:
        exists = os.path.isfile(os.path.expanduser(parts[0]))
        if exists:
            print(f"  {NEON_Y}⚠ File already exists — this will overwrite it (backup kept, /undo can restore).{R}")
        preview = parts[1][:400]
        print(f"  {DIM}{'─'*min(c,50)}{R}")
        for line in preview.split("\n")[:15]:
            print(f"  {NEON_G}+ {line}{R}")
        if len(parts[1]) > 400 or len(parts[1].split(chr(10))) > 15:
            print(f"  {DIM}  … ({len(parts[1])} chars total){R}")

    elif atype == "edit_file" and len(parts) > 2:
        path, old, new = parts[0], parts[1], parts[2]
        full_path = os.path.expanduser(path)
        diff_lines = list(difflib.unified_diff(
            old.splitlines(keepends=True), new.splitlines(keepends=True),
            lineterm="", n=1
        ))
        print(f"  {DIM}{'─'*min(c,50)}{R}")
        if diff_lines:
            for line in diff_lines[2:22]:  # skip the --- / +++ header lines
                if line.startswith("+"):
                    print(f"  {NEON_G}{line}{R}")
                elif line.startswith("-"):
                    print(f"  {NEON_R}{line}{R}")
                elif line.startswith("@@"):
                    print(f"  {NEON_C}{line}{R}")
                else:
                    print(f"  {DIM}{line}{R}")
        else:
            print(f"  {DIM}(no visible diff — check whitespace){R}")

    sys.stdout.write(f"\n  {NEON_Y}Approve? [y/N]: {R}")
    try: ans = input().strip().lower()
    except: ans = "n"
    return ans in ("y","yes")

def _agent_backup_dir() -> str:
    d = os.path.expanduser("~/.cybersh_backups")
    os.makedirs(d, exist_ok=True)
    return d

def _agent_backup_log_path() -> str:
    return os.path.join(_agent_backup_dir(), "log.json")

def _agent_backup_log_load() -> list:
    p = _agent_backup_log_path()
    if not os.path.isfile(p):
        return []
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return []

def _agent_backup_log_save(log: list) -> None:
    with open(_agent_backup_log_path(), "w") as f:
        json.dump(log[-50:], f)  # cap history so this can't grow forever

def _agent_snapshot(path: str, action: str) -> None:
    """Save a pre-change snapshot of a file the agent is about to create/
    edit/delete, so /undo can restore it. If the file doesn't exist yet
    (a brand-new create_file), there's nothing to snapshot — undoing that
    just means deleting the file, tracked via backup_file=None."""
    full = os.path.expanduser(path)
    entry = {"ts": time.time(), "path": full, "action": action, "backup_file": None}
    if os.path.isfile(full):
        try:
            ts_tag = time.strftime("%Y%m%d_%H%M%S_%f")
            backup_path = os.path.join(_agent_backup_dir(), f"{ts_tag}_{os.path.basename(full)}.bak")
            shutil.copy2(full, backup_path)
            entry["backup_file"] = backup_path
        except Exception:
            return  # never block the real operation over a failed backup
    log = _agent_backup_log_load()
    log.append(entry)
    _agent_backup_log_save(log)

def cmd_undo() -> None:
    """Restore the most recent agent-driven file change (create/edit/delete)."""
    log = _agent_backup_log_load()
    if not log:
        print(f"\n{NEON_Y}Nothing to undo — no tracked agent file changes yet.{R}\n")
        return
    entry = log.pop()
    path, action, backup_file = entry["path"], entry["action"], entry.get("backup_file")
    try:
        if backup_file and os.path.isfile(backup_file):
            shutil.copy2(backup_file, path)
            print(f"\n{NEON_G}✓ Restored {path} to its state before the last {action}.{R}\n")
        elif os.path.isfile(path):
            os.remove(path)
            print(f"\n{NEON_G}✓ Removed {path} (it didn't exist before that change).{R}\n")
        else:
            print(f"\n{NEON_Y}Nothing to restore — {path} is already gone.{R}\n")
        _agent_backup_log_save(log)
    except Exception as e:
        print(f"\n{NEON_R}✗ Undo failed: {e}{R}\n")

def _quick_syntax_check(path: str) -> str:
    """Run a fast syntax-only check right after the agent writes a file, so
    a broken edit surfaces immediately in the tool result instead of the
    agent finding out several steps later. Currently covers Python and JSON;
    silently no-ops for other file types."""
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".py":
            r = subprocess.run([sys.executable, "-m", "py_compile", path],
                               capture_output=True, text=True, timeout=10)
            if r.returncode != 0:
                return f"\n⚠ SYNTAX ERROR:\n{r.stderr.strip()[-500:]}"
        elif ext == ".json":
            with open(path) as f:
                json.load(f)
    except subprocess.TimeoutExpired:
        return ""
    except json.JSONDecodeError as e:
        return f"\n⚠ INVALID JSON: {e}"
    except Exception:
        return ""
    return ""

def execute_action(atype: str, parts: list, cfg: dict | None = None) -> str:
    try:
        if atype in PLUGIN_TOOL_FUNCS:
            try:
                return str(PLUGIN_TOOL_FUNCS[atype](parts, cfg))
            except Exception as e:
                return f"✗ Plugin tool '{atype}' error: {e}"

        if atype == "web_search":
            return web_search(parts[0], max_results=5)

        elif atype == "rag_search":
            if cfg is None:
                return "RAG unavailable right now."
            hits = rag_search(parts[0], cfg, top_k=4)
            if not hits:
                return "No relevant local knowledge found. (Index files first with /rag index <path>)"
            return "\n\n".join(f"[source: {h['source']}]\n{h['text']}" for h in hits)

        elif atype == "run_command":
            r = subprocess.run(parts[0], shell=True, capture_output=True,
                               text=True, timeout=60, cwd=os.getcwd())
            out = r.stdout.strip()
            if r.stderr.strip(): out += f"\n[stderr] {r.stderr.strip()}"
            if r.returncode != 0: out += f"\n[exit code] {r.returncode}"
            return out or "(no output)"

        elif atype == "create_file":
            path = os.path.expanduser(parts[0])
            content = parts[1] if len(parts) > 1 else ""
            _agent_snapshot(path, "create")
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
            with open(path,"w") as f: f.write(content)
            return f"Created: {path}" + _quick_syntax_check(path)

        elif atype == "edit_file":
            path = os.path.expanduser(parts[0])
            old  = parts[1] if len(parts) > 1 else ""
            new  = parts[2] if len(parts) > 2 else ""
            with open(path,"r") as f: c = f.read()
            count = c.count(old)
            if count == 0:
                return f"⚠ Text not found in {path} — read_file it first to get the exact text."
            if count > 1:
                return (f"⚠ That text appears {count} times in {path} — edit_file needs a unique "
                        f"match. Include more surrounding context (a line above/below) and try again.")
            _agent_snapshot(path, "edit")
            with open(path,"w") as f: f.write(c.replace(old,new,1))
            return f"Edited: {path}" + _quick_syntax_check(path)

        elif atype == "delete_file":
            path = os.path.expanduser(parts[0])
            _agent_snapshot(path, "delete")
            os.remove(path)
            return f"Deleted: {parts[0]} (backup kept — /undo can restore it)"

        elif atype == "open_app":
            subprocess.Popen(parts[0], shell=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Launched: {parts[0]}"

        elif atype == "search_files":
            found = glob.glob(os.path.expanduser(parts[0]), recursive=True)[:20]
            return "\n".join(found) if found else "No matches."

        elif atype == "grep_files":
            pattern = parts[0]
            path    = parts[1] if len(parts) > 1 else "."
            return _grep_files(pattern, path)

        elif atype == "list_dir":
            path = parts[0] if parts and parts[0] else "."
            return _list_dir(path)

        elif atype == "read_file":
            with open(os.path.expanduser(parts[0]),"r",errors="replace") as f:
                return f.read(6000)

        elif atype == "make_dir":
            os.makedirs(os.path.expanduser(parts[0]), exist_ok=True)
            return f"Created: {parts[0]}"

    except Exception as e:
        return f"✗ Error: {e}"
    return "done"

def process_actions(text: str, cfg: dict | None = None) -> str:
    actions = parse_actions(text)
    if not actions: return ""
    results = []
    for a in actions:
        if confirm_action(a["type"], a["parts"]):
            print(f"  {NEON_G}⟳ Running…{R}")
            out = execute_action(a["type"], a["parts"], cfg)
            print(f"  {NEON_G}✓{R}")
            for line in out.split("\n")[:10]:
                print(f"    {DIM}{line}{R}")
            # feed back enough for the model to actually self-correct on errors —
            # 150 chars used to cut error messages off mid-sentence, which made
            # the agent guess instead of reading what actually went wrong
            trimmed = out if len(out) <= 3000 else out[:3000] + "\n…[truncated, output was longer]"
            results.append(f"[{a['type']}] {trimmed}")
        else:
            print(f"  {NEON_Y}⊘ Skipped{R}")
            results.append(f"[{a['type']}] skipped")
        print()
    return "\n".join(results)

# ══════════════════════════════════════════════════════════════
#  PLUGIN ENGINE — drop-in .py extensions
# ══════════════════════════════════════════════════════════════
# Plugins are plain Python files placed in PLUGINS_DIR (or ./cybersh_plugins/
# next to wherever you run cybersh from). Each one can define a setup(api)
# function that registers new slash commands and/or new agent-callable tools.
# See PLUGIN_TEMPLATE below for the exact shape — /plugins new <name> writes it out.
PLUGINS_DIR = os.path.expanduser("~/.cybersh_plugins")

PLUGIN_COMMANDS: dict   = {}   # "/name" -> {"handler": fn, "help": str, "category": str}
PLUGIN_TOOL_FUNCS: dict = {}   # "tool_name" -> fn(parts, cfg) -> str
LOADED_PLUGINS: list    = []   # [{"name","version","desc","file"}, ...]

class PluginAPI:
    """Passed to every plugin's setup(api). This is the whole plugin surface —
    kept small and stable on purpose so plugins don't break across cybersh updates."""

    def register_command(self, name: str, handler, help: str = "", category: str = "🔌 PLUGINS") -> None:
        """Register a new /command.
        handler(arg: str, ctx: dict) -> str | None
        ctx = {"cfg": dict, "messages": list, "session_msgs": list, "ask": ask_fn}
        Return a string to have it treated like an AI response (saved to history);
        return None/"" if your command already printed everything itself."""
        if not name.startswith("/"):
            name = "/" + name
        PLUGIN_COMMANDS[name] = {"handler": handler, "help": help, "category": category}
        if name not in ALL_COMMANDS:
            ALL_COMMANDS.append(name)

    def register_tool(self, name: str, fn, confirm: bool = True,
                       danger: bool = False, desc: str = "") -> None:
        """Register a new agent-callable tool. The model can invoke it with
        'ACTION: <name> | <arg>' and fn(parts: list, cfg: dict) -> str runs it.
        confirm=True means the user is asked to approve each call (use this for
        anything destructive/side-effecting); confirm=False runs immediately."""
        TOOLS[name] = {"confirm": confirm, "danger": danger, "desc": desc or f"Plugin tool: {name}"}
        PLUGIN_TOOL_FUNCS[name] = fn
        _rebuild_action_re()

    def log(self, msg: str) -> None:
        print(f"{DIM}[plugin] {msg}{R}")


def _ensure_plugin_dirs() -> None:
    os.makedirs(PLUGINS_DIR, exist_ok=True)

def _plugin_source_dirs() -> list:
    dirs = [PLUGINS_DIR]
    local = os.path.join(os.getcwd(), "cybersh_plugins")
    if os.path.isdir(local) and local not in dirs:
        dirs.append(local)
    return dirs

def load_plugins(cfg: dict, verbose: bool = True) -> None:
    """Scan plugin directories and load every *.py file that defines setup(api)."""
    global LOADED_PLUGINS
    LOADED_PLUGINS = []
    PLUGIN_COMMANDS.clear()
    for name in list(PLUGIN_TOOL_FUNCS):     # drop only plugin-added tools, keep builtins
        TOOLS.pop(name, None)
    PLUGIN_TOOL_FUNCS.clear()

    _ensure_plugin_dirs()
    api = PluginAPI()

    for d in _plugin_source_dirs():
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".py") or fn.startswith("_"):
                continue
            path     = os.path.join(d, fn)
            mod_name = f"cybersh_plugin_{os.path.splitext(fn)[0]}"
            try:
                spec   = importlib.util.spec_from_file_location(mod_name, path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "setup"):
                    module.setup(api)
                LOADED_PLUGINS.append({
                    "name":    getattr(module, "PLUGIN_NAME", os.path.splitext(fn)[0]),
                    "version": getattr(module, "PLUGIN_VERSION", "?"),
                    "desc":    getattr(module, "PLUGIN_DESC", ""),
                    "file":    path,
                })
                if verbose:
                    print(f"{NEON_G}  ✓ plugin loaded: {LOADED_PLUGINS[-1]['name']}{R}")
            except Exception as e:
                if verbose:
                    print(f"{NEON_R}  ✗ plugin {fn} failed: {e}{R}")

    _rebuild_action_re()


PLUGIN_TEMPLATE = '''"""
CyberSH plugin — drop this file into ~/.cybersh_plugins/ and it loads automatically.
"""

PLUGIN_NAME    = "{name}"
PLUGIN_VERSION = "1.0"
PLUGIN_DESC    = "Describe what this plugin does."


def my_command(arg: str, ctx: dict) -> str:
    """/{name} <text> — example command."""
    cfg, messages, session_msgs, ask = ctx["cfg"], ctx["messages"], ctx["session_msgs"], ctx["ask"]
    if not arg:
        print("Usage: /{name} <text>")
        return ""
    # Replace this with your own logic, or call ask(cfg, messages, session_msgs, "...")
    # to route something through the AI.
    print(f"You said: {{arg}}")
    return ""


def my_tool(parts: list, cfg: dict) -> str:
    """Agent-callable tool — the AI triggers this with: ACTION: {name}_tool | <arg>"""
    return f"{name}_tool ran with: {{parts[0] if parts else ''}}"


def setup(api) -> None:
    api.register_command("{name}", my_command,
                          help="Example plugin command", category="🔌 PLUGINS")
    api.register_tool("{name}_tool", my_tool, confirm=False,
                       desc="Example agent-callable plugin tool")
'''

def cmd_plugins(action: str, arg: str, cfg: dict) -> None:
    """/plugins [list|reload|dir|new <name>]"""
    a = (action or "list").lower()
    w = min(cols(), 62)

    if a in ("list", ""):
        print(f"\n{NEON_C}{'─'*w}")
        print(f"{NEON_C}{BOLD}  🔌 Plugins — {len(LOADED_PLUGINS)} loaded{R}")
        print(f"{NEON_C}{'─'*w}{R}")
        if not LOADED_PLUGINS:
            print(f"{DIM}  None yet. Drop a .py file in {PLUGINS_DIR}, "
                  f"or run /plugins new <name> to scaffold one.{R}")
        for p in LOADED_PLUGINS:
            print(f"  {NEON_G}{p['name']}{R} {DIM}v{p['version']} — {p['desc']}{R}")
            print(f"    {DIM}{p['file']}{R}")
        if PLUGIN_COMMANDS:
            print(f"\n  {NEON_Y}Commands:{R} {', '.join(sorted(PLUGIN_COMMANDS))}")
        print(f"\n  {DIM}dir: {PLUGINS_DIR}{R}\n")

    elif a == "reload":
        print(f"\n{NEON_C}🔄 Reloading plugins…{R}\n")
        load_plugins(cfg, verbose=True)
        print()

    elif a == "dir":
        _ensure_plugin_dirs()
        print(f"\n{NEON_C}Plugin directory: {PLUGINS_DIR}{R}\n")

    elif a == "new":
        if not arg:
            print(f"{NEON_Y}Usage: /plugins new <name>{R}\n"); return
        _ensure_plugin_dirs()
        safe = re.sub(r"[^a-zA-Z0-9_]", "_", arg.strip())
        dest = os.path.join(PLUGINS_DIR, f"{safe}.py")
        if os.path.exists(dest):
            print(f"{NEON_R}✗ {dest} already exists.{R}\n"); return
        with open(dest, "w") as f:
            f.write(PLUGIN_TEMPLATE.format(name=safe))
        print(f"\n{NEON_G}✓ Created {dest}{R}")
        print(f"{DIM}Edit it, then run /plugins reload (or just restart cybersh).{R}\n")

    else:
        print(f"{NEON_Y}Usage: /plugins [list|reload|dir|new <name>]{R}\n")

# ══════════════════════════════════════════════════════════════
#  SPINNER
# ══════════════════════════════════════════════════════════════
class Spinner:
    MSGS = ["Cracking the matrix","Routing through proxies","Agent thinking",
            "Vibe coding","Enumerating endpoints","Fuzzing parameters"]
    def __init__(self, label=None):
        import random
        self.label = label or random.choice(self.MSGS)
        self._active = False; self._t = None; self._s = 0.0
    def __enter__(self):
        self._active = True; self._s = time.time()
        self._t = threading.Thread(target=self._spin, daemon=True)
        self._t.start(); return self
    def __exit__(self, *_):
        self._active = False
        if self._t: self._t.join(0.5)
        sys.stdout.write(CLEAR); sys.stdout.flush()
    def _spin(self):
        f = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"; i = 0
        while self._active:
            sys.stdout.write(
                f"\r  {NEON_G}{f[i%len(f)]}{R} {NEON_C}{self.label}{DIM}…{R} "
                f"{DIM}[{time.time()-self._s:.1f}s]{R}"
            )
            sys.stdout.flush(); time.sleep(0.07); i += 1

# ══════════════════════════════════════════════════════════════
#  UI
# ══════════════════════════════════════════════════════════════
def cols(): return shutil.get_terminal_size((80,24)).columns
def div(color=DIM, ch="─"): return f"{color}{ch*cols()}{R}"

_LOGO_LINES = (
    r" ██████╗██╗   ██╗██████╗ ███████╗██████╗     ███████╗██╗  ██╗",
    r"██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗    ██╔════╝██║  ██║",
    r"██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝    ███████╗███████║",
    r"██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗    ╚════██║██╔══██║",
    r"╚██████╗   ██║   ██████╔╝███████╗██║  ██║    ███████║██║  ██║",
    r" ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═╝",
)

def _print_logo() -> None:
    print(f"\n{NEON_C}{BOLD}")
    for line in _LOGO_LINES:
        print(line)

def _subsystem_status(cfg: dict) -> str:
    """One compact line showing what's actually configured/loaded right now."""
    bits = []
    n_plugins = len(LOADED_PLUGINS)
    bits.append(f"{NEON_G}🔌 {n_plugins}{R}" if n_plugins else f"{DIM}🔌 0{R}")

    rag_n = len(rag_load_index()) if cfg.get("rag_enabled", True) else 0
    bits.append(f"{NEON_G}📚 {rag_n}{R}" if rag_n else f"{DIM}📚 0{R}")

    vision_on = bool(cfg.get("vision_model_path") and cfg.get("vision_mmproj_path"))
    bits.append(f"{NEON_G}👁 on{R}" if vision_on else f"{DIM}👁 off{R}")

    return "  ".join(bits)

def print_banner(cfg: dict) -> None:
    mode = MODES.get(cfg.get("mode","chat"), MODES["chat"])
    mc   = mode["color"]
    bw   = min(cols(), 66)
    now  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    model_name = os.path.basename(cfg.get("model_path","no model")).replace(".gguf","")

    print(f"{DIM}{'─'*bw}{R}")
    print(f"  {NEON_C}MODEL{R} {BOLD}{model_name}{R}  "
          f"{NEON_C}MODE{R} {mc}{BOLD}{mode['icon']} {mode['label']}{R}  "
          f"{NEON_C}TEMP{R} {NEON_Y}{cfg['temperature']}{R}  {DIM}{now}{R}")
    print(f"  {NEON_C}v{APP_VERSION}{R}  {_subsystem_status(cfg)}")
    print(f"{DIM}{'─'*bw}{R}")
    print(f"  {DIM}Modes:{R} {NEON_P}/vibe{R} {NEON_G}/sec{R} "
          f"{NEON_Y}/code{R} {NEON_C}/chat{R} {NEON_O}/agent{R}  "
          f"{DIM}Files:{R} {NEON_C}/f <path>  /o <path>{R}  "
          f"{DIM}Help:{R} {NEON_C}/help{R}")
    print(f"{DIM}{'─'*bw}{R}\n")

def startup_selector(cfg: dict) -> None:
    """Show the logo once + mode selector on startup."""
    bw = min(cols(), 66)
    _print_logo()
    model_name = os.path.basename(cfg.get("model_path","no model")).replace(".gguf","")
    print(f"  DIRECT — No Server · Pure Python  ·  {model_name}{R}\n")
    print(f"{DIM}{'─'*bw}{R}")
    print(f"\n  {BOLD}Select mode:{R}\n")
    menu = [
        ("1","agent",NEON_O,"🤖","Agent  — AI controls your computer"),
        ("2","sec",  NEON_G,"🔐","Sec    — Bug bounty & pentest expert"),
        ("3","vibe", NEON_P,"🎨","Vibe   — Creative coding & UI/UX"),
        ("4","code", NEON_Y,"⚡","Code   — Clean production code"),
        ("5","chat", NEON_C,"💬","Chat   — General assistant"),
    ]
    for num, key, color, icon, desc in menu:
        cur = f"  {DIM}← current{R}" if key == cfg.get("mode","chat") else ""
        print(f"  {color}{BOLD}[{num}]{R}  {icon}  {color}{desc}{R}{cur}")
    print(f"\n{DIM}{'─'*bw}{R}")
    sys.stdout.write(f"\n  {NEON_Y}Choose [1-5] (Enter = keep current): {R}")
    sys.stdout.flush()
    try: choice = input().strip()
    except: choice = ""
    m = {"1":"agent","2":"sec","3":"vibe","4":"code","5":"chat"}
    if choice in m: cfg["mode"] = m[choice]

def _help_sections() -> list:
    """Built fresh each call so plugin-registered commands always show up."""
    sections = [
        ("🕹️  MODES", [
            ("/agent","AI controls your computer"),
            ("/sec",  "Bug bounty expert"),
            ("/vibe", "Creative vibe coding"),
            ("/code", "Production code"),
            ("/chat", "General chat"),
        ]),
        ("🧠 MEMORY", [
            ("/remember <anything>",  "AI remembers this (plain-text JSON, not encrypted)"),
            ("/remember name is X",   "Remember your name"),
            ("/remember project X Y", "Save a project description"),
            ("/memories",             "Show everything remembered"),
            ("/forget <keyword>",     "Delete a memory"),
        ]),
        ("🎭 PERSONALITY", [
            ("/persona",              "List AI personalities"),
            ("/persona teacher",      "Patient teacher mode"),
            ("/persona hacker",       "Elite hacker mentor"),
            ("/persona coach",        "Motivating life coach"),
            ("/persona roaster",      "Roasts bad ideas (with fixes)"),
            ("/persona sherlock",     "Sherlock Holmes mode"),
        ]),
        ("🌍 EVERYDAY", [
            ("/convert 100 km to miles", "Convert units, temperature, data, time"),
            ("/qr <text>",               "Generate QR code in terminal"),
            ("/speedtest",               "Test your internet speed + latency"),
            ("/pwcheck <password>",      "AI rates your password strength"),
            ("/uuid [n]",                "Generate UUID4s (or /uuid 5 <name>)"),
            ("/json <text>",             "Validate + pretty-print JSON (/json minify)"),
            ("/base <number>",           "Convert number across bin/oct/dec/hex"),
            ("/color <hex|rgb>",         "Convert color + show swatch"),
            ("/slugify <text>",          "Turn text into a URL slug"),
            ("/lorem [n]",               "Generate lorem ipsum placeholder text"),
            ("/countdown <date>",        "Days/hours remaining until a date"),
            ("/ip [address]",            "IP geolocation lookup (yours or any IP)"),
            ("/clock [+offset]",         "World clock across timezones"),
            ("/gist <url|id>",           "Fetch + display a GitHub Gist"),
        ]),
        ("🌐 WEB & MODELS", [
            ("/web <query>",             "Search web, feed results to AI"),
            ("/models",                  "Download a new model"),
            ("/fetch <url> [task]",      "Fetch URL, save it, ask AI about it"),
            ("/fetchauth <url>",         "Add/update auth (cookie/bearer/basic) for a site"),
            ("/fetchsites",              "List all saved sites"),
            ("/fetchforget <url>",       "Remove a saved site"),
        ]),
        ("🎨 GENERATIVE", [
            ("/image <prompt>",             "Generate image with Stable Diffusion → saves .png"),
            ("/see <image> [question]",     "Vision: analyze an image locally (/see setup to configure)"),
            ("/rag index <path>",           "Index a file/folder into your local knowledge base"),
            ("/rag ask <question>",         "Ask a question grounded in your indexed files"),
            ("/rag list | /rag clear",      "View or wipe the local RAG index"),
        ]),
        ("👨‍💻 DEVELOPER", [
            ("/debug",                   "Paste broken code, AI finds every bug"),
            ("/review",                  "Full code review — bugs, security, performance"),
            ("/template flask api",      "Generate a production-ready project template"),
            ("/gitlog",                  "AI summarizes your recent git commits"),
            ("/testgen",                 "Paste code, AI writes a pytest test suite"),
            ("/docstring",               "Paste code, AI adds docstrings + type hints"),
            ("/complexity",              "Big-O time/space analysis of pasted code"),
            ("/gitdiff [staged]",        "AI reviews uncommitted changes before you commit"),
            ("/commitmsg",               "Generate a conventional commit message from your diff"),
            ("/todo [path]",             "Scan for TODO/FIXME/HACK markers, AI triages them"),
            ("/gitignore <stack>",       "Generate + optionally write a .gitignore"),
            ("/license <type> [holder]", "Generate + optionally write a LICENSE file"),
            ("/lint <file>",             "Run a real linter if installed, AI explains findings"),
            ("/profile <script.py>",     "cProfile a script, AI explains the hotspots"),
            ("/explaincode",             "Paste code → AI explains every line"),
            ("/roast",                   "AI roasts your bad code (with fixes)"),
            ("/rename <name>",           "AI suggests better variable/function names"),
            ("/regex <desc>",            "AI writes a regex for you"),
            ("/git <task>",              "AI gives exact git commands"),
            ("/diff",                    "Paste git diff → AI explains changes"),
        ]),
        ("🔌 PLUGINS", [
            ("/plugins",                 "List loaded plugins and their commands"),
            ("/plugins new <name>",      "Scaffold a new plugin in ~/.cybersh_plugins/"),
            ("/plugins reload",          "Reload all plugins without restarting"),
            ("/plugins dir",             "Show the plugin directory path"),
        ]),
        ("🔐 SECURITY", [
            ("/hash <hash>",             "Identify hash type + attempt crack"),
            ("/headers <url>",           "Check HTTP security headers of any site"),
            ("/osint <username>",        "Full OSINT checklist for a target"),
            ("/wordlist <theme>",        "Generate targeted password wordlist"),
            ("/recon <target>",          "Bug bounty recon plan"),
            ("/payload <type>",          "Payloads: xss|sqli|ssrf|lfi|rce"),
            ("/explain <cmd>",           "Explain a command"),
            ("/cvesearch <id>",          "Search & analyze CVE/vulnerability"),
            ("/ctf <data>",              "CTF challenge analyzer"),
        ]),
        ("🤖 AI TOOLS", [
            ("/think <question>",        "AI thinks step by step before answering"),
            ("/debate <topic>",          "AI argues both sides of any topic"),
            ("/improve",                 "AI rewrites your text to be cleaner"),
            ("/eli5 <topic>",            "Explain anything like you are 5"),
            ("/cheatsheet <topic>",      "Quick-reference cheat sheet for any tool/topic"),
            ("/cron <expr|english>",     "Explain a cron expr, or build one from English"),
            ("/quiz <topic>",            "5-question multiple-choice quiz"),
            ("/name <description>",      "Brainstorm names for a project/product"),
            ("/challenge [level]",       "Get a coding/hacking challenge"),
        ]),
        ("💾 SAVED SESSIONS", [
            ("/session save <name>",    "Save current chat with a name"),
            ("/session list",           "Show all saved sessions"),
            ("/session load <n>",       "Load session by number or name"),
            ("/session search <word>",  "Search all sessions for a keyword"),
            ("/session delete <n>",     "Delete a saved session"),
        ]),
        ("🎯 PRODUCTIVITY", [
            ("/goals",                "Show today's goals"),
            ("/goals add <goal>",     "Add a daily goal"),
            ("/goals done <n>",       "Mark goal as done"),
            ("/calc <expr>",          "Quick math: /calc 15% of 240"),
            ("/summarize <url>",      "Fetch + summarize any webpage"),
            ("/timer 5m",             "Countdown timer (5m, 30s, 1h)"),
            ("/weather [city]",       "ASCII weather forecast"),
            ("/translate <l> <t>",    "Translate text to any language"),
            ("/recap",                "Summary of this session"),
            ("/note <text>",          "Save a quick note"),
            ("/notes list",           "Show all notes"),
            ("/tip",                  "Show tip of the day"),
            ("/syswatch",             "Live CPU/RAM/disk monitor"),
            ("/benchmark",            "CPU + RAM + disk speed test with score"),
            ("/passgen [type]",       "Generate passwords/phrases/API keys"),
            ("/encode <text>",        "Base64/hex/URL/MD5/SHA256 encode"),
            ("/tldr <cmd>",           "Explain any command in plain English"),
            ("/howto <task>",         "Get exact command for any task"),
            ("/fix <error>",          "Paste error, get instant fix"),
        ]),
        ("📁 FILES", [
            ("/f <path>", "Load file into AI context"),
            ("/o <path>", "Save last response to file"),
            ("/run",      "Execute last code block"),
            ("/copy",     "Copy to clipboard"),
        ]),
        ("⚙️  SETTINGS", [
            ("/clear",   "Clear history"),
            ("/history", "Show history"),
            ("/temp <n>","Set temperature"),
            ("/context", "Show context window usage"),
            ("/compact", "AI-summarize older history to free up context"),
            ("/regen",   "Regenerate the last response"),
            ("/model",   "List or hot-swap the loaded model (no restart)"),
            ("/export [html]", "Export the conversation to a file"),
            ("/undo",    "Restore the last agent-made file change"),
            ("/info",    "Show model info"),
            ("/save",    "Save config"),
            ("/exit",    "Exit"),
        ]),
    ]

    # merge in plugin-registered commands, grouped by whatever category they asked for
    if PLUGIN_COMMANDS:
        by_cat: dict = {}
        for name, meta in PLUGIN_COMMANDS.items():
            by_cat.setdefault(meta.get("category") or "🔌 PLUGINS", []).append(
                (name, meta.get("help") or "(no description)"))
        for cat, entries in by_cat.items():
            existing = next((s for s in sections if s[0] == cat), None)
            if existing:
                existing[1].extend(entries)
            else:
                sections.append((cat, entries))

    return sections


def print_help(query: str = "") -> None:
    sections = _help_sections()
    q = query.strip().lower()

    w = min(cols(), 74)
    total_cmds = sum(len(cmds) for _, cmds in sections)

    # ── /help <category> or /help all ──────────────────────────
    if q in ("all", "everything"):
        print(f"\n{div(BOLD_C)}")
        print(f"{BOLD_C}  CYBER SH DIRECT — ALL COMMANDS ({total_cmds}){R}")
        print(div(BOLD_C))
        for section, cmds in sections:
            print(f"\n  {NEON_Y}{BOLD}{section}{R}")
            for cmd, desc in cmds:
                print(f"    {NEON_C}{cmd:<26}{R}{DIM}{desc}{R}")
        print(f"\n{div()}\n")
        return

    if q:
        cat_match = [s for s in sections if q in s[0].lower()]
        if cat_match:
            print(f"\n{div(BOLD_C)}")
            for section, cmds in cat_match:
                print(f"{BOLD_C}  {section}{R}")
                print(div(BOLD_C))
                for cmd, desc in cmds:
                    print(f"    {NEON_C}{cmd:<26}{R}{DIM}{desc}{R}")
                print()
            return

        # search command names + descriptions
        needle = q.lstrip("/")
        hits = [(section, cmd, desc) for section, cmds in sections for cmd, desc in cmds
                if needle in cmd.lower().lstrip("/") or needle in desc.lower()]
        print(f"\n{div(BOLD_C)}")
        if hits:
            print(f"{BOLD_C}  🔍 /help \"{query}\" — {len(hits)} match(es){R}")
            print(div(BOLD_C))
            for section, cmd, desc in hits:
                print(f"    {NEON_C}{cmd:<26}{R}{DIM}{desc}{R}  {DIM}({section}){R}")
        else:
            print(f"{NEON_R}  No commands matched \"{query}\".{R}")
            print(f"  {DIM}Try /help (no argument) for the full index, or /help all for everything.{R}")
        print(f"\n{div()}\n")
        return

    # ── default: compact index, not a wall of text ─────────────
    print(f"\n{div(BOLD_C)}")
    print(f"{BOLD_C}  CYBER SH DIRECT — {total_cmds} COMMANDS ACROSS {len(sections)} CATEGORIES{R}")
    print(div(BOLD_C))
    for section, cmds in sections:
        preview = ", ".join(c for c, _ in cmds[:3])
        print(f"  {NEON_Y}{BOLD}{section:<20}{R}{DIM}({len(cmds)})  {preview}{'…' if len(cmds) > 3 else ''}{R}")
    print(f"\n  {NEON_C}/help <category>{R}{DIM}  — e.g. /help developer, /help security{R}")
    print(f"  {NEON_C}/help <word>{R}{DIM}     — search command names + descriptions{R}")
    print(f"  {NEON_C}/help all{R}{DIM}        — dump everything at once{R}")
    print(f"{div()}\n")

# ══════════════════════════════════════════════════════════════
#  HISTORY
# ══════════════════════════════════════════════════════════════
def save_history(path: str, history: list, maxh: int) -> None:
    try:
        with open(path,"w") as f: json.dump(history[-maxh:], f, indent=2)
    except: pass

# ══════════════════════════════════════════════════════════════
#  MEMORY SYSTEM — Remembers things between sessions
# ══════════════════════════════════════════════════════════════
MEMORY_PATH = os.path.expanduser("~/.cybersh_memory.json")

def load_memory() -> dict:
    try:
        with open(MEMORY_PATH) as f: return json.load(f)
    except Exception:
        return {"facts": [], "preferences": {}, "projects": {}}

def save_memory(mem: dict) -> None:
    try:
        with open(MEMORY_PATH, "w") as f: json.dump(mem, f, indent=2)
    except Exception: pass

def memory_context(mem: dict) -> str:
    """Build a context string from memory to inject into AI system prompt."""
    if not mem["facts"] and not mem["preferences"] and not mem["projects"]:
        return ""
    parts = ["[MEMORY — things the user told you to remember:]"]
    if mem["facts"]:
        parts.append("Facts: " + " | ".join(mem["facts"][-20:]))
    if mem["preferences"]:
        prefs = ", ".join(f"{k}={v}" for k, v in mem["preferences"].items())
        parts.append(f"Preferences: {prefs}")
    if mem["projects"]:
        for name, info in list(mem["projects"].items())[-5:]:
            parts.append(f"Project '{name}': {info}")
    return "\n".join(parts)

def cmd_remember(arg: str, mem: dict) -> None:
    """Save something to persistent memory."""
    if not arg:
        print(f"{NEON_Y}Usage: /remember <anything>{R}")
        print(f"  Examples:")
        print(f"    /remember my name is Ahmed")
        print(f"    /remember I prefer Python 3.11")
        print(f"    /remember project myapp is a flask REST API\n")
        return
    w   = min(cols(), 60)
    div_line = f"{NEON_C}{'─'*w}{R}"

    # detect project
    if arg.lower().startswith("project "):
        rest  = arg[8:].strip()
        parts = rest.split(" ", 1)
        name  = parts[0]
        info  = parts[1] if len(parts) > 1 else ""
        mem["projects"][name] = info
        save_memory(mem)
        print(f"\n{NEON_G}✓ Project '{name}' remembered.{R}\n")
        return

    # detect preference (key=value or "prefer X")
    if "=" in arg and len(arg.split("=")) == 2:
        k, v = arg.split("=", 1)
        mem["preferences"][k.strip()] = v.strip()
        save_memory(mem)
        print(f"\n{NEON_G}✓ Preference saved: {k.strip()} = {v.strip()}{R}\n")
        return

    # general fact
    print(f"{NEON_Y}⚠  Memories are stored as plain-text JSON at {MEMORY_PATH} — do not store passwords or secrets.{R}")
    ts   = datetime.datetime.now().strftime("%Y-%m-%d")
    fact = f"[{ts}] {arg}"
    mem["facts"].append(fact)
    if len(mem["facts"]) > 100: mem["facts"].pop(0)
    save_memory(mem)
    print(f"\n{NEON_G}✓ Remembered: {arg}{R}\n")

def cmd_memories(mem: dict) -> None:
    """Show everything in memory."""
    w        = min(cols(), 65)
    div_line = f"{NEON_C}{'─'*w}{R}"
    print(f"\n{div_line}")
    print(f"{NEON_C}{BOLD}  🧠 Memory{R}")
    print(div_line)

    if not mem["facts"] and not mem["preferences"] and not mem["projects"]:
        print(f"  {DIM}Nothing remembered yet. Use /remember <anything>{R}")
        print(f"{div_line}\n"); return

    if mem["facts"]:
        print(f"\n  {NEON_Y}Facts:{R}")
        for i, f in enumerate(mem["facts"][-15:], 1):
            print(f"    {DIM}{i:>2}.{R} {f}")

    if mem["preferences"]:
        print(f"\n  {NEON_Y}Preferences:{R}")
        for k, v in mem["preferences"].items():
            print(f"    {NEON_C}{k}{R} = {v}")

    if mem["projects"]:
        print(f"\n  {NEON_Y}Projects:{R}")
        for name, info in mem["projects"].items():
            print(f"    {NEON_C}{name}{R}: {info}")

    print(f"\n  {DIM}Use /forget <text> to remove something{R}")
    print(f"{div_line}\n")

def cmd_forget(arg: str, mem: dict) -> None:
    """Remove something from memory."""
    if not arg:
        print(f"{NEON_Y}Usage: /forget <keyword or project name>{R}\n"); return

    removed = 0
    # check projects
    if arg in mem["projects"]:
        del mem["projects"][arg]
        removed += 1

    # check preferences
    if arg in mem["preferences"]:
        del mem["preferences"][arg]
        removed += 1

    # check facts
    before = len(mem["facts"])
    mem["facts"] = [f for f in mem["facts"] if arg.lower() not in f.lower()]
    removed += before - len(mem["facts"])

    if removed:
        save_memory(mem)
        print(f"\n{NEON_G}✓ Removed {removed} memory item(s) matching '{arg}'{R}\n")
    else:
        print(f"\n{NEON_Y}⚠ Nothing found matching '{arg}'{R}\n")

# ══════════════════════════════════════════════════════════════
#  MOOD / PERSONALITY SYSTEM
# ══════════════════════════════════════════════════════════════
PERSONALITIES = {
    "default":  "You are CYBER SH, a helpful AI assistant. Be concise and direct.",
    "teacher":  "You are a patient teacher. Explain everything simply with analogies, never assume prior knowledge. After explaining, ask if the user understood.",
    "hacker":   "You are an elite hacker mentor. Be direct, technical, use proper security terminology. Challenge the user to think deeper. Occasionally use l33tspeak for emphasis.",
    "coach":    "You are an energetic life and productivity coach. Be encouraging, positive, break problems into small steps. Celebrate every win, no matter how small.",
    "roaster":  "You are a brutally honest senior dev who roasts bad ideas and code with sharp humor — but ALWAYS follows up with the correct approach. Be funny, accurate, and genuinely helpful.",
    "sherlock": "You are Sherlock Holmes. Make deductions from every detail the user gives you. Be dramatic, logical, brilliant. Say 'Elementary.' when something is obvious.",
    "prof":     "You are a university professor — expert, thorough, academic but approachable. Use precise language, cite reasoning, structure answers clearly with examples.",
    "eli5":     "You are explaining everything to a 5-year-old. Use the simplest words possible, fun analogies, and short sentences. Never use jargon.",
    "pirate":   "You are a pirate who happens to be a genius programmer and hacker. Speak like a pirate (Arr, matey, etc.) but give genuinely expert technical advice.",
    "stoic":    "You are a Stoic philosopher AI. Give wise, calm, measured responses. Reference Marcus Aurelius, Epictetus, Seneca where relevant. Focus on what the user can control.",
}

def cmd_persona(arg: str, cfg: dict) -> None:
    """Switch AI personality."""
    w = min(cols(), 60)
    if not arg:
        print(f"\n{NEON_C}{'─'*w}{R}")
        print(f"{NEON_C}{BOLD}  🎭 Personalities{R}")
        print(f"{NEON_C}{'─'*w}{R}")
        for k, v in PERSONALITIES.items():
            cur = f" {NEON_G}← active{R}" if cfg.get("persona","default") == k else ""
            print(f"  {NEON_Y}{k:<12}{R}{DIM}{v[:55]}…{R}{cur}")
        print(f"\n  {DIM}Usage: /persona teacher{R}")
        print(f"{NEON_C}{'─'*w}{R}\n"); return
    if arg not in PERSONALITIES:
        close = [k for k in PERSONALITIES if k.startswith(arg[:3])]
        hint  = f"  Did you mean: {close[0]}?" if close else ""
        print(f"{NEON_R}✗ Unknown persona '{arg}'.{R}{hint}")
        print(f"  Options: {', '.join(PERSONALITIES)}\n"); return
    cfg["persona"] = arg
    desc = PERSONALITIES[arg][:80]
    bw   = min(cols(), 62)
    print(f"\n{NEON_P}{'▓'*bw}")
    print(f"{NEON_P}{BOLD}  🎭 PERSONA → {arg.upper()}{R}")
    print(f"{NEON_P}{'▓'*bw}{R}")
    print(f"  {DIM}{desc}…{R}\n")

# ══════════════════════════════════════════════════════════════
#  SMART SUMMARIZER
# ══════════════════════════════════════════════════════════════
def cmd_summarize_url(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Fetch a URL and AI summarizes it."""
    if not arg:
        print(f"{NEON_Y}Usage: /summarize <url>{R}\n"); return ""
    print(f"\n{NEON_C}🌐 Fetching {arg}…{R}\n")
    r = subprocess.run(
        ["curl", "-sL", "--max-time", "10",
         "-A", "Mozilla/5.0", arg],
        capture_output=True, text=True
    )
    if not r.stdout:
        print(f"{NEON_R}✗ Could not fetch URL.{R}\n"); return ""
    # strip HTML tags crudely
    text = re.sub(r"<[^>]+>", " ", r.stdout)
    text = re.sub(r"\s+", " ", text).strip()[:4000]
    return ask(cfg, messages, session_msgs,
        f"Summarize this webpage content in bullet points. "
        f"Extract: main topic, key points, any important numbers or dates, and conclusion.\n\n{text}")

# ══════════════════════════════════════════════════════════════
#  RAG COMMAND ROUTER
# ══════════════════════════════════════════════════════════════
def cmd_rag(action: str, arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Router for /rag subcommands: index, ask, list, clear."""
    a = (action or "").lower()

    if a in ("index", "add"):
        if not arg:
            print(f"{NEON_Y}Usage: /rag index <file-or-directory>{R}\n"); return ""
        print(f"\n{NEON_C}📚 Indexing {arg}…{R}")
        print(f"{DIM}(first run loads an embedding model — may take a moment){R}\n")
        print(rag_index_path(arg, cfg) + "\n")
        return ""

    elif a in ("list", "status", ""):
        index = rag_load_index()
        srcs  = sorted({e["source"] for e in index})
        w = min(cols(), 60)
        print(f"\n{NEON_C}{'─'*w}")
        print(f"  📚 Local RAG Index — {len(index)} chunk(s), {len(srcs)} file(s)")
        print(f"{'─'*w}{R}")
        for s in srcs[:30]:
            print(f"  {DIM}{s}{R}")
        if len(srcs) > 30:
            print(f"  {DIM}… and {len(srcs)-30} more{R}")
        print(f"\n{DIM}/rag index <path>  ·  /rag ask <question>  ·  /rag clear{R}\n")
        return ""

    elif a == "clear":
        global _RAG_INDEX_CACHE, _RAG_INDEX_MTIME
        if os.path.exists(RAG_INDEX_PATH):
            os.remove(RAG_INDEX_PATH)
        _RAG_INDEX_CACHE, _RAG_INDEX_MTIME = [], None
        print(f"\n{NEON_G}✓ RAG index cleared.{R}\n")
        return ""

    elif a == "ask":
        if not arg:
            print(f"{NEON_Y}Usage: /rag ask <question>{R}\n"); return ""
        hits = rag_search(arg, cfg, top_k=5)
        if not hits:
            print(f"\n{NEON_Y}⚠ Nothing indexed yet (or no match). Run /rag index <path> first.{R}\n")
            return ""
        context = "\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)
        return ask(cfg, messages, session_msgs,
            f"Using ONLY the local context below, answer the question. "
            f"If the context doesn't contain the answer, say so plainly.\n\n"
            f"--- LOCAL CONTEXT ---\n{context}\n--- END CONTEXT ---\n\nQuestion: {arg}")

    else:
        # treat the whole thing as a question if it doesn't match a subcommand
        return cmd_rag("ask", (action + " " + arg).strip(), cfg, messages, session_msgs)

# ══════════════════════════════════════════════════════════════
#  QUICK MATH
# ══════════════════════════════════════════════════════════════
def cmd_calc(arg: str) -> None:
    """Safe math evaluator."""
    if not arg:
        print(f"{NEON_Y}Usage: /calc <expression>  e.g. /calc 2**32 or /calc 15% of 240{R}\n"); return
    w   = min(cols(), 50)
    div_line = f"{NEON_C}{'─'*w}{R}"

    # handle "X% of Y"
    pct = re.match(r"(\d+\.?\d*)%\s*of\s*(\d+\.?\d*)", arg.lower())
    if pct:
        a, b = float(pct.group(1)), float(pct.group(2))
        result = a / 100 * b
        print(f"\n  {NEON_C}{a}% of {b}{R} = {NEON_G}{BOLD}{result:,.4g}{R}\n")
        return

    # safe eval — only allow math chars
    safe = re.sub(r"[^0-9+\-*/().% eE]", "", arg)
    try:
        result = eval(safe, {"__builtins__": {}})
        print(f"\n{div_line}")
        print(f"  {NEON_C}{arg}{R} = {NEON_G}{BOLD}{result:,}{R}")
        print(f"{div_line}\n")
    except Exception as e:
        print(f"{NEON_R}✗ Math error: {e}{R}\n")

# ══════════════════════════════════════════════════════════════
#  DAILY GOALS
# ══════════════════════════════════════════════════════════════
GOALS_PATH = os.path.expanduser("~/.cybersh_goals.json")

def load_goals() -> list:
    try:
        with open(GOALS_PATH) as f:
            data = json.load(f)
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            return [g for g in data if g.get("date") == today]
    except Exception: return []

def save_goals(goals: list) -> None:
    try:
        with open(GOALS_PATH, "w") as f: json.dump(goals, f, indent=2)
    except Exception: pass

def cmd_goals(action: str, arg: str) -> None:
    """Daily goal tracker."""
    goals = load_goals()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    w     = min(cols(), 55)
    div_line = f"{NEON_C}{'─'*w}{R}"

    if action in ("add", "") and arg:
        goals.append({"date": today, "text": arg, "done": False})
        save_goals(goals); print(f"{NEON_G}✓ Goal added.{R}\n"); return

    if action in ("done", "check") and arg.isdigit():
        idx = int(arg) - 1
        if 0 <= idx < len(goals):
            goals[idx]["done"] = True
            save_goals(goals); print(f"{NEON_G}✓ Marked done!{R}\n")
        return

    if action in ("clear", "reset"):
        save_goals([]); print(f"{NEON_G}✓ Goals cleared.{R}\n"); return

    # show
    print(f"\n{div_line}")
    print(f"{NEON_C}{BOLD}  🎯 Today's Goals — {today}{R}")
    print(div_line)
    if not goals:
        print(f"  {DIM}No goals yet. Add one: /goals add <goal>{R}")
    done = sum(1 for g in goals if g["done"])
    for i, g in enumerate(goals, 1):
        icon  = f"{NEON_G}✓{R}" if g["done"] else f"{NEON_Y}○{R}"
        text  = f"{DIM}{g['text']}{R}" if g["done"] else g["text"]
        print(f"  {icon} {i}. {text}")
    if goals:
        pct = int(100 * done / len(goals))
        bar_w = 25; filled = int(bar_w * pct / 100)
        bar = f"{NEON_G}{'█'*filled}{DIM}{'░'*(bar_w-filled)}{R}"
        print(f"\n  {bar} {NEON_Y}{pct}%{R} ({done}/{len(goals)} done)")
    print(f"\n  {DIM}/goals add <goal> | /goals done <n> | /goals clear{R}")
    print(f"{div_line}\n")



# ══════════════════════════════════════════════════════════════
#  DAILY TIP
# ══════════════════════════════════════════════════════════════
TIPS = [
    "Use `Ctrl+R` to search your bash history interactively.",
    "Use `!!` to repeat the last command. `sudo !!` to run it as root.",
    "Use `cd -` to go back to the previous directory.",
    "Use `grep -r 'text' .` to search inside all files in a folder.",
    "Use `man <command>` to read the full manual for any command.",
    "Use `watch -n 1 <cmd>` to run a command every second and see output live.",
    "Use `curl wttr.in` to check the weather in your terminal.",
    "Use `history | grep <keyword>` to find old commands fast.",
    "Use `tar -xzf file.tar.gz` to extract a .tar.gz file.",
    "Use `df -h` to see disk space in human readable format.",
    "Use `htop` for a beautiful interactive process monitor.",
    "Use `ss -tulpn` to see all open ports and what's using them.",
    "Use `find / -name '*.log' 2>/dev/null` to find all log files.",
    "Use `alias ll='ls -la'` to create a shortcut command.",
    "Use `screen` or `tmux` to keep sessions alive after disconnect.",
    "Use `chmod +x script.sh && ./script.sh` to run a bash script.",
    "Use `curl -O <url>` to download a file from the internet.",
    "Use `zip -r archive.zip folder/` to zip an entire folder.",
    "Use `wc -l file.txt` to count lines in a file.",
    "Use `cut -d',' -f1 file.csv` to extract the first column of a CSV.",
]

def show_tip() -> None:
    import random, hashlib
    # same tip per day, changes daily
    day_seed = datetime.datetime.now().strftime("%Y%m%d")
    idx = int(hashlib.md5(day_seed.encode()).hexdigest(), 16) % len(TIPS)
    tip = TIPS[idx]
    w   = min(cols(), 70)
    print(f"\n{NEON_Y}{'─'*w}")
    print(f"  💡 Tip of the day")
    print(f"{'─'*w}{R}")
    print(f"  {tip}")
    print(f"{NEON_Y}{'─'*w}{R}\n")

def cmd_passgen(arg: str) -> None:
    """Generate passwords, passphrases, or API keys."""
    import random, string, secrets
    w    = min(cols(), 60)
    div  = f"{NEON_C}{'─'*w}{R}"
    kind = arg.lower() if arg else "password"

    print(f"\n{div}")
    print(f"{NEON_C}{BOLD}  🔑 Password Generator{R}")
    print(div)

    if "phrase" in kind or "word" in kind:
        words = ["alpha","bravo","charlie","delta","echo","foxtrot","golf","hotel",
                 "india","juliet","kilo","lima","mike","november","oscar","paper",
                 "router","signal","tango","ultra","victor","whiskey","xray","yankee",
                 "zebra","rocket","flame","storm","pixel","ghost","blade","cipher",
                 "tower","nexus","forge","prism","orbit","quartz","vault","warden"]
        for _ in range(3):
            phrase = "-".join(secrets.choice(words) for _ in range(4))
            num    = secrets.randbelow(9999)
            print(f"  {NEON_G}{phrase}-{num}{R}")
    elif "api" in kind or "key" in kind or "token" in kind:
        for _ in range(3):
            key = secrets.token_hex(32)
            print(f"  {NEON_G}{key}{R}")
    else:
        chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        for length in (16, 24, 32):
            pwd = "".join(secrets.choice(chars) for _ in range(length))
            print(f"  {NEON_Y}[{length} chars]{R} {NEON_G}{pwd}{R}")

    print(f"\n  {DIM}Usage: /passgen phrase | /passgen api | /passgen (default=password){R}")
    print(f"{div}\n")

def cmd_encode(arg: str) -> None:
    """Encode/decode/hash text in multiple formats."""
    import base64, hashlib, urllib.parse
    if not arg:
        print(f"{NEON_Y}Usage: /encode <text>  or  /encode decode <base64>{R}\n")
        return

    w   = min(cols(), 70)
    div = f"{NEON_C}{'─'*w}{R}"
    print(f"\n{div}")
    print(f"{NEON_C}{BOLD}  🔐 Encode / Hash{R}")
    print(div)

    # decode mode
    if arg.lower().startswith("decode "):
        raw = arg[7:].strip()
        try:
            b64 = base64.b64decode(raw).decode(errors="replace")
            print(f"  {NEON_Y}Base64 decode:{R} {NEON_G}{b64}{R}")
        except Exception:
            print(f"  {NEON_R}✗ Not valid base64{R}")
        try:
            url = urllib.parse.unquote(raw)
            print(f"  {NEON_Y}URL decode:    {R} {NEON_G}{url}{R}")
        except Exception:
            pass
        print(f"{div}\n")
        return

    text = arg.encode()
    b64  = base64.b64encode(text).decode()
    hex_ = text.hex()
    url  = urllib.parse.quote(arg)
    md5  = hashlib.md5(text).hexdigest()
    sha1 = hashlib.sha1(text).hexdigest()
    sha256 = hashlib.sha256(text).hexdigest()

    rows = [
        ("Base64",  b64),
        ("Hex",     hex_),
        ("URL",     url),
        ("MD5",     md5),
        ("SHA1",    sha1),
        ("SHA256",  sha256),
    ]
    for label, val in rows:
        print(f"  {NEON_Y}{label:<10}{R} {NEON_G}{val}{R}")
    print(f"\n  {DIM}Decode: /encode decode <base64>{R}")
    print(f"{div}\n")

def cmd_syswatch() -> None:
    """Live CPU/RAM/Disk monitor — updates every second. Ctrl+C to stop."""
    import time as _time
    print(f"\n{NEON_C}  🖥  SYSWATCH — Live Monitor  {DIM}(Ctrl+C to stop){R}\n")
    try:
        while True:
            # CPU
            try:
                with open("/proc/stat") as f: cpu1 = f.readline().split()
                _time.sleep(0.5)
                with open("/proc/stat") as f: cpu2 = f.readline().split()
                idle1 = int(cpu1[4]); total1 = sum(int(x) for x in cpu1[1:])
                idle2 = int(cpu2[4]); total2 = sum(int(x) for x in cpu2[1:])
                cpu_pct = 100 * (1 - (idle2-idle1)/(total2-total1+0.001))
            except Exception:
                cpu_pct = 0.0

            # RAM
            try:
                meminfo = {}
                with open("/proc/meminfo") as f:
                    for line in f:
                        k, v = line.split(":")
                        meminfo[k.strip()] = int(v.strip().split()[0])
                total_ram  = meminfo.get("MemTotal", 1)
                avail_ram  = meminfo.get("MemAvailable", 0)
                used_ram   = total_ram - avail_ram
                ram_pct    = 100 * used_ram / total_ram
                ram_used_g = used_ram / 1048576
                ram_tot_g  = total_ram / 1048576
            except Exception:
                ram_pct = 0.0; ram_used_g = 0; ram_tot_g = 0

            # Disk
            try:
                st = os.statvfs("/")
                disk_total = st.f_blocks * st.f_frsize
                disk_free  = st.f_bavail * st.f_frsize
                disk_used  = disk_total - disk_free
                disk_pct   = 100 * disk_used / (disk_total + 1)
                disk_used_g = disk_used / 1e9
                disk_tot_g  = disk_total / 1e9
            except Exception:
                disk_pct = 0.0; disk_used_g = 0; disk_tot_g = 0

            def bar(pct, width=30):
                filled = int(width * pct / 100)
                color  = NEON_G if pct < 60 else NEON_Y if pct < 85 else NEON_R
                return f"{color}{'█'*filled}{DIM}{'░'*(width-filled)}{R} {color}{pct:5.1f}%{R}"

            now = datetime.datetime.now().strftime("%H:%M:%S")
            sys.stdout.write(f"\r\033[3A" if True else "")
            print(f"\033[2K  {NEON_C}CPU {R} {bar(cpu_pct)}  {DIM}{now}{R}")
            print(f"\033[2K  {NEON_C}RAM {R} {bar(ram_pct)}  {DIM}{ram_used_g:.1f}/{ram_tot_g:.1f} GB{R}")
            print(f"\033[2K  {NEON_C}DISK{R} {bar(disk_pct)}  {DIM}{disk_used_g:.1f}/{disk_tot_g:.1f} GB{R}")
            _time.sleep(0.5)
    except KeyboardInterrupt:
        print(f"\n{NEON_G}✓ Syswatch stopped.{R}\n")

def cmd_benchmark() -> None:
    """Quick CPU + RAM + disk benchmark."""
    import time as _time, random
    w   = min(cols(), 60)
    div = f"{NEON_C}{'─'*w}{R}"
    print(f"\n{div}")
    print(f"{NEON_C}{BOLD}  ⚡ Benchmark{R}")
    print(div)

    # CPU
    print(f"  {NEON_Y}CPU{R}  — calculating primes…", end="", flush=True)
    t0 = _time.time()
    primes = 0
    for n in range(2, 50000):
        if all(n % i for i in range(2, int(n**0.5)+1)): primes += 1
    cpu_t = _time.time() - t0
    cpu_score = int(3000 / (cpu_t + 0.001))
    bar_w = 20; bar_f = min(bar_w, int(cpu_score / 50))
    color = NEON_G if cpu_score > 1500 else NEON_Y if cpu_score > 800 else NEON_R
    print(f"\r  {NEON_Y}CPU{R}  {color}{'█'*bar_f}{'░'*(bar_w-bar_f)}{R} {cpu_score} pts  {DIM}({cpu_t:.2f}s){R}")

    # RAM
    print(f"  {NEON_Y}RAM{R}  — read/write test…", end="", flush=True)
    t0   = _time.time()
    data = bytearray(50 * 1024 * 1024)  # 50MB
    for i in range(0, len(data), 4096): data[i] = i % 256
    _ = sum(data[::4096])
    ram_t = _time.time() - t0
    ram_score = int(500 / (ram_t + 0.001))
    bar_f = min(bar_w, int(ram_score / 25))
    color = NEON_G if ram_score > 300 else NEON_Y if ram_score > 150 else NEON_R
    print(f"\r  {NEON_Y}RAM{R}  {color}{'█'*bar_f}{'░'*(bar_w-bar_f)}{R} {ram_score} pts  {DIM}({ram_t:.2f}s){R}")

    # Disk
    print(f"  {NEON_Y}DISK{R} — write test…", end="", flush=True)
    tmp = os.path.expanduser("~/.cybersh_bench_tmp")
    t0  = _time.time()
    try:
        with open(tmp, "wb") as f: f.write(os.urandom(20 * 1024 * 1024))
        disk_t = _time.time() - t0
        os.remove(tmp)
        disk_score = int(200 / (disk_t + 0.001))
    except Exception:
        disk_t = 99; disk_score = 0
    bar_f = min(bar_w, int(disk_score / 10))
    color = NEON_G if disk_score > 100 else NEON_Y if disk_score > 50 else NEON_R
    print(f"\r  {NEON_Y}DISK{R} {color}{'█'*bar_f}{'░'*(bar_w-bar_f)}{R} {disk_score} pts  {DIM}({disk_t:.2f}s){R}")

    total = cpu_score + ram_score + disk_score
    grade = "S" if total > 2500 else "A" if total > 1800 else "B" if total > 1200 else "C" if total > 700 else "D"
    grade_color = {
        "S": NEON_G, "A": NEON_G, "B": NEON_Y, "C": NEON_O, "D": NEON_R
    }.get(grade, NEON_C)
    print(div)
    print(f"  {NEON_C}Total score:{R} {BOLD}{total}{R}  Grade: {grade_color}{BOLD}{grade}{R}")
    print(f"{div}\n")


# ══════════════════════════════════════════════════════════════
#  SESSION SYSTEM — Save, list, load, search past chats
# ══════════════════════════════════════════════════════════════
SESSIONS_DIR = os.path.expanduser("~/.cybersh_sessions")

def _ensure_sessions_dir() -> None:
    os.makedirs(SESSIONS_DIR, exist_ok=True)

def session_save(name: str, messages: list, cfg: dict) -> None:
    """Save current conversation to a named session file."""
    _ensure_sessions_dir()
    w   = min(shutil.get_terminal_size((80,24)).columns, 60)
    div = f"{NEON_C}{chr(9472)*w}{R}"

    if not name:
        print(f"{NEON_Y}Usage: /session save <name>{R}")
        print(f"  Example: /session save pentest-example-com{chr(10)}")
        return

    # only keep user/assistant messages, skip system
    convo = [m for m in messages if m["role"] in ("user","assistant")]
    if not convo:
        print(f"{NEON_Y}⚠ Nothing to save — conversation is empty.{R}{chr(10)}")
        return

    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", name)
    ts        = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename  = f"{safe_name}__{ts}.json"
    path      = os.path.join(SESSIONS_DIR, filename)

    data = {
        "name":     name,
        "saved_at": ts,
        "mode":     cfg.get("mode","chat"),
        "messages": convo,
        "turns":    len([m for m in convo if m["role"]=="user"]),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"{chr(10)}{div}")
    print(f"{NEON_G}{chr(9608*0+9787)}  Session saved: {name}{R}")
    print(f"  {DIM}{len(data['messages'])} messages · {data['turns']} turns · {ts}{R}")
    print(f"{div}{chr(10)}")

def session_list() -> list:
    """List all saved sessions."""
    _ensure_sessions_dir()
    w   = min(shutil.get_terminal_size((80,24)).columns, 68)
    div = f"{NEON_C}{chr(9472)*w}{R}"

    files = sorted(glob.glob(os.path.join(SESSIONS_DIR, "*.json")), reverse=True)
    if not files:
        print(f"{chr(10)}{NEON_Y}No saved sessions yet.{R}")
        print(f"{DIM}Save one with: /session save <name>{R}{chr(10)}")
        return []

    print(f"{chr(10)}{div}")
    print(f"{NEON_C}{BOLD}  💾 Saved Sessions{R}")
    print(div)
    sessions = []
    for i, fpath in enumerate(files[:20], 1):
        try:
            with open(fpath, encoding="utf-8") as f:
                d = json.load(f)
            name    = d.get("name","?")
            ts      = d.get("saved_at","?")
            mode    = d.get("mode","chat")
            turns   = d.get("turns", len([m for m in d.get("messages",[]) if m["role"]=="user"]))
            mode_icon = {"chat":"💬","sec":"🔐","code":"⚡","vibe":"🎨","agent":"🤖"}.get(mode,"💬")
            print(f"  {NEON_Y}[{i:>2}]{R} {mode_icon} {NEON_C}{name:<25}{R} {DIM}{turns} turns · {ts}{R}")
            sessions.append(fpath)
        except Exception:
            pass
    print(f"{chr(10)}  {DIM}Load with: /session load <number>{R}")
    print(f"  {DIM}Search with: /session search <keyword>{R}")
    print(f"  {DIM}Delete with: /session delete <number>{R}")
    print(f"{div}{chr(10)}")
    return sessions

def session_load(arg: str, messages: list, session_msgs: list, cfg: dict) -> None:
    """Load a session and merge it into current conversation."""
    _ensure_sessions_dir()
    files = sorted(glob.glob(os.path.join(SESSIONS_DIR, "*.json")), reverse=True)
    w     = min(shutil.get_terminal_size((80,24)).columns, 60)
    div   = f"{NEON_C}{chr(9472)*w}{R}"

    if not arg:
        print(f"{NEON_Y}Usage: /session load <number> or /session load <name>{R}{chr(10)}")
        session_list()
        return

    target = None
    # try by number
    if arg.isdigit():
        idx = int(arg) - 1
        if 0 <= idx < len(files):
            target = files[idx]
    else:
        # try by name match
        for f in files:
            try:
                with open(f, encoding="utf-8") as fh:
                    d = json.load(fh)
                if arg.lower() in d.get("name","").lower():
                    target = f; break
            except Exception:
                pass

    if not target:
        print(f"{NEON_R}✗ Session not found: {arg}{R}{chr(10)}")
        session_list()
        return

    try:
        with open(target, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"{NEON_R}✗ Could not load session: {e}{R}{chr(10)}")
        return

    old_msgs = data.get("messages", [])
    name     = data.get("name","?")
    ts       = data.get("saved_at","?")
    turns    = data.get("turns", len([m for m in old_msgs if m["role"]=="user"]))

    print(f"{chr(10)}{div}")
    print(f"{NEON_G}{BOLD}  📂 Loading session: {name}{R}")
    print(f"  {DIM}{turns} turns from {ts} — merging into current chat{R}")
    print(div)

    # inject old messages right after system prompt, before current conversation
    # messages[0] is always the system prompt
    system_msg  = messages[0] if messages else {"role":"system","content":""}
    current_convo = [m for m in messages[1:] if m["role"] in ("user","assistant")]

    # build merged: system + old + separator context + current
    separator = {
        "role": "user",
        "content": f"[LOADED SESSION: '{name}' from {ts}. The above messages are from a previous conversation. Continue helping me based on both the old context and our current conversation.]"
    }
    sep_reply = {
        "role": "assistant",
        "content": f"Got it. I can see your previous session '{name}' and will use that context alongside our current conversation."
    }

    messages.clear()
    messages.append(system_msg)
    messages.extend(old_msgs)
    messages.append(separator)
    messages.append(sep_reply)
    messages.extend(current_convo)

    print(f"  {NEON_G}✓ Merged {len(old_msgs)} old messages into current chat{R}")
    print(f"  {DIM}The AI now remembers both sessions.{R}")
    print(f"{div}{chr(10)}")

def session_search(keyword: str) -> None:
    """Search all saved sessions for a keyword."""
    _ensure_sessions_dir()
    if not keyword:
        print(f"{NEON_Y}Usage: /session search <keyword>{R}{chr(10)}"); return

    files = sorted(glob.glob(os.path.join(SESSIONS_DIR, "*.json")), reverse=True)
    w     = min(shutil.get_terminal_size((80,24)).columns, 68)
    div   = f"{NEON_C}{chr(9472)*w}{R}"
    found = 0

    print(f"{chr(10)}{div}")
    print(f"{NEON_C}{BOLD}  🔍 Search: {keyword}{R}")
    print(div)

    for fpath in files:
        try:
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
            name = data.get("name","?")
            ts   = data.get("saved_at","?")
            hits = []
            for msg in data.get("messages",[]):
                content = msg.get("content","")
                if keyword.lower() in content.lower():
                    # find the snippet around the keyword
                    idx   = content.lower().find(keyword.lower())
                    start = max(0, idx-40)
                    end   = min(len(content), idx+80)
                    snip  = content[start:end].replace(chr(10)," ").strip()
                    role  = "You" if msg["role"]=="user" else "AI"
                    hits.append((role, snip))

            if hits:
                found += len(hits)
                print(f"{chr(10)}  {NEON_Y}📁 {name}{R} {DIM}({ts}){R}")
                for role, snip in hits[:3]:
                    role_color = NEON_C if role=="You" else NEON_G
                    print(f"    {role_color}{role}:{R} {DIM}…{snip}…{R}")
                if len(hits) > 3:
                    print(f"    {DIM}+ {len(hits)-3} more matches{R}")
        except Exception:
            pass

    if found == 0:
        print(f"  {DIM}No matches found for: {keyword}{R}")
    else:
        print(f"{chr(10)}  {NEON_G}✓ Found {found} match(es){R}")
    print(f"{div}{chr(10)}")

def session_delete(arg: str) -> None:
    """Delete a saved session by number or name."""
    _ensure_sessions_dir()
    files = sorted(glob.glob(os.path.join(SESSIONS_DIR, "*.json")), reverse=True)

    if not arg:
        print(f"{NEON_Y}Usage: /session delete <number>{R}{chr(10)}")
        session_list(); return

    target = None
    if arg.isdigit():
        idx = int(arg) - 1
        if 0 <= idx < len(files): target = files[idx]
    else:
        for f in files:
            if arg.lower() in os.path.basename(f).lower():
                target = f; break

    if not target:
        print(f"{NEON_R}✗ Session not found: {arg}{R}{chr(10)}"); return

    name = os.path.basename(target)
    os.remove(target)
    print(f"{chr(10)}{NEON_G}✓ Deleted session: {name}{R}{chr(10)}")

def cmd_session(action: str, arg: str, messages: list,
                session_msgs: list, cfg: dict) -> None:
    """Router for all /session subcommands."""
    a = action.lower() if action else "list"
    if a in ("save","s"):
        session_save(arg, messages, cfg)
    elif a in ("list","ls",""):
        session_list()
    elif a in ("load","open","l"):
        session_load(arg, messages, session_msgs, cfg)
    elif a in ("search","find","f"):
        session_search(arg)
    elif a in ("delete","del","rm","remove"):
        session_delete(arg)
    else:
        # treat whole thing as a name to load if it looks like one
        session_load(action + (" " + arg if arg else ""), messages, session_msgs, cfg)

def cmd_fix(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Paste any error and get an instant fix."""
    error = arg or ""
    if not error:
        print(f"{NEON_Y}Paste the error message:{R} ", end=""); sys.stdout.flush()
        error = input().strip()
    if not error:
        print(f"{NEON_Y}⚠ No error provided.{R}\n"); return ""
    return ask(cfg, messages, session_msgs,
        f"Fix this error — give the exact command or code to solve it:\n\n{error}")

def cmd_howto(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """How do I do X in Linux?"""
    if not arg:
        print(f"{NEON_Y}Usage: /howto <task>{R}\n"); return ""
    return ask(cfg, messages, session_msgs,
        f"How do I {arg} in Linux? Give me the exact command(s) to run. "
        f"Be concise — show the command first, then a one-line explanation.")

def cmd_tldr(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Explain a command in plain English."""
    if not arg:
        print(f"{NEON_Y}Usage: /tldr <command>{R}\n"); return ""
    return ask(cfg, messages, session_msgs,
        f"Explain the command `{arg}` in plain English — no jargon. "
        f"Format: 1) What it does in one sentence. 2) Common examples with explanations. "
        f"3) Any warnings or things to be careful about.")


# ══════════════════════════════════════════════════════════════
#  EVERYDAY TOOLS
# ══════════════════════════════════════════════════════════════

def cmd_convert(arg: str) -> None:
    """Convert units, temperature, and common values."""
    if not arg:
        print(f"{NEON_Y}Usage: /convert <value> <from> to <to>")
        print(f"  Examples:")
        print(f"    /convert 100 km to miles")
        print(f"    /convert 37 celsius to fahrenheit")
        print(f"    /convert 1024 mb to gb")
        print(f"    /convert 5 hours to minutes{R}\n")
        return

    w   = min(cols(), 55)
    div = f"{NEON_C}{chr(9472)*w}{R}"

    # parse: value from_unit to to_unit
    m = re.match(r"([\d.]+)\s+(.+?)\s+to\s+(.+)", arg.lower().strip())
    if not m:
        print(f"{NEON_R}✗ Format: /convert <value> <unit> to <unit>{R}\n"); return

    val   = float(m.group(1))
    frm   = m.group(2).strip()
    to    = m.group(3).strip()
    result = None; label = ""

    # temperature
    if frm in ("c","celsius","°c") and to in ("f","fahrenheit","°f"):
        result = val * 9/5 + 32; label = "°F"
    elif frm in ("f","fahrenheit","°f") and to in ("c","celsius","°c"):
        result = (val - 32) * 5/9; label = "°C"
    elif frm in ("c","celsius") and to in ("k","kelvin"):
        result = val + 273.15; label = "K"
    elif frm in ("k","kelvin") and to in ("c","celsius"):
        result = val - 273.15; label = "°C"

    # distance
    elif frm in ("km","kilometers","kilometres") and to in ("mi","miles","mile"):
        result = val * 0.621371; label = "miles"
    elif frm in ("mi","miles","mile") and to in ("km","kilometers","kilometres"):
        result = val * 1.60934; label = "km"
    elif frm in ("m","meters","metres") and to in ("ft","feet","foot"):
        result = val * 3.28084; label = "ft"
    elif frm in ("ft","feet","foot") and to in ("m","meters","metres"):
        result = val * 0.3048; label = "m"
    elif frm in ("cm","centimeters") and to in ("in","inches","inch"):
        result = val * 0.393701; label = "inches"
    elif frm in ("in","inches","inch") and to in ("cm","centimeters"):
        result = val * 2.54; label = "cm"

    # weight
    elif frm in ("kg","kilograms") and to in ("lb","lbs","pounds"):
        result = val * 2.20462; label = "lbs"
    elif frm in ("lb","lbs","pounds") and to in ("kg","kilograms"):
        result = val * 0.453592; label = "kg"
    elif frm in ("g","grams") and to in ("oz","ounces"):
        result = val * 0.035274; label = "oz"

    # data
    elif frm in ("mb","megabytes") and to in ("gb","gigabytes"):
        result = val / 1024; label = "GB"
    elif frm in ("gb","gigabytes") and to in ("mb","megabytes"):
        result = val * 1024; label = "MB"
    elif frm in ("gb","gigabytes") and to in ("tb","terabytes"):
        result = val / 1024; label = "TB"
    elif frm in ("tb","terabytes") and to in ("gb","gigabytes"):
        result = val * 1024; label = "GB"
    elif frm in ("kb","kilobytes") and to in ("mb","megabytes"):
        result = val / 1024; label = "MB"
    elif frm in ("mb","megabytes") and to in ("kb","kilobytes"):
        result = val * 1024; label = "KB"
    elif frm in ("bytes","byte") and to in ("kb","kilobytes"):
        result = val / 1024; label = "KB"

    # time
    elif frm in ("hours","hour","hr","h") and to in ("minutes","minute","min","m"):
        result = val * 60; label = "minutes"
    elif frm in ("minutes","minute","min") and to in ("hours","hour","hr","h"):
        result = val / 60; label = "hours"
    elif frm in ("hours","hour","hr") and to in ("seconds","second","sec","s"):
        result = val * 3600; label = "seconds"
    elif frm in ("days","day","d") and to in ("hours","hour","hr","h"):
        result = val * 24; label = "hours"
    elif frm in ("weeks","week","wk") and to in ("days","day","d"):
        result = val * 7; label = "days"

    # speed
    elif frm in ("kmh","km/h","kph") and to in ("mph","mi/h"):
        result = val * 0.621371; label = "mph"
    elif frm in ("mph","mi/h") and to in ("kmh","km/h","kph"):
        result = val * 1.60934; label = "km/h"
    elif frm in ("m/s","mps") and to in ("kmh","km/h","kph"):
        result = val * 3.6; label = "km/h"

    print(f"\n{div}")
    if result is not None:
        print(f"  {NEON_Y}{val:g} {frm}{R} = {NEON_G}{BOLD}{result:,.4g} {label}{R}")
    else:
        print(f"  {NEON_R}✗ Conversion not supported: {frm} → {to}{R}")
        print(f"  {DIM}Supported: temperature, distance, weight, data, time, speed{R}")
    print(f"{div}\n")


def cmd_json(arg: str) -> None:
    """Validate and pretty-print JSON. /json minify <text> to compact it."""
    if not arg:
        print(f"{NEON_Y}Usage: /json <text>  |  /json minify <text>{R}\n"); return
    w   = min(cols(), 70)
    div = f"{NEON_C}{'─'*w}{R}"
    minify = False
    if arg.lower().startswith("minify "):
        minify = True
        arg = arg[7:]
    try:
        obj = json.loads(arg)
    except Exception as e:
        print(f"\n{div}")
        print(f"{NEON_R}✗ Invalid JSON: {e}{R}")
        print(f"{div}\n")
        return
    out = json.dumps(obj, separators=(",", ":")) if minify else json.dumps(obj, indent=2)
    print(f"\n{div}")
    print(f"{NEON_C}{BOLD}  {'🗜  Minified' if minify else '📄 Pretty-printed'} JSON{R}")
    print(div)
    print(f"{NEON_G}{out}{R}")
    print(f"{div}\n")

def cmd_color(arg: str) -> None:
    """Convert a color between HEX, RGB, and HSL — with a terminal swatch."""
    if not arg:
        print(f"{NEON_Y}Usage: /color <hex|rgb>")
        print(f"  Examples: /color #1e90ff  |  /color 30,144,255{R}\n"); return
    w   = min(cols(), 50)
    div = f"{NEON_C}{'─'*w}{R}"
    raw = arg.strip().lstrip("#")
    try:
        if "," in raw:
            r, g, b = [int(x.strip()) for x in raw.split(",")]
        else:
            if len(raw) == 3:
                raw = "".join(c*2 for c in raw)
            r, g, b = int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
    except Exception:
        print(f"{NEON_R}✗ Could not parse color.{R}\n"); return

    hexv = f"#{r:02x}{g:02x}{b:02x}"
    rn, gn, bn = r/255, g/255, b/255
    mx, mn = max(rn,gn,bn), min(rn,gn,bn)
    l = (mx+mn)/2
    if mx == mn:
        h = s = 0.0
    else:
        d = mx - mn
        s = d/(2-mx-mn) if l > 0.5 else d/(mx+mn)
        if mx == rn:   h = (gn-bn)/d + (6 if gn < bn else 0)
        elif mx == gn: h = (bn-rn)/d + 2
        else:          h = (rn-gn)/d + 4
        h *= 60
    swatch_bg = f"\033[48;2;{r};{g};{b}m"

    print(f"\n{div}")
    print(f"{NEON_C}{BOLD}  🎨 Color Converter{R}")
    print(div)
    print(f"  {swatch_bg}        {R}  {NEON_Y}swatch{R}")
    print(f"  {NEON_Y}HEX:{R} {NEON_G}{hexv}{R}")
    print(f"  {NEON_Y}RGB:{R} {NEON_G}rgb({r}, {g}, {b}){R}")
    print(f"  {NEON_Y}HSL:{R} {NEON_G}hsl({h:.0f}, {s*100:.0f}%, {l*100:.0f}%){R}")
    print(f"{div}\n")

def cmd_slugify(arg: str) -> None:
    """Turn text into a clean URL slug."""
    if not arg:
        print(f"{NEON_Y}Usage: /slugify <text>{R}\n"); return
    slug = arg.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    w   = min(cols(), 60)
    div = f"{NEON_C}{'─'*w}{R}"
    print(f"\n{div}")
    print(f"{NEON_C}{BOLD}  🔗 Slugify{R}")
    print(div)
    print(f"  {NEON_G}{slug}{R}")
    print(f"{div}\n")

def cmd_countdown(arg: str) -> None:
    """Show days/hours remaining until a date. /countdown 2026-12-25"""
    if not arg:
        print(f"{NEON_Y}Usage: /countdown <YYYY-MM-DD> [HH:MM]{R}\n"); return
    raw = arg.strip()
    fmt = "%Y-%m-%d %H:%M" if " " in raw else "%Y-%m-%d"
    try:
        target = datetime.datetime.strptime(raw, fmt)
    except ValueError:
        print(f"{NEON_R}✗ Use format YYYY-MM-DD or YYYY-MM-DD HH:MM{R}\n"); return
    now   = datetime.datetime.now()
    delta = target - now
    w   = min(cols(), 50)
    div = f"{NEON_C}{'─'*w}{R}"
    print(f"\n{div}")
    print(f"{NEON_C}{BOLD}  ⏳ Countdown → {target.strftime('%Y-%m-%d %H:%M')}{R}")
    print(div)
    if delta.total_seconds() < 0:
        print(f"  {NEON_Y}That date has already passed ({-delta.days} days ago).{R}")
    else:
        days, rem = divmod(int(delta.total_seconds()), 86400)
        hours, rem = divmod(rem, 3600)
        mins, _    = divmod(rem, 60)
        print(f"  {NEON_G}{days}d {hours}h {mins}m{R} remaining")
    print(f"{div}\n")

def cmd_qr(arg: str) -> None:
    """Generate a QR code in the terminal as ASCII blocks."""
    if not arg:
        print(f"{NEON_Y}Usage: /qr <text or url>{R}\n"); return
    try:
        import urllib.request, urllib.parse
        encoded = urllib.parse.quote(arg)
        url     = f"https://qrcode.show/{encoded}"
        r = subprocess.run(
            ["curl", "-s", "--max-time", "5", "-H", "Accept: text/plain", url],
            capture_output=True, text=True
        )
        if r.returncode == 0 and r.stdout.strip():
            w   = min(cols(), 60)
            div = f"{NEON_C}{chr(9472)*w}{R}"
            print(f"\n{div}")
            print(f"{NEON_C}{BOLD}  QR Code: {arg[:40]}{R}")
            print(div)
            print(r.stdout)
            print(f"{div}\n")
        else:
            raise Exception("no output")
    except Exception:
        # fallback: manual QR using qrencode if available
        r2 = subprocess.run(
            ["qrencode", "-t", "UTF8", "-o", "-", arg],
            capture_output=True, text=True
        )
        if r2.returncode == 0:
            print(r2.stdout)
        else:
            print(f"{NEON_Y}  Install qrencode for offline QR:{R}")
            print(f"  {NEON_C}sudo apt install qrencode{R}\n")


def cmd_uuid(arg: str) -> None:
    """Generate UUID4s (or namespace UUID5s) — pure stdlib, no network."""
    import uuid as _uuid
    w   = min(cols(), 60)
    div = f"{NEON_C}{'─'*w}{R}"
    arg = (arg or "").strip()

    print(f"\n{div}")
    print(f"{NEON_C}{BOLD}  🆔 UUID Generator{R}")
    print(div)

    parts = arg.split(maxsplit=1)
    kind  = parts[0].lower() if parts else ""

    if kind == "5" and len(parts) > 1:
        name = parts[1]
        val  = _uuid.uuid5(_uuid.NAMESPACE_DNS, name)
        print(f"  {NEON_Y}v5 (dns:{name}){R} {NEON_G}{val}{R}")
    else:
        try:
            count = int(arg) if arg.isdigit() else 1
        except ValueError:
            count = 1
        count = max(1, min(count, 20))
        for _ in range(count):
            print(f"  {NEON_G}{_uuid.uuid4()}{R}")

    print(f"\n  {DIM}Usage: /uuid [count]  |  /uuid 5 <name>  (deterministic v5){R}")
    print(f"{div}\n")


def cmd_speedtest() -> None:
    """Quick internet speed test using curl."""
    import time as _time
    w   = min(cols(), 55)
    div = f"{NEON_C}{chr(9472)*w}{R}"
    print(f"\n{div}")
    print(f"{NEON_C}{BOLD}  🌐 Speed Test{R}")
    print(div)

    test_url = "https://speed.cloudflare.com/__down?bytes=10000000"  # 10MB
    print(f"  {DIM}Downloading 10MB from Cloudflare…{R}", end="", flush=True)
    t0 = _time.time()
    try:
        r = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{size_download}",
             "--max-time", "15", test_url],
            capture_output=True, text=True, timeout=20
        )
        elapsed = _time.time() - t0
        if r.returncode == 0 and r.stdout.strip().isdigit():
            bytes_dl  = int(r.stdout.strip())
            mbps      = (bytes_dl * 8) / (elapsed * 1_000_000)
            bar_w     = 25
            fill      = min(bar_w, int(bar_w * mbps / 200))
            color     = NEON_G if mbps > 50 else NEON_Y if mbps > 10 else NEON_R
            bar       = f"{color}{'█'*fill}{DIM}{'░'*(bar_w-fill)}{R}"
            grade     = "🚀 Fast" if mbps > 100 else "✅ Good" if mbps > 25 else "⚠️  Slow" if mbps > 5 else "🐌 Very slow"
            print(f"\r  {NEON_Y}Download:{R} {bar} {color}{BOLD}{mbps:.1f} Mbps{R}  {grade}")
            print(f"  {DIM}Time: {elapsed:.1f}s · Data: {bytes_dl//1024//1024}MB{R}")
        else:
            print(f"\r  {NEON_R}✗ Test failed.{R}")
    except Exception as e:
        print(f"\r  {NEON_R}✗ Error: {e}{R}")

    # ping test
    print(f"  {DIM}Testing latency…{R}", end="", flush=True)
    try:
        r2 = subprocess.run(
            ["ping", "-c", "4", "-q", "8.8.8.8"],
            capture_output=True, text=True, timeout=10
        )
        for line in r2.stdout.splitlines():
            if "min/avg/max" in line or "rtt" in line.lower():
                parts = line.split("/")
                if len(parts) >= 5:
                    avg_ms = parts[4] if "/" in line else parts[1]
                    ping_c = NEON_G if float(avg_ms.strip()) < 50 else NEON_Y if float(avg_ms.strip()) < 100 else NEON_R
                    print(f"\r  {NEON_Y}Latency: {R}{ping_c}{BOLD}{avg_ms.strip()} ms avg{R}              ")
    except Exception:
        print(f"\r  {DIM}Latency test skipped.{R}          ")
    print(f"{div}\n")


def cmd_pwcheck(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """AI rates password strength using real entropy + rule checks."""
    if not arg:
        print(f"{NEON_Y}Usage: /pwcheck <password>{R}\n"); return ""
    term_w = min(cols(), 55)
    div    = f"{NEON_C}{'─'*term_w}{R}"

    COMMON_WORDS = ["password","123456","qwerty","admin","letmein",
                    "welcome","monkey","dragon","master","iloveyou"]

    # local checks first — use a name that can't collide with terminal width
    checks = {
        "length >= 12":     len(arg) >= 12,
        "uppercase":        any(c.isupper() for c in arg),
        "lowercase":        any(c.islower() for c in arg),
        "numbers":          any(c.isdigit() for c in arg),
        "symbols":          any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in arg),
        "no common words":  not any(word in arg.lower() for word in COMMON_WORDS),
        "no simple sequence": not re.search(r"(0123|1234|2345|3456|4567|5678|6789|abcd|qwer)", arg.lower()),
        "no repeated chars":  not re.search(r"(.)\1{2,}", arg),  # aaa, 111, etc.
    }

    # real entropy calculation (bits)
    import math
    pool = 0
    if any(c.islower() for c in arg): pool += 26
    if any(c.isupper() for c in arg): pool += 26
    if any(c.isdigit() for c in arg): pool += 10
    if any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for c in arg): pool += 32
    entropy = len(arg) * math.log2(pool) if pool else 0

    passed = sum(checks.values())
    rule_score = passed / len(checks) * 100
    # blend rule score with entropy (entropy capped at 100 around 80 bits)
    entropy_score = min(100, entropy / 80 * 100)
    score = int((rule_score + entropy_score) / 2)

    color = NEON_G if score >= 75 else NEON_Y if score >= 45 else NEON_R
    grade = "Strong 💪" if score >= 75 else "Medium ⚠️" if score >= 45 else "Weak ❌"

    print(f"\n{div}")
    print(f"{NEON_C}{BOLD}  🔑 Password Strength Check{R}")
    print(div)
    for label, ok in checks.items():
        icon = f"{NEON_G}✓{R}" if ok else f"{NEON_R}✗{R}"
        print(f"  {icon} {label}")
    print(f"  {DIM}Entropy: {entropy:.0f} bits{R}")
    bar_w = 20; fill = int(bar_w * score / 100)
    print(f"\n  {color}{'█'*fill}{'░'*(bar_w-fill)}{R}  {color}{BOLD}{score}% — {grade}{R}")
    print(f"{div}\n")

    failed = [k for k,v in checks.items() if not v]
    return ask(cfg, messages, session_msgs,
        f"A password was checked with these RULE-BASED results (do not contradict these facts):\n"
        f"Score: {score}/100 ({grade})\n"
        f"Entropy: {entropy:.0f} bits\n"
        f"Checks PASSED: {[k for k,v in checks.items() if v]}\n"
        f"Checks FAILED: {failed if failed else 'none — all checks passed'}\n\n"
        f"Give a SHORT analysis that is consistent with the score above: "
        f"1) One line verdict matching the grade ({grade}). "
        f"2) The specific weaknesses from the FAILED list only — do not invent others. "
        f"3) A concrete stronger example password in similar style. "
        f"Never reveal or repeat the original password.")


# ══════════════════════════════════════════════════════════════
#  DEVELOPER TOOLS
# ══════════════════════════════════════════════════════════════

def _read_pasted_code(arg: str, prompt: str = "Paste your code (type END on a new line when done):") -> str:
    """Shared helper for /review, /testgen, /docstring, /complexity, /lint, /debug.
    If arg is a path to a real file, feed that file's actual content straight
    in — no copy-paste needed for anything already on disk."""
    if arg:
        candidate = os.path.expanduser(arg.strip())
        if os.path.isfile(candidate):
            try:
                if os.path.getsize(candidate) > 2_000_000:
                    print(f"{NEON_Y}⚠ {candidate} is large — truncating to first 2MB.{R}")
                with open(candidate, "r", errors="ignore") as f:
                    content = f.read(2_000_000)
                print(f"{DIM}  📄 Reading {candidate} ({len(content)} chars){R}")
                return content
            except Exception as e:
                print(f"{NEON_R}✗ Could not read {candidate}: {e}{R}")
                return ""
        return arg
    print(f"{NEON_Y}{prompt}{R}")
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "END": break
            lines.append(line)
        except EOFError: break
    return "\n".join(lines)


def cmd_debug(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Paste broken code, AI finds and explains every bug."""
    code = _read_pasted_code(arg, "Paste your broken code (type END on a new line when done):")
    if not code: return ""
    return ask(cfg, messages, session_msgs,
        f"Debug this code. Find EVERY bug, error, and problem:\n\n```\n{code}\n```\n\n"
        f"Format: 1) List each bug with line number and what's wrong. "
        f"2) Explain WHY it breaks. 3) Show the fully fixed code.")


def cmd_review(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Full code review — bugs, security, performance, style."""
    code = _read_pasted_code(arg, "Paste your code for review (END to finish):")
    if not code: return ""
    return ask(cfg, messages, session_msgs,
        f"Do a thorough code review of this code:\n\n```\n{code}\n```\n\n"
        f"Cover these sections:\n"
        f"🐛 BUGS — any errors or logic problems\n"
        f"🔐 SECURITY — vulnerabilities, injection risks, exposed secrets\n"
        f"⚡ PERFORMANCE — slow parts, unnecessary loops, memory issues\n"
        f"📖 READABILITY — naming, comments, structure\n"
        f"✅ GOOD — what is done well\n"
        f"Give a score out of 10 at the end.")


def cmd_template(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Generate a production-ready project template."""
    if not arg:
        print(f"{NEON_Y}Usage: /template <type>")
        print(f"  Examples:")
        print(f"    /template flask api")
        print(f"    /template fastapi")
        print(f"    /template python cli")
        print(f"    /template bash script")
        print(f"    /template react app{R}\n")
        return ""
    return ask(cfg, messages, session_msgs,
        f"Generate a complete, production-ready {arg} project template.\n"
        f"Include: proper file structure, all necessary files with content, "
        f"error handling, comments, a requirements.txt or equivalent, "
        f"and a short README explaining how to run it. "
        f"Make it something a real developer would actually use.")


def cmd_gitlog(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Run git log locally or fetch commits from a GitHub repo URL."""
    w   = min(cols(), 68)
    div = f"{NEON_C}{chr(9472)*w}{R}"

    github_url = arg.strip() if arg else ""
    if "github.com" in github_url:
        m = re.search(r"github\.com[:/]([^/]+)/([^/.\s]+)", github_url)
        if not m:
            print(f"{NEON_R}✗ Could not parse GitHub URL.{R}\n"); return ""
        owner, repo = m.group(1), m.group(2).replace(".git","")
        api_url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=20"
        print(f"\n{NEON_C}🌐 Fetching commits: {owner}/{repo}…{R}\n")
        data = _http_get(api_url)
        if not data:
            print(f"{NEON_R}✗ Could not reach GitHub API.{R}\n"); return ""
        try:
            commits = json.loads(data)
            if isinstance(commits, dict) and "message" in commits:
                print(f"{NEON_R}✗ GitHub API: {commits['message']}{R}\n"); return ""
        except Exception:
            print(f"{NEON_R}✗ Could not parse response.{R}\n"); return ""

        print(f"\n{div}")
        print(f"{NEON_C}{BOLD}  📜 Commits: {owner}/{repo}{R}")
        print(div)
        log_lines = []
        for c in commits[:20]:
            sha    = c.get("sha","")[:7]
            msg    = c.get("commit",{}).get("message","").split("\n")[0][:60]
            author = c.get("commit",{}).get("author",{}).get("name","?")[:15]
            date   = c.get("commit",{}).get("author",{}).get("date","")[:10]
            log_lines.append(f"{sha} {msg}")
            print(f"  {NEON_Y}{sha}{R} {msg}  {DIM}{author} · {date}{R}")
        print(f"{div}\n")
        log_text = "\n".join(log_lines)
    else:
        limit = arg.strip() if arg.strip().isdigit() else "20"
        r = subprocess.run(
            ["git", "log", f"-{limit}", "--oneline", "--no-merges"],
            capture_output=True, text=True, cwd=os.getcwd()
        )
        if r.returncode != 0:
            print(f"\n{NEON_R}✗ Not inside a git repository.{R}")
            print(f"{NEON_Y}  Tip: pass a GitHub URL:{R}")
            print(f"  {NEON_C}/gitlog https://github.com/neo4-svg/cybersh{R}\n")
            return ""
        log_text = r.stdout.strip()
        if not log_text:
            print(f"\n{NEON_Y}No commits found.{R}\n"); return ""
        print(f"\n{div}")
        print(f"{NEON_C}{BOLD}  📜 Git Log (last {limit} commits){R}")
        print(div)
        print(f"{DIM}{log_text}{R}")
        print(f"{div}\n")

    return ask(cfg, messages, session_msgs,
        f"Summarize these git commits in plain English:\n{log_text}\n\n"
        f"Tell me: 1) What features were added. 2) What was fixed. "
        f"3) Any concerning patterns. 4) Overall project health.")


def cmd_testgen(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Paste code, AI generates unit tests for it."""
    code = _read_pasted_code(arg, "Paste the code to generate tests for (END to finish):")
    if not code: return ""
    return ask(cfg, messages, session_msgs,
        f"Write a complete test suite for this code:\n\n```\n{code}\n```\n\n"
        f"Use pytest style. Cover: normal/expected inputs, edge cases (empty, None, "
        f"zero, negative, huge input), and error conditions that should raise. "
        f"Include the imports needed and brief comments explaining what each test checks. "
        f"Output only runnable test code plus a one-line note per test group.")


def cmd_docstring(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Paste code, AI adds docstrings + type hints without changing behavior."""
    code = _read_pasted_code(arg, "Paste the code to document (END to finish):")
    if not code: return ""
    return ask(cfg, messages, session_msgs,
        f"Add proper docstrings and type hints to this code, without changing its "
        f"behavior:\n\n```\n{code}\n```\n\n"
        f"Use Google-style docstrings (Args/Returns/Raises). Add type hints to every "
        f"function signature. Output the full updated code, nothing else.")


def cmd_complexity(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Paste code, AI analyzes time/space complexity (Big-O)."""
    code = _read_pasted_code(arg, "Paste the code to analyze (END to finish):")
    if not code: return ""
    return ask(cfg, messages, session_msgs,
        f"Analyze the time and space complexity of this code:\n\n```\n{code}\n```\n\n"
        f"For each function: give Big-O time and space complexity, explain WHY "
        f"(which lines/loops drive it), point out the worst-case input, and suggest "
        f"a faster approach if one exists (with its own Big-O).")


def cmd_gitdiff(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """AI reviews your uncommitted git changes before you commit."""
    staged_only = arg.strip().lower() in ("staged", "cached", "--staged", "--cached")
    diff_cmd = ["git", "diff", "--cached"] if staged_only else ["git", "diff"]
    r = subprocess.run(diff_cmd, capture_output=True, text=True, cwd=os.getcwd())
    if r.returncode != 0:
        print(f"\n{NEON_R}✗ Not inside a git repository.{R}\n"); return ""
    diff = r.stdout.strip()
    if not diff and not staged_only:
        # nothing unstaged — fall back to staged changes automatically
        r2 = subprocess.run(["git", "diff", "--cached"], capture_output=True, text=True, cwd=os.getcwd())
        diff = r2.stdout.strip()
    if not diff:
        print(f"\n{NEON_Y}No changes found (working tree clean).{R}\n"); return ""

    w = min(cols(), 68)
    print(f"\n{NEON_C}{'─'*w}")
    print(f"{NEON_C}{BOLD}  🔍 Reviewing {len(diff.splitlines())} diff line(s){R}")
    print(f"{NEON_C}{'─'*w}{R}\n")

    return ask(cfg, messages, session_msgs,
        f"Review this git diff before I commit it:\n\n```diff\n{diff[:6000]}\n```\n\n"
        f"Flag: 🐛 bugs introduced, 🔐 secrets/credentials accidentally included, "
        f"⚠️ risky changes (deletions, broad refactors), and 💬 anything unclear. "
        f"End with a one-line verdict: SAFE TO COMMIT / FIX FIRST.")


def cmd_commitmsg(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Generate a conventional commit message from staged (or all) changes."""
    r = subprocess.run(["git", "diff", "--cached"], capture_output=True, text=True, cwd=os.getcwd())
    if r.returncode != 0:
        print(f"\n{NEON_R}✗ Not inside a git repository.{R}\n"); return ""
    diff = r.stdout.strip()
    if not diff:
        r2 = subprocess.run(["git", "diff"], capture_output=True, text=True, cwd=os.getcwd())
        diff = r2.stdout.strip()
        if diff:
            print(f"{DIM}  (nothing staged — using unstaged changes){R}")
    if not diff:
        print(f"\n{NEON_Y}No changes to describe (working tree clean).{R}\n"); return ""

    return ask(cfg, messages, session_msgs,
        f"Write a conventional commit message for this diff:\n\n```diff\n{diff[:6000]}\n```\n\n"
        f"Format: '<type>(<scope>): <subject>' on the first line (feat/fix/refactor/docs/"
        f"test/chore/perf/style), 50 chars max for the subject. Then a blank line, then "
        f"2-4 bullet points explaining WHAT changed and WHY. Output ONLY the commit "
        f"message, nothing else — no preamble." + (f"\n\nContext from user: {arg}" if arg else ""))


def cmd_todo(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Scan a file/directory for TODO/FIXME/HACK/XXX comments."""
    path = os.path.expanduser(arg.strip()) if arg.strip() else os.getcwd()
    if not os.path.exists(path):
        print(f"\n{NEON_R}✗ Not found: {path}{R}\n"); return ""

    pattern = re.compile(r"(TODO|FIXME|HACK|XXX|BUG)[:\s](.{0,120})", re.IGNORECASE)
    hits = []
    files = [path] if os.path.isfile(path) else []
    if os.path.isdir(path):
        for root, dirs, fnames in os.walk(path):
            dirs[:] = [d for d in dirs if d not in (".git","node_modules","__pycache__",".venv","venv")]
            for fn in fnames:
                if os.path.splitext(fn)[1] in RAG_TEXT_EXTS:
                    files.append(os.path.join(root, fn))

    for fp in files[:1000]:
        try:
            with open(fp, "r", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    m = pattern.search(line)
                    if m:
                        hits.append((fp, i, m.group(1).upper(), m.group(2).strip()))
        except Exception:
            continue

    w = min(cols(), 74)
    print(f"\n{NEON_C}{'─'*w}")
    print(f"{NEON_C}{BOLD}  📌 Found {len(hits)} marker(s){R}")
    print(f"{NEON_C}{'─'*w}{R}")
    if not hits:
        print(f"{DIM}  Clean — nothing found.{R}\n"); return ""

    tag_color = {"TODO": NEON_C, "FIXME": NEON_Y, "HACK": NEON_O, "XXX": NEON_R, "BUG": NEON_R}
    for fp, ln, tag, text in hits[:200]:
        rel = os.path.relpath(fp, os.getcwd()) if os.path.isdir(path) else fp
        c = tag_color.get(tag, NEON_C)
        print(f"  {c}{BOLD}{tag:<6}{R} {DIM}{rel}:{ln}{R}  {text[:70]}")
    print()
    if len(hits) > 200:
        print(f"{DIM}  … and {len(hits)-200} more (truncated){R}\n")

    summary = "\n".join(f"{tag} {os.path.relpath(fp, os.getcwd()) if os.path.isdir(path) else fp}:{ln} — {text}"
                         for fp, ln, tag, text in hits[:200])
    return ask(cfg, messages, session_msgs,
        f"Here are TODO/FIXME/HACK markers found in the codebase:\n\n{summary[:6000]}\n\n"
        f"Group them by theme, flag anything that looks like a real bug or security "
        f"risk (not just a style note), and suggest which 3 to tackle first.")


GITIGNORE_TEMPLATES = {
    "python":  "__pycache__/\n*.py[cod]\n*.egg-info/\n.venv/\nvenv/\n.env\ndist/\nbuild/\n.pytest_cache/\n.mypy_cache/\n",
    "node":    "node_modules/\nnpm-debug.log*\n.env\ndist/\nbuild/\n.next/\ncoverage/\n",
    "rust":    "target/\nCargo.lock\n",
    "go":      "bin/\n*.exe\nvendor/\n",
    "java":    "target/\n*.class\n.gradle/\nbuild/\n",
}

def cmd_gitignore(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Generate a .gitignore for a stack, optionally write it to the cwd."""
    stack = arg.strip().lower()
    if not stack:
        print(f"{NEON_Y}Usage: /gitignore <stack>   e.g. /gitignore python{R}")
        print(f"{DIM}  Built-in: {', '.join(GITIGNORE_TEMPLATES)}  (anything else asks the AI){R}\n")
        return ""

    base = GITIGNORE_TEMPLATES.get(stack, "")
    if not base:
        # not a built-in template — ask the AI to write one
        return ask(cfg, messages, session_msgs,
            f"Write a complete, production-quality .gitignore for a {stack} project. "
            f"Output ONLY the file content, no explanation, no markdown fences.")

    common = "\n# OS/editor\n.DS_Store\n*.swp\n.vscode/\n.idea/\n"
    content = base + common
    print(f"\n{DIM}{content}{R}")
    print(f"{NEON_Y}Write this to ./.gitignore? [y/N]: {R}", end="")
    if input().strip().lower() == "y":
        dest = os.path.join(os.getcwd(), ".gitignore")
        mode = "a" if os.path.exists(dest) else "w"
        with open(dest, mode) as f:
            if mode == "a": f.write("\n")
            f.write(content)
        print(f"{NEON_G}✓ {'Appended to' if mode=='a' else 'Wrote'} {dest}{R}\n")
    return ""


LICENSE_TEMPLATES = {
    "mit":        "MIT License",
    "apache-2.0": "Apache License 2.0",
    "gpl-3.0":    "GNU General Public License v3.0",
    "bsd-3":      "BSD 3-Clause License",
    "unlicense":  "The Unlicense",
}

def cmd_license(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Generate a LICENSE file for the current project."""
    parts_ = arg.split(maxsplit=1)
    ltype  = (parts_[0].lower() if parts_ else "")
    holder = parts_[1] if len(parts_) > 1 else "neo4"

    if ltype not in LICENSE_TEMPLATES:
        print(f"{NEON_Y}Usage: /license <type> [holder name]{R}")
        print(f"{DIM}  Types: {', '.join(LICENSE_TEMPLATES)}{R}\n")
        return ""

    year = datetime.date.today().year
    resp = ask(cfg, messages, session_msgs,
        f"Output the full, exact, standard text of the {LICENSE_TEMPLATES[ltype]}, "
        f"with copyright year {year} and copyright holder \"{holder}\" filled in "
        f"where the template requires it. Output ONLY the license text, nothing else.")
    if resp:
        print(f"{NEON_Y}Write this to ./LICENSE? [y/N]: {R}", end="")
        if input().strip().lower() == "y":
            with open(os.path.join(os.getcwd(), "LICENSE"), "w") as f:
                f.write(resp.strip() + "\n")
            print(f"{NEON_G}✓ Wrote LICENSE{R}\n")
    return resp


def cmd_lint(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Run a real linter on a file if one's installed, then AI explains the findings."""
    if not arg:
        print(f"{NEON_Y}Usage: /lint <file>{R}\n"); return ""
    path = os.path.expanduser(arg.strip())
    if not os.path.exists(path):
        print(f"\n{NEON_R}✗ Not found: {path}{R}\n"); return ""

    ext = os.path.splitext(path)[1]
    linter_cmds = {
        ".py":  [["ruff", "check", path], ["flake8", path], ["pylint", path]],
        ".js":  [["eslint", path]],
        ".ts":  [["eslint", path]],
        ".sh":  [["shellcheck", path]],
    }
    output, used = None, None
    for cmd in linter_cmds.get(ext, []):
        if shutil.which(cmd[0]):
            r = subprocess.run(cmd, capture_output=True, text=True)
            output = (r.stdout + r.stderr).strip()
            used = cmd[0]
            break

    if output is None:
        print(f"{NEON_Y}⚠ No linter installed for {ext or 'this filetype'} — "
              f"falling back to an AI-only review.{R}\n")
        with open(path, "r", errors="ignore") as f:
            code = f.read()[:6000]
        return ask(cfg, messages, session_msgs,
            f"Act as a strict linter for this code:\n\n```\n{code}\n```\n\n"
            f"List every style issue, unused variable/import, and likely bug, "
            f"in a compact list format like a real linter's output.")

    print(f"\n{DIM}{used} output:{R}")
    print(output[:3000] or f"{NEON_G}✓ No issues found.{R}")
    if not output.strip():
        return ""
    return ask(cfg, messages, session_msgs,
        f"Here is raw {used} output on {os.path.basename(path)}:\n\n{output[:4000]}\n\n"
        f"Explain the top 5 most important findings in plain English and show the fix "
        f"for each. Ignore pure nitpicks (line length etc.) unless nothing else is found.")


def cmd_profile(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Run cProfile on a Python script and have the AI summarize the hotspots."""
    if not arg:
        print(f"{NEON_Y}Usage: /profile <script.py> [args...]{R}\n"); return ""
    parts_ = arg.split()
    script = os.path.expanduser(parts_[0])
    if not os.path.exists(script):
        print(f"\n{NEON_R}✗ Not found: {script}{R}\n"); return ""
    if not script.endswith(".py"):
        print(f"\n{NEON_Y}⚠ /profile currently only supports Python scripts.{R}\n"); return ""

    print(f"\n{NEON_C}⏱ Profiling {os.path.basename(script)}…{R}\n")
    r = subprocess.run(
        [sys.executable, "-m", "cProfile", "-s", "cumulative"] + parts_,
        capture_output=True, text=True, timeout=60
    )
    out = (r.stdout + r.stderr).strip()
    if not out:
        print(f"{NEON_R}✗ No profiler output (script may have crashed).{R}\n"); return ""

    lines = out.splitlines()
    top = "\n".join(lines[:35])
    print(f"{DIM}{top}{R}\n")

    return ask(cfg, messages, session_msgs,
        f"Here is cProfile output for {os.path.basename(script)}:\n\n{top}\n\n"
        f"Identify the top 3 performance hotspots (by cumulative time), explain "
        f"likely causes in plain English, and suggest concrete optimizations.")




# ══════════════════════════════════════════════════════════════
#  MORE FEATURES
# ══════════════════════════════════════════════════════════════

def cmd_ipinfo(arg: str) -> None:
    """Show info about an IP address or your own public IP."""
    target = arg.strip() if arg.strip() else ""
    url    = f"https://ipinfo.io/{target}/json" if target else "https://ipinfo.io/json"
    w   = min(cols(), 55)
    div = f"{NEON_C}{chr(9472)*w}{R}"
    print(f"\n{NEON_C}🌐 Looking up IP…{R}", end="", flush=True)
    data = _http_get(url)
    if not data:
        print(f"\r{NEON_R}✗ Could not reach ipinfo.io{R}\n"); return
    try:
        info = json.loads(data)
    except Exception:
        print(f"\r{NEON_R}✗ Parse error{R}\n"); return

    print(f"\r{div}")
    label = f"IP Info: {info.get('ip','?')}"
    if target: label += f" (lookup: {target})"
    print(f"{NEON_C}{BOLD}  {label}{R}")
    print(div)
    fields = [
        ("IP",       info.get("ip","")),
        ("Hostname", info.get("hostname","")),
        ("City",     info.get("city","")),
        ("Region",   info.get("region","")),
        ("Country",  info.get("country","")),
        ("Location", info.get("loc","")),
        ("ISP/Org",  info.get("org","")),
        ("Timezone", info.get("timezone","")),
    ]
    for label, val in fields:
        if val:
            print(f"  {NEON_Y}{label:<12}{R} {val}")
    print(f"{div}\n")


def cmd_base(arg: str) -> None:
    """Convert numbers between bases (binary, octal, hex, decimal)."""
    if not arg:
        print(f"{NEON_Y}Usage: /base <number> [from_base]")
        print(f"  Examples:")
        print(f"    /base 255          → shows binary, octal, hex")
        print(f"    /base 0xff         → hex to decimal etc")
        print(f"    /base 11111111 2   → binary to others{R}\n")
        return

    parts = arg.strip().split()
    num_str = parts[0].lower()
    w   = min(cols(), 50)
    div = f"{NEON_C}{chr(9472)*w}{R}"

    try:
        if len(parts) > 1 and parts[1].isdigit():
            n = int(num_str, int(parts[1]))
        elif num_str.startswith("0x"):
            n = int(num_str, 16)
        elif num_str.startswith("0b"):
            n = int(num_str, 2)
        elif num_str.startswith("0o"):
            n = int(num_str, 8)
        else:
            n = int(num_str)

        print(f"\n{div}")
        print(f"{NEON_C}{BOLD}  🔢 Base Converter: {num_str}{R}")
        print(div)
        print(f"  {NEON_Y}Decimal{R}  (base 10): {NEON_G}{n:,}{R}")
        print(f"  {NEON_Y}Binary  {R} (base  2): {NEON_G}{bin(n)}{R}  {DIM}({len(bin(n))-2} bits){R}")
        print(f"  {NEON_Y}Octal   {R} (base  8): {NEON_G}{oct(n)}{R}")
        print(f"  {NEON_Y}Hex     {R} (base 16): {NEON_G}{hex(n).upper().replace("0X","0x")}{R}")
        if 32 <= n <= 126:
            print(f"  {NEON_Y}ASCII   {R}          : {NEON_G}{chr(n)}{R}")
        print(f"{div}\n")
    except ValueError:
        print(f"{NEON_R}✗ Could not parse: {num_str}{R}\n")


def cmd_clock(arg: str) -> None:
    """Show current time in multiple timezones."""
    import time as _time
    w   = min(cols(), 55)
    div = f"{NEON_C}{chr(9472)*w}{R}"
    now = datetime.datetime.utcnow()

    zones = {
        "UTC":          0,
        "Baghdad (IQ)": 3,
        "London":       1 if _time.daylight else 0,
        "New York":    -4 if _time.daylight else -5,
        "Los Angeles": -7 if _time.daylight else -8,
        "Tokyo":        9,
        "Sydney":      10,
        "Dubai":        4,
    }

    # if user gave a custom offset like /clock +5
    if arg.strip():
        m = re.match(r"([+-]?\d+)", arg.strip())
        if m:
            zones[f"UTC{'+' if int(m.group(1))>=0 else ''}{m.group(1)}"] = int(m.group(1))

    print(f"\n{div}")
    print(f"{NEON_C}{BOLD}  🕐 World Clock{R}")
    print(div)
    for name, offset in zones.items():
        local = now + datetime.timedelta(hours=offset)
        time_str = local.strftime("%H:%M:%S")
        date_str = local.strftime("%a %d %b")
        is_now   = "← you" if "Baghdad" in name or "IQ" in name else ""
        color    = NEON_G if is_now else NEON_Y
        print(f"  {color}{name:<18}{R} {NEON_C}{BOLD}{time_str}{R}  {DIM}{date_str}  {is_now}{R}")
    print(f"{div}\n")


def cmd_lorem(arg: str) -> None:
    """Generate placeholder lorem ipsum text."""
    try:
        count = int(arg.strip()) if arg.strip().isdigit() else 1
    except Exception:
        count = 1

    paras = [
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.",
        "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim.",
        "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt.",
        "At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident.",
    ]
    w   = min(cols(), 70)
    div = f"{NEON_C}{chr(9472)*w}{R}"
    print(f"\n{div}")
    print(f"{NEON_C}{BOLD}  📄 Lorem Ipsum ({count} paragraph{'s' if count>1 else ''}){R}")
    print(div)
    for i in range(min(count, len(paras))):
        print(f"\n{paras[i]}")
    print(f"\n{div}\n")


def cmd_gist(arg: str) -> None:
    """Fetch and display a GitHub Gist."""
    if not arg:
        print(f"{NEON_Y}Usage: /gist <gist_url or gist_id>{R}\n"); return

    gist_id = arg.strip().split("/")[-1].replace(".git","")
    url     = f"https://api.github.com/gists/{gist_id}"
    w   = min(cols(), 68)
    div = f"{NEON_C}{chr(9472)*w}{R}"

    print(f"\n{NEON_C}Fetching gist…{R}", end="", flush=True)
    data = _http_get(url)
    if not data:
        print(f"\r{NEON_R}✗ Could not fetch gist.{R}\n"); return
    try:
        gist = json.loads(data)
    except Exception:
        print(f"\r{NEON_R}✗ Parse error.{R}\n"); return

    desc  = gist.get("description","(no description)")
    owner = gist.get("owner",{}).get("login","?")
    files = gist.get("files",{})

    print(f"\r{div}")
    print(f"{NEON_C}{BOLD}  📎 Gist: {desc[:50]}{R}")
    print(f"  {DIM}by {owner} · {len(files)} file(s){R}")
    print(div)

    for fname, finfo in list(files.items())[:3]:
        lang    = finfo.get("language","") or ""
        size    = finfo.get("size",0)
        content = finfo.get("content","") or ""
        print(f"\n  {NEON_Y}📄 {fname}{R}  {DIM}{lang} · {size} bytes{R}")
        print(f"{DIM}{content[:500]}{'…' if len(content)>500 else ''}{R}")

    if len(files) > 3:
        print(f"\n  {DIM}+ {len(files)-3} more files — view at: https://gist.github.com/{gist_id}{R}")
    print(f"{div}\n")



# ══════════════════════════════════════════════════════════════
#  SECURITY TOOLS
# ══════════════════════════════════════════════════════════════

def cmd_hash(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Identify hash type and attempt to crack common ones."""
    if not arg:
        print(f"{NEON_Y}Usage: /hash <hash_string>{R}\n"); return ""

    import hashlib
    h   = arg.strip()
    w   = min(cols(), 65)
    div = f"{NEON_C}{chr(9472)*w}{R}"

    # identify by length and charset
    hex_chars  = set("0123456789abcdefABCDEF")
    b64_chars  = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
    is_hex     = all(c in hex_chars for c in h)

    type_map = {
        32:  ["MD5", "NTLM"],
        40:  ["SHA-1", "MySQL v4"],
        56:  ["SHA-224"],
        64:  ["SHA-256", "BLAKE2s"],
        96:  ["SHA-384"],
        128: ["SHA-512", "BLAKE2b"],
        16:  ["MySQL v3 (half MD5)"],
        60:  ["bcrypt (starts with $2)"] if h.startswith("$2") else ["?"],
    }

    identified = []
    if is_hex and len(h) in type_map:
        identified = type_map[len(h)]
    elif h.startswith("$2"):
        identified = ["bcrypt"]
    elif h.startswith("$1$"):
        identified = ["MD5-crypt"]
    elif h.startswith("$6$"):
        identified = ["SHA-512-crypt (Linux shadow)"]
    elif h.startswith("$5$"):
        identified = ["SHA-256-crypt"]

    print(f"\n{div}")
    print(f"{NEON_C}{BOLD}  # Hash Analyzer{R}")
    print(div)
    print(f"  {NEON_Y}Hash   :{R} {DIM}{h[:60]}{'…' if len(h)>60 else ''}{R}")
    print(f"  {NEON_Y}Length :{R} {len(h)} chars")
    print(f"  {NEON_Y}Type   :{R} {NEON_G}{', '.join(identified) if identified else 'Unknown'}{R}")

    # try cracking against common passwords
    common = ["password","123456","admin","letmein","qwerty","welcome",
              "password123","abc123","monkey","dragon","master","sunshine",
              "princess","shadow","superman","michael","football","baseball"]
    cracked = None
    for word in common:
        for algo, fn in [("md5", hashlib.md5), ("sha1", hashlib.sha1),
                         ("sha256", hashlib.sha256), ("sha512", hashlib.sha512)]:
            if fn(word.encode()).hexdigest() == h.lower():
                cracked = word; break
        if cracked: break

    if cracked:
        print(f"  {NEON_R}{BOLD}⚠ CRACKED: '{cracked}' (common password list){R}")
    else:
        print(f"  {NEON_G}✓ Not in common password list{R}")

    print(f"{div}\n")

    return ask(cfg, messages, session_msgs,
        f"Analyze this hash for security research:\n"
        f"Hash: {h}\nIdentified as: {', '.join(identified) if identified else 'unknown'}\n"
        f"Cracked: {cracked or 'no'}\n\n"
        f"Tell me: 1) How strong is this hash algorithm. "
        f"2) Known attack methods. 3) Tools to crack it (hashcat, john). "
        f"4) Recommended algorithm to use instead if weak.")


def cmd_headers(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Check HTTP security headers of a website — with severity-tagged results."""
    if not arg:
        print(f"{NEON_Y}Usage: /headers <url or domain>")
        print(f"  Example: /headers example.com{R}\n"); return ""

    url = arg.strip()
    if not url.startswith("http"):
        url = "https://" + url

    w   = min(cols(), 72)
    div = f"{NEON_C}{'─'*w}{R}"
    print(f"\n{div}")
    print(f"{NEON_C}{BOLD}  🔒 Security Headers: {arg}{R}")
    print(div)
    print(f"  {DIM}Fetching headers…{R}", end="", flush=True)

    r = subprocess.run(
        ["curl", "-sI", "--max-time", "8", "-L", url],
        capture_output=True, text=True
    )
    if r.returncode != 0 or not r.stdout:
        print(f"\r  {NEON_R}✗ Could not reach {url}{R}\n")
        return ""

    headers = {}
    for line in r.stdout.splitlines():
        if ":" in line and not line.startswith("HTTP"):
            k, _, v = line.partition(":")
            headers[k.strip().lower()] = v.strip()

    # (header_key, label, severity_if_missing)
    # severity: "Critical" / "Warning" / "Info"
    security_headers = [
        ("strict-transport-security", "HSTS",              "Critical"),
        ("content-security-policy",   "CSP",                "Critical"),
        ("x-frame-options",           "Clickjacking Protect","Warning"),
        ("x-content-type-options",    "MIME Sniffing Block", "Warning"),
        ("referrer-policy",           "Referrer Policy",     "Info"),
        ("permissions-policy",        "Permissions Policy",  "Info"),
    ]
    sev_color = {"Critical": NEON_R, "Warning": NEON_Y, "Info": NEON_C}

    print(f"\r  {'Header':<24}{'Status':<14}{'Severity':<10}")
    print(f"  {'─'*60}")
    results = []  # for AI prompt — single source of truth, matches what's printed
    for h_key, label, sev in security_headers:
        present = h_key in headers
        if present:
            status_txt = f"{NEON_G}✓ Present{R}"
            sev_txt    = f"{DIM}—{R}"
        else:
            status_txt = f"{NEON_R}✗ Missing{R}"
            sev_txt    = f"{sev_color[sev]}{sev}{R}"
        print(f"  {NEON_Y}{label:<24}{R}{status_txt:<23}{sev_txt}")
        results.append({"label": label, "present": present, "severity": sev if not present else None})

    # Server banner — informational only, never "critical"
    server_val = headers.get("server", "")
    server_hidden = (not server_val) or len(server_val) < 10
    print(f"  {'─'*60}")
    if server_hidden:
        print(f"  {NEON_Y}{'Server Banner':<24}{R}{NEON_G}✓ Hidden{R}{'':<13}{DIM}Info — good practice{R}")
    else:
        print(f"  {NEON_Y}{'Server Banner':<24}{R}{NEON_Y}⚠ Exposed{R}{'':<12}{NEON_C}Info — not a real risk{R}")
        print(f"    {DIM}Value: {server_val[:40]}{R}")
    print(div + "\n")

    raw_headers   = "\n".join(f"{k}: {v}" for k,v in headers.items())
    missing_lines = []
    for r in results:
        if r["present"]:
            missing_lines.append(f"- {r['label']}: present")
        else:
            missing_lines.append(f"- {r['label']}: MISSING (severity: {r['severity']})")
    missing_table = "\n".join(missing_lines)

    return ask(cfg, messages, session_msgs,
        f"Security header scan for {url}. Use ONLY this exact data — do not invent "
        f"additional headers or findings not listed here:\n\n"
        f"{missing_table}\n"
        f"Server banner: {'hidden' if server_hidden else f'exposed ({server_val[:30]})'} "
        f"— this is INFORMATIONAL ONLY, never call it critical.\n\n"
        f"Raw response headers:\n{raw_headers}\n\n"
        f"Give: 1) Overall score out of 10 based strictly on the Critical/Warning/Info "
        f"counts above. 2) List only the Critical and Warning missing headers with the "
        f"exact header line to add (e.g. 'Content-Security-Policy: default-src self'). "
        f"3) One line noting server banner is informational, not a real vulnerability. "
        f"Do not list headers that are already present as problems.")


def cmd_osint(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """OSINT checklist and tools for a username or target."""
    if not arg:
        print(f"{NEON_Y}Usage: /osint <username or target>{R}\n"); return ""
    return ask(cfg, messages, session_msgs,
        f"Create a complete OSINT investigation checklist for: {arg}\n\n"
        f"Cover:\n"
        f"1. Username search — which platforms to check and exact URLs\n"
        f"2. Email/domain investigation tools and techniques\n"
        f"3. Social media footprint — what to look for\n"
        f"4. Public records and data breach databases to check\n"
        f"5. Metadata investigation (images, documents)\n"
        f"6. Tools to use: Sherlock, Maltego, theHarvester, etc.\n"
        f"7. What NOT to do (stay legal)\n"
        f"Format as a step-by-step actionable checklist.")


def cmd_wordlist(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Generate a targeted wordlist based on a theme or target."""
    if not arg:
        print(f"{NEON_Y}Usage: /wordlist <theme or target info>")
        print(f"  Examples:")
        print(f"    /wordlist company named TechCorp founded 2010 in London")
        print(f"    /wordlist person named John Smith born 1990 loves football{R}\n")
        return ""
    return ask(cfg, messages, session_msgs,
        f"Generate a targeted wordlist for password auditing based on:\n{arg}\n\n"
        f"Include:\n"
        f"1. Name variations (first, last, initials, combinations)\n"
        f"2. Years and dates (birth year, founding year, etc.)\n"
        f"3. Common substitutions (a→@, e→3, i→1, o→0, s→$)\n"
        f"4. Common suffixes (123, !, 2024, #1, etc.)\n"
        f"5. Combined patterns\n"
        f"Output as a plain list, one word per line, 50-100 entries.")


# ══════════════════════════════════════════════════════════════
#  AI TOOLS
# ══════════════════════════════════════════════════════════════

def cmd_think(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Make AI think step by step before answering."""
    if not arg:
        print(f"{NEON_Y}Usage: /think <question>{R}\n"); return ""
    return ask(cfg, messages, session_msgs,
        f"Think through this carefully before answering. "
        f"Use this format:\n"
        f"🧠 THINKING:\n[break down the problem step by step, consider different angles]\n\n"
        f"✅ ANSWER:\n[your final clear answer]\n\n"
        f"Question: {arg}")


def cmd_debate(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """AI argues both sides of any topic."""
    if not arg:
        print(f"{NEON_Y}Usage: /debate <topic>")
        print(f"  Example: /debate AI will replace programmers{R}\n"); return ""
    return ask(cfg, messages, session_msgs,
        f"Debate both sides of: {arg}\n\n"
        f"Format:\n"
        f"✅ FOR (strongest arguments in favor):\n"
        f"[3-4 compelling points]\n\n"
        f"❌ AGAINST (strongest arguments against):\n"
        f"[3-4 compelling points]\n\n"
        f"⚖️ VERDICT:\n"
        f"[which side has stronger arguments and why — be honest]")


def cmd_improve(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """AI rewrites any text to be clearer and more professional."""
    text = arg
    if not text:
        print(f"{NEON_Y}Paste your text to improve (END to finish):{R}")
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "END": break
                lines.append(line)
            except EOFError: break
        text = "\n".join(lines)
    if not text: return ""
    return ask(cfg, messages, session_msgs,
        f"Improve this text — make it clearer, more professional, and more impactful. "
        f"Keep the same meaning and tone but fix grammar, flow, and word choice.\n\n"
        f"Original:\n{text}\n\n"
        f"Show: 1) The improved version. 2) A bullet list of what you changed and why.")


def cmd_eli5_topic(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Explain any complex topic like the person is 5 years old."""
    if not arg:
        print(f"{NEON_Y}Usage: /eli5 <topic>")
        print(f"  Example: /eli5 how does encryption work{R}\n"); return ""
    return ask(cfg, messages, session_msgs,
        f"Explain this like I am literally 5 years old: {arg}\n\n"
        f"Rules: no jargon, short sentences, use fun real-world analogies "
        f"(toys, food, playground, etc.), make it memorable and fun. "
        f"If there is a common misconception about this topic, clear it up simply.")

def cmd_cron_explain(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """AI explains (or builds) a cron schedule expression."""
    if not arg:
        print(f"{NEON_Y}Usage: /cron <expression>  |  /cron every day at 5pm")
        print(f"  Example: /cron 0 */4 * * *{R}\n"); return ""
    return ask(cfg, messages, session_msgs,
        f"This input is either a cron expression to explain, or a plain-English "
        f"schedule to convert into a cron expression: \"{arg}\"\n\n"
        f"If it looks like a cron expression, explain exactly when it runs in "
        f"plain English. If it's plain English, give the correct cron expression "
        f"and explain it. Keep it short and precise.")

def cmd_quiz(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """AI generates a short multiple-choice quiz on any topic."""
    if not arg:
        print(f"{NEON_Y}Usage: /quiz <topic>")
        print(f"  Example: /quiz networking basics{R}\n"); return ""
    return ask(cfg, messages, session_msgs,
        f"Create a 5-question multiple-choice quiz about: {arg}\n\n"
        f"Format: numbered questions, each with 4 options (A-D). "
        f"Put the answer key at the very end under a clearly marked 'Answers' "
        f"section so it's easy to scroll past without spoiling.")

def cmd_namebrainstorm(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """AI brainstorms names for a project, product, or variable scheme."""
    if not arg:
        print(f"{NEON_Y}Usage: /name <description>")
        print(f"  Example: /name a CLI tool for managing dotfiles{R}\n"); return ""
    return ask(cfg, messages, session_msgs,
        f"Brainstorm 10 creative name ideas for: {arg}\n\n"
        f"Format as a numbered list, each with the name in bold-ish caps and "
        f"a 5-8 word reason it fits. Mix styles: a few literal, a few clever/punny, "
        f"a few abstract/brandable. No explanations beyond the one line each.")

def cmd_cheatsheet(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """AI-generated quick-reference cheat sheet for any tool, language, or topic."""
    if not arg:
        print(f"{NEON_Y}Usage: /cheatsheet <tool or topic>")
        print(f"  Example: /cheatsheet tmux{R}\n"); return ""
    return ask(cfg, messages, session_msgs,
        f"Write a concise terminal-friendly cheat sheet for: {arg}\n\n"
        f"Format: short intro line, then grouped sections with the most useful "
        f"commands/syntax/shortcuts as a list (`command` — what it does). "
        f"Keep each entry to one line. Cover the 80% of use cases people actually need. "
        f"No fluff, no long paragraphs.")

def cmd_notes(action: str, arg: str) -> None:
    """Quick note-taking during sessions."""
    notes_file = os.path.expanduser("~/.cybersh_notes.json")
    try:
        with open(notes_file) as f: notes = json.load(f)
    except Exception:
        notes = []

    w   = min(cols(), 60)
    div = f"{NEON_C}{'─'*w}{R}"

    if action in ("add", "note", "") and arg:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        notes.append({"time": ts, "text": arg})
        with open(notes_file, "w") as f: json.dump(notes, f, indent=2)
        print(f"{NEON_G}✓ Note saved.{R}\n")
    elif action in ("list", "show", "ls", ""):
        if not notes:
            print(f"{NEON_Y}No notes yet. Use: /note <text>{R}\n"); return
        print(f"\n{div}")
        print(f"{NEON_C}{BOLD}  📝 Notes{R}")
        print(div)
        for i, n in enumerate(notes[-20:], 1):
            print(f"  {NEON_Y}{i:>2}.{R} {DIM}[{n['time']}]{R} {n['text']}")
        print(f"{div}\n")
    elif action in ("clear", "wipe"):
        with open(notes_file, "w") as f: json.dump([], f)
        print(f"{NEON_G}✓ Notes cleared.{R}\n")
    elif action in ("del", "delete", "rm") and arg.isdigit():
        idx = int(arg) - 1
        if 0 <= idx < len(notes):
            removed = notes.pop(idx)
            with open(notes_file, "w") as f: json.dump(notes, f, indent=2)
            print(f"{NEON_G}✓ Deleted: {removed['text'][:50]}{R}\n")
        else:
            print(f"{NEON_R}✗ Note #{arg} not found.{R}\n")
    else:
        # treat whole arg as a note if no subcommand matched
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        text = (action + " " + arg).strip()
        notes.append({"time": ts, "text": text})
        with open(notes_file, "w") as f: json.dump(notes, f, indent=2)
        print(f"{NEON_G}✓ Note saved.{R}\n")

def setup_wizard(cfg: dict) -> None:
    print(f"\n{BOLD_C}{'─'*60}")
    print(f"  CYBER SH DIRECT — Setup Wizard")
    print(f"{'─'*60}{R}\n")

    # check llama-cpp-python
    try:
        import llama_cpp
        print(f"{NEON_G}✓ llama-cpp-python installed{R}")
    except ImportError:
        print(f"{NEON_R}✗ llama-cpp-python not found{R}")
        print(f"\n{NEON_Y}Install it:{R}")
        print(f"  pip install llama-cpp-python --break-system-packages\n")
        ans = input("Install now? [y/N]: ").strip().lower()
        if ans == "y":
            os.system("pip install llama-cpp-python --break-system-packages")
        else:
            print(f"{NEON_R}Cannot continue without llama-cpp-python{R}")
            return

    # model selection
    print(f"\n{NEON_Y}Do you have a .gguf model file already? [y/N]: {R}", end="")
    has_model = input().strip().lower()

    if has_model == "y":
        print(f"{NEON_C}Path to .gguf file: {R}", end="")
        path = input().strip()
        path = os.path.expanduser(path)
        if os.path.exists(path):
            cfg["model_path"] = path
            print(f"{NEON_G}✓ Model set: {path}{R}")
        else:
            print(f"{NEON_R}✗ File not found{R}")
    else:
        print(f"\n{NEON_Y}Available models to download:{R}\n")
        for k, m in KNOWN_MODELS.items():
            print(f"  {NEON_C}[{k}]{R} {m['name']}")
        print(f"\n{NEON_Y}Choose [1-{len(KNOWN_MODELS)}] or Enter to skip: {R}", end="")
        choice = input().strip()
        if choice in KNOWN_MODELS:
            model   = KNOWN_MODELS[choice]
            dl_dir  = os.path.expanduser("~/ollama-models")
            os.makedirs(dl_dir, exist_ok=True)
            dest    = os.path.join(dl_dir, model["file"])
            print(f"\n{NEON_C}Downloading {model['file']}…{R}")
            print(f"{DIM}This may take a while depending on your connection{R}\n")
            ok = _download_file(model["url"], dest, label=model["file"])
            if ok:
                ok = _verify_model_sha256(dest, KNOWN_MODEL_SHA256.get(choice), model["file"])
            if ok and os.path.exists(dest):
                cfg["model_path"] = dest
                print(f"\n{NEON_G}✓ Downloaded to: {dest}{R}")
            else:
                print(f"{NEON_R}✗ Download failed. Try again, or download manually:{R}")
                print(f"  {model['url']}  →  ~/ollama-models/{model['file']}")

    # threads
    import multiprocessing
    cpu_count = multiprocessing.cpu_count()
    print(f"\n{NEON_Y}CPU threads to use [{cpu_count}]: {R}", end="")
    t = input().strip()
    cfg["threads"] = int(t) if t.isdigit() else cpu_count

    # GPU check
    gpu = _detect_gpu()
    if gpu["type"] == "nvidia":
        print(f"\n{NEON_G}✓ NVIDIA GPU detected: {gpu['name']} {gpu['vram']}{R}")
        print(f"{NEON_Y}For GPU acceleration, reinstall llama-cpp-python with CUDA:{R}")
        print(f"  {NEON_C}CMAKE_ARGS=\"-DGGML_CUDA=on\" pip install llama-cpp-python --force-reinstall --break-system-packages{R}")
        print(f"{DIM}(GPU will be used automatically every time you run the tool){R}")
    elif gpu["type"] == "amd":
        print(f"\n{NEON_Y}⚠ AMD GPU detected: {gpu['name']}{R}")
        print(f"{DIM}ROCm support is experimental. CPU will be used by default.{R}")
    elif gpu["type"] == "intel":
        print(f"\n{NEON_Y}⚠ Intel GPU detected: {gpu['name']}{R}")
        print(f"{DIM}Intel GPU acceleration not yet supported. CPU will be used.{R}")
    else:
        print(f"\n{DIM}No dedicated GPU detected — running on CPU (normal){R}")

    save_cfg(cfg)
    print(f"\n{NEON_G}✓ Setup complete!{R}")
    print(f"  Run: {NEON_C}python3 {sys.argv[0]}{R}")
    print(f"\n{DIM}New: /agent mode now auto-loops tool calls, /see gives you vision "
          f"(run '/see setup'), /rag builds a local knowledge base.{R}\n")

# ══════════════════════════════════════════════════════════════
#  IMAGE GENERATION — Stable Diffusion via diffusers (CPU/GPU)
# ══════════════════════════════════════════════════════════════

def cmd_image(arg: str) -> None:
    """Generate an image from a text prompt using Stable Diffusion (diffusers).
    Saves as .png in the same directory as this script.
    Usage: /image <prompt>
    Options you can append to prompt:
      --steps N      number of inference steps (default 20)
      --size WxH     output resolution, e.g. 512x512 (default 512x512)
      --model <id>   HuggingFace model id (default: runwayml/stable-diffusion-v1-5)
      --neg <text>   negative prompt (things to avoid)
    """
    if not arg:
        print(f"\n{NEON_Y}Usage: /image <prompt> [options]")
        print(f"  Options:")
        print(f"    --steps N       inference steps (default 20, more = better quality)")
        print(f"    --size WxH      e.g. 512x512 or 768x512 (default 512x512)")
        print(f"    --model <id>    HuggingFace model ID")
        print(f"    --neg <text>    negative prompt")
        print(f"  Examples:")
        print(f"    /image a neon cyberpunk city at night")
        print(f"    /image a portrait of a hacker --steps 30 --size 512x768")
        print(f"    /image fantasy castle --neg blurry, ugly, low quality{R}\n")
        return

    # ── parse flags out of the prompt ────────────────────────
    steps     = 20
    width     = 512
    height    = 512
    model_id  = "runwayml/stable-diffusion-v1-5"
    neg_prompt = "blurry, ugly, low quality, watermark, text, deformed"
    prompt    = arg

    import re as _re
    def _extract(flag, default, cast=str):
        nonlocal prompt
        m = _re.search(rf"{flag}\s+(\S+)", prompt)
        if m:
            prompt = prompt.replace(m.group(0), "").strip()
            try: return cast(m.group(1))
            except: pass
        return default

    steps    = _extract("--steps",  20,    int)
    model_id = _extract("--model",  model_id, str)

    size_m = _re.search(r"--size\s+(\d+)x(\d+)", prompt)
    if size_m:
        width  = int(size_m.group(1))
        height = int(size_m.group(2))
        prompt = prompt.replace(size_m.group(0), "").strip()

    neg_m = _re.search(r"--neg\s+(.+?)(?=--|$)", prompt)
    if neg_m:
        neg_prompt = neg_m.group(1).strip()
        prompt = prompt.replace(neg_m.group(0), "").strip()

    prompt = prompt.strip()
    if not prompt:
        print(f"{NEON_R}✗ Prompt cannot be empty.{R}\n"); return

    # ── check / install diffusers ─────────────────────────────
    try:
        import torch
        from diffusers import StableDiffusionPipeline
    except ImportError:
        print(f"\n{NEON_Y}📦 diffusers not installed — installing now…{R}\n")
        _install_packages(["diffusers", "transformers", "accelerate", "safetensors"])
        try:
            import torch
            from diffusers import StableDiffusionPipeline
        except ImportError:
            print(f"{NEON_R}✗ Could not import diffusers after install.")
            print(f"  Manual fix: pip install diffusers transformers accelerate safetensors --break-system-packages{R}\n")
            return

    # ── determine device ──────────────────────────────────────
    device = "cpu"
    dtype  = torch.float32
    if torch.cuda.is_available():
        device = "cuda"
        dtype  = torch.float16
        gpu_name = torch.cuda.get_device_name(0)
        print(f"\n{NEON_G}✓ CUDA GPU: {gpu_name} — using GPU acceleration ⚡{R}")
    else:
        print(f"\n{DIM}  No CUDA GPU found — running on CPU (this will be slow){R}")

    w = min(shutil.get_terminal_size((80, 24)).columns, 65)
    dline = f"{NEON_C}{'─'*w}{R}"
    print(f"\n{dline}")
    print(f"{NEON_C}{BOLD}  🎨 Image Generation{R}")
    print(dline)
    print(f"  {NEON_Y}Prompt:{R}  {prompt}")
    print(f"  {NEON_Y}Size:  {R}  {width}×{height}")
    print(f"  {NEON_Y}Steps: {R}  {steps}")
    print(f"  {NEON_Y}Model: {R}  {DIM}{model_id}{R}")
    print(f"  {NEON_Y}Device:{R}  {device.upper()}")
    print(dline)

    # ── load pipeline (cached after first load) ───────────────
    print(f"\n{DIM}  Loading model (first run downloads ~4GB)…{R}")
    try:
        pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=dtype,
            safety_checker=None,     # let the user manage content locally
        )
        pipe = pipe.to(device)
        if device == "cpu":
            pipe.enable_attention_slicing()   # saves RAM on CPU
    except Exception as e:
        print(f"\n{NEON_R}✗ Failed to load model: {e}{R}\n")
        return

    # ── generate ──────────────────────────────────────────────
    print(f"\n{NEON_C}  Generating image… {DIM}(Ctrl+C to cancel){R}\n")
    import time as _time
    t0 = _time.time()
    try:
        result = pipe(
            prompt,
            negative_prompt   = neg_prompt,
            num_inference_steps = steps,
            width             = width,
            height            = height,
        )
        image = result.images[0]
    except KeyboardInterrupt:
        print(f"\n{NEON_Y}  Generation cancelled.{R}\n")
        return
    except Exception as e:
        print(f"\n{NEON_R}✗ Generation error: {e}{R}\n")
        return

    elapsed = _time.time() - t0

    # ── save .png in same dir as this script ──────────────────
    import re as _re2, datetime as _dt
    script_dir = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
    safe_name  = _re2.sub(r"[^a-zA-Z0-9]+", "_", prompt[:40]).strip("_")
    ts_str     = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename   = f"cybersh_img_{safe_name}_{ts_str}.png"
    out_path   = os.path.join(script_dir, filename)

    try:
        image.save(out_path)
    except Exception as e:
        print(f"{NEON_R}✗ Could not save image: {e}{R}\n")
        return

    print(f"\n{dline}")
    print(f"{NEON_G}{BOLD}  ✓ Image saved!{R}")
    print(f"  {NEON_C}Path:{R}  {out_path}")
    print(f"  {NEON_C}Size:{R}  {width}×{height} px")
    print(f"  {NEON_C}Time:{R}  {elapsed:.1f}s")
    print(f"{dline}\n")


# ══════════════════════════════════════════════════════════════
#  WEB AGENT — persistent site memory + auth (TinyDB)
# ══════════════════════════════════════════════════════════════
#
#  Commands:
#    /fetch <url> [task]     — fetch URL (save it), optionally ask AI about it
#    /fetchauth <url>        — add / update auth for a saved site
#    /fetchsites             — list all saved sites
#    /fetchforget <url>      — remove a saved site
#
#  When the AI is asked anything mentioning a saved URL (or its domain),
#  cybersh auto-fetches a fresh snapshot and injects it as context.
# ══════════════════════════════════════════════════════════════

import sqlite3 as _sqlite3  # only used for type hint — actual store is TinyDB

def _wa_db():
    """Return a TinyDB instance, auto-creating the file next to this script."""
    try:
        from tinydb import TinyDB
    except ImportError:
        _install_packages(["tinydb"])
        from tinydb import TinyDB
    script_dir = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
    db_path = os.path.join(script_dir, "cybersh_webagent.json")
    return TinyDB(db_path)

def _wa_clean_html(raw_text: str) -> str:
    """Strip HTML tags and collapse whitespace into readable plain text."""
    import re as _re
    text = _re.sub(r"<script[^>]*>.*?</script>", "", raw_text, flags=_re.S)
    text = _re.sub(r"<style[^>]*>.*?</style>",   "", text,     flags=_re.S)
    text = _re.sub(r"<[^>]+>", " ", text)
    text = _re.sub(r"[ \t]{2,}", " ", text)
    text = "\n".join(l.strip() for l in text.splitlines() if l.strip())
    return text[:12000]


# Sites known to be JS-heavy SPAs that need a real browser
_JS_HEAVY_DOMAINS = {
    "x.com", "twitter.com", "instagram.com", "facebook.com",
    "linkedin.com", "reddit.com", "tiktok.com", "pinterest.com",
    "youtube.com", "discord.com", "twitch.tv", "github.com",
}

def _wa_is_spa(url: str) -> bool:
    import re as _re
    m = _re.match(r"https?://(?:www\.)?([^/]+)", url)
    return bool(m and m.group(1) in _JS_HEAVY_DOMAINS)


def _wa_fetch_playwright(url: str, auth: dict | None = None) -> tuple[int, str]:
    """Render page with a real Chromium browser via Playwright, return plain text."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        _install_packages(["playwright"])
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return 0, "playwright not installed — run: pip install playwright --break-system-packages && playwright install chromium"

    # ensure chromium is installed
    import subprocess as _sp
    _sp.run(["playwright", "install", "chromium", "--quiet"], capture_output=True)

    print(f"  {DIM}Launching Chromium browser…{R}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx_opts = {}

        # inject auth as cookies or headers
        if auth:
            atype = auth.get("type", "")
            if atype == "cookie":
                # parse "name=value; name2=value2" into list of dicts
                import re as _re
                cookies = []
                import urllib.parse as _up
                parsed = _up.urlparse(url)
                domain  = parsed.netloc
                for pair in auth["value"].split(";"):
                    pair = pair.strip()
                    if "=" in pair:
                        n, v = pair.split("=", 1)
                        cookies.append({"name": n.strip(), "value": v.strip(),
                                        "domain": domain, "path": "/"})
                ctx_opts["storage_state"] = {"cookies": cookies, "origins": []}

        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            **ctx_opts
        )

        # bearer / basic — inject as extra HTTP headers
        if auth:
            atype = auth.get("type", "")
            if atype == "bearer":
                context.set_extra_http_headers({"Authorization": f"Bearer {auth['value']}"})
            elif atype == "basic":
                import base64 as _b64
                creds = _b64.b64encode(f"{auth['user']}:{auth['pass']}".encode()).decode()
                context.set_extra_http_headers({"Authorization": f"Basic {creds}"})

        page = context.new_page()
        try:
            resp = page.goto(url, wait_until="networkidle", timeout=30000)
            status = resp.status if resp else 200
            # wait a little extra for dynamic content
            page.wait_for_timeout(2000)
            content = page.inner_text("body")
            content = "\n".join(l.strip() for l in content.splitlines() if l.strip())
            return status, content[:12000]
        except Exception as e:
            return 0, str(e)
        finally:
            browser.close()


def _wa_fetch_urllib(url: str, auth: dict | None = None) -> tuple[int, str]:
    """Fetch URL with urllib (fast, for regular static sites)."""
    import urllib.request as _ur, urllib.error as _ue, ssl as _ssl
    ctx = _ssl.create_default_context()
    headers = {"User-Agent": "Mozilla/5.0 (CyberSH WebAgent)"}
    if auth:
        atype = auth.get("type", "")
        if atype == "bearer":
            headers["Authorization"] = f"Bearer {auth['value']}"
        elif atype == "basic":
            import base64 as _b64
            creds = _b64.b64encode(f"{auth['user']}:{auth['pass']}".encode()).decode()
            headers["Authorization"] = f"Basic {creds}"
        elif atype == "cookie":
            headers["Cookie"] = auth["value"]
    req = _ur.Request(url, headers=headers)
    try:
        with _ur.urlopen(req, timeout=15, context=ctx) as r:
            ct  = r.headers.get_content_type() or ""
            raw = r.read().decode("utf-8", errors="replace")
            return 200, _wa_clean_html(raw) if "html" in ct else raw[:12000]
    except _ue.HTTPError as e:
        return e.code, str(e)
    except Exception as e:
        return 0, str(e)


def _wa_fetch(url: str, auth: dict | None = None) -> tuple[int, str]:
    """
    Smart fetch: uses Playwright (real Chromium) for JS-heavy SPAs like X/Twitter,
    Instagram, Reddit etc. Falls back to fast urllib for everything else.
    Auth (cookie/bearer/basic) is forwarded to whichever engine is used.
    """
    if _wa_is_spa(url):
        print(f"  {DIM}JS-heavy site detected — using Chromium renderer…{R}")
        return _wa_fetch_playwright(url, auth)
    status, content = _wa_fetch_urllib(url, auth)
    # if urllib got back almost nothing (JS shell), retry with Playwright
    if status == 200 and len(content.strip()) < 600:
        print(f"  {DIM}Response too small ({len(content.strip())} chars) — retrying with Chromium…{R}")
        return _wa_fetch_playwright(url, auth)
    return status, content

def _wa_find(url: str):
    """Return TinyDB record matching url or its domain, or None."""
    from tinydb import Query
    db  = _wa_db()
    W   = Query()
    rec = db.get(W.url == url)
    if rec:
        return rec
    # try domain match
    import re as _re
    m = _re.match(r"https?://([^/]+)", url)
    if m:
        domain = m.group(1)
        rec = db.get(W.domain == domain)
    return rec

def cmd_web(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """
    /fetch <url> [task]
    Fetch a URL, persist it in the agent DB, optionally ask the AI a question about it.
    """
    if not arg:
        print(f"\n{NEON_Y}Usage: /fetch <url> [task/question]")
        print(f"  Examples:")
        print(f"    /fetch https://example.com")
        print(f"    /fetch https://example.com summarise the main content")
        print(f"    /fetch https://api.example.com/data what are the available endpoints?{R}\n")
        return ""

    parts  = arg.split(None, 1)
    url    = parts[0]
    task   = parts[1] if len(parts) > 1 else ""

    if not url.startswith("http"):
        url = "https://" + url

    import re as _re
    m      = _re.match(r"https?://([^/]+)", url)
    domain = m.group(1) if m else url

    w = min(shutil.get_terminal_size((80, 24)).columns, 65)
    dline = f"{NEON_C}{'─'*w}{R}"
    print(f"\n{dline}")
    print(f"{NEON_C}{BOLD}  🌐 Web Agent{R}")
    print(dline)
    print(f"  {NEON_Y}URL:{R} {url}")

    # check for saved auth
    existing = _wa_find(url)
    auth     = existing.get("auth") if existing else None

    print(f"  {NEON_Y}Auth:{R} {DIM}{auth['type'] if auth else 'none'}{R}")
    print(f"  {DIM}Fetching…{R}")

    status, content = _wa_fetch(url, auth)

    if status == 401 or status == 403:
        print(f"\n{NEON_Y}  ⚠  Status {status} — site requires authentication.")
        print(f"  Run: {NEON_C}/fetchauth {url}{R} to add credentials.\n")
        # still save the URL so next /fetch auto-prompts
        _wa_save(url, domain, auth=None)
        return ""

    if status == 0 or status >= 400:
        print(f"\n{NEON_R}  ✗ Fetch failed (status {status}): {content}{R}\n")
        return ""

    print(f"  {NEON_G}✓ Fetched {len(content)} chars (status {status}){R}")
    print(dline)

    # persist / update
    _wa_save(url, domain, auth)

    if not task:
        # just show a short preview
        preview = content[:800].replace("\n", " ")
        print(f"\n{DIM}{preview}…{R}\n")
        print(f"{NEON_C}  Tip: /fetch {url} <your question> to ask the AI about this page{R}\n")
        return ""

    # ask AI with page content injected as context
    context_prompt = (
        f"The user fetched this webpage ({url}).\n"
        f"Here is the page content (truncated to 12 000 chars):\n\n"
        f"---\n{content}\n---\n\n"
        f"User task: {task}"
    )
    print(f"\n{NEON_C}  Asking AI about this page…{R}\n")
    return ask(cfg, messages, session_msgs, context_prompt)


def _wa_save(url: str, domain: str, auth):
    """Upsert a site record in TinyDB."""
    from tinydb import Query
    db  = _wa_db()
    W   = Query()
    rec = db.get(W.url == url)
    data = {"url": url, "domain": domain, "auth": auth}
    if rec:
        db.update(data, W.url == url)
    else:
        db.insert(data)


def cmd_webauth(arg: str) -> None:
    """/fetchauth <url> — add or update authentication for a saved site."""
    if not arg:
        print(f"\n{NEON_Y}Usage: /fetchauth <url>{R}\n"); return

    url = arg.strip()
    if not url.startswith("http"):
        url = "https://" + url

    import re as _re
    m      = _re.match(r"https?://([^/]+)", url)
    domain = m.group(1) if m else url

    w = min(shutil.get_terminal_size((80, 24)).columns, 65)
    dline = f"{NEON_C}{'─'*w}{R}"
    print(f"\n{dline}")
    print(f"{NEON_C}{BOLD}  🔐 Web Auth Setup — {domain}{R}")
    print(dline)
    print(f"  {NEON_Y}1{R}  Cookie  (paste Cookie: header from browser DevTools)")
    print(f"  {NEON_Y}2{R}  Bearer token")
    print(f"  {NEON_Y}3{R}  Basic auth (username + password)")
    print(f"  {NEON_Y}0{R}  Remove auth")
    choice = input(f"\n  {NEON_C}Choose [{NEON_Y}1/2/3/0{NEON_C}]: {R}").strip()

    auth = None
    if choice == "1":
        val = input(f"  {NEON_C}Paste cookie value: {R}").strip()
        auth = {"type": "cookie", "value": val}
    elif choice == "2":
        val = input(f"  {NEON_C}Paste bearer token: {R}").strip()
        auth = {"type": "bearer", "value": val}
    elif choice == "3":
        u = input(f"  {NEON_C}Username: {R}").strip()
        p = input(f"  {NEON_C}Password: {R}").strip()
        auth = {"type": "basic", "user": u, "pass": p}
    elif choice == "0":
        auth = None
        print(f"  {NEON_Y}Auth removed.{R}")
    else:
        print(f"  {NEON_R}Invalid choice — cancelled.{R}\n"); return

    _wa_save(url, domain, auth)
    print(f"\n  {NEON_G}✓ Auth saved for {domain}{R}")
    print(dline + "\n")


def cmd_websites() -> None:
    """/fetchsites — list all sites saved in the web agent DB."""
    from tinydb import Query
    db   = _wa_db()
    rows = db.all()
    w    = min(shutil.get_terminal_size((80, 24)).columns, 65)
    dline = f"{NEON_C}{'─'*w}{R}"
    print(f"\n{dline}")
    print(f"{NEON_C}{BOLD}  🌐 Saved Sites ({len(rows)}){R}")
    print(dline)
    if not rows:
        print(f"  {DIM}No sites saved yet. Use /fetch <url> to add one.{R}")
    for r in rows:
        auth_label = r["auth"]["type"] if r.get("auth") else "no auth"
        print(f"  {NEON_Y}•{R} {r['url']}  {DIM}[{auth_label}]{R}")
    print(dline + "\n")


def cmd_webforget(arg: str) -> None:
    """/fetchforget <url> — remove a site from the web agent DB."""
    if not arg:
        print(f"\n{NEON_Y}Usage: /fetchforget <url>{R}\n"); return
    from tinydb import Query
    url = arg.strip()
    if not url.startswith("http"):
        url = "https://" + url
    db  = _wa_db()
    W   = Query()
    removed = db.remove(W.url == url)
    if removed:
        print(f"\n  {NEON_G}✓ Removed: {url}{R}\n")
    else:
        print(f"\n  {NEON_Y}Not found: {url}{R}\n")


def wa_auto_inject(user_input: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """
    Called before every AI query. If the user's message mentions a saved URL
    or its domain, silently fetch a fresh snapshot and prepend it as context.
    Returns the (possibly enriched) prompt to pass to ask().
    """
    try:
        db   = _wa_db()
        rows = db.all()
    except Exception:
        return user_input

    import re as _re
    for r in rows:
        url    = r.get("url", "")
        domain = r.get("domain", "")
        if url in user_input or (domain and domain in user_input):
            auth   = r.get("auth")
            status, content = _wa_fetch(url, auth)
            if status == 200 and content:
                return (
                    f"[WebAgent context — {url}]\n{content[:8000]}\n\n"
                    f"---\nUser: {user_input}"
                )
            elif status in (401, 403):
                return (
                    f"[WebAgent: site {url} requires auth — run /fetchauth {url}]\n\n"
                    f"User: {user_input}"
                )
    return user_input


# ══════════════════════════════════════════════════════════════
#  CORE ASK
# ══════════════════════════════════════════════════════════════
def _stream_one_turn(cfg: dict, messages: list) -> str:
    """Stream a single model turn to stdout, return the full text (or '' on error)."""
    full_response = []; token_count = 0; start = time.time()
    try:
        for token in stream_local(cfg, messages):
            sys.stdout.write(token); sys.stdout.flush()
            full_response.append(token); token_count += 1
    except KeyboardInterrupt:
        print(f"\n{NEON_Y}[interrupted]{R}")
        return "".join(full_response)
    except Exception as e:
        print(f"\n{NEON_R}✗ {e}{R}")
        return ""
    elapsed = time.time() - start
    tok_s   = token_count / elapsed if elapsed > 0 else 0
    print(f"\n\n{DIM}  ⏱ {elapsed:.1f}s · {token_count} tokens · {tok_s:.1f} tok/s{R}\n")
    return "".join(full_response)


def ask(cfg: dict, messages: list, session_msgs: list,
        user_input: str, prefix: str = "") -> str:

    full_input = (prefix + "\n\n" + user_input).strip() if prefix else user_input
    messages.append({"role":"user","content":full_input})
    session_msgs.append({"role":"user","content":full_input})
    manage_context(cfg, messages)   # keep the live prompt inside the model's context window

    mode = MODES.get(cfg.get("mode","chat"), MODES["chat"])
    mc   = mode["color"]
    bw   = min(cols(), 62)
    is_agent_mode = cfg.get("mode") == "agent"
    max_iters     = max(1, int(cfg.get("max_agent_iters", 12)))

    print(f"\n{mc}{'▓'*bw}{R}")
    print(f"{mc}{BOLD}  {mode['icon']} {mode['label']}{R}")
    print(f"{mc}{'▓'*bw}{R}\n")

    response = _stream_one_turn(cfg, messages)
    if not response:
        messages.pop(); session_msgs.pop()
        return ""

    messages.append({"role":"assistant","content":response})
    session_msgs.append({"role":"assistant","content":response})

    # ── Real tool-calling loop ─────────────────────────────────
    # Read-only tool results (search_files/grep_files/list_dir/read_file/
    # web_search/rag_search) get fed straight back to the model automatically,
    # up to max_iters times, so the agent can act on what it learned without
    # the user repeating itself. Destructive actions still stop the loop to
    # wait for explicit approval.
    iters = 0
    last_response = response
    recent_actions: list = []  # signatures of recently-run actions — catches stuck loops
    while is_agent_mode and iters < max_iters:
        actions = parse_actions(last_response)
        if not actions:
            break

        # loop detection: if the model issues the exact same action twice in a
        # row, it's almost certainly stuck (e.g. re-running a command that
        # already failed the same way) — nudge it to change approach instead
        # of burning iterations repeating the same mistake.
        sig = tuple((a["type"], tuple(a["parts"])) for a in actions)
        if recent_actions and recent_actions[-1] == sig:
            action_results = ("[SYSTEM] You just issued the exact same action(s) again. "
                "That already ran and its result is above — repeating it won't change the "
                "outcome. Read the previous result carefully and try a genuinely different "
                "approach, or explain to the user what's blocking you.")
        else:
            action_results = process_actions(last_response, cfg)
        recent_actions.append(sig)
        if not action_results:
            break

        messages.append({"role":"user","content":f"[SYSTEM] Tool results:\n{action_results}"})
        session_msgs.append({"role":"user","content":f"[SYSTEM] Tool results:\n{action_results}"})
        manage_context(cfg, messages)

        iters += 1
        print(f"{DIM}  ↻ agent continuing — round {iters}/{max_iters}…{R}\n")

        last_response = _stream_one_turn(cfg, messages)
        if not last_response:
            break
        messages.append({"role":"assistant","content":last_response})
        session_msgs.append({"role":"assistant","content":last_response})
        response = last_response

    if iters >= max_iters:
        print(f"{NEON_Y}  ⚠ Hit max agent rounds ({max_iters}). Ask a follow-up to continue.{R}\n")

    # non-agent modes (or the final agent round) still get one pass of
    # process_actions so a stray ACTION block doesn't just get ignored.
    if not is_agent_mode:
        action_results = process_actions(response, cfg)
        if action_results:
            messages.append({"role":"user","content":f"[SYSTEM] Results:\n{action_results}"})

    save_history(cfg["history_file"], session_msgs, cfg["max_history"])
    return response


def cmd_context_status(cfg: dict, messages: list) -> None:
    """Show how much of the model's context window the live conversation
    is using — an early warning before /auto-trim (or a hard crash) kicks in."""
    budget = cfg.get("context", 4096)
    used   = _messages_token_estimate(messages)
    pct    = min(100, int(used / budget * 100)) if budget else 0
    bar_len = 30
    filled  = int(bar_len * pct / 100)
    bar     = "█" * filled + "░" * (bar_len - filled)
    color   = NEON_G if pct < 60 else (NEON_Y if pct < 85 else NEON_R)
    print(f"\n{color}{bar}{R}  {pct}%")
    print(f"{DIM}  ~{used:,} / {budget:,} tokens (estimate) · {len(messages)} messages "
          f"in active context{R}")
    if not cfg.get("auto_trim_context", True):
        print(f"{NEON_Y}  ⚠ auto_trim_context is off in your config — long sessions can "
              f"still hit a hard context-window error.{R}")
    print()


def cmd_regenerate(cfg: dict, messages: list, session_msgs: list) -> str:
    """Redo the last AI reply — pops the previous assistant turn and re-asks
    with the same conversation state, for when the answer wasn't quite right."""
    if len(messages) < 2 or messages[-1]["role"] != "assistant":
        print(f"\n{NEON_Y}Nothing to regenerate yet — ask something first.{R}\n")
        return ""
    messages.pop()
    if session_msgs and session_msgs[-1]["role"] == "assistant":
        session_msgs.pop()
    print(f"{DIM}  ↻ Regenerating last response…{R}")
    response = _stream_one_turn(cfg, messages)
    if response:
        messages.append({"role":"assistant","content":response})
        session_msgs.append({"role":"assistant","content":response})
        save_history(cfg["history_file"], session_msgs, cfg["max_history"])
    return response


def cmd_model_switch(arg: str, cfg: dict) -> None:
    """List or hot-swap the loaded chat model — no restart required. This is
    the single biggest ease-of-use gap next to tools like Ollama, where
    switching models is a one-liner instead of relaunching the whole app."""
    global _llm_instance
    models_dir = os.path.expanduser("~/ollama-models")
    found = []
    if os.path.isdir(models_dir):
        for f in sorted(os.listdir(models_dir)):
            if f.lower().endswith(".gguf"):
                found.append(os.path.join(models_dir, f))

    if not arg:
        current = cfg.get("model_path", "")
        print(f"\n{NEON_C}Models in ~/ollama-models:{R}")
        if not found:
            print(f"{DIM}  (none found — run --setup or /models to download one){R}")
        for i, path in enumerate(found, 1):
            marker  = f" {NEON_G}← active{R}" if os.path.abspath(path) == os.path.abspath(current) else ""
            size_gb = os.path.getsize(path) / 1e9
            print(f"  {NEON_Y}{i}{R}  {os.path.basename(path)}  {DIM}({size_gb:.1f}GB){R}{marker}")
        print(f"\n{DIM}Switch with: /model <number>, /model <name>, or /model <path>{R}\n")
        return

    target = None
    if arg.strip().isdigit():
        idx = int(arg.strip()) - 1
        if 0 <= idx < len(found):
            target = found[idx]
    else:
        candidate = os.path.expanduser(arg.strip())
        if os.path.isfile(candidate):
            target = candidate
        else:
            for path in found:
                if arg.strip().lower() in os.path.basename(path).lower():
                    target = path
                    break

    if not target:
        print(f"\n{NEON_R}✗ Model not found. Run /model with no argument to see what's available.{R}\n")
        return

    print(f"\n{NEON_C}Switching to {os.path.basename(target)}…{R}")
    cfg["model_path"] = target
    save_cfg(cfg)
    _llm_instance = None  # drop the old loaded model so get_llm() reloads fresh
    get_llm(cfg)


def cmd_compact(cfg: dict, messages: list) -> None:
    """AI-summarize older conversation turns into a single compact summary,
    freeing up context budget while preserving what actually matters —
    smarter than the automatic /context trim, which just drops history.
    Only affects the live prompt (`messages`); the full saved session
    transcript is untouched."""
    system_msgs = [m for m in messages if m["role"] == "system"]
    convo       = [m for m in messages if m["role"] != "system"]

    if len(convo) <= 4:
        print(f"\n{NEON_Y}Not enough history yet to compact.{R}\n")
        return

    keep_tail    = convo[-2:]           # leave the most recent exchange intact
    to_summarize = convo[:-2]
    transcript   = "\n\n".join(f"{m['role'].upper()}: {m['content']}" for m in to_summarize)[:12000]

    print(f"\n{DIM}  ⚙ Compacting {len(to_summarize)} older message(s) into a summary…{R}\n")
    summary_prompt = [
        {"role": "system", "content": (
            "Summarize the following conversation concisely, preserving any decisions, "
            "facts, file paths, code snippets, or commitments made. Write it as a compact "
            "briefing for someone continuing the conversation, not a transcript.")},
        {"role": "user", "content": transcript},
    ]
    summary = _stream_one_turn(cfg, summary_prompt)
    if not summary:
        print(f"{NEON_R}✗ Compaction failed — history left unchanged.{R}\n")
        return

    before = _messages_token_estimate(convo)
    compacted = system_msgs + [{"role": "user",
        "content": f"[Conversation summary so far]\n{summary}"}] + keep_tail
    messages[:] = compacted
    after = _messages_token_estimate(compacted)
    print(f"\n{NEON_G}✓ Compacted: ~{before:,} → ~{after:,} tokens in active context.{R}\n")


def cmd_export(arg: str, session_msgs: list) -> None:
    """Export the full conversation transcript to a Markdown or HTML file
    in the current directory."""
    if not session_msgs:
        print(f"\n{NEON_Y}Nothing to export yet.{R}\n")
        return
    fmt   = "html" if arg.strip().lower() == "html" else "md"
    ts    = time.strftime("%Y%m%d_%H%M%S")
    dest  = os.path.join(os.getcwd(), f"cybersh_export_{ts}.{fmt}")

    try:
        if fmt == "md":
            parts = [f"# CyberSH conversation — {time.strftime('%Y-%m-%d %H:%M')}\n"]
            for m in session_msgs:
                if m["role"] == "system":
                    continue
                who = "You" if m["role"] == "user" else "AI"
                parts.append(f"**{who}:**\n\n{m['content']}\n")
            content = "\n---\n\n".join(parts)
        else:
            import html as _html
            rows = []
            for m in session_msgs:
                if m["role"] == "system":
                    continue
                who = "You" if m["role"] == "user" else "AI"
                rows.append(f"<div class='msg {m['role']}'><b>{who}:</b>"
                            f"<pre>{_html.escape(m['content'])}</pre></div>")
            content = (
                "<html><head><meta charset='utf-8'><title>CyberSH export</title>"
                "<style>body{font-family:sans-serif;background:#0d0d0d;color:#ddd;padding:2em}"
                ".msg{margin-bottom:1.5em;padding:1em;border-radius:8px;background:#1a1a1a}"
                ".user{border-left:4px solid #00e5ff}.assistant{border-left:4px solid #39ff14}"
                "pre{white-space:pre-wrap;word-wrap:break-word}</style></head><body>"
                f"<h1>CyberSH conversation — {time.strftime('%Y-%m-%d %H:%M')}</h1>"
                + "".join(rows) + "</body></html>"
            )
        with open(dest, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\n{NEON_G}✓ Exported {len([m for m in session_msgs if m['role']!='system'])} "
              f"messages → {dest}{R}\n")
    except Exception as e:
        print(f"\n{NEON_R}✗ Export failed: {e}{R}\n")


# ══════════════════════════════════════════════════════════════
#  GUI — local browser-based interface (stdlib only, no extra deps)
# ══════════════════════════════════════════════════════════════
GUI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CYBER SH DIRECT</title>
<style>
  :root {
    --bg: #0a0a0f; --panel: #11121a; --panel2: #171826; --border: #232336;
    --text: #e6e6f0; --dim: #7a7a94;
    --green: #39ff14; --cyan: #00e5ff; --purple: #b026ff; --yellow: #ffe066; --red: #ff3860;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; height: 100vh; display: flex; background: var(--bg); color: var(--text);
    font-family: 'SF Mono', 'Fira Code', Consolas, monospace; overflow: hidden;
  }
  #sidebar {
    width: 260px; background: var(--panel); border-right: 1px solid var(--border);
    display: flex; flex-direction: column; padding: 16px; gap: 18px; flex-shrink: 0;
  }
  .brand { font-weight: 700; font-size: 15px; letter-spacing: 1px; }
  .brand span { color: var(--green); text-shadow: 0 0 8px var(--green); }
  .ver { color: var(--dim); font-size: 11px; }
  .section-label { color: var(--dim); font-size: 10px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
  .mode-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
  .mode-btn {
    background: var(--panel2); border: 1px solid var(--border); color: var(--text);
    padding: 8px 6px; border-radius: 6px; cursor: pointer; font-size: 12px; text-align: center;
    transition: all .15s;
  }
  .mode-btn:hover { border-color: var(--cyan); }
  .mode-btn.active { border-color: var(--green); color: var(--green); box-shadow: 0 0 10px rgba(57,255,20,.25); }
  select, .ctrl-btn {
    width: 100%; background: var(--panel2); border: 1px solid var(--border); color: var(--text);
    padding: 8px; border-radius: 6px; font-family: inherit; font-size: 12px; cursor: pointer;
  }
  .ctrl-btn:hover { border-color: var(--cyan); color: var(--cyan); }
  .ctrl-row { display: flex; gap: 6px; }
  .ctrl-row .ctrl-btn { flex: 1; }
  #ctxwrap { margin-top: auto; }
  #ctxbar-outer { width: 100%; height: 6px; background: var(--panel2); border-radius: 4px; overflow: hidden; }
  #ctxbar-inner { height: 100%; width: 0%; background: var(--green); transition: width .3s; }
  #ctxlabel { color: var(--dim); font-size: 11px; margin-top: 4px; }
  #main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
  #chat { flex: 1; overflow-y: auto; padding: 24px 12%; display: flex; flex-direction: column; gap: 16px; }
  .msg { max-width: 100%; padding: 12px 16px; border-radius: 10px; line-height: 1.55; font-size: 14px; white-space: pre-wrap; word-wrap: break-word; }
  .msg.user { align-self: flex-end; background: rgba(0,229,255,.08); border: 1px solid rgba(0,229,255,.3); }
  .msg.assistant { align-self: flex-start; background: var(--panel2); border: 1px solid var(--border); }
  .msg .role { display: block; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
  .msg.user .role { color: var(--cyan); }
  .msg.assistant .role { color: var(--green); }
  .msg code, .msg pre { font-family: 'SF Mono', Consolas, monospace; }
  .msg pre { background: #05050a; border: 1px solid var(--border); padding: 10px; border-radius: 6px; overflow-x: auto; margin: 8px 0; }
  #inputbar { padding: 16px 12%; border-top: 1px solid var(--border); background: var(--panel); }
  #inputrow { display: flex; gap: 10px; }
  #msginput {
    flex: 1; background: var(--panel2); border: 1px solid var(--border); color: var(--text);
    padding: 12px 14px; border-radius: 8px; font-family: inherit; font-size: 14px; resize: none; max-height: 160px;
  }
  #msginput:focus { outline: none; border-color: var(--green); }
  #sendbtn {
    background: var(--green); color: #04140a; border: none; padding: 0 22px; border-radius: 8px;
    cursor: pointer; font-weight: 700; font-size: 13px;
  }
  #sendbtn:hover { filter: brightness(1.1); }
  #sendbtn:disabled { background: var(--dim); cursor: default; }
  .hint { color: var(--dim); font-size: 11px; margin-top: 6px; }
  ::-webkit-scrollbar { width: 8px; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
</style>
</head>
<body>

<div id="sidebar">
  <div>
    <div class="brand">CYBER <span>SH</span> DIRECT</div>
    <div class="ver" id="verlabel">v__VERSION__ · GUI</div>
  </div>

  <div>
    <div class="section-label">Mode</div>
    <div class="mode-grid" id="modegrid"></div>
  </div>

  <div>
    <div class="section-label">Model</div>
    <select id="modelselect"></select>
  </div>

  <div>
    <div class="section-label">Session</div>
    <div class="ctrl-row">
      <button class="ctrl-btn" id="btn-regen">↻ Regen</button>
      <button class="ctrl-btn" id="btn-compact">🗜 Compact</button>
    </div>
    <div class="ctrl-row" style="margin-top:6px">
      <button class="ctrl-btn" id="btn-export">📤 Export</button>
      <button class="ctrl-btn" id="btn-clear">🗑 Clear</button>
    </div>
  </div>

  <div id="ctxwrap">
    <div class="section-label">Context window</div>
    <div id="ctxbar-outer"><div id="ctxbar-inner"></div></div>
    <div id="ctxlabel">0%</div>
  </div>
</div>

<div id="main">
  <div id="chat"></div>
  <div id="inputbar">
    <div id="inputrow">
      <textarea id="msginput" rows="1" placeholder="Ask anything… (Enter to send, Shift+Enter for newline)"></textarea>
      <button id="sendbtn">Send</button>
    </div>
    <div class="hint">Agent mode with tool execution + approval prompts is only available in the terminal (run without --gui, use /agent).</div>
  </div>
</div>

<script>
const MODES = ["chat","sec","code","vibe"];
const MODE_ICON = {chat:"💬 Chat", sec:"🔐 Sec", code:"⚡ Code", vibe:"🎨 Vibe"};
let currentMode = "chat";
let sending = false;

const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("msginput");
const sendBtn = document.getElementById("sendbtn");
const modeGrid = document.getElementById("modegrid");
const modelSelect = document.getElementById("modelselect");

function escapeHtml(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}
function renderContent(text) {
  // lightweight fenced-code-block rendering, everything else stays plain text
  const parts = text.split(/```/);
  let html = "";
  parts.forEach((part, i) => {
    if (i % 2 === 1) {
      const lines = part.split("\\n");
      const body = lines.slice(lines[0].trim() && !lines[0].includes(" ") ? 1 : 0).join("\\n") || part;
      html += "<pre>" + escapeHtml(body) + "</pre>";
    } else {
      html += escapeHtml(part);
    }
  });
  return html;
}

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.innerHTML = "<span class='role'>" + (role === "user" ? "You" : "AI") + "</span>" + renderContent(text);
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
  return div;
}

function buildModeGrid() {
  modeGrid.innerHTML = "";
  MODES.forEach(m => {
    const btn = document.createElement("div");
    btn.className = "mode-btn" + (m === currentMode ? " active" : "");
    btn.textContent = MODE_ICON[m];
    btn.onclick = () => setMode(m);
    modeGrid.appendChild(btn);
  });
}

async function setMode(m) {
  currentMode = m;
  buildModeGrid();
  await fetch("/api/mode", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({mode:m})});
  chatEl.innerHTML = "";
  refreshStatus();
}

async function refreshStatus() {
  const r = await fetch("/api/status");
  const s = await r.json();
  document.getElementById("verlabel").textContent = "v" + s.version + " · GUI";
  document.getElementById("ctxbar-inner").style.width = s.context_pct + "%";
  document.getElementById("ctxbar-inner").style.background =
    s.context_pct < 60 ? "var(--green)" : (s.context_pct < 85 ? "var(--yellow)" : "var(--red)");
  document.getElementById("ctxlabel").textContent =
    s.context_pct + "% · ~" + s.context_used.toLocaleString() + " / " + s.context_budget.toLocaleString() + " tok";
}

async function refreshModels() {
  const r = await fetch("/api/models");
  const d = await r.json();
  modelSelect.innerHTML = "";
  if (!d.models.length) {
    const opt = document.createElement("option");
    opt.textContent = "No models found in ~/ollama-models";
    modelSelect.appendChild(opt);
    return;
  }
  d.models.forEach(m => {
    const opt = document.createElement("option");
    opt.value = m; opt.textContent = m;
    if (m === d.active) opt.selected = true;
    modelSelect.appendChild(opt);
  });
}

modelSelect.onchange = async () => {
  await fetch("/api/model", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({target: modelSelect.value})});
  refreshStatus();
};

async function streamRequest(path, body) {
  sending = true; sendBtn.disabled = true; sendBtn.textContent = "…";
  const aiDiv = addMessage("assistant", "");
  const resp = await fetch(path, {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(body || {})});
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let full = "";
  while (true) {
    const {done, value} = await reader.read();
    if (done) break;
    full += decoder.decode(value, {stream:true});
    aiDiv.innerHTML = "<span class='role'>AI</span>" + renderContent(full);
    chatEl.scrollTop = chatEl.scrollHeight;
  }
  sending = false; sendBtn.disabled = false; sendBtn.textContent = "Send";
  refreshStatus();
}

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text || sending) return;
  inputEl.value = ""; inputEl.style.height = "auto";
  addMessage("user", text);
  await streamRequest("/api/chat", {message: text});
}

sendBtn.onclick = sendMessage;
inputEl.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});
inputEl.addEventListener("input", () => {
  inputEl.style.height = "auto";
  inputEl.style.height = Math.min(inputEl.scrollHeight, 160) + "px";
});

document.getElementById("btn-regen").onclick = async () => {
  if (sending) return;
  await streamRequest("/api/regen", {});
};
document.getElementById("btn-compact").onclick = async () => {
  await fetch("/api/compact", {method:"POST"});
  refreshStatus();
  addMessage("assistant", "[history compacted — older messages summarized]");
};
document.getElementById("btn-clear").onclick = async () => {
  await fetch("/api/clear", {method:"POST"});
  chatEl.innerHTML = "";
  refreshStatus();
};
document.getElementById("btn-export").onclick = async () => {
  const r = await fetch("/api/export", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({format:"md"})});
  const d = await r.json();
  addMessage("assistant", "[exported to " + (d.path || "file") + "]");
};

buildModeGrid();
refreshStatus();
refreshModels();
inputEl.focus();
</script>
</body>
</html>
"""

_GUI_STATE = {}
_GUI_LOCK  = threading.Lock()

def _gui_reset_messages(cfg: dict, clear_session: bool = False) -> None:
    mode = MODES.get(cfg.get("mode", "chat"), MODES["chat"])
    _GUI_STATE["messages"] = [{"role": "system", "content": mode["system"] + "\n\n" + get_env_context()}]
    if clear_session:
        _GUI_STATE["session_msgs"] = []

def _gui_status() -> dict:
    cfg, messages = _GUI_STATE["cfg"], _GUI_STATE["messages"]
    budget = cfg.get("context", 4096)
    used   = _messages_token_estimate(messages)
    pct    = min(100, int(used / budget * 100)) if budget else 0
    return {
        "version": APP_VERSION, "mode": cfg.get("mode", "chat"),
        "model": os.path.basename(cfg.get("model_path", "")),
        "context_pct": pct, "context_used": used, "context_budget": budget,
    }

def _gui_list_models() -> dict:
    models_dir = os.path.expanduser("~/ollama-models")
    found = []
    if os.path.isdir(models_dir):
        found = sorted(f for f in os.listdir(models_dir) if f.lower().endswith(".gguf"))
    return {"models": found, "active": os.path.basename(_GUI_STATE["cfg"].get("model_path", ""))}

def _send_chunk(wfile, text: str) -> None:
    data = text.encode("utf-8")
    wfile.write(f"{len(data):X}\r\n".encode())
    wfile.write(data)
    wfile.write(b"\r\n")
    wfile.flush()

def _end_chunks(wfile) -> None:
    wfile.write(b"0\r\n\r\n")
    wfile.flush()

class _GUIHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass  # keep the terminal clean — GUI has its own status area

    def _json(self, obj: dict, status: int = 200) -> None:
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", ""):
            body = GUI_HTML.replace("__VERSION__", APP_VERSION).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/status":
            self._json(_gui_status())
        elif self.path == "/api/models":
            self._json(_gui_list_models())
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        length  = int(self.headers.get("Content-Length", 0) or 0)
        raw     = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw or b"{}")
        except Exception:
            payload = {}

        cfg = _GUI_STATE["cfg"]

        if self.path == "/api/chat":
            self._stream_chat(payload.get("message", ""))
        elif self.path == "/api/regen":
            self._stream_chat(None, regen=True)
        elif self.path == "/api/mode":
            if payload.get("mode") in MODES:
                cfg["mode"] = payload["mode"]
                _gui_reset_messages(cfg)
            self._json({"ok": True})
        elif self.path == "/api/model":
            cmd_model_switch(payload.get("target", ""), cfg)
            self._json({"ok": True})
        elif self.path == "/api/compact":
            with _GUI_LOCK:
                cmd_compact(cfg, _GUI_STATE["messages"])
            self._json({"ok": True})
        elif self.path == "/api/clear":
            with _GUI_LOCK:
                _gui_reset_messages(cfg, clear_session=True)
            self._json({"ok": True})
        elif self.path == "/api/export":
            with _GUI_LOCK:
                dest = _gui_export(payload.get("format", "md"))
            self._json({"ok": True, "path": dest})
        else:
            self._json({"error": "not found"}, 404)

    def _stream_chat(self, user_text, regen: bool = False) -> None:
        cfg, messages, session_msgs = _GUI_STATE["cfg"], _GUI_STATE["messages"], _GUI_STATE["session_msgs"]
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

        with _GUI_LOCK:
            if regen:
                if len(messages) < 2 or messages[-1]["role"] != "assistant":
                    _send_chunk(self.wfile, "[nothing to regenerate yet]")
                    _end_chunks(self.wfile)
                    return
                messages.pop()
                if session_msgs and session_msgs[-1]["role"] == "assistant":
                    session_msgs.pop()
            else:
                messages.append({"role": "user", "content": user_text})
                session_msgs.append({"role": "user", "content": user_text})
            manage_context(cfg, messages)

            full = []
            try:
                for token in stream_local(cfg, messages):
                    full.append(token)
                    _send_chunk(self.wfile, token)
            except Exception as e:
                _send_chunk(self.wfile, f"\n[error: {e}]")
            response = "".join(full)
            if response:
                messages.append({"role": "assistant", "content": response})
                session_msgs.append({"role": "assistant", "content": response})
                save_history(cfg["history_file"], session_msgs, cfg["max_history"])
        _end_chunks(self.wfile)

def _gui_export(fmt: str) -> str:
    """Same export logic as /export in the terminal, callable from the GUI."""
    session_msgs = _GUI_STATE["session_msgs"]
    if not session_msgs:
        return ""
    fmt  = "html" if fmt.lower() == "html" else "md"
    ts   = time.strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(os.getcwd(), f"cybersh_export_{ts}.{fmt}")
    if fmt == "md":
        parts = [f"# CyberSH conversation — {time.strftime('%Y-%m-%d %H:%M')}\n"]
        for m in session_msgs:
            if m["role"] == "system": continue
            who = "You" if m["role"] == "user" else "AI"
            parts.append(f"**{who}:**\n\n{m['content']}\n")
        content = "\n---\n\n".join(parts)
    else:
        import html as _html
        rows = []
        for m in session_msgs:
            if m["role"] == "system": continue
            who = "You" if m["role"] == "user" else "AI"
            rows.append(f"<div class='msg {m['role']}'><b>{who}:</b><pre>{_html.escape(m['content'])}</pre></div>")
        content = ("<html><head><meta charset='utf-8'></head><body>"
                   f"<h1>CyberSH conversation</h1>" + "".join(rows) + "</body></html>")
    with open(dest, "w", encoding="utf-8") as f:
        f.write(content)
    return dest

def launch_gui(cfg: dict, port: int = 8420) -> None:
    """Serve a browser-based GUI for cybersh — same local model, same
    context management, no cloud, no extra dependencies (stdlib http.server
    only). Chat/Sec/Code/Vibe modes are supported; Agent mode's tool
    execution + approval flow is terminal-only by design, since it needs a
    real confirm prompt before running destructive actions."""
    import webbrowser

    get_llm(cfg)  # load the model up front so the first chat isn't slow
    mode = MODES.get(cfg.get("mode", "chat"), MODES["chat"])
    _GUI_STATE["cfg"]          = cfg
    _GUI_STATE["messages"]     = [{"role": "system", "content": mode["system"] + "\n\n" + get_env_context()}]
    _GUI_STATE["session_msgs"] = []

    class _Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True

    url = f"http://127.0.0.1:{port}"
    try:
        httpd = _Server(("127.0.0.1", port), _GUIHandler)
    except OSError as e:
        print(f"\n{NEON_R}✗ Could not start GUI on port {port}: {e}{R}")
        print(f"{NEON_Y}Try a different port: --gui --port 8421{R}\n")
        return

    print(f"\n{NEON_G}✓ GUI running at {NEON_C}{url}{R}")
    print(f"{DIM}  Ctrl+C to stop.{R}\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{NEON_Y}Shutting down GUI…{R}")
        httpd.shutdown()


# ══════════════════════════════════════════════════════════════
#  REPL
# ══════════════════════════════════════════════════════════════
def repl(cfg: dict, one_shot: str | None = None) -> None:
    try: import readline
    except: pass

    if not one_shot:
        startup_selector(cfg)
        show_tip()
        print_banner(cfg)

    mem          = load_memory()
    load_plugins(cfg, verbose=not one_shot)
    mode         = MODES.get(cfg.get("mode","chat"), MODES["chat"])
    messages     = [{"role":"system","content":""}]   # placeholder, filled below
    session_msgs : list = []
    last_response = ""

    def _build_sys() -> str:
        """Build the full system prompt: persona + mode + memory + environment."""
        m    = MODES.get(cfg.get("mode","chat"), MODES["chat"])
        base = m["system"]
        # inject OS/environment awareness
        base += f"\n\n{get_env_context()}"
        # inject memory
        ctx = memory_context(mem)
        if ctx:
            base += f"\n\n{ctx}"
        # persona overrides the personality part but keeps mode instructions
        persona = cfg.get("persona","default")
        if persona and persona != "default" and persona in PERSONALITIES:
            base = PERSONALITIES[persona] + "\n\nAdditionally: " + base
        return base

    def rebuild_system() -> None:
        messages[0]["content"] = _build_sys()

    def switch_mode(new_mode: str) -> None:
        nonlocal messages
        cfg["mode"] = new_mode
        m = MODES[new_mode]
        new_msgs = [{"role":"system","content":_build_sys()}]
        messages.clear()
        messages.extend(new_msgs)
        session_msgs.clear()
        bw = min(cols(), 62)
        print(f"\n{m['color']}{BOLD}{'▓'*bw}\n  {m['icon']}  MODE → {m['label']}\n{'▓'*bw}{R}\n")

    # initialise system prompt now that helpers exist
    rebuild_system()

    if one_shot:
        ask(cfg, messages, session_msgs, one_shot)
        return

    while True:
        mode = MODES.get(cfg.get("mode","chat"), MODES["chat"])
        cwd  = os.path.basename(os.getcwd()) or "~"
        try:
            user_input = rich_prompt(mode["color"], mode["icon"], cwd)
        except KeyboardInterrupt:
            print(f"\n{DIM}Stay safe out there.{R}\n"); break

        if not user_input: continue

        if not user_input.startswith("/"):
            enriched = wa_auto_inject(user_input, cfg, messages, session_msgs)
            last_response = ask(cfg, messages, session_msgs, enriched)
            continue

        parts = user_input.split(maxsplit=1)
        cmd   = parts[0].lower()
        arg   = parts[1].strip() if len(parts) > 1 else ""

        if cmd in ("/vibe","/sec","/code","/chat","/agent"):
            switch_mode(cmd[1:])
        elif cmd == "/remember":
            cmd_remember(arg, mem)
            rebuild_system()
        elif cmd in ("/memories", "/memory"):
            cmd_memories(mem)
        elif cmd == "/forget":
            cmd_forget(arg, mem)
            rebuild_system()
        elif cmd == "/persona":
            cmd_persona(arg, cfg)
            rebuild_system()
        elif cmd == "/summarize":
            last_response = cmd_summarize_url(arg, cfg, messages, session_msgs)
        elif cmd == "/calc":
            cmd_calc(arg)
        elif cmd in ("/goals", "/goal"):
            parts2 = arg.split(maxsplit=1)
            action = parts2[0] if parts2 else ""
            arg2   = parts2[1] if len(parts2) > 1 else ""
            if action not in ("done","check","clear","reset","add"):
                cmd_goals("add", arg) if arg else cmd_goals("", "")
            else:
                cmd_goals(action, arg2)
        elif cmd in ("/exit","/quit","/q"):
            print(f"\n{DIM}Stay safe out there.{R}\n"); break
        elif cmd == "/help":     print_help(arg)
        elif cmd == "/save":     save_cfg(cfg)
        elif cmd == "/clear":
            mode = MODES.get(cfg.get("mode","chat"),MODES["chat"])
            messages[:] = [{"role":"system","content":mode["system"]}]
            session_msgs.clear()
            print(f"{NEON_G}✓ Memory wiped.{R}\n")
        elif cmd == "/history":
            for m in messages:
                if m["role"]=="system": continue
                col = NEON_Y if m["role"]=="user" else NEON_G
                lbl = "YOU" if m["role"]=="user" else " AI"
                print(f"  {col}{BOLD}[{lbl}]{R} {textwrap.shorten(m['content'],70)}")
            print()
        elif cmd == "/temp":
            try: cfg["temperature"] = float(arg); print(f"{NEON_G}✓ Temp → {arg}{R}\n")
            except: print(f"{NEON_Y}Usage: /temp <0.0-2.0>{R}\n")
        elif cmd == "/context":
            cmd_context_status(cfg, messages)
        elif cmd == "/regen":
            last_response = cmd_regenerate(cfg, messages, session_msgs)
        elif cmd == "/model":
            cmd_model_switch(arg, cfg)
        elif cmd == "/compact":
            cmd_compact(cfg, messages)
        elif cmd == "/export":
            cmd_export(arg, session_msgs)
        elif cmd == "/undo":
            cmd_undo()
        elif cmd == "/info":
            mp = cfg.get("model_path","none")
            sz = f"{os.path.getsize(mp)/1e9:.1f} GB" if os.path.exists(mp) else "?"
            print(f"\n  {NEON_C}Model:{R}  {os.path.basename(mp)}")
            print(f"  {NEON_C}Size:{R}   {sz}")
            print(f"  {NEON_C}Ctx:{R}    {cfg['context']}")
            print(f"  {NEON_C}Temp:{R}   {cfg['temperature']}")
            print(f"  {NEON_C}Threads:{R}{cfg.get('threads',4)}\n")
        elif cmd == "/f":
            if not arg: print(f"{NEON_Y}Usage: /f <path>{R}\n")
            else:
                try:
                    path = os.path.expanduser(arg)
                    with open(path,"r",errors="replace") as f: content = f.read(50000)
                    ext    = os.path.splitext(arg)[1][1:] or ""
                    prefix = f"[FILE: {arg}]\n```{ext}\n{content}\n```"
                    print(f"{NEON_G}✓ Loaded {arg} ({len(content)} chars){R}")
                    sys.stdout.write(f"{NEON_C}What to do with it? ▶ {R}")
                    follow = input().strip()
                    if follow:
                        last_response = ask(cfg, messages, session_msgs, follow, prefix=prefix)
                except Exception as e: print(f"{NEON_R}✗ {e}{R}\n")
        elif cmd == "/o":
            if not arg: print(f"{NEON_Y}Usage: /o <path>{R}\n")
            elif not last_response: print(f"{NEON_Y}⚠ Nothing to save.{R}\n")
            else:
                try:
                    with open(os.path.expanduser(arg),"w") as f: f.write(last_response)
                    print(f"{NEON_G}✓ Saved → {arg}{R}\n")
                except Exception as e: print(f"{NEON_R}✗ {e}{R}\n")
        elif cmd == "/run":
            matches = re.findall(r"```(?:\w+)?\n(.*?)```", last_response, re.DOTALL)
            code    = matches[-1].strip() if matches else ""
            if not code: print(f"{NEON_Y}⚠ No code block found.{R}\n")
            else:
                print(f"{NEON_Y}Run:{R}\n{DIM}{code[:200]}{R}")
                if input(f"{NEON_R}Execute? [y/N]: {R}").strip().lower() == "y":
                    r = subprocess.run(["bash","-c",code], capture_output=True, text=True)
                    if r.stdout: print(f"{NEON_G}{r.stdout}{R}")
                    if r.stderr: print(f"{NEON_R}{r.stderr}{R}")
        elif cmd == "/copy":
            if not last_response: print(f"{NEON_Y}⚠ Nothing to copy yet — ask something first.{R}\n")
            else:
                copy_to_clipboard(last_response)
        elif cmd == "/recon":
            if not arg: print(f"{NEON_Y}Usage: /recon <target>{R}\n")
            else:
                switch_mode("sec")
                last_response = ask(cfg, messages, session_msgs,
                    f"Full bug bounty recon plan for: {arg}. "
                    f"Cover subdomain enum, ports, tech fingerprinting, wayback, "
                    f"dir fuzzing, API discovery, vuln areas. Real commands only.")
        elif cmd == "/payload":
            switch_mode("sec")
            last_response = ask(cfg, messages, session_msgs,
                f"Generate comprehensive {(arg or 'xss').upper()} payloads for bug bounty: "
                f"basic, encoded, bypass, polyglots. Ready-to-use list.")
        elif cmd == "/explain":
            if not arg: print(f"{NEON_Y}Usage: /explain <cmd>{R}\n")
            else:
                last_response = ask(cfg, messages, session_msgs,
                    f"Explain this command step by step, all flags, security implications:\n`{arg}`")
        elif cmd == "/web":
            if not arg: print(f"{NEON_Y}Usage: /web <query>{R}\n")
            else:
                print(f"\n{NEON_C}🌐 Searching: {arg}…{R}\n")
                results = web_search(arg)
                print(f"{DIM}{results[:600]}…{R}\n")
                sys.stdout.write(f"{NEON_C}Ask AI about results? (Enter to skip): {R}")
                follow = input().strip()
                if follow:
                    last_response = ask(cfg, messages, session_msgs,
                        follow, prefix=f"[WEB SEARCH: {arg}]\n{results}")
                else:
                    last_response = ask(cfg, messages, session_msgs,
                        f"Summarize these search results about '{arg}':\n{results}")
        elif cmd == "/cvesearch":
            if not arg: print(f"{NEON_Y}Usage: /cvesearch <CVE-ID or software>{R}\n")
            else:
                print(f"\n{NEON_C}🔍 Searching CVE info for: {arg}…{R}\n")
                results = web_search(f"{arg} CVE vulnerability exploit POC", max_results=4)
                switch_mode("sec")
                last_response = ask(cfg, messages, session_msgs,
                    f"Analyze this CVE/vulnerability for bug bounty and pentesting:\n{results}\n\n"
                    f"Cover: severity, affected versions, exploit method, detection, mitigation.")
        elif cmd == "/tldr":
            last_response = cmd_tldr(arg, cfg, messages, session_msgs)
        elif cmd == "/howto":
            last_response = cmd_howto(arg, cfg, messages, session_msgs)
        elif cmd == "/fix":
            last_response = cmd_fix(arg, cfg, messages, session_msgs)
        elif cmd == "/passgen":
            cmd_passgen(arg)
        elif cmd == "/encode":
            cmd_encode(arg)
        elif cmd == "/syswatch":
            cmd_syswatch()
        elif cmd == "/benchmark":
            cmd_benchmark()
        elif cmd in ("/note", "/notes"):
            parts2 = arg.split(maxsplit=1)
            action = parts2[0] if parts2 else ""
            arg2   = parts2[1] if len(parts2) > 1 else ""
            # if action is not a subcommand keyword treat whole arg as note text
            if action not in ("list","show","ls","clear","wipe","del","delete","rm"):
                cmd_notes(arg, "")
            else:
                cmd_notes(action, arg2)
        elif cmd == "/tip":
            show_tip()
        elif cmd == "/session":
            parts2 = arg.split(maxsplit=1)
            s_action = parts2[0] if parts2 else "list"
            s_arg    = parts2[1] if len(parts2) > 1 else ""
            cmd_session(s_action, s_arg, messages, session_msgs, cfg)
        # ── everyday tools ───────────────────────────────────
        elif cmd == "/convert":
            cmd_convert(arg)
        elif cmd == "/qr":
            cmd_qr(arg)
        elif cmd == "/speedtest":
            cmd_speedtest()
        elif cmd == "/pwcheck":
            last_response = cmd_pwcheck(arg, cfg, messages, session_msgs)
        elif cmd == "/uuid":
            cmd_uuid(arg)
        elif cmd == "/json":
            cmd_json(arg)
        elif cmd == "/base":
            cmd_base(arg)
        elif cmd == "/color":
            cmd_color(arg)
        elif cmd == "/slugify":
            cmd_slugify(arg)
        elif cmd == "/lorem":
            cmd_lorem(arg)
        elif cmd == "/countdown":
            cmd_countdown(arg)
        elif cmd == "/ip":
            cmd_ipinfo(arg)
        elif cmd == "/clock":
            cmd_clock(arg)
        elif cmd == "/gist":
            cmd_gist(arg)
        elif cmd == "/image":
            cmd_image(arg)
        elif cmd == "/fetch":
            last_response = cmd_web(arg, cfg, messages, session_msgs)
        elif cmd == "/fetchauth":
            cmd_webauth(arg)
        elif cmd == "/fetchsites":
            cmd_websites()
        elif cmd == "/fetchforget":
            cmd_webforget(arg)
        elif cmd == "/see":
            cmd_vision(arg, cfg)
        elif cmd == "/rag":
            parts2  = arg.split(maxsplit=1)
            raction = parts2[0] if parts2 else ""
            rarg    = parts2[1] if len(parts2) > 1 else ""
            last_response = cmd_rag(raction, rarg, cfg, messages, session_msgs)
        # ── developer tools ──────────────────────────────────
        elif cmd == "/debug":
            last_response = cmd_debug(arg, cfg, messages, session_msgs)
        elif cmd == "/review":
            last_response = cmd_review(arg, cfg, messages, session_msgs)
        elif cmd == "/template":
            last_response = cmd_template(arg, cfg, messages, session_msgs)
        elif cmd == "/gitlog":
            last_response = cmd_gitlog(arg, cfg, messages, session_msgs)
        elif cmd == "/testgen":
            last_response = cmd_testgen(arg, cfg, messages, session_msgs)
        elif cmd == "/docstring":
            last_response = cmd_docstring(arg, cfg, messages, session_msgs)
        elif cmd == "/complexity":
            last_response = cmd_complexity(arg, cfg, messages, session_msgs)
        elif cmd == "/gitdiff":
            last_response = cmd_gitdiff(arg, cfg, messages, session_msgs)
        elif cmd == "/commitmsg":
            last_response = cmd_commitmsg(arg, cfg, messages, session_msgs)
        elif cmd == "/todo":
            last_response = cmd_todo(arg, cfg, messages, session_msgs)
        elif cmd == "/gitignore":
            last_response = cmd_gitignore(arg, cfg, messages, session_msgs)
        elif cmd == "/license":
            last_response = cmd_license(arg, cfg, messages, session_msgs)
        elif cmd == "/lint":
            last_response = cmd_lint(arg, cfg, messages, session_msgs)
        elif cmd == "/profile":
            last_response = cmd_profile(arg, cfg, messages, session_msgs)
        # ── security tools ───────────────────────────────────
        elif cmd == "/hash":
            last_response = cmd_hash(arg, cfg, messages, session_msgs)
        elif cmd == "/headers":
            last_response = cmd_headers(arg, cfg, messages, session_msgs)
        elif cmd == "/osint":
            last_response = cmd_osint(arg, cfg, messages, session_msgs)
        elif cmd == "/wordlist":
            last_response = cmd_wordlist(arg, cfg, messages, session_msgs)
        # ── ai tools ─────────────────────────────────────────
        elif cmd == "/think":
            last_response = cmd_think(arg, cfg, messages, session_msgs)
        elif cmd == "/debate":
            last_response = cmd_debate(arg, cfg, messages, session_msgs)
        elif cmd == "/improve":
            last_response = cmd_improve(arg, cfg, messages, session_msgs)
        elif cmd == "/eli5":
            last_response = cmd_eli5_topic(arg, cfg, messages, session_msgs)
        elif cmd == "/cheatsheet":
            last_response = cmd_cheatsheet(arg, cfg, messages, session_msgs)
        elif cmd == "/cron":
            last_response = cmd_cron_explain(arg, cfg, messages, session_msgs)
        elif cmd == "/quiz":
            last_response = cmd_quiz(arg, cfg, messages, session_msgs)
        elif cmd == "/name":
            last_response = cmd_namebrainstorm(arg, cfg, messages, session_msgs)
        elif cmd == "/explaincode":
            last_response = cmd_explain_code(arg, cfg, messages, session_msgs)
        elif cmd == "/roast":
            last_response = cmd_roast(arg, cfg, messages, session_msgs)
        elif cmd == "/challenge":
            last_response = cmd_challenge(arg, cfg, messages, session_msgs)
        elif cmd == "/recap":
            cmd_recap(messages)
        elif cmd == "/translate":
            last_response = cmd_translate(arg, cfg, messages, session_msgs)
        elif cmd == "/weather":
            cmd_weather_ascii(arg)
        elif cmd == "/timer":
            cmd_timer(arg)
        elif cmd == "/rename":
            last_response = cmd_ai_rename(arg, cfg, messages, session_msgs)
        elif cmd == "/regex":
            last_response = cmd_regex(arg, cfg, messages, session_msgs)
        elif cmd == "/git":
            last_response = cmd_githelp(arg, cfg, messages, session_msgs)
        elif cmd == "/ctf":
            last_response = cmd_ctf(arg, cfg, messages, session_msgs)
        elif cmd == "/diff":
            last_response = cmd_diff_explain(arg, cfg, messages, session_msgs)
        elif cmd == "/models":
            print(f"\n{NEON_Y}{BOLD}Available models to download:{R}\n")
            for k, m in KNOWN_MODELS.items():
                print(f"  {NEON_C}[{k}]{R} {m['name']}")
            print(f"\n{NEON_Y}Choose [1-{len(KNOWN_MODELS)}] or Enter to cancel: {R}", end="")
            choice = input().strip()
            if choice in KNOWN_MODELS:
                model  = KNOWN_MODELS[choice]
                dl_dir = os.path.expanduser("~/ollama-models")
                os.makedirs(dl_dir, exist_ok=True)
                dest   = os.path.join(dl_dir, model["file"])
                print(f"\n{NEON_C}Downloading {model['file']}…{R}")
                ok = _download_file(model["url"], dest, label=model["file"])
                if ok:
                    ok = _verify_model_sha256(dest, KNOWN_MODEL_SHA256.get(choice), model["file"])
                if ok and os.path.exists(dest):
                    cfg["model_path"] = dest
                    save_cfg(cfg)
                    global _llm_instance
                    _llm_instance = None
                    get_llm(cfg)
                    print(f"\n{NEON_G}✓ Downloaded and loaded — ready to use now.{R}\n")
                else:
                    print(f"{NEON_R}✗ Download failed.{R}\n")
        elif cmd == "/plugins":
            parts2  = arg.split(maxsplit=1)
            paction = parts2[0] if parts2 else ""
            parg    = parts2[1] if len(parts2) > 1 else ""
            cmd_plugins(paction, parg, cfg)
        elif cmd in PLUGIN_COMMANDS:
            plugin_ctx = {"cfg": cfg, "messages": messages, "session_msgs": session_msgs, "ask": ask}
            try:
                result = PLUGIN_COMMANDS[cmd]["handler"](arg, plugin_ctx)
                if result:
                    last_response = result
            except Exception as e:
                print(f"{NEON_R}✗ Plugin command '{cmd}' error: {e}{R}\n")
        else:
            print(f"{NEON_R}Unknown: {cmd}{R} — /help\n")

# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cybersh",
        description="CYBER SH DIRECT — No server local LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-p","--prompt", help="One-shot prompt")
    parser.add_argument("-f","--file",   help="File context")
    parser.add_argument("-o","--output", help="Save output to file")
    parser.add_argument("-m","--model",  help="Path to .gguf model")
    parser.add_argument("-t","--temp",   type=float)
    parser.add_argument("--mode",        choices=list(MODES.keys()))
    parser.add_argument("--ctx",         type=int)
    parser.add_argument("--threads",     type=int)
    parser.add_argument("--setup",       action="store_true", help="Run setup wizard")
    parser.add_argument("--gui",         action="store_true", help="Launch the browser-based GUI instead of the terminal REPL")
    parser.add_argument("--port",        type=int, default=8420, help="Port for --gui (default 8420)")
    parser.add_argument("--update",      action="store_true", help="Force update from GitHub")
    parser.add_argument("--no-update",   action="store_true", help="Skip update check")
    parser.add_argument("--version",     action="version", version=f"CYBER SH DIRECT v{APP_VERSION}")

    args = parser.parse_args()
    cfg  = load_cfg()

    if args.model:   cfg["model_path"]  = args.model
    if args.temp:    cfg["temperature"] = args.temp
    if args.mode:    cfg["mode"]        = args.mode
    if args.ctx:     cfg["context"]     = args.ctx
    if args.threads: cfg["threads"]     = args.threads

    if args.setup:
        setup_wizard(cfg); return

    # auto-update: run on interactive startup unless --no-update
    if not args.no_update and sys.stdin.isatty():
        check_and_update(force=getattr(args, 'update', False))
    elif getattr(args, 'update', False):
        check_and_update(force=True); return

    if not cfg.get("model_path") or not os.path.exists(cfg.get("model_path","")):
        print(f"\n{NEON_Y}No model configured. Running setup…{R}\n")
        setup_wizard(cfg)
        if not cfg.get("model_path"): return

    piped = ""
    if not sys.stdin.isatty(): piped = sys.stdin.read().strip()

    if args.prompt or piped:
        mode     = MODES.get(cfg.get("mode","chat"), MODES["chat"])
        messages = [{"role":"system","content":mode["system"] + "\n\n" + get_env_context()}]
        sess     = []
        prefix   = ""
        if args.file:
            try:
                with open(os.path.expanduser(args.file),"r",errors="replace") as f:
                    content = f.read(50000)
                ext    = os.path.splitext(args.file)[1][1:] or ""
                prefix = f"[FILE: {args.file}]\n```{ext}\n{content}\n```"
            except Exception as e:
                print(f"{NEON_R}✗ {e}{R}"); sys.exit(1)
        prompt   = args.prompt or ""
        if piped: prompt = f"{prompt}\n\nSTDIN:\n{piped}".strip()
        response = ask(cfg, messages, sess, prompt, prefix=prefix)
        if args.output and response:
            with open(os.path.expanduser(args.output),"w") as f: f.write(response)
            print(f"{NEON_G}✓ Saved → {args.output}{R}")
        return

    if args.gui:
        launch_gui(cfg, port=args.port)
        return

    repl(cfg)

if __name__ == "__main__":
    main()
