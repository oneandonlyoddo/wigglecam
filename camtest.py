from picamera2 import Picamera2, Preview

camera = Picamera2()
camera.configure(camera.create_still_configuration())
running = True
WIDTH, HEIGHT = (800, 600)  # Set the desired width and height for the previw

try:
    while running:
      camera.start_preview(Preview.DRM, x=0, y=0, width=, height=HEIGHT)
      camera.start()
except KeyboardInterrupt:
  running = False
  camera.stop_preview()
  camera.stop()
  camera.close()
  print("Camera preview stopped gracefully.")
except Exception as e:
  camera.stop_preview()
  camera.stop()
  camera.close()
  print(f"Error starting camera preview: {e}")
    