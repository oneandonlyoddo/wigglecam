#!/usr/bin/python3
import time

from picamera2 import Picamera2, Preview
import RPi.GPIO as GPIO
from settings import *

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_TRIGGER_PIN, GPIO.OUT)
GPIO.output(GPIO_TRIGGER_PIN, GPIO.LOW)

camera = Picamera2()
camera.configure(camera.create_still_configuration())
camera.start()

def generate_filename(camera_id):
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return f"capture_{camera_id}_{timestamp}.jpg"

def capture_synchronized():
    print("Triggering capture...")
    # Trigger all cameras including self
    GPIO.output(GPIO_TRIGGER_PIN, GPIO.HIGH)
    camera.capture_file(generate_filename(0))
    time.sleep(0.05)  # 50ms pulse
    GPIO.output(GPIO_TRIGGER_PIN, GPIO.LOW)
    # Wait for captures to complete
    time.sleep(1)

if __name__ == '__main__':
    try:
        capture_synchronized()
    finally:
        GPIO.cleanup()