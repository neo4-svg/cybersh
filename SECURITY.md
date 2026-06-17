# 🔒 CyberSH Security Policy (VDP Announcement)

CyberSH is a local AI framework built for transparency and hacker‑grade experimentation.  
We run a **Vulnerability Disclosure Program (VDP)** to encourage responsible reporting of security issues.

---

## 📢 VDP Announcement
If you discover a vulnerability in CyberSH:

- **Do not** disclose it publicly.
- **Report privately** via email: **neo4linux404@proton.me**
- Provide:
  - Steps to reproduce
  - Impact assessment
  - Suggested mitigation

We will acknowledge reports within **48 hours**.  
**Bug triage time** will be based on **priority level** and the **availability of the CyberSH Security Team**.  
Critical issues are prioritized first, followed by high, medium, and low severity.

**Rewards:**  
- Valid, non‑duplicate, informative bug reports will receive an official **CyberSH Security Researcher Certificate**.  
- Multiple valid reports may qualify for **Diamond Certificate** status, granting recognition as part of the CyberSH team.  
- Manual testing reports have a **higher chance** of earning certificates.  
- Automated spam reports will result in **temporary ban** from the VDP.

---

## 🧩 Vulnerability Classes

| Class | Level | Description | Example |
|-------|-------|-------------|---------|
| **Injection** | Critical | Prompt injection, command injection, or malicious input that alters AI behavior. | Malicious prompt bypassing filters. |
| **Jailbreak** | High | Attempts to override safety layers or gain unauthorized model access. | Custom payload forcing unrestricted mode. |
| **Persistence** | High | Exploits that survive restarts or poison memory. | Malicious memory entry reloading on boot. |
| **Data Exposure** | Medium | Leakage of sensitive local data or unintended output. | Revealing system paths or configs. |
| **Dependency Risk** | Medium | Vulnerabilities in third‑party libraries. | CVE in `transformers` or `torch`. |
| **Logic Flaw** | Low | Misconfigurations or workflow bypasses that reduce security. | Skipping auth checks in CLI. |

---

## ⚙️ Security Principles
- **Local‑first** → No cloud dependency.  
- **Zero telemetry** → No external data calls.  
- **Sandboxed execution** → AI agents isolated in subprocesses.  
- **Memory integrity** → Encrypted persistent memory.  
- **Dependency hygiene** → Regular CVE scans with `pip-audit`.  

---

## 🧰 Tools & Testing Rules
- Allowed tools: `bandit`, `pip-audit`, `gitleaks`, `trivy`.  
- **Manual testing is preferred** → higher chance of certificate.  
- **Automated spam scanning is forbidden** → violators will be **temporarily banned** from the VDP.  

---

## 🧠 Scope Rules
- VDP applies **only** to:
  - Real CyberSH code maintained by the official team.  
  - Starred forks officially recognized by the CyberSH team.  
- Out‑of‑scope:
  - Random forks not listed by CyberSH team.  
  - Modified tools or derivative repos outside official scope.  

---

## 🧠 Contributor Guidelines
- Never commit secrets or tokens.  
- Run `make security-check` before PRs.  
- Respect disclosure timelines — no leaks before patch release.  

---

## 📧 Contact
For urgent issues:  
**neo4linux404@proton.me**  
Or open a **private GitHub security advisory**.

---

## 🧾 Patch Notes
Security fixes are tracked in `CHANGELOG.md` under **Security Updates**.  
Versioning follows **SemVer** — patch releases increment the `z` digit.
