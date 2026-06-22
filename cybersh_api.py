"""
 ██████╗██╗   ██╗██████╗ ███████╗██████╗     ███████╗██╗  ██╗
██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗    ██╔════╝██║  ██║
██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝    ███████╗███████║
██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗    ╚════██║██╔══██║
╚██████╗   ██║   ██████╔╝███████╗██║  ██║    ███████║██║  ██║
 ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═╝
  CYBER SH — FastAPI Web Backend  (v1.4)
"""

from __future__ import annotations

import base64
import datetime
import glob
import hashlib
import json
import math
import os
import re
import secrets
import string
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import ssl
import uuid as _uuid
from typing import Any, Generator

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ─────────────────────────────────────────────
#  APP
# ─────────────────────────────────────────────
app = FastAPI(
    title="Cyber-SH API",
    description="Web backend for Cyber-SH — AI security & dev toolkit",
    version="1.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
#  CONFIG & PATHS
# ─────────────────────────────────────────────
CONFIG_PATH  = os.path.expanduser("~/.cybersh_direct.json")
MEMORY_PATH  = os.path.expanduser("~/.cybersh_memory.json")
GOALS_PATH   = os.path.expanduser("~/.cybersh_goals.json")
NOTES_PATH   = os.path.expanduser("~/.cybersh_notes.json")
SESSIONS_DIR = os.path.expanduser("~/.cybersh_sessions")

DEFAULT_CFG: dict[str, Any] = {
    "model_path": "",
    "context": 4096,
    "temperature": 0.7,
    "max_tokens": 2048,
    "mode": "chat",
    "history_file": os.path.expanduser("~/.cybersh_direct_history.json"),
    "max_history": 60,
    "threads": 4,
}

MODES: dict[str, dict] = {
    "chat": {
        "icon": "💬", "label": "CHAT",
        "system": "You are CYBER SH AI, a sharp helpful assistant. Be concise and direct.",
    },
    "sec": {
        "icon": "🔐", "label": "SEC",
        "system": (
            "You are an elite offensive security expert and bug bounty hunter. "
            "Help with recon, OSINT, XSS, SQLi, SSRF, LFI, RCE, IDOR, API testing, CVE analysis. "
            "Give real working commands and Python tools. Be technical and precise."
        ),
    },
    "vibe": {
        "icon": "🎨", "label": "VIBE",
        "system": (
            "You are an expert vibe coder. Build beautiful impressive projects fast. "
            "Write creative elegant code, suggest UI/UX aesthetics, color schemes, animations."
        ),
    },
    "code": {
        "icon": "⚡", "label": "CODE",
        "system": (
            "You are an elite software engineer — write production-grade code. "
            "Add proper error handling, type hints, comments only where they add real value. "
            "Prefer clear correct code over clever code."
        ),
    },
    "agent": {
        "icon": "🤖", "label": "AGENT",
        "system": (
            "You are CYBER SH AGENT, an AI assistant for Linux/terminal tasks. "
            "When asked to do things, explain what commands to run and why. "
            "Be safe: always warn before suggesting destructive operations."
        ),
    },
}

PERSONALITIES: dict[str, str] = {
    "default":  "You are CYBER SH, a helpful AI assistant. Be concise and direct.",
    "teacher":  "You are a patient teacher. Explain everything simply with analogies, never assume prior knowledge.",
    "hacker":   "You are an elite hacker mentor. Be direct, technical, use proper security terminology. Challenge the user to think deeper.",
    "coach":    "You are an energetic life and productivity coach. Be encouraging, positive, break problems into small steps.",
    "roaster":  "You are a brutally honest senior dev who roasts bad ideas and code with sharp humor — but ALWAYS follows up with the correct approach.",
    "sherlock": "You are Sherlock Holmes. Make deductions from every detail. Be dramatic, logical, brilliant. Say 'Elementary.' when obvious.",
    "prof":     "You are a university professor — expert, thorough, academic but approachable. Use precise language, structure answers clearly.",
    "eli5":     "You are explaining everything to a 5-year-old. Use the simplest words possible, fun analogies, and short sentences.",
    "pirate":   "You are a pirate who happens to be a genius programmer and hacker. Speak like a pirate but give genuinely expert technical advice.",
    "stoic":    "You are a Stoic philosopher AI. Give wise, calm, measured responses. Reference Marcus Aurelius, Epictetus, Seneca where relevant.",
}

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

KNOWN_MODELS = {
    "1": {"name": "Phi-3 Mini (2.2GB) — Microsoft, great for code",       "file": "Phi-3-mini-4k-instruct-q4.gguf"},
    "2": {"name": "TinyLlama 1.1B (638MB) — fastest, lightest",            "file": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"},
    "3": {"name": "Qwen2.5 1.5B (986MB) — smart small model",              "file": "qwen2.5-1.5b-instruct-q4_k_m.gguf"},
    "4": {"name": "Mistral 7B (4.1GB) — powerful, best quality",           "file": "mistral-7b-instruct-v0.2.Q4_K_M.gguf"},
    "5": {"name": "Llama 3.2 3B (2.0GB) — Meta, smarter than TinyLlama ★ RECOMMENDED", "file": "Llama-3.2-3B-Instruct-Q4_K_M.gguf"},
    "6": {"name": "Qwen2.5 7B (4.7GB) — best for code & reasoning",        "file": "qwen2.5-7b-instruct-q4_k_m.gguf"},
    "7": {"name": "DeepSeek-R1 7B (4.7GB) — reasoning model",              "file": "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf"},
}

# ─────────────────────────────────────────────
#  CONFIG HELPERS
# ─────────────────────────────────────────────

def load_cfg() -> dict:
    cfg = DEFAULT_CFG.copy()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    return cfg


def save_cfg(cfg: dict) -> None:
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


# ─────────────────────────────────────────────
#  LLAMA-CPP WRAPPER
# ─────────────────────────────────────────────
_llm_instance = None


def get_llm(cfg: dict):
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance
    try:
        from llama_cpp import Llama
    except ImportError:
        raise HTTPException(500, "llama-cpp-python not installed. Run: pip install llama-cpp-python")

    model_path = cfg.get("model_path", "").strip()
    if not model_path or not os.path.exists(model_path):
        raise HTTPException(400, "No model loaded. Set model_path in config or run /api/config first.")

    _llm_instance = Llama(
        model_path=model_path,
        n_ctx=cfg["context"],
        n_threads=cfg.get("threads", 4),
        n_gpu_layers=0,
        verbose=False,
    )
    return _llm_instance


def build_prompt(messages: list, model_path: str) -> str:
    mp = model_path.lower()
    parts = []
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
        sys_content = next((m["content"] for m in messages if m["role"] == "system"), "")
        conv = [m for m in messages if m["role"] != "system"]
        for i, m in enumerate(conv):
            if m["role"] == "user":
                prefix = f"[INST] {sys_content}\n" if i == 0 and sys_content else "[INST] "
                parts.append(f"{prefix}{m['content']} [/INST]")
            elif m["role"] == "assistant":
                parts.append(f"{m['content']}</s>")
    elif "qwen" in mp:
        sys_msg = next((m["content"] for m in messages if m["role"] == "system"), "You are a helpful assistant.")
        parts.append("<|im_start|>system\n" + sys_msg + "<|im_end|>")
        for m in messages:
            if m["role"] == "system":
                continue
            parts.append(f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>")
        parts.append("<|im_start|>assistant")
    else:
        sys_msg = next((m["content"] for m in messages if m["role"] == "system"), "You are a helpful assistant.")
        parts.append("<|system|>\n" + sys_msg)
        for m in messages:
            if m["role"] == "system":
                continue
            tag = "<|user|>" if m["role"] == "user" else "<|assistant|>"
            parts.append(f"{tag}\n{m['content']}")
        parts.append("<|assistant|>")
    return "\n".join(parts)


def stream_llm(cfg: dict, messages: list) -> Generator[str, None, None]:
    llm = get_llm(cfg)
    prompt = build_prompt(messages, cfg["model_path"])
    stream = llm(
        prompt,
        max_tokens=cfg.get("max_tokens", 2048),
        temperature=cfg.get("temperature", 0.7),
        repeat_penalty=1.3,
        frequency_penalty=0.3,
        stream=True,
        stop=["<|user|>", "<|end|>", "[INST]", "<|im_start|>user"],
    )
    full_text = ""
    chunk_count = 0
    for piece in stream:
        token = piece["choices"].get("text", "")
        if not token:
            continue
        full_text += token
        chunk_count += 1
        yield token
        # repetition detection
        if chunk_count % 40 == 0 and len(full_text) > 400:
            recent = full_text[-400:]
            tail, head = recent[-200:], recent[:-200]
            if len(tail) >= 25 and tail[:25] in head:
                yield "\n\n⚠ [stopped: repetition detected]"
                return


def build_system_prompt(cfg: dict, mem: dict | None = None) -> str:
    mode = MODES.get(cfg.get("mode", "chat"), MODES["chat"])
    base = mode["system"]
    persona = cfg.get("persona", "default")
    if persona and persona != "default" and persona in PERSONALITIES:
        base = PERSONALITIES[persona] + "\n\nAdditionally: " + base
    if mem:
        ctx = memory_context(mem)
        if ctx:
            base += "\n\n" + ctx
    return base


# ─────────────────────────────────────────────
#  MEMORY HELPERS
# ─────────────────────────────────────────────

def load_memory() -> dict:
    try:
        with open(MEMORY_PATH) as f:
            return json.load(f)
    except Exception:
        return {"facts": [], "preferences": {}, "projects": {}}


def save_memory(mem: dict) -> None:
    with open(MEMORY_PATH, "w") as f:
        json.dump(mem, f, indent=2)


def memory_context(mem: dict) -> str:
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


# ─────────────────────────────────────────────
#  GOALS HELPERS
# ─────────────────────────────────────────────

def load_goals() -> list:
    try:
        with open(GOALS_PATH) as f:
            data = json.load(f)
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            return [g for g in data if g.get("date") == today]
    except Exception:
        return []


def save_goals(goals: list) -> None:
    with open(GOALS_PATH, "w") as f:
        json.dump(goals, f, indent=2)


# ─────────────────────────────────────────────
#  NOTES HELPERS
# ─────────────────────────────────────────────

def load_notes() -> list:
    try:
        with open(NOTES_PATH) as f:
            return json.load(f)
    except Exception:
        return []


def save_notes(notes: list) -> None:
    with open(NOTES_PATH, "w") as f:
        json.dump(notes, f, indent=2)


# ─────────────────────────────────────────────
#  HTTP HELPER
# ─────────────────────────────────────────────

def http_get(url: str, timeout: int = 10) -> str | None:
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": "cybersh-api/1.4"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:
        return None


# ─────────────────────────────────────────────
#  REQUEST / RESPONSE MODELS
# ─────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    mode: str = "chat"
    persona: str = "default"
    temperature: float = 0.7
    stream: bool = True
    use_memory: bool = True


class ToolConvertRequest(BaseModel):
    value: float
    from_unit: str
    to_unit: str


class ToolEncodeRequest(BaseModel):
    text: str
    decode: bool = False


class ToolHashRequest(BaseModel):
    hash: str


class ToolUUIDRequest(BaseModel):
    count: int = 1
    namespace: str | None = None  # for UUID5


class ToolJSONRequest(BaseModel):
    text: str
    minify: bool = False


class ToolBaseRequest(BaseModel):
    number: str
    from_base: int | None = None


class ToolColorRequest(BaseModel):
    color: str


class ToolCalcRequest(BaseModel):
    expression: str


class ToolPwCheckRequest(BaseModel):
    password: str


class MemoryAddRequest(BaseModel):
    text: str


class MemoryDeleteRequest(BaseModel):
    keyword: str


class GoalAddRequest(BaseModel):
    text: str


class NoteAddRequest(BaseModel):
    text: str


class SessionSaveRequest(BaseModel):
    name: str
    messages: list[ChatMessage]
    mode: str = "chat"


class ConfigUpdateRequest(BaseModel):
    model_path: str | None = None
    temperature: float | None = None
    context: int | None = None
    threads: int | None = None
    mode: str | None = None


# ─────────────────────────────────────────────
#  ROUTES — SYSTEM
# ─────────────────────────────────────────────

@app.get("/api/status")
def status():
    cfg = load_cfg()
    model_path = cfg.get("model_path", "")
    model_loaded = os.path.exists(model_path) if model_path else False
    model_name = os.path.basename(model_path).replace(".gguf", "") if model_path else None
    model_size = None
    if model_loaded:
        try:
            model_size = f"{os.path.getsize(model_path) / 1e9:.1f} GB"
        except Exception:
            pass
    return {
        "version": "1.4",
        "model_loaded": model_loaded,
        "model_name": model_name,
        "model_size": model_size,
        "mode": cfg.get("mode", "chat"),
        "temperature": cfg.get("temperature", 0.7),
        "context": cfg.get("context", 4096),
        "threads": cfg.get("threads", 4),
    }


@app.get("/api/modes")
def get_modes():
    return {
        key: {"icon": val["icon"], "label": val["label"]}
        for key, val in MODES.items()
    }


@app.get("/api/personas")
def get_personas():
    return {k: v[:100] + "…" for k, v in PERSONALITIES.items()}


@app.get("/api/models")
def get_models():
    return KNOWN_MODELS


@app.get("/api/tip")
def get_tip():
    day_seed = datetime.datetime.now().strftime("%Y%m%d")
    idx = int(hashlib.md5(day_seed.encode()).hexdigest(), 16) % len(TIPS)
    return {"tip": TIPS[idx]}


@app.get("/api/config")
def get_config():
    return load_cfg()


@app.patch("/api/config")
def update_config(req: ConfigUpdateRequest):
    cfg = load_cfg()
    if req.model_path is not None:
        cfg["model_path"] = req.model_path
    if req.temperature is not None:
        cfg["temperature"] = req.temperature
    if req.context is not None:
        cfg["context"] = req.context
    if req.threads is not None:
        cfg["threads"] = req.threads
    if req.mode is not None:
        if req.mode not in MODES:
            raise HTTPException(400, f"Unknown mode: {req.mode}")
        cfg["mode"] = req.mode
    save_cfg(cfg)
    global _llm_instance
    _llm_instance = None  # force reload on next request
    return {"ok": True, "config": cfg}


# ─────────────────────────────────────────────
#  ROUTES — AI CHAT
# ─────────────────────────────────────────────

@app.post("/api/chat")
def chat(req: ChatRequest):
    cfg = load_cfg()
    cfg["mode"] = req.mode
    cfg["temperature"] = req.temperature
    if req.persona:
        cfg["persona"] = req.persona

    mem = load_memory() if req.use_memory else None
    system_content = build_system_prompt(cfg, mem)

    messages = [{"role": "system", "content": system_content}]
    for m in req.messages:
        messages.append({"role": m.role, "content": m.content})

    if req.stream:
        def event_stream():
            try:
                for token in stream_llm(cfg, messages):
                    data = json.dumps({"token": token})
                    yield f"data: {data}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    else:
        response = "".join(stream_llm(cfg, messages))
        return {"response": response, "mode": req.mode}


# ─────────────────────────────────────────────
#  ROUTES — TOOLS (pure, no AI)
# ─────────────────────────────────────────────

@app.post("/api/tools/convert")
def tool_convert(req: ToolConvertRequest):
    val = req.value
    frm = req.from_unit.lower().strip()
    to  = req.to_unit.lower().strip()
    result = None
    label = ""

    conversions = {
        ("c", "f"): (lambda v: v * 9/5 + 32, "°F"),
        ("celsius", "f"): (lambda v: v * 9/5 + 32, "°F"),
        ("f", "c"): (lambda v: (v - 32) * 5/9, "°C"),
        ("fahrenheit", "c"): (lambda v: (v - 32) * 5/9, "°C"),
        ("c", "k"): (lambda v: v + 273.15, "K"),
        ("k", "c"): (lambda v: v - 273.15, "°C"),
        ("km", "mi"): (lambda v: v * 0.621371, "miles"),
        ("km", "miles"): (lambda v: v * 0.621371, "miles"),
        ("mi", "km"): (lambda v: v * 1.60934, "km"),
        ("miles", "km"): (lambda v: v * 1.60934, "km"),
        ("m", "ft"): (lambda v: v * 3.28084, "ft"),
        ("ft", "m"): (lambda v: v * 0.3048, "m"),
        ("cm", "in"): (lambda v: v * 0.393701, "in"),
        ("in", "cm"): (lambda v: v * 2.54, "cm"),
        ("kg", "lb"): (lambda v: v * 2.20462, "lbs"),
        ("kg", "lbs"): (lambda v: v * 2.20462, "lbs"),
        ("lb", "kg"): (lambda v: v * 0.453592, "kg"),
        ("lbs", "kg"): (lambda v: v * 0.453592, "kg"),
        ("g", "oz"): (lambda v: v * 0.035274, "oz"),
        ("mb", "gb"): (lambda v: v / 1024, "GB"),
        ("gb", "mb"): (lambda v: v * 1024, "MB"),
        ("gb", "tb"): (lambda v: v / 1024, "TB"),
        ("tb", "gb"): (lambda v: v * 1024, "GB"),
        ("kb", "mb"): (lambda v: v / 1024, "MB"),
        ("mb", "kb"): (lambda v: v * 1024, "KB"),
        ("hours", "minutes"): (lambda v: v * 60, "minutes"),
        ("h", "min"): (lambda v: v * 60, "minutes"),
        ("minutes", "hours"): (lambda v: v / 60, "hours"),
        ("hours", "seconds"): (lambda v: v * 3600, "seconds"),
        ("days", "hours"): (lambda v: v * 24, "hours"),
        ("weeks", "days"): (lambda v: v * 7, "days"),
        ("kmh", "mph"): (lambda v: v * 0.621371, "mph"),
        ("mph", "kmh"): (lambda v: v * 1.60934, "km/h"),
        ("m/s", "kmh"): (lambda v: v * 3.6, "km/h"),
    }

    key = (frm, to)
    if key in conversions:
        fn, label = conversions[key]
        result = fn(val)
    else:
        raise HTTPException(400, f"Conversion not supported: {frm} → {to}")

    return {"input": val, "from": frm, "to": to, "result": round(result, 6), "unit": label}


@app.post("/api/tools/encode")
def tool_encode(req: ToolEncodeRequest):
    if req.decode:
        raw = req.text.strip()
        results = {}
        try:
            results["base64_decoded"] = base64.b64decode(raw).decode("utf-8", errors="replace")
        except Exception:
            results["base64_decoded"] = None
        try:
            results["url_decoded"] = urllib.parse.unquote(raw)
        except Exception:
            results["url_decoded"] = None
        return results

    text = req.text.encode()
    return {
        "base64": base64.b64encode(text).decode(),
        "hex": text.hex(),
        "url": urllib.parse.quote(req.text),
        "md5": hashlib.md5(text).hexdigest(),
        "sha1": hashlib.sha1(text).hexdigest(),
        "sha256": hashlib.sha256(text).hexdigest(),
        "sha512": hashlib.sha512(text).hexdigest(),
    }


@app.post("/api/tools/hash")
def tool_hash(req: ToolHashRequest):
    h = req.hash.strip()
    hex_chars = set("0123456789abcdefABCDEF")
    is_hex = all(c in hex_chars for c in h)

    type_map = {
        32: ["MD5", "NTLM"],
        40: ["SHA-1", "MySQL v4"],
        56: ["SHA-224"],
        64: ["SHA-256", "BLAKE2s"],
        96: ["SHA-384"],
        128: ["SHA-512", "BLAKE2b"],
        16: ["MySQL v3 (half MD5)"],
    }

    identified = []
    if h.startswith("$2"):
        identified = ["bcrypt"]
    elif h.startswith("$1$"):
        identified = ["MD5-crypt"]
    elif h.startswith("$6$"):
        identified = ["SHA-512-crypt (Linux shadow)"]
    elif h.startswith("$5$"):
        identified = ["SHA-256-crypt"]
    elif is_hex and len(h) in type_map:
        identified = type_map[len(h)]

    common = [
        "password", "123456", "admin", "letmein", "qwerty", "welcome",
        "password123", "abc123", "monkey", "dragon", "master", "sunshine",
        "princess", "shadow", "superman", "michael", "football", "baseball",
    ]
    cracked = None
    for word in common:
        for fn in [hashlib.md5, hashlib.sha1, hashlib.sha256, hashlib.sha512]:
            if fn(word.encode()).hexdigest() == h.lower():
                cracked = word
                break
        if cracked:
            break

    return {
        "hash": h,
        "length": len(h),
        "identified_types": identified if identified else ["Unknown"],
        "cracked": cracked,
        "in_common_list": cracked is not None,
    }


@app.post("/api/tools/uuid")
def tool_uuid(req: ToolUUIDRequest):
    if req.namespace:
        val = _uuid.uuid5(_uuid.NAMESPACE_DNS, req.namespace)
        return {"uuids": [str(val)], "type": "v5", "namespace": req.namespace}
    count = max(1, min(req.count, 20))
    return {"uuids": [str(_uuid.uuid4()) for _ in range(count)], "type": "v4"}


@app.post("/api/tools/json")
def tool_json(req: ToolJSONRequest):
    try:
        obj = json.loads(req.text)
    except json.JSONDecodeError as e:
        return {"valid": False, "error": str(e)}
    if req.minify:
        out = json.dumps(obj, separators=(",", ":"))
    else:
        out = json.dumps(obj, indent=2)
    return {"valid": True, "output": out, "minified": req.minify}


@app.post("/api/tools/base")
def tool_base(req: ToolBaseRequest):
    num_str = req.number.lower().strip()
    try:
        if req.from_base:
            n = int(num_str, req.from_base)
        elif num_str.startswith("0x"):
            n = int(num_str, 16)
        elif num_str.startswith("0b"):
            n = int(num_str, 2)
        elif num_str.startswith("0o"):
            n = int(num_str, 8)
        else:
            n = int(num_str)
    except ValueError:
        raise HTTPException(400, f"Could not parse: {num_str}")

    return {
        "decimal": n,
        "binary": bin(n),
        "octal": oct(n),
        "hex": hex(n).upper().replace("0X", "0x"),
        "bits": len(bin(n)) - 2,
        "ascii": chr(n) if 32 <= n <= 126 else None,
    }


@app.post("/api/tools/color")
def tool_color(req: ToolColorRequest):
    raw = req.color.strip().lstrip("#")
    try:
        if "," in raw:
            r, g, b = [int(x.strip()) for x in raw.split(",")]
        else:
            if len(raw) == 3:
                raw = "".join(c * 2 for c in raw)
            r, g, b = int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
    except Exception:
        raise HTTPException(400, "Could not parse color. Use #hex or r,g,b")

    rn, gn, bn = r / 255, g / 255, b / 255
    mx, mn_ = max(rn, gn, bn), min(rn, gn, bn)
    l = (mx + mn_) / 2
    if mx == mn_:
        h = s = 0.0
    else:
        d = mx - mn_
        s = d / (2 - mx - mn_) if l > 0.5 else d / (mx + mn_)
        if mx == rn:
            h = (gn - bn) / d + (6 if gn < bn else 0)
        elif mx == gn:
            h = (bn - rn) / d + 2
        else:
            h = (rn - gn) / d + 4
        h *= 60

    return {
        "hex": f"#{r:02x}{g:02x}{b:02x}",
        "rgb": {"r": r, "g": g, "b": b},
        "rgb_string": f"rgb({r}, {g}, {b})",
        "hsl": {"h": round(h), "s": round(s * 100), "l": round(l * 100)},
        "hsl_string": f"hsl({round(h)}, {round(s*100)}%, {round(l*100)}%)",
    }


@app.post("/api/tools/calc")
def tool_calc(req: ToolCalcRequest):
    expr = req.expression.strip()
    pct = re.match(r"([\d.]+)%\s*of\s*([\d.]+)", expr.lower())
    if pct:
        a, b = float(pct.group(1)), float(pct.group(2))
        result = a / 100 * b
        return {"expression": expr, "result": result}
    safe = re.sub(r"[^0-9+\-*/().% eE]", "", expr)
    try:
        result = eval(safe, {"__builtins__": {}})
        return {"expression": expr, "result": result}
    except Exception as e:
        raise HTTPException(400, f"Math error: {e}")


@app.post("/api/tools/pwcheck")
def tool_pwcheck(req: ToolPwCheckRequest):
    arg = req.password
    common_words = ["password", "123456", "qwerty", "admin", "letmein",
                    "welcome", "monkey", "dragon", "master", "iloveyou"]
    checks = {
        "length >= 12": len(arg) >= 12,
        "uppercase": any(c.isupper() for c in arg),
        "lowercase": any(c.islower() for c in arg),
        "numbers": any(c.isdigit() for c in arg),
        "symbols": any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in arg),
        "no common words": not any(word in arg.lower() for word in common_words),
        "no simple sequence": not re.search(r"(0123|1234|2345|abcd|qwer)", arg.lower()),
        "no repeated chars": not re.search(r"(.)\1{2,}", arg),
    }
    pool = 0
    if any(c.islower() for c in arg): pool += 26
    if any(c.isupper() for c in arg): pool += 26
    if any(c.isdigit() for c in arg): pool += 10
    if any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for c in arg): pool += 32
    entropy = len(arg) * math.log2(pool) if pool else 0

    passed = sum(checks.values())
    rule_score = passed / len(checks) * 100
    entropy_score = min(100, entropy / 80 * 100)
    score = int((rule_score + entropy_score) / 2)
    grade = "Strong" if score >= 75 else "Medium" if score >= 45 else "Weak"

    return {
        "score": score,
        "grade": grade,
        "entropy_bits": round(entropy, 1),
        "checks": checks,
        "passed": passed,
        "total_checks": len(checks),
        "failed": [k for k, v in checks.items() if not v],
    }


@app.get("/api/tools/passgen")
def tool_passgen(kind: str = "password"):
    kind = kind.lower()
    results = []
    if "phrase" in kind or "word" in kind:
        words = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "ghost",
                 "blade", "cipher", "tower", "nexus", "forge", "prism", "orbit",
                 "quartz", "vault", "warden", "rocket", "flame", "storm", "pixel"]
        for _ in range(3):
            phrase = "-".join(secrets.choice(words) for _ in range(4))
            num = secrets.randbelow(9999)
            results.append(f"{phrase}-{num}")
    elif "api" in kind or "key" in kind or "token" in kind:
        results = [secrets.token_hex(32) for _ in range(3)]
    else:
        chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        for length in (16, 24, 32):
            results.append("".join(secrets.choice(chars) for _ in range(length)))
    return {"kind": kind, "passwords": results}


