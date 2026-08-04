# Brixy (Desktop)

Always-on Windows background voice assistant — wake word diye activate hoy, tarpor
command ke AI (LLM) ke pathay, LLM function-calling er madhyome system er upor
control pay (predefined, safe function set diye — arbitrary command run kore na).

## Ei Stage e Ki Ache (Foundation)

Eই version e **shudhu wake-word listener + tray app** — pipeline er "always-on,
battery-efficient" onshoTa. Porer stage e add hobe: STT capture, LLM function-calling
loop, ar dispatcher (system control functions).

```
src/brixy/
    config.py         -> shob environment/settings ekhane
    logging_utils.py   -> file-based logger (background service e print() kaje lagbe na)
    audio_utils.py      -> mic stream wrapper (sounddevice)
    wake_word.py        -> Porcupine-based always-on listener (background thread)
    pipeline.py          -> stub: wake word detect hole ki hobe (porer step e STT/LLM boshbe)
    tray.py                -> system tray icon, "Exit" menu
    main.py                -> shobkichu wire kore, entry point
```

## Setup (Windows e run korar jonno)

### 1. `uv` install (na thakle)
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Dependencies install
```powershell
cd brixy-desktop
uv sync
```

### 3. Picovoice Access Key nao
1. https://console.picovoice.ai e free account banao
2. "AccessKey" copy koro
3. `.env.example` ke `.env` name diye copy koro, tar moddhe `PICOVOICE_ACCESS_KEY=` er
   pashe key paste koro

### 4. Test run (built-in wake word diye)
```powershell
uv run python -m brixy.main
```
Default e wake word `jarvis` — eta bole test koro. Console e "Wake word detected!"
dekhle mane thik ache.

### 5. Custom "Brixy" wake word train kora (optional, kintu recommended)
Built-in list e "brixy" nai, tai custom train korte hobe:
1. https://console.picovoice.ai e login kore "Porcupine" section e jao
2. "Train Wake Word" e "Brixy" likhe, platform hishebe **Windows** select koro
3. Generated `.ppn` file download koro
4. `.env` e `BRIXY_WAKE_WORD_PPN=C:\path\to\Brixy_en_windows.ppn` set koro

(Free tier e limited number of custom wake words train kora jay per month —
eta Picovoice er policy, tumi console e dekhte pabe.)

## Battery / Performance Notes

- **Idle state e** (wake word wait korar shomoy): shudhu mic + Porcupine model
  active — CPU usage typically 1-3% ekta core e, NIC/WiFi/network **kono
  touch e nai**.
- Wake word detect hole i shudhu porer stage (STT + LLM + network call) trigger
  hobe — eta already `pipeline.py` te design kora ache, porer step e implement hobe.
- `idle_unload_seconds` config (config.py e) diye — pipeline er heavy model
  (STT/LLM session) ekta nirdisto shomoy no-activity er por unload kore dewa
  jabe, memory/battery duitai bachbe. (Implement hobe pipeline stage e.)

## Startup e Auto-run + Packaging (Porer Step)

Ei stage e cover kora hoyni, kintu plan:
1. `pyinstaller --noconsole --onefile -n Brixy src/brixy/main.py`
2. Inno Setup script diye `.exe` ke installer e wrap kora, "Run at Windows
   startup" checkbox add kora — install hole
   `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` e registry entry add hobe

## Porer Step (Next Stage)

- `dispatcher.py`: allowlisted system functions (`open_app`, `close_app`,
  `list_processes`, `read_active_window`, `take_screenshot`, etc.)
- STT integration (`faster-whisper`, local)
- LLM client (function-calling / tool_use loop) — Claude ba OpenAI API
- TTS output (`pyttsx3` ba Edge TTS)
- `pipeline.py` er TODO gula fill up kora
