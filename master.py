#!/usr/bin/python3
import time
import os
import glob
import requests
from flask import Flask, send_file, render_template, redirect, url_for
from picamera2 import Picamera2, Preview
import RPi.GPIO as GPIO
from settings import *
import threading

SLAVE_IPS = ['192.168.0.162']

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_TRIGGER_PIN, GPIO.OUT)
GPIO.output(GPIO_TRIGGER_PIN, GPIO.LOW)
GPIO.setup(GPIO_SHUTTER_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


camera = Picamera2()
camera.configure(camera.create_still_configuration())
camera.start()

os.makedirs(IMAGE_SAVE_PATH, exist_ok=True)

app = Flask(__name__)

def generate_filename(camera_id):
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return os.path.join(IMAGE_SAVE_PATH, f"capture_{camera_id}_{timestamp}.jpg")

def capture_synchronized():
    print("Triggering capture...")
    # Trigger all cameras including self
    GPIO.output(GPIO_TRIGGER_PIN, GPIO.HIGH)
    file_names = []
    for i in range(len(SLAVE_IPS) + 1):
        file_names.append(generate_filename(i))
    camera.capture_file(file_names[0])
    time.sleep(0.05)  # 50ms pulse
    GPIO.output(GPIO_TRIGGER_PIN, GPIO.LOW)
    # Wait for captures to complete
    time.sleep(1)

    # Collect images from slaves
    for i, ip in enumerate(SLAVE_IPS):
        try:
            print(f"Fetching from slave {i+1}...")
            response = requests.get(f'http://{ip}:5000/get_image', timeout=5)
            path = os.path.join(file_names[i+1])
            with open(path, 'wb') as f:
                f.write(response.content)
            print(f"Saved {path}")
        except Exception as e:
            print(f"Error fetching from slave {i+1}: {e}")

    print("All images collected!")

def shutter_listener():
    while True:
        GPIO.wait_for_edge(GPIO_SHUTTER_PIN, GPIO.RISING)
        time.sleep(GPIO_DEBOUNCE_TIME)  # debounce
        capture_synchronized()

@app.route('/capture', methods=['POST'])
def capture():
    capture_synchronized()
    return redirect(url_for('gallery'))

@app.route('/images/<filename>')
def serve_image(filename):
    return send_file(os.path.join(IMAGE_SAVE_PATH, filename), mimetype='image/jpeg')

@app.route('/')
def gallery():
    images = sorted(
        (os.path.basename(f) for f in glob.glob(os.path.join(IMAGE_SAVE_PATH, '*.jpg'))),
        reverse=True
    )
    return render_template('gallery.html', images=images)

# Start trigger listener in background
threading.Thread(target=shutter_listener, daemon=True).start()

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        GPIO.cleanup()