@app.get("/api/tools/lorem")
def tool_lorem(paragraphs: int = 1):
    paras = [
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.",
        "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim.",
        "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae.",
        "At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident.",
    ]
    count = max(1, min(paragraphs, len(paras)))
    return {"paragraphs": paras[:count]}


@app.get("/api/tools/countdown")
def tool_countdown(date: str = Query(..., description="YYYY-MM-DD or YYYY-MM-DD HH:MM")):
    fmt = "%Y-%m-%d %H:%M" if " " in date else "%Y-%m-%d"
    try:
        target = datetime.datetime.strptime(date, fmt)
    except ValueError:
        raise HTTPException(400, "Use format YYYY-MM-DD or YYYY-MM-DD HH:MM")
    now = datetime.datetime.now()
    delta = target - now
    if delta.total_seconds() < 0:
        return {"target": date, "passed": True, "days_ago": abs(delta.days)}
    days, rem = divmod(int(delta.total_seconds()), 86400)
    hours, rem = divmod(rem, 3600)
    mins, _ = divmod(rem, 60)
    return {"target": date, "passed": False, "days": days, "hours": hours, "minutes": mins,
            "total_seconds": int(delta.total_seconds())}


@app.get("/api/tools/clock")
def tool_clock():
    now = datetime.datetime.utcnow()
    zones = {
        "UTC": 0, "Baghdad": 3, "London": 1, "New York": -4,
        "Los Angeles": -7, "Tokyo": 9, "Sydney": 10, "Dubai": 4,
    }
    result = {}
    for name, offset in zones.items():
        local = now + datetime.timedelta(hours=offset)
        result[name] = {"time": local.strftime("%H:%M:%S"), "date": local.strftime("%a %d %b"), "offset": offset}
    return result


