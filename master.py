#!/usr/bin/python3
import time
import os
import glob
import requests
from flask import Flask, send_file, render_template, redirect, url_for
from picamera2 import Picamera2
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
wiggler = WigglegramMaker()

def capture_synchronized():
    print("Triggering capture...")
    folder = os.path.join(IMAGE_SAVE_PATH, str(int(time.time())))
    os.makedirs(folder, exist_ok=True)

    GPIO.output(GPIO_TRIGGER_PIN, GPIO.HIGH)
    camera.capture_file(os.path.join(folder, "cam_0.jpg"))
    time.sleep(0.05)  # 50ms pulse
    GPIO.output(GPIO_TRIGGER_PIN, GPIO.LOW)
    time.sleep(1)

    for i, ip in enumerate(SLAVE_IPS):
        try:
            print(f"Fetching from slave {i+1}...")
            response = requests.get(f'http://{ip}:5000/get_image', timeout=5)
            path = os.path.join(folder, f"cam_{i+1}.jpg")
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

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_file(os.path.join(IMAGE_SAVE_PATH, filename), mimetype='image/jpeg')

@app.route('/')
def gallery():
    subfolders = sorted(glob.glob(os.path.join(IMAGE_SAVE_PATH, '*/')), reverse=True)
    groups = []
    for folder in subfolders:
        name = os.path.basename(os.path.normpath(folder))
        imgs = sorted(os.path.relpath(f, IMAGE_SAVE_PATH) for f in glob.glob(os.path.join(folder, '*.jpg')))
        if imgs:
            groups.append({'name': name, 'images': imgs})
    return render_template('gallery.html', groups=groups)

# Start trigger listener in background
threading.Thread(target=shutter_listener, daemon=True).start()

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        GPIO.cleanup()
