#!/usr/bin/env python
import time
import logging
import threading
import copy
import base64

from flask import Flask, render_template, Response
from PIL import Image, ImageDraw
from io import BytesIO, StringIO
from flask_socketio import SocketIO, emit

class ImageSource(object):
    def __init__(self):
        self.image_lock = threading.Lock()
        self.image = None
        self.i = 0
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
            time.sleep(0.1)

    def get_frame(self):
        while True:
            time.sleep(1)
            with self.image_lock:
                frame = self.image

                if frame is not None:
                    print("emitting frame")
                    emit('image', {"image": True, "buffer": frame})

app = Flask(__name__)
image_source = ImageSource()
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handle_message(message):
    print('received message: ' + str(message))
    image_source.get_frame()


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)