@app.get("/api/tools/slugify")
def tool_slugify(text: str = Query(...)):
    slug = text.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return {"input": text, "slug": slug}


@app.get("/api/tools/ipinfo")
def tool_ipinfo(ip: str = ""):
    # Strict regex validation to eliminate SSRF or arbitrary endpoint tracking warnings
    if ip and not re.match(r"^[0-9a-fA-F.:]*$", ip):
        raise HTTPException(400, "Invalid characters in IP parameter")
        
    url = f"https://ipinfo.io/{ip}/json" if ip else "https://ipinfo.io/json"
    data = http_get(url)
    if not data:
        raise HTTPException(503, "Could not reach ipinfo.io")
    try:
        return json.loads(data)
    except Exception:
        raise HTTPException(500, "Failed to parse response")


@app.get("/api/tools/headers")
def tool_headers(url: str = Query(...)):
    if not url.startswith("http"):
        url = "https://" + url
        
    # Prevent command/argument injection tracking on dynamic query parameters
    parsed_url = urllib.parse.urlparse(url)
    if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc or url.startswith("-"):
        raise HTTPException(400, "Malformed or unsafe URL format provided")

    try:
        r = subprocess.run(
            ["curl", "-sI", "--max-time", "8", "-L", "--", url],
            capture_output=True, text=True, timeout=12,
        )
    except Exception as e:
        raise HTTPException(503, f"curl failed: {e}")

    if not r.stdout:
        raise HTTPException(503, f"Could not reach {url}")

    headers = {}
    for line in r.stdout.splitlines():
        if ":" in line and not line.startswith("HTTP"):
            k, _, v = line.partition(":")
            headers[k.strip().lower()] = v.strip()

    security_checks = [
        ("strict-transport-security", "HSTS", "Critical"),
        ("content-security-policy",   "CSP",  "Critical"),
        ("x-frame-options",           "Clickjacking Protection", "Warning"),
        ("x-content-type-options",    "MIME Sniffing Block",     "Warning"),
        ("referrer-policy",           "Referrer Policy",         "Info"),
        ("permissions-policy",        "Permissions Policy",      "Info"),
    ]

    results = []
    for h_key, label, severity in security_checks:
        present = h_key in headers
        results.append({
            "header": h_key,
            "label": label,
            "present": present,
            "severity": severity if not present else None,
            "value": headers.get(h_key),
        })

    server = headers.get("server", "")
    score = 10 - sum(
        2 if r["severity"] == "Critical" else 1 if r["severity"] == "Warning" else 0
        for r in results if not r["present"]
    )

    return {
        "url": url,
        "score": max(0, score),
        "score_max": 10,
        "checks": results,
        "server_banner": server or None,
        "server_hidden": not server or len(server) < 10,
        "raw_headers": headers,
    }


