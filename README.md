# 🎙️ Whisper PTT

> Local push-to-talk dictation for Windows. Hold a hotkey, talk, release — transcription pastes at your cursor. Runs entirely on your GPU. Nothing leaves your machine.

**In plain English:** Dictation that actually works — no cloud, no subscription, no latency. Built on OpenAI's Whisper model running locally via faster-whisper. Faster and more accurate than Windows dictation or any cloud service.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Platform](https://img.shields.io/badge/platform-Windows-blue?style=flat-square)
![GPU](https://img.shields.io/badge/runs_on-local_GPU-green?style=flat-square)

---

## Features

- **Hold-to-talk** — Left Shift (or any hotkey) activates recording
- **Instant paste** — transcription appears at cursor on release
- **GPU-accelerated** — faster-whisper on CUDA, runs in real time
- **100% local** — no API calls, no data sent anywhere
- **Tray icon** — runs silently in the background

---

## Requirements

- Windows 10/11
- NVIDIA GPU (CUDA)
- Python 3.10+

## Quick Start

```bash
pip install faster-whisper sounddevice pyperclip keyboard pynput
python whisper_ptt.py
```

---

## Builder

Ryan Milly — [ryanmilly.com](https://ryanmilly.com) · [LinkedIn](https://linkedin.com/in/rdmilly)
