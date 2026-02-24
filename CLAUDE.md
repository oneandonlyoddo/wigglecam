# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wigglecam is a Raspberry Pi multi-camera synchronization system. Multiple Pis are wired together via GPIO for hardware-synchronized capture. The master Pi also runs a Flask web server for triggering captures and browsing results.

## Setup (on each Raspberry Pi)

```bash
sudo apt update
sudo apt install -y python3-picamera2 python3-flask git
git clone git@github.com:oneandonlyoddo/wigglecam.git
```

## Running

Test a single camera (preview only, no GPIO):
```bash
python3 camtest.py
```

On each slave Pi (start before master):
```bash
python3 slave.py
```

On the master Pi (serves gallery at `http://<master-ip>:5000`):
```bash
python3 master.py
```

## Architecture

```
Master Pi  ──GPIO 27 (OUT, 50ms HIGH pulse)──┬── Slave Pi 1 (GPIO 27 IN)
    │                                         └── Slave Pi N (GPIO 27 IN)
    │
    └── HTTP GET http://<slave-ip>:5000/get_image  (after capture)
```

- `settings.py` — single source of truth for GPIO pins (BCM), debounce timing, and `IMAGE_SAVE_PATH`. Imported via `*` in master and slave.
- `master.py` — Flask server on port 5000. `GET /` serves the image gallery. `POST /capture` fires the GPIO trigger pulse, captures the master image, then fetches images from each slave over HTTP. All images saved to `IMAGE_SAVE_PATH` (`./DCIM`). Slave IPs are configured in the `SLAVE_IPS` list at the top of the file.
- `slave.py` — Flask server on port 5000. GPIO trigger listener runs in a background thread (`wait_for_trigger`). On RISING edge, captures to `./tmp/captured.jpg` (overwrites each time). `GET /get_image` serves the latest capture to the master.
- `camtest.py` — standalone preview test, no GPIO; uses `Preview.DRM` (requires DRM display on the Pi).

## Key Notes

- All GPIO uses BCM numbering (`GPIO.setmode(GPIO.BCM)`). Trigger pin is GPIO 27.
- `GPIO_SHUTTER_PIN = 26` is defined in `settings.py` but not yet wired up — reserved for a future physical shutter button.
- `IMAGE_SAVE_PATH` (`./DCIM`) and `./tmp` are created automatically on startup.
- Slave images are fetched by the master after capture and saved with timestamped names into `IMAGE_SAVE_PATH`. The slave's own `./tmp/captured.jpg` is always overwritten.
- `picamera2` uses an internal asyncio event loop — never call `configure`, `start_preview`, or `start` inside a loop. Call them once at startup.
- Flask's development server is used (`app.run`). This is single-threaded, so the `/capture` route will block the server for ~1.05s during each capture cycle.

## SSH / Remote Dev

Add each Pi to `~/.ssh/config`:
```
Host [hostname]
  HostName 192.168.0.xxx
  Port 22
  User [username]
  IdentityFile [path/to/key]   # use \\ on Windows
```

Generate and push a key:
```bash
ssh-keygen -t ed25519
ssh-copy-id -i ~/.ssh/key.pub username@host
```
