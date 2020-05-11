#!/usr/bin/env python
import time
import logging
import threading
import copy

from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit
from PIL import Image, ImageDraw
from io import BytesIO, StringIO


class ImageSource(object):
    def __init__(self):
        self.image_lock = threading.Lock()
        self.image = None
        self.i = 0
        self.new_image = threading.Event()
        t = threading.Thread(target=self.generate_new_images)
        t.start()

    def generate_new_images(self):
        """Generate an image this can take sometime..."""
        i = 0
        while True:
            i += 1
            image = Image.new("RGB", (300, 50))
            draw = ImageDraw.Draw(image)
            draw.text((0, 0), str(i))

            img_io = BytesIO()
            image.save(img_io, 'JPEG', quality=70)
            img_io.seek(0)
            with self.image_lock:
                self.image = img_io.read()
            print("Updated image")
            self.new_image.set()
            time.sleep(10)

    def get_frame(self):
        while True:
            if self.new_image.wait(1):
                with self.image_lock:
                    frame = self.image

                    if frame is None:
                        continue

                    emint(frame)
                    yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            # TODO check for shutdown


app = Flask(__name__)
image_source = ImageSource()
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    res = Response(image_source.get_frame(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
    return res

@socketio.on('message')
def handle_message(message):
    print('received message: ' + message)

@socketio.on('my event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))
    print(image_source.get_frame())

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
