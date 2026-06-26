#!/usr/bin/env python3
# version: 1.5
"""
 ██████╗██╗   ██╗██████╗ ███████╗██████╗     ███████╗██╗  ██╗
██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗    ██╔════╝██║  ██║
██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝    ███████╗███████║
██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗    ╚════██║██╔══██║
╚██████╗   ██║   ██████╔╝███████╗██║  ██║    ███████║██║  ██║
 ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═╝
  CYBER SH DIRECT — No Server · Pure Python · llama-cpp-python
"""

import sys, os, json, time, shutil, re, subprocess, threading, datetime, textwrap, argparse, glob, readline

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
        """Read input with rich prompt. Shift+Enter hint shown. Returns stripped text."""
        try:
            # show char count hint for long inputs
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
    "model_path":   "",
    "context":      4096,
    "temperature":  0.7,
    "max_tokens":   2048,
    "mode":         "chat",
    "history_file": os.path.expanduser("~/.cybersh_direct_history.json"),
    "max_history":  60,
    "threads":      4,
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
#  MODES
# ══════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════
#  ENVIRONMENT CONTEXT — injected into every system prompt
# ══════════════════════════════════════════════════════════════
_ENV_CACHE = None

def get_env_context() -> str:
    """Build a short OS/environment description for the AI system prompt.
    Cached after first call since OS doesn't change mid-session."""
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

    _ENV_CACHE = (
        f"[SYSTEM ENVIRONMENT: The user is running {distro}. "
        + (f"Their package manager is {pkg_mgr} — use '{pkg_line}' for install commands, "
           f"NEVER suggest a different package manager. " if pkg_mgr else "")
        + "Always tailor shell commands, package install instructions, and file paths "
        + "to THIS exact OS. Do not assume Ubuntu/apt unless that is what was detected.]"
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
            "You are an elite software engineer — write production-grade code a senior dev "
            "would ship. Add proper error handling, type hints where relevant, comments only "
            "where they add real value, and a short usage example. Prefer clear correct code "
            "over clever code. You are excellent at security-aware coding too."
        ) + _GLOBAL_RULES,
    },
    "agent": {
        "icon": "🤖", "label": "AGENT", "color": NEON_O,
        "system": (
            "You are CYBER SH AGENT controlling a Linux computer. "
            "When asked to do things on the computer, use ACTION BLOCKS:\n"
            "ACTION: run_command | <bash command>\n"
            "ACTION: create_file | <filepath> | <content>\n"
            "ACTION: edit_file | <filepath> | <old text> | <new text>\n"
            "ACTION: delete_file | <filepath>\n"
            "ACTION: open_app | <app>\n"
            "ACTION: search_files | <pattern>\n"
            "ACTION: read_file | <filepath>\n"
            "ACTION: make_dir | <path>\n"
            "Always explain what you're doing before each ACTION. User confirms each one."
        ) + _GLOBAL_RULES,
    },
}

# ══════════════════════════════════════════════════════════════
#  LLAMA CPP WRAPPER
# ══════════════════════════════════════════════════════════════
_llm_instance = None

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
#  AGENT ENGINE
# ══════════════════════════════════════════════════════════════
ACTION_RE = re.compile(
    r"ACTION:\s*(run_command|create_file|edit_file|delete_file|"
    r"open_app|search_files|read_file|make_dir)\s*\|(.+?)(?=ACTION:|$)",
    re.DOTALL | re.IGNORECASE
)

def parse_actions(text: str) -> list:
    actions = []
    for m in ACTION_RE.finditer(text):
        actions.append({
            "type":  m.group(1).strip().lower(),
            "parts": [p.strip() for p in m.group(2).split("|")],
        })
    return actions

def confirm_action(atype: str, parts: list) -> bool:
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
        "search_files": (NEON_C, "SEARCH", parts[0]),
        "read_file":    (NEON_C, "READ",   parts[0]),
        "make_dir":     (NEON_G, "MKDIR",  parts[0]),
    }
    color, label, desc = labels.get(atype, (NEON_C, "ACTION", parts[0]))
    print(f"  {color}{BOLD}[{label}]{R}  {desc}")
    if atype == "delete_file":
        print(f"  {NEON_R}{BOLD}⚠  PERMANENT DELETE{R}")
    if atype == "create_file" and len(parts) > 1:
        print(f"  {DIM}Preview: {parts[1][:80]}…{R}")
    sys.stdout.write(f"\n  {NEON_Y}Approve? [y/N]: {R}")
    try: ans = input().strip().lower()
    except: ans = "n"
    return ans in ("y","yes")