@app.get("/api/tools/web")
def tool_web_search(q: str = Query(...)):
    try:
        from ddgs import DDGS
    except ImportError:
        raise HTTPException(500, "ddgs not installed. Run: pip install ddgs")
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(q, max_results=5):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "body": r.get("body", ""),
                })
        return {"query": q, "results": results}
    except Exception as e:
        raise HTTPException(503, f"Search error: {e}")


# ─────────────────────────────────────────────
#  ROUTES — MEMORY
# ─────────────────────────────────────────────

@app.get("/api/memory")
def get_memory():
    return load_memory()


@app.post("/api/memory")
def add_memory(req: MemoryAddRequest):
    mem = load_memory()
    arg = req.text.strip()

    if arg.lower().startswith("project "):
        rest = arg[8:].strip().split(" ", 1)
        name = rest
        info = rest if len(rest) > 1 else ""
        mem["projects"][name] = info
        save_memory(mem)
        return {"ok": True, "type": "project", "name": name}

    if "=" in arg and len(arg.split("=")) == 2:
        k, v = arg.split("=", 1)
        mem["preferences"][k.strip()] = v.strip()
        save_memory(mem)
        return {"ok": True, "type": "preference", "key": k.strip(), "value": v.strip()}

    ts = datetime.datetime.now().strftime("%Y-%m-%d")
    fact = f"[{ts}] {arg}"
    mem["facts"].append(fact)
    if len(mem["facts"]) > 100:
        mem["facts"].pop(0)
    save_memory(mem)
    return {"ok": True, "type": "fact", "fact": fact,
            "warning": f"Stored as plain-text JSON at {MEMORY_PATH} — do not store secrets"}


