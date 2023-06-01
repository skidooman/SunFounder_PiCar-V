import numpy as np
import cv2
import threading
import os
from flask import Flask, render_template, Response
from flask_sock import Sock
from multiprocessing import Process, Manager
import time
import datetime
from .driver import camera, stream
from picar import back_wheels, front_wheels
import picar, json

app = Flask(__name__)
sock = Sock(app)

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

def gen():
    """Video streaming generator function."""
    while True:  

        frame = cv2.imencode('.jpg', Vilib.img_array[0])[1].tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

db_file = "remote_control/drive/config"
mycam = camera.Camera(debug=False, db=db_file)
motion = back_wheels.Back_Wheels(debug=True, db=db_file)
steering = front_wheels.Front_Wheels(debug=False, db=db_file)
myDict = {};
in_motion = 0;

@sock.route('/socket')
def socket(sock):
    print ('socket activated')
    print (sock)
    while True:
        print ('Socket waiting for instructions')
        data = sock.receive()
        print ('DATA: %s' % data)
        global myDict
        myDict = json.loads(data)
        #performActions(myDict, cam, motion, steering)
        processor = Process(name='processor',target=performActions)
        processor.start()
        #sock.send(counter)
        

def socket_start():
   app.run(host='0.0.0.0', port=5000, threaded=True)

def performActions():
   global mycam, motion, steering, myDict, in_motion
   print ('processing %s' % myDict)
   for entry in myDict:
        if type(entry) == str:
           entry = json.loads(entry)
        if entry['target'] == 'camera':
           if entry['action'] == 'up':
              mycam.turn_up(20)
           elif entry['action'] == 'down':
              mycam.turn_down(20)
           elif entry['action'] == 'left':
              mycam.turn_left(20)
           elif entry['action'] == "right":
              mycam.turn_right(20)
           elif entry['action'] == "reset":
              mycam.ready()
        elif entry['target'] == 'steering':
           if entry['action'] == 'turn_left':
              steering.turn_left()
           elif entry['action'] == 'turn_right':
              steering.turn_right()
           elif entry['action'] == 'reset':
              steering.ready()
        elif entry['target'] == 'motion':
           if entry['action'] == 'forward':
              motion.forward()
           elif entry['action'] == 'backward':
              motion.backward()

           elif entry['action'] == 'stop':
              motion.stop()
              in_motion = 0
           elif entry['action'] == 'reset':
              motion.ready()
              in_motion = 0
        elif entry['target'] == 'speed' and entry['action'] != '0' and in_motion == 0:
              print ('speed: %i' % int(entry['action']))
              motion._speed = int(entry['action'])
              ''' Set moving speeds '''
              motion.left_wheel.speed = motion._speed
              motion.right_wheel.speed = motion._speed
              print ('We are cruising!')
              #motion.set_speed(int(entry['action']))
              in_motion = 1 
        #time.sleep(0.2)
   print ('done with %s' % myDict)

@app.route('/mjpg')
def video_feed():
    # from camera import Camera
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame') 

def web_camera_start():
    app.run(host='0.0.0.0', port=8765,threaded=True)


class Vilib(object): 

    video_source = 0

    detect_obj_parameter = Manager().dict()
    img_array = Manager().list(range(2))
    rt_img = np.ones((320,240),np.uint8)     
    img_array[0] = rt_img


    @staticmethod
    def camera_start(web_func = True):
        from multiprocessing import Process
       
        worker_2 = Process(name='worker 2',target=Vilib.camera_clone)
        if web_func == True:
            worker_1 = Process(name='worker 1',target=web_camera_start)
            worker_1.start()
        worker_2.start()
        print ('sockets start')
        my_socket = Process(name='my_socket',target=socket_start)
        my_socket.start()
        #speed_socket = Process(name='my_second_socket', target=speed_socket_start)
        #speed_socket.start()
        print ('sockets started')

    
    @staticmethod
    def camera_clone():
        Vilib.camera()     

    @staticmethod
    def camera():
        print ('launching camera') 
        # This was working, but no more!
        #camera = cv2.VideoCapture(Vilib.video_source)
        camera = cv2.VideoCapture(Vilib.video_source, apiPreference=cv2.CAP_V4L2)
        print (camera)
        camera.set(3,320)
        camera.set(4,240)
        width = int(camera.get(3))
        height = int(camera.get(4))
        camera.set(cv2.CAP_PROP_BUFFERSIZE,1)
        cv2.setUseOptimized(True)
 

        while True:
            _, img = camera.read()

            Vilib.img_array[0] = img

if __name__ == "__main__":
    Vilib.camera_start()
    while True:
        pass