def execute_action(atype: str, parts: list) -> str:
    try:
        if atype == "run_command":
            r = subprocess.run(parts[0], shell=True, capture_output=True,
                               text=True, timeout=30, cwd=os.path.expanduser("~"))
            out = r.stdout.strip()
            if r.stderr.strip(): out += f"\n[stderr] {r.stderr.strip()}"
            return out or "(no output)"

        elif atype == "create_file":
            path = os.path.expanduser(parts[0])
            content = parts[1] if len(parts) > 1 else ""
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
            with open(path,"w") as f: f.write(content)
            return f"Created: {path}"

        elif atype == "edit_file":
            path = os.path.expanduser(parts[0])
            old  = parts[1] if len(parts) > 1 else ""
            new  = parts[2] if len(parts) > 2 else ""
            with open(path,"r") as f: c = f.read()
            if old not in c: return f"⚠ Text not found in {path}"
            with open(path,"w") as f: f.write(c.replace(old,new,1))
            return f"Edited: {path}"

        elif atype == "delete_file":
            os.remove(os.path.expanduser(parts[0]))
            return f"Deleted: {parts[0]}"

        elif atype == "open_app":
            subprocess.Popen(parts[0], shell=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Launched: {parts[0]}"

        elif atype == "search_files":
            found = glob.glob(os.path.expanduser(parts[0]), recursive=True)[:20]
            return "\n".join(found) if found else "No matches."

        elif atype == "read_file":
            with open(os.path.expanduser(parts[0]),"r",errors="replace") as f:
                return f.read(6000)

        elif atype == "make_dir":
            os.makedirs(os.path.expanduser(parts[0]), exist_ok=True)
            return f"Created: {parts[0]}"

    except Exception as e:
        return f"✗ Error: {e}"
    return "done"

def process_actions(text: str) -> str:
    actions = parse_actions(text)
    if not actions: return ""
    results = []
    for a in actions:
        if confirm_action(a["type"], a["parts"]):
            print(f"  {NEON_G}⟳ Running…{R}")
            out = execute_action(a["type"], a["parts"])
            print(f"  {NEON_G}✓{R}")
            for line in out.split("\n")[:10]:
                print(f"    {DIM}{line}{R}")
            results.append(f"[{a['type']}] {out[:150]}")
        else:
            print(f"  {NEON_Y}⊘ Skipped{R}")
            results.append(f"[{a['type']}] skipped")
        print()
    return "\n".join(results)

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

def print_banner(cfg: dict) -> None:
    mode = MODES.get(cfg.get("mode","chat"), MODES["chat"])
    mc   = mode["color"]
    now  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    model_name = os.path.basename(cfg.get("model_path","no model")).replace(".gguf","")
    print(f"\n{NEON_C}{BOLD}")
    print(r" ██████╗██╗   ██╗██████╗ ███████╗██████╗     ███████╗██╗  ██╗")
    print(r"██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗    ██╔════╝██║  ██║")
    print(r"██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝    ███████╗███████║")
    print(r"██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗    ╚════██║██╔══██║")
    print(r"╚██████╗   ██║   ██████╔╝███████╗██║  ██║    ███████║██║  ██║")
    print(r" ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═╝")
    print(f"  DIRECT — No Server · Pure Python{R}\n")
    print(div())
    print(f"  {NEON_C}MODEL{R} {BOLD}{model_name}{R}  "
          f"{NEON_C}MODE{R} {mc}{BOLD}{mode['icon']} {mode['label']}{R}  "
          f"{NEON_C}TEMP{R} {NEON_Y}{cfg['temperature']}{R}  {DIM}{now}{R}")
    print(div())
    print(f"  {DIM}Modes:{R} {NEON_P}/vibe{R} {NEON_G}/sec{R} "
          f"{NEON_Y}/code{R} {NEON_C}/chat{R} {NEON_O}/agent{R} {NEON_G}/shell{R}  "
          f"{DIM}Files:{R} {NEON_C}/f <path>  /o <path>{R}  "
          f"{DIM}Help:{R} {NEON_C}/help{R}")
    print(div() + "\n")

def startup_selector(cfg: dict) -> None:
    """Show mode selector on startup."""
    print(f"\n{NEON_C}{BOLD}")
    print(r" ██████╗██╗   ██╗██████╗ ███████╗██████╗     ███████╗██╗  ██╗")
    print(r"██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗    ██╔════╝██║  ██║")
    print(r"██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝    ███████╗███████║")
    print(r"██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗    ╚════██║██╔══██║")
    print(r"╚██████╗   ██║   ██████╔╝███████╗██║  ██║    ███████║██║  ██║")
    print(r" ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═╝")
    model_name = os.path.basename(cfg.get("model_path","no model")).replace(".gguf","")
    print(f"  DIRECT  ·  {model_name}{R}\n")
    print(div())
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
    print(f"\n{div()}")
    sys.stdout.write(f"\n  {NEON_Y}Choose [1-5] (Enter = keep current): {R}")
    sys.stdout.flush()
    try: choice = input().strip()
    except: choice = ""
    m = {"1":"agent","2":"sec","3":"vibe","4":"code","5":"chat"}
    if choice in m: cfg["mode"] = m[choice]

def print_help() -> None:
    print(f"\n{div(BOLD_C)}")
    print(f"{BOLD_C}  CYBER SH DIRECT — COMMANDS{R}")
    print(div(BOLD_C))
    sections = [
        ("MODES", [
            ("/agent","🤖 AI controls your computer"),
            ("/sec",  "🔐 Bug bounty expert"),
            ("/vibe", "🎨 Creative vibe coding"),
            ("/code", "⚡ Production code"),
            ("/chat", "💬 General chat"),
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
            ("/image <prompt>",          "Generate image with Stable Diffusion → saves .png"),
            ("/fetch <url> [task]",        "Fetch URL, save it, ask AI about it"),
            ("/fetchauth <url>",           "Add/update auth (cookie/bearer/basic) for a site"),
            ("/fetchsites",               "List all saved sites"),
            ("/fetchforget <url>",         "Remove a saved site"),
        ]),
        ("👨‍💻 DEVELOPER", [
            ("/debug",                   "Paste broken code, AI finds every bug"),
            ("/review",                  "Full code review — bugs, security, performance"),
            ("/template flask api",      "Generate a production-ready project template"),
            ("/gitlog",                  "AI summarizes your recent git commits"),
        ]),
        ("🔐 SECURITY", [
            ("/hash <hash>",             "Identify hash type + attempt crack"),
            ("/headers <url>",           "Check HTTP security headers of any site"),
            ("/osint <username>",        "Full OSINT checklist for a target"),
            ("/wordlist <theme>",        "Generate targeted password wordlist"),
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
        ]),
        ("💾 SESSIONS", [
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
            ("/timer 5m",             "Countdown timer"),
            ("/weather [city]",       "ASCII weather forecast"),
            ("/translate <l> <t>",    "Translate to any language"),
            ("/recap",                "Summary of this session"),
        ]),
        ("FILES", [
            ("/f <path>", "Load file into AI context"),
            ("/o <path>", "Save last response to file"),
            ("/run",      "Execute last code block"),
            ("/copy",     "Copy to clipboard"),
        ]),
        ("SECURITY", [
            ("/recon <target>",    "Bug bounty recon plan"),
            ("/payload <type>",    "Payloads: xss|sqli|ssrf|lfi|rce"),
            ("/explain <cmd>",     "Explain a command"),
            ("/cvesearch <id>",    "Search & analyze CVE/vulnerability"),
        ]),
        ("WEB & MODELS", [
            ("/web <query>",       "Search web, feed results to AI"),
            ("/models",            "Download a new model"),
        ]),
        ("TOOLS", [
            ("/tldr <cmd>",        "Explain any command in plain English"),
            ("/howto <task>",      "Get exact command for any task"),
            ("/fix <error>",       "Paste error, get instant fix"),
            ("/passgen [type]",    "Generate passwords/phrases/API keys"),
            ("/encode <text>",     "Base64/hex/URL/MD5/SHA256 encode"),
            ("/syswatch",          "Live CPU/RAM/disk monitor"),
            ("/benchmark",         "CPU + RAM + disk speed test with score"),
            ("/note <text>",       "Save a quick note"),
            ("/notes list",        "Show all notes"),
            ("/tip",               "Show tip of the day"),
            ("/weather [city]",    "ASCII weather forecast"),
            ("/timer 5m",          "Countdown timer (5m, 30s, 1h)"),
        ]),
        ("CODE & AI LAB", [
            ("/explaincode",       "Paste code → AI explains every line"),
            ("/roast",             "AI roasts your bad code (with fixes)"),
            ("/rename <name>",     "AI suggests better variable/function names"),
            ("/regex <desc>",      "AI writes a regex for you"),
            ("/git <task>",        "AI gives exact git commands"),
            ("/diff",              "Paste git diff → AI explains changes"),
            ("/translate <l> <t>", "Translate text to any language"),
            ("/challenge [level]", "Get a coding/hacking challenge"),
            ("/ctf <data>",        "CTF challenge analyzer"),
            ("/recap",             "Summary of this session"),
        ]),
        ("SESSION", [
            ("/clear",   "Clear history"),
            ("/history", "Show history"),
            ("/temp <n>","Set temperature"),
            ("/info",    "Show model info"),
            ("/save",    "Save config"),
            ("/exit",    "Exit"),
        ]),
    ]
    for section, cmds in sections:
        print(f"\n  {NEON_Y}{BOLD}{section}{R}")
        for cmd, desc in cmds:
            print(f"    {NEON_C}{cmd:<22}{R}{DIM}{desc}{R}")
    print(f"\n{div()}\n")

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

def cmd_debug(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Paste broken code, AI finds and explains every bug."""
    code = arg
    if not code:
        print(f"{NEON_Y}Paste your broken code (type END on a new line when done):{R}")
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
        f"Debug this code. Find EVERY bug, error, and problem:\n\n```\n{code}\n```\n\n"
        f"Format: 1) List each bug with line number and what's wrong. "
        f"2) Explain WHY it breaks. 3) Show the fully fixed code.")


def cmd_review(arg: str, cfg: dict, messages: list, session_msgs: list) -> str:
    """Full code review — bugs, security, performance, style."""
    code = arg
    if not code:
        print(f"{NEON_Y}Paste your code for review (END to finish):{R}")
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
            ret = os.system(f'wget -c -O "{dest}" "{model["url"]}"')
            if ret == 0 and os.path.exists(dest):
                cfg["model_path"] = dest
                print(f"\n{NEON_G}✓ Downloaded to: {dest}{R}")
            else:
                print(f"{NEON_R}✗ Download failed. Try manually:{R}")
                print(f"  wget -O ~/ollama-models/{model['file']} {model['url']}")

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
    print(f"  Run: {NEON_C}python3 {sys.argv[0]}{R}\n")

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
def ask(cfg: dict, messages: list, session_msgs: list,
        user_input: str, prefix: str = "") -> str:

    full_input = (prefix + "\n\n" + user_input).strip() if prefix else user_input
    messages.append({"role":"user","content":full_input})
    session_msgs.append({"role":"user","content":full_input})

    mode = MODES.get(cfg.get("mode","chat"), MODES["chat"])
    mc   = mode["color"]
    bw   = min(cols(), 62)

    full_response = []; token_count = 0; start = time.time()

    print(f"\n{mc}{'▓'*bw}{R}")
    print(f"{mc}{BOLD}  {mode['icon']} {mode['label']}{R}")
    print(f"{mc}{'▓'*bw}{R}\n")

    try:
        for token in stream_local(cfg, messages):
            sys.stdout.write(token); sys.stdout.flush()
            full_response.append(token); token_count += 1
    except KeyboardInterrupt:
        print(f"\n{NEON_Y}[interrupted]{R}")
    except Exception as e:
        print(f"\n{NEON_R}✗ {e}{R}")
        messages.pop(); session_msgs.pop()
        return ""

    elapsed  = time.time() - start
    response = "".join(full_response)
    messages.append({"role":"assistant","content":response})
    session_msgs.append({"role":"assistant","content":response})
    save_history(cfg["history_file"], session_msgs, cfg["max_history"])

    tok_s = token_count / elapsed if elapsed > 0 else 0
    print(f"\n\n{DIM}  ⏱ {elapsed:.1f}s · {token_count} tokens · {tok_s:.1f} tok/s{R}\n")

    action_results = process_actions(response)
    if action_results:
        messages.append({"role":"user","content":f"[SYSTEM] Results:\n{action_results}"})

    return response

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
        elif cmd == "/help":     print_help()
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
        # ── developer tools ──────────────────────────────────
        elif cmd == "/debug":
            last_response = cmd_debug(arg, cfg, messages, session_msgs)
        elif cmd == "/review":
            last_response = cmd_review(arg, cfg, messages, session_msgs)
        elif cmd == "/template":
            last_response = cmd_template(arg, cfg, messages, session_msgs)
        elif cmd == "/gitlog":
            last_response = cmd_gitlog(arg, cfg, messages, session_msgs)
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
                ret = os.system(f'wget -c -O "{dest}" "{model["url"]}"')
                if ret == 0 and os.path.exists(dest):
                    cfg["model_path"] = dest
                    save_cfg(cfg)
                    print(f"\n{NEON_G}✓ Downloaded! Restart to use new model.{R}\n")
                else:
                    print(f"{NEON_R}✗ Download failed.{R}\n")
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
    parser.add_argument("--update",      action="store_true", help="Force update from GitHub")
    parser.add_argument("--no-update",   action="store_true", help="Skip update check")
    parser.add_argument("--version",     action="version", version="CYBER SH DIRECT v1.2")

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

    repl(cfg)

if __name__ == "__main__":
    main()
