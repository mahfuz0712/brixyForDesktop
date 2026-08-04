# Brixy (Desktop)

Always-on Windows background voice assistant — wake word diye activate hoy, tarpor
command ke AI (LLM) ke pathay, LLM function-calling er madhyome system er upor
control pay (predefined, safe function set diye — arbitrary command run kore na).

## Ei Stage e Ki Ache (Foundation)

Eই version e **shudhu wake-word listener + tray app** — pipeline er "always-on,
battery-efficient" onshoTa. Wake word engine: **openWakeWord** — fully offline,
open-source, kono account/API key/network lage na.

```
src/brixy/
    config.py         -> shob environment/settings ekhane
    logging_utils.py   -> file-based logger (background service e print() kaje lagbe na)
    audio_utils.py      -> mic stream wrapper (sounddevice)
    wake_word.py         -> openWakeWord-based always-on listener (background thread)
    pipeline.py           -> stub: wake word detect hole ki hobe (porer step e STT/LLM boshbe)
    tray.py                 -> system tray icon, "Exit" menu
    main.py                  -> shobkichu wire kore, entry point
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

### 3. Test run (bundled wake word diye — kono setup lage na)
```powershell
uv run python -m brixy.main
```
Default e wake word `hey_jarvis_v0.1` (package er shathei bundled model) — eta bole
test koro: **"Hey Jarvis"**. Log file (`%APPDATA%\Brixy\brixy.log`) e "Wake word
detected!" dekhle mane thik ache.

Onno bundled options try korte chaile `.env` e `BRIXY_WAKE_WORD_BUILTIN` change koro:
`alexa_v0.1`, `hey_mycroft_v0.1`, `hey_marvin_v0.1`, `timer_v0.1`, `weather_v0.1`

### 4. Custom "Brixy" wake word train kora (porer step, recommended)
openWakeWord er official Colab notebook diye custom wake word train kora jay —
**kono real voice recording lage na**, text-to-speech diye synthetic training data
generate kore:

1. Notebook: https://github.com/dscripka/openWakeWord (README e "Training New Models"
   section e Colab link ache)
2. Notebook e target phrase hishebe "Brixy" (ba "Hey Brixy") likhe run koro — eta
   TTS diye hajar hajar positive sample generate kore, background noise/negative
   sample er sathe mix kore, ekta choto CNN train kore
3. Output `.onnx` file download koro
4. `.env` e `BRIXY_WAKE_WORD_MODEL=C:\path\to\brixy.onnx` set koro (eta
   `BRIXY_WAKE_WORD_BUILTIN` ke override kore dibe)
5. Training e GPU free (Colab free tier) e mott 10-20 minute lagte pare

### 5. Threshold tune kora
`.env` e `BRIXY_WAKE_THRESHOLD` (default 0.5) — beshi hole false-positive kombe
kintu kokhono real wake word miss hote pare, kom hole ulto. Real-world e test kore
adjust koro.

## Battery / Performance Notes

- **Idle state e**: shudhu mic + openWakeWord model active. Real inference test
  kore dekha gyeche — protiti 80ms audio chunk process korte ~2.5-3.5ms lage
  (CPU e), mane practically ekta core er ~3-4% e thake, NIC/WiFi/network **kono
  touch e nai**.
- Model load hote (startup e) ~1.5 second lage — eta ekbar-i hoy, app start howar
  shomoy.
- Wake word detect hole i shudhu porer stage (STT + LLM + network call) trigger
  hobe — eta already `pipeline.py` te design kora ache, porer step e implement hobe.
- `idle_unload_seconds` config (config.py e, porer stage e use hobe) diye pipeline
  er heavy model (STT/LLM session) ekta nirdisto shomoy no-activity er por unload
  kore dewa jabe.

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