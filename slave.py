from picamera2 import Picamera2
import RPi.GPIO as GPIO
from settings import *

camera = Picamera2()
camera.configure(camera.create_still_configuration())
camera.start()

def wait_for_trigger():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_TRIGGER_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    while True:
        GPIO.wait_for_edge(GPIO_TRIGGER_PIN, GPIO.RISING)
        latest_image = "./tmp/captured.jpg"
        camera.capture_file(latest_image)
        print("Image captured!")

if __name__ == '__main__':
    try:
        wait_for_trigger()
    finally:
        GPIO.cleanup()