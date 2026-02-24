# wigglecam

Multi-camera synchronized capture system for Raspberry Pi. Cameras are triggered simultaneously via a GPIO hardware pulse, eliminating network timing jitter. The master Pi hosts a minimal web gallery for browsing and triggering captures.

## How it works

One Pi acts as **master** — it fires a 50ms HIGH pulse on GPIO 27, captures its own image, then fetches images from each slave over HTTP. Each **slave** Pi listens for the RISING edge on GPIO 27 and captures immediately.

```
Master ──GPIO 27──┬── Slave 1
                  └── Slave N
```

## Quick start

**1. Install on each Pi**
```bash
sudo apt update && sudo apt install -y python3-picamera2 python3-flask git
git clone git@github.com:oneandonlyoddo/wigglecam.git
cd wigglecam
```

**2. Configure**

Edit `settings.py` to set GPIO pins. Edit `SLAVE_IPS` in `master.py` to list slave IP addresses.

**3. Run slaves first**
```bash
python3 slave.py
```

**4. Run master**
```bash
python3 master.py
```

Open `http://<master-ip>:5000` in a browser. Hit **Capture** to trigger all cameras.

Images are saved to `./DCIM` on the master.

## Test single camera
```bash
python3 camtest.py  # preview only, no GPIO required
```
