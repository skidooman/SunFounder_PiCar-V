import numpy as np
import cv2
import threading
import os
from flask import Flask, render_template, Response
from flask_sock import Sock
from multiprocessing import Process, Manager
import time
import datetime
from driver import camera, stream
import picar, json

app = Flask(__name__)
sock = Sock(app)

@app.route('/')
def index():
    """Video streaming home page."""
    #return 'Hello'
    return render_template('index.html')

def gen():
    """Video streaming generator function."""
    print ('gen accessed')
    while True:  

        frame = cv2.imencode('.jpg', Vilib.img_array[0])[1].tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


in_motion = 0

@sock.route('/socket')
def socket(sock):
    # These are globals for the camera, back wheels (move the car) and the front wheels (steering)
    db_file = "remote_control/driver/config"
    motion = picar.back_wheels.Back_Wheels(debug=False, db=db_file)
    steering = picar.front_wheels.Front_Wheels(debug=False, db=db_file)
    
    print ('socket activated ')
    while True:
        print ('Socket waiting for instructions')
        data = sock.receive()
        print ('Socket received: %s' % data)
        myDict = json.loads(data)
        
        # Calling setup systematically before issuing low-level calls seems
        # to improve the stability
        picar.setup()

        # These are all the actions that concern the rear wheels
        # Essentially, the car can go forward, backward, stop or reset
        if myDict['action'] == 'forward':
           motion.forward()
           motion.speed = int(myDict['speed'])
        elif myDict['action'] == 'backward':
           motion.backward()
           motion.speed = int(myDict['speed'])
        elif myDict['action'] == 'stop':
           motion.stop()
           steering.turn_straight()
        elif myDict['action'] == 'reset':
           motion.ready()
           steering.reset()

           # Front wheels are in charge of direction (steering)
           # Valid values are left, right and straight
        if myDict['orientation'] == 'left':
           time.sleep(1)
           steering.turn_left()
        elif myDict['orientation'] == 'right':
           time.sleep(1)
           steering.turn_right()
        sock.send('done')

def socket_start():
   app.run(host='0.0.0.0', port=5001, threaded=True)


@sock.route('/cam_socket')
def socket_camera(sock):
   db_file = "remote_control/driver/config"
   cam = camera.Camera(debug=False, db=db_file)
   print ('cam socket activated')
   while True:
        print ('Cam socket waiting for instructions')
        data = sock.receive()
        print ('Cam socket received: %s' % data)
        myDict = json.loads(data)
        
        # Calling setup systematically before issuing low-level calls seems
        # to improve the stability
        picar.setup()

        # Camera activity here shall be (1) up or down and (2) left or right
        # There is also the reset case
        if myDict['vertical'] == 'up':
           cam.turn_up()
        elif myDict['vertical'] == 'down':
           cam.turn_down()
        elif myDict['vertical'] == 'reset':
           cam.ready()
        
        if myDict['horizontal'] == 'left':
           cam.turn_left()
        elif myDict['horizontal'] == 'right':
           cam.turn_right()
           
def socket_camera_start():
   app.run(host='0.0.0.0', port=5002, threaded=True)

@app.route('/mjpg')
def video_feed():
    # from camera import Camera
    """Video streaming route. Put this in the src attribute of an img tag."""
    print ('video feed accessed')
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame') 

def web_camera_start():
    app.run(host='0.0.0.0', port=8765,threaded=True)


def website_start():
    app.run(host='0.0.0.0', port=5000,threaded=True)


class Vilib(object): 

    video_source = 0

    detect_obj_parameter = Manager().dict()
    img_array = Manager().list(range(2))
    rt_img = np.ones((320,240),np.uint8)     
    img_array[0] = rt_img


    @staticmethod
    def camera_start(web_func = True):
        from multiprocessing import Process
       
        print ('video stream starts')
        worker_2 = Process(name='worker 2',target=Vilib.camera_clone)
        if web_func == True:
            worker_1 = Process(name='worker 1',target=web_camera_start)
            worker_1.start()
        worker_2.start()

        print ('sockets start')
        my_socket = Process(name='my_socket',target=socket_start)
        my_socket.start()
        cam_socket = Process(name='cam_socket', target=socket_camera_start)
        cam_socket.start()
        
        print ('Web site starts')
        my_website = Process(name='my_website', target=website_start)
        my_website.start()
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
    # Calling that method will instantiate three server ports too
    Vilib.camera_start()
   
    while True:
        pass