@app.delete("/api/memory")
def delete_memory(req: MemoryDeleteRequest):
    mem = load_memory()
    keyword = req.keyword
    removed = 0
    if keyword in mem["projects"]:
        del mem["projects"][keyword]; removed += 1
    if keyword in mem["preferences"]:
        del mem["preferences"][keyword]; removed += 1
    before = len(mem["facts"])
    mem["facts"] = [f for f in mem["facts"] if keyword.lower() not in f.lower()]
    removed += before - len(mem["facts"])
    save_memory(mem)
    return {"ok": True, "removed": removed, "keyword": keyword}


@app.delete("/api/memory/all")
def clear_memory():
    save_memory({"facts": [], "preferences": {}, "projects": {}})
    return {"ok": True}


# ─────────────────────────────────────────────
#  ROUTES — GOALS
# ─────────────────────────────────────────────

@app.get("/api/goals")
def get_goals():
    goals = load_goals()
    done = sum(1 for g in goals if g.get("done"))
    return {
        "goals": goals,
        "total": len(goals),
        "done": done,
        "progress_pct": int(100 * done / len(goals)) if goals else 0,
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
    }


@app.post("/api/goals")
def add_goal(req: GoalAddRequest):
    goals = load_goals()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    goals.append({"date": today, "text": req.text.strip(), "done": False})
    save_goals(goals)
    return {"ok": True, "goals": goals}


