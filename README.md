# CYBER SH — Full Installation Guide

## Requirements

- OS:     Linux (Kali, Ubuntu, Debian) or Windows WSL2
- Python: 3.10 or higher
- RAM:    8GB minimum, 16GB recommended
- Disk:   1GB+ free space in /home
- CPU:    Any x86_64 with AVX2 support
- Note:   Runs 100% locally — no internet needed after setup

## Step 1: Check Python version

python3 --version
# Need 3.10 or higher

## Step 2: Install build tools (Linux/WSL)

sudo apt update
sudo apt install python3-dev build-essential wget -y

## Step 3: Install the AI engine

pip install llama-cpp-python --break-system-packages

# This compiles C++ code on your machine
# CPU will hit 99% for 5-10 minutes — this is normal
# Only happens once, never again after first install

## Step 4: Verify installation

python3 -c "import llama_cpp; print('engine OK')"
# Should print: engine OK

## Step 5: Run setup wizard

python3 cybersh_direct.py --setup

# The wizard will ask:
# - Do you have a .gguf file already? (y/n)
# - If no, pick a model to download:
#     [1] Phi-3 Mini     2.2GB  great for code
#     [2] TinyLlama      638MB  fastest, lightest
#     [3] Qwen2.5 1.5B   986MB  recommended sweet spot
#     [4] Mistral 7B     4.1GB  best quality (needs 16GB RAM)
# - How many CPU threads (press Enter to use all)

## Step 6: Run it

python3 cybersh_direct.py

# Startup menu asks which mode:
# [1] Agent  — AI controls your computer
# [2] Sec    — Bug bounty and pentest expert
# [3] Vibe   — Creative coding and UI/UX
# [4] Code   — Production code and scripts
# [5] Chat   — General assistant

## Windows WSL2 Setup

# Open PowerShell as admin and run:
wsl --install

# Then open WSL terminal and follow
# the Linux steps above from Step 1

## Troubleshooting

# pip install fails:
sudo apt install python3-dev build-essential -y
pip install llama-cpp-python --break-system-packages

# No space on root partition:
df -h /home
mkdir -p ~/models
# Point setup wizard to ~/models

# Model not found error:
python3 cybersh_direct.py --setup

## Important Notes

- Everything runs locally on your machine
- No data is sent anywhere
- No API keys needed
- No internet needed after model download
- Model files are stored in ~/ollama-models by default
