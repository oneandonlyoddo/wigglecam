#!/usr/bin/python3
from picamera2 import Picamera2, Preview
import time

camera = Picamera2()

WIDTH, HEIGHT = (800, 600)  # Set the desired width and height for the preview

try:
    camera.configure(camera.create_still_configuration())
    camera.start_preview(Preview.DRM, x=0, y=0, width=WIDTH, height=HEIGHT)
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