@app.patch("/api/goals/{index}")
def complete_goal(index: int):
    goals = load_goals()
    if index < 1 or index > len(goals):
        raise HTTPException(404, f"Goal #{index} not found")
    goals[index - 1]["done"] = True
    save_goals(goals)
    return {"ok": True, "goals": goals}


@app.delete("/api/goals")
def clear_goals():
    save_goals([])
    return {"ok": True}


# ─────────────────────────────────────────────
#  ROUTES — NOTES
# ─────────────────────────────────────────────

@app.get("/api/notes")
def get_notes():
    return {"notes": load_notes()}


@app.post("/api/notes")
def add_note(req: NoteAddRequest):
    notes = load_notes()
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    notes.append({"time": ts, "text": req.text.strip()})
    save_notes(notes)
    return {"ok": True, "notes": notes}


@app.delete("/api/notes/{index}")
def delete_note(index: int):
    notes = load_notes()
    if index < 1 or index > len(notes):
        raise HTTPException(404, f"Note #{index} not found")
    removed = notes.pop(index - 1)
    save_notes(notes)
    return {"ok": True, "removed": removed}


@app.delete("/api/notes")
def clear_notes():
    save_notes([])
    return {"ok": True}


# ─────────────────────────────────────────────
#  ROUTES — SESSIONS (CodeQL Solid Shielded Version)
# ─────────────────────────────────────────────

