# Whisper PTT

Local push-to-talk dictation for Windows. Hold Left Shift, talk, release — the transcription gets pasted at your cursor. Runs entirely on your GPU via [faster-whisper](https://github.com/SYSTRAN/faster-whisper). Nothing leaves your machine.

## Features

- **Hold-to-talk** with Left Shift (held >150ms; quick taps for capitals are ignored)
- **GPU transcription** via faster-whisper + CUDA 12
- **Hot-swappable mic** — audio stream re-opens on each press, so changing USB ports doesn't require restarting
- **System tray icon** with state colors (grey idle, green recording, blue transcribing)
- **Silent background launch** via VBS shim + Startup folder shortcut — no console window
- **Clipboard-safe paste** — your previous clipboard contents are restored after the paste
- ~0.4s transcribe latency on `base.en` model with a modern NVIDIA GPU

## Requirements

- Windows 10 / 11
- Python 3.10+
- NVIDIA GPU + driver (CUDA 12 capable)
- Admin PowerShell for the install script (it sets up Startup folder shortcuts)

## Install

```powershell
git clone https://github.com/rdmilly/whisper-ptt.git C:\Users\$env:USERNAME\whisper-ptt
cd C:\Users\$env:USERNAME\whisper-ptt
.\install.ps1
```

The installer:

1. `pip install`s requirements (`faster-whisper`, `sounddevice`, `keyboard`, `pyperclip`, `pystray`, `pillow`)
2. Installs the CUDA 12 runtime via `nvidia-cublas-cu12` and `nvidia-cudnn-cu12` pip wheels
3. Copies the CUDA DLLs adjacent to the script (works around CTranslate2's Windows DLL search-path quirk)
4. Generates `whisper_ptt_launcher.vbs` for silent background launch
5. Drops a Startup folder shortcut so PTT runs on login

## Usage

First launch will download the Whisper model (`base.en`, ~150MB) into the HuggingFace cache.

- **Hold Left Shift** — starts recording after 150ms
- **Release** — stops recording, transcribes, pastes at your cursor
- **Right-click tray icon → Quit** — clean shutdown
- **Ctrl+Shift+Q** — also quits

Logs go to `whisper_ptt.log` in the project folder.

## Configuration

Edit the CONFIG block near the top of `whisper_ptt.py`:

```python
HOTKEY         = "left shift"   # "f8", "right ctrl", "pause", etc.
MODEL_SIZE     = "base.en"      # "small.en", "medium.en", "large-v3-turbo"
DEVICE         = "cuda"         # "cpu" if no GPU
COMPUTE_TYPE   = "float16"      # "int8" for CPU mode
HOLD_THRESHOLD = 0.15           # seconds; ignore quick taps
```

Larger models trade speed for accuracy. `base.en` is ~0.4s on a modern GPU; `large-v3-turbo` is ~1.5s with significantly better accuracy.

## Troubleshooting

**`Library cublas64_12.dll is not found`**
The CUDA wheels installed but Windows can't find them. Re-run `install.ps1` — step 3 copies the DLLs adjacent to the script, which always wins.

**Recording starts when typing capitals**
Increase `HOLD_THRESHOLD` from 0.15 to 0.3.

**Mic stopped working after switching ports**
Fixed in this build — the audio stream re-opens on each press. If you still hit it, check `whisper_ptt.log` for `mic open error:`.

**No tray icon visible**
Windows hides new tray icons by default. Click the `^` arrow on the taskbar and drag the dot out so it stays visible.

## Architecture

- Tray icon runs on the main thread (pystray requires this on Windows)
- Keyboard listener runs on a daemon thread
- Each press opens a fresh `sounddevice.InputStream`, captures audio while held, and closes the stream on release
- Transcription happens in a separate daemon thread so the UI stays responsive
- Quit forces `os._exit(0)` so audio threads don't hang shutdown

## License

MIT — see `LICENSE`.
