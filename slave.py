#!/usr/bin/python3
from flask import Flask, send_file
import threading
from picamera2 import Picamera2
import RPi.GPIO as GPIO
import os
from settings import *

os.makedirs("./tmp", exist_ok=True)

app = Flask(__name__)
camera = Picamera2()
camera.configure(camera.create_still_configuration())
camera.start()

latest_image = None

def wait_for_trigger():
    global latest_image
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_TRIGGER_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    while True:
        GPIO.wait_for_edge(GPIO_TRIGGER_PIN, GPIO.RISING)
        latest_image = "./tmp/captured.jpg"
        camera.capture_file(latest_image)
        print("Image captured!")

@app.route('/get_image')
def get_image():
    if latest_image:
        return send_file(latest_image, mimetype='image/jpeg')
    return "No image yet", 404

# Start trigger listener in background
threading.Thread(target=wait_for_trigger, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)