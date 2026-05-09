"""
Whisper PTT - Push-to-talk dictation using local faster-whisper on GPU.

Hold Left Shift, speak, release. Transcription is pasted at the cursor.

Hotkey: Left Shift (held >150ms; quick taps for capitals are ignored)
Quit:   Ctrl+Shift+Q  OR  right-click tray icon -> Quit

Audio stream is opened fresh on each press, so swapping mic ports
no longer requires restarting the script.

Tray icon shows status: grey = idle, green = recording, blue = transcribing.
"""

import sys
import time
import threading
import numpy as np
import sounddevice as sd
import keyboard
import pyperclip
from faster_whisper import WhisperModel
from PIL import Image, ImageDraw
import pystray

# ---- CONFIG -----------------------------------------------------------
HOTKEY         = "left shift"
QUIT_HOTKEY    = "ctrl+shift+q"
SAMPLE_RATE    = 16000
MODEL_SIZE     = "base.en"
DEVICE         = "cuda"
COMPUTE_TYPE   = "float16"
LANGUAGE       = "en"
MIN_DURATION   = 0.3
HOLD_THRESHOLD = 0.15
PASTE_SUFFIX   = " "
# ----------------------------------------------------------------------

print("[whisper-ptt] loading model:", MODEL_SIZE)
t0 = time.time()
model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
print(f"[whisper-ptt] model loaded in {time.time()-t0:.1f}s")
print(f"[whisper-ptt] HOLD [{HOTKEY.upper()}] to record. Release to transcribe.")
print(f"[whisper-ptt] Press [{QUIT_HOTKEY.upper()}] to quit.")

recording, key_held = False, False
press_timer, stream = None, None
audio_buffer = []
state_lock = threading.Lock()
tray_icon = None

def make_icon(color):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((8, 8, 56, 56), fill=color)
    return img

ICON_IDLE         = make_icon((140, 140, 140, 255))
ICON_RECORDING    = make_icon((50, 200, 80, 255))
ICON_TRANSCRIBING = make_icon((60, 130, 230, 255))

def set_icon_state(state):
    if tray_icon is None: return
    if state == "idle":
        tray_icon.icon = ICON_IDLE
        tray_icon.title = "Whisper PTT \u2014 idle"
    elif state == "recording":
        tray_icon.icon = ICON_RECORDING
        tray_icon.title = "Whisper PTT \u2014 recording"
    elif state == "transcribing":
        tray_icon.icon = ICON_TRANSCRIBING
        tray_icon.title = "Whisper PTT \u2014 transcribing"

def quit_app(icon=None, item=None):
    print("[whisper-ptt] quit")
    try:
        if tray_icon is not None: tray_icon.stop()
    except Exception: pass
    import os; os._exit(0)

def audio_callback(indata, frames, time_info, status):
    if recording: audio_buffer.append(indata.copy())

def start_recording():
    global recording, audio_buffer, stream
    with state_lock:
        if recording: return
        audio_buffer = []
        try:
            stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=audio_callback)
            stream.start()
        except Exception as e:
            print(f"[whisper-ptt] mic open error: {e}")
            stream = None
            return
        recording = True
    set_icon_state("recording")
    print("[whisper-ptt] recording...", flush=True)

def stop_and_transcribe():
    global recording, stream
    with state_lock:
        if not recording: return
        recording = False
        local_stream = stream
        stream = None
        buf = audio_buffer[:]
    if local_stream is not None:
        try:
            local_stream.stop(); local_stream.close()
        except Exception as e:
            print(f"[whisper-ptt] stream close warn: {e}")
    if not buf:
        print("[whisper-ptt] no audio"); set_icon_state("idle"); return
    audio = np.concatenate(buf, axis=0).flatten().astype(np.float32)
    duration = len(audio) / SAMPLE_RATE
    if duration < MIN_DURATION:
        print(f"[whisper-ptt] too short ({duration:.2f}s)"); set_icon_state("idle"); return
    set_icon_state("transcribing")
    print(f"[whisper-ptt] {duration:.1f}s -> transcribing...", flush=True)
    t0 = time.time()
    try:
        segments, _ = model.transcribe(audio, language=LANGUAGE, beam_size=1, vad_filter=True)
        text = " ".join(s.text.strip() for s in segments).strip()
    except Exception as e:
        print(f"[whisper-ptt] transcribe error: {e}"); set_icon_state("idle"); return
    elapsed = time.time() - t0
    print(f"[whisper-ptt] {elapsed:.2f}s -> {text!r}")
    if not text: set_icon_state("idle"); return
    paste_text(text + PASTE_SUFFIX)
    set_icon_state("idle")

def paste_text(text):
    try: prev = pyperclip.paste()
    except Exception: prev = None
    pyperclip.copy(text)
    time.sleep(0.05)
    keyboard.press_and_release("ctrl+v")
    if prev is not None:
        def restore():
            time.sleep(0.4)
            try: pyperclip.copy(prev)
            except Exception: pass
        threading.Thread(target=restore, daemon=True).start()

def _maybe_start_recording():
    if key_held: start_recording()

def on_press(e):
    global key_held, press_timer
    if not key_held:
        key_held = True
        press_timer = threading.Timer(HOLD_THRESHOLD, _maybe_start_recording)
        press_timer.start()

def on_release(e):
    global key_held, press_timer
    if key_held:
        key_held = False
        if press_timer is not None:
            press_timer.cancel(); press_timer = None
        threading.Thread(target=stop_and_transcribe, daemon=True).start()

keyboard.on_press_key(HOTKEY, on_press, suppress=False)
keyboard.on_release_key(HOTKEY, on_release, suppress=False)
keyboard.add_hotkey(QUIT_HOTKEY, quit_app)

threading.Thread(target=keyboard.wait, daemon=True).start()
print("[whisper-ptt] ready.")

tray_icon = pystray.Icon(
    "whisper-ptt", ICON_IDLE, "Whisper PTT \u2014 idle",
    menu=pystray.Menu(
        pystray.MenuItem("Whisper PTT (hold Left Shift)", None, enabled=False),
        pystray.MenuItem("Quit", quit_app),
    ),
)
tray_icon.run()