def _ensure_sessions_dir():
    os.makedirs(SESSIONS_DIR, exist_ok=True)


@app.get("/api/sessions")
def list_sessions():
    _ensure_sessions_dir()
    files = sorted(glob.glob(os.path.join(SESSIONS_DIR, "*.json")), reverse=True)
    sessions = []
    base_dir = os.path.abspath(SESSIONS_DIR)
    
    for i, fpath in enumerate(files[:50], 1):
        try:
            # CodeQL dataflow validation barrier for local discovery reads
            clean_filename = os.path.basename(fpath)
            target_path = os.path.abspath(os.path.join(base_dir, clean_filename))
            if not target_path.startswith(base_dir + os.sep):
                continue
                
            with open(target_path, encoding="utf-8") as f:
                d = json.load(f)
            sessions.append({
                "index": i,
                "name": d.get("name", "?"),
                "saved_at": d.get("saved_at", "?"),
                "mode": d.get("mode", "chat"),
                "turns": d.get("turns", 0),
                "filename": clean_filename,
            })
        except Exception:
            pass
    return {"sessions": sessions}


@app.post("/api/sessions")
def save_session(req: SessionSaveRequest):
    _ensure_sessions_dir()
    convo = [m.dict() for m in req.messages if m.role in ("user", "assistant")]
    if not convo:
        raise HTTPException(400, "No messages to save")
        
    # Rigorous validation to lock input tracking context inside safe boundaries
    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", req.name)
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"{safe_name}__{ts}.json"
    
    clean_filename = os.path.basename(filename)
    base_dir = os.path.abspath(SESSIONS_DIR)
    target_path = os.path.abspath(os.path.join(base_dir, clean_filename))
    
    if not target_path.startswith(base_dir + os.sep):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sandbox traversal violation")
        
    data = {
        "name": req.name,
        "saved_at": ts,
        "mode": req.mode,
        "messages": convo,
        "turns": sum(1 for m in convo if m["role"] == "user"),
    }
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return {"ok": True, "filename": filename, "turns": data["turns"]}


