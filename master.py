#!/usr/bin/python3
import time
import requests
from picamera2 import Picamera2, Preview
import RPi.GPIO as GPIO
from settings import *

SLAVE_IPS = ['192.168.0.162']
# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_TRIGGER_PIN, GPIO.OUT)
GPIO.output(GPIO_TRIGGER_PIN, GPIO.LOW)

camera = Picamera2()
camera.configure(camera.create_still_configuration())
camera.start()

current_image_name = None

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

    # Collect images from slaves
    for i, ip in enumerate(SLAVE_IPS):
        try:
            print(f"Fetching from slave {i+1}...")
            response = requests.get(f'http://{ip}:5000/get_image', timeout=5)
            with open(f'slave_{i+1}.jpg', 'wb') as f:
                f.write(response.content)
            print(f"Saved slave_{i+1}.jpg")
        except Exception as e:
            print(f"Error fetching from slave {i+1}: {e}")
    
    print("All images collected!")

if __name__ == '__main__':
    try:
        capture_synchronized()
    finally:
        GPIO.cleanup()