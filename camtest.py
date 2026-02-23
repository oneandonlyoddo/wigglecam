#!/usr/bin/python3
from picamera2 import Picamera2, Preview
import time

camera = Picamera2()

try:
    camera.configure(camera.create_preview_configuration())
    camera.start_preview(Preview.DRM)
    camera.start()
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    camera.stop_preview()
    camera.stop()
    camera.close()
    print("Camera preview stopped gracefully.")
except Exception as e:
    camera.stop_preview()
    camera.stop()
    camera.close()
    print(f"Error starting camera preview: {e}")