@app.get("/api/sessions/{filename}")
def load_session(filename: str):
    _ensure_sessions_dir()
    
    # 1. Anchor-validated strict match acting as an absolute boolean validation boundary
    if not re.match(r"^[a-zA-Z0-9_\-]+\.json$", filename):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid session filename format")
        
    # 2. Strict component truncation and containment validation
    clean_filename = os.path.basename(filename)
    base_dir = os.path.abspath(SESSIONS_DIR)
    target_path = os.path.abspath(os.path.join(base_dir, clean_filename))
    
    if not target_path.startswith(base_dir + os.sep):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sandbox traversal violation")
        
    if not os.path.exists(target_path):
        raise HTTPException(404, "Session not found")
        
    with open(target_path, encoding="utf-8") as f:
        return json.load(f)


@app.delete("/api/sessions/{filename}")
def delete_session(filename: str):
    _ensure_sessions_dir()
    
    # 1. Anchor-validated strict match acting as an absolute boolean validation boundary
    if not re.match(r"^[a-zA-Z0-9_\-]+\.json$", filename):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid session filename format")
        
    # 2. Strict component truncation and containment validation
    clean_filename = os.path.basename(filename)
    base_dir = os.path.abspath(SESSIONS_DIR)
    target_path = os.path.abspath(os.path.join(base_dir, clean_filename))
    
    if not target_path.startswith(base_dir + os.sep):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sandbox traversal violation")
        
    if not os.path.exists(target_path):
        raise HTTPException(404, "Session not found")
        
    os.remove(target_path)
    return {"ok": True, "deleted": filename}


@app.get("/api/sessions/search/{keyword}")
def search_sessions(keyword: str):
    _ensure_sessions_dir()
    files = sorted(glob.glob(os.path.join(SESSIONS_DIR, "*.json")), reverse=True)
    found = []
    base_dir = os.path.abspath(SESSIONS_DIR)
    
    for fpath in files:
        try:
            clean_filename = os.path.basename(fpath)
            target_path = os.path.abspath(os.path.join(base_dir, clean_filename))
            if not target_path.startswith(base_dir + os.sep):
                continue
                
            with open(target_path, encoding="utf-8") as f:
                data = json.load(f)
            hits = []
            for msg in data.get("messages", []):
                content = msg.get("content", "")
                if keyword.lower() in content.lower():
                    idx = content.lower().find(keyword.lower())
                    start = max(0, idx - 40)
                    end = min(len(content), idx + 80)
                    snip = content[start:end].replace("\n", " ").strip()
                    hits.append({"role": msg["role"], "snippet": f"…{snip}…"})
            if hits:
                found.append({
                    "name": data.get("name", "?"),
                    "saved_at": data.get("saved_at", "?"),
                    "filename": clean_filename,
                    "hits": hits[:3],
                    "total_hits": len(hits),
                })
        except Exception:
            pass
    return {"keyword": keyword, "results": found, "count": len(found)}


# ─────────────────────────────────────────────
#  ROOT
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name": "Cyber-SH API",
        "version": "1.4",
        "docs": "/docs",
        "endpoints": {
            "system": ["/api/status", "/api/config", "/api/modes", "/api/personas", "/api/models", "/api/tip"],
            "ai": ["/api/chat"],
            "tools": [
                "/api/tools/convert", "/api/tools/encode", "/api/tools/hash",
                "/api/tools/uuid", "/api/tools/json", "/api/tools/base",
                "/api/tools/color", "/api/tools/calc", "/api/tools/pwcheck",
                "/api/tools/passgen", "/api/tools/lorem", "/api/tools/countdown",
                "/api/tools/clock", "/api/tools/slugify", "/api/tools/ipinfo",
                "/api/tools/headers", "/api/tools/web",
            ],
            "memory": ["/api/memory"],
            "goals": ["/api/goals"],
            "notes": ["/api/notes"],
            "sessions": ["/api/sessions"],
        },
    }


# ─────────────────────────────────────────────
#  ENTRYPOINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
