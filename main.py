import firebase_admin
from firebase_admin import credentials, db, storage

import os
import pickle
import cv2
import cvzone
import face_recognition
import numpy as np

from datetime import datetime

from flask import Flask, render_template, Response

#from flask_socketio import SocketIO

app = Flask(__name__)

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL':'https://facerecognition-41dc8-default-rtdb.asia-southeast1.firebasedatabase.app/',
    'storageBucket':"facerecognition-41dc8.appspot.com"
    })

bucket = storage.bucket()
imageStudent = []

modePath = 'Interface/modes'
modePathList = os.listdir(modePath)
modeList = []
for path in modePathList:
    modeList.append(cv2.imread(os.path.join(modePath, path)))


def gen_camera():
    cap = cv2.VideoCapture(0)  # open Camera (order of cam)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # 0 (onTime), 1 (alraedy), 2 (notFound), 3 (mark), 4 (default), 5 (late)
    modeType = 4
    counter = 0 # count fram for change mode 
    id = -1
    checkMatche = 0
 
    # SETTING TIME #
    late = True
    alreadyCheck = False
    now = datetime.now()
    # morning class
    mr0900 = now.replace(hour = 9, minute = 0, second = 0)
    mr0915 = now.replace(hour = 9, minute = 15, second = 59)
    endClass1 = now.replace(hour = 12, minute = 00, second = 00)
    # afternoon class
    af1300 = now.replace(hour = 13, minute = 0, second = 0)
    af1315 = now.replace(hour = 13, minute = 15, second = 59)
    mid = now.replace(hour = 23, minute = 59, second = 59)

    file = open('EncodeFace.p', 'rb')
    encodeListandID = pickle.load(file)
    file.close()

    matchIndex = -1

    encodeFaceList, studentIDList = encodeListandID
    while True:
        success, image = cap.read()
        imageResize = cv2.resize(image, (0, 0), None, 0.25, 0.25)
        imageResize = cv2.cvtColor(imageResize, cv2.COLOR_BGR2RGB)

        faceCurrent = face_recognition.face_locations(imageResize)
        encodeNewface = face_recognition.face_encodings(imageResize, faceCurrent, num_jitters=10, model="cnn")

        #frame
        for top, right, bottom, left in faceCurrent:
            cv2.rectangle(image, (left * 4, top * 4), (right * 4, bottom * 4), (0, 0, 255), 2)
        ret, buffer = cv2.imencode('.jpg', image)
        if not ret:
            break
        image = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + image + b'\r\n')
        
        for encodeFace, faceLocation in zip(encodeNewface, faceCurrent):
            matches = face_recognition.compare_faces(encodeFaceList, encodeFace, tolerance=0.4)
            faceDistance = face_recognition.face_distance(encodeFaceList, encodeFace)
            matchIndex = np.argmin(faceDistance)

            if matches[matchIndex]:
                y1, x2, y2, x1 = faceLocation
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4

                # setting point for frame dectect
                bbox = 45 + x1, 162 + y1, x2 - x1, y2 - y1

                id = studentIDList[matchIndex]
            
                studentInfo = db.reference(f'Students/{id}').get()
                if studentInfo['day'] != '0':
                    beforeDay = datetime.strptime(studentInfo['day'], "%d/%m/%Y")
                    lastChecking = datetime.strptime(studentInfo['check the time'], "%H:%M")
                    today = now.strftime("%d/%m/%Y")
                    if (beforeDay.strftime("%d/%m/%Y") == today and 
                        (mr0900.strftime("%H:%M") <= lastChecking.strftime("%H:%M")  <= endClass1.strftime("%H:%M") 
                        or af1300.strftime("%H:%M") <= lastChecking.strftime("%H:%M") <= mid.strftime("%H:%M"))):
                        modeType = 1
                        checkMatche = 0
                        counter = 1
                if counter == 0:
                    modeType = 0
                    counter = 1
                    checkMatche = 1
    
        if counter != 0 and checkMatche != 0:
            if counter == 1:
                ref = db.reference(f'Students/{id}')
                day = datetime.now().strftime("%d/%m/%Y")
                ref.child('day').set(day)

                now = datetime.now()
                checkingTime = now.strftime("%H:%M")
                ref.child('check the time').set(checkingTime)

                if mr0900 <= now <= mr0915 or af1300 <= now <= af1315:
                    late = False

                studentInfo['total attendance'] = str(int(studentInfo['total attendance']) + 1)
                ref.child('total attendance').set(studentInfo['total attendance'])
                if 'rate attendance' not in studentInfo:
                    studentInfo['rate attendance'] = 0
                if late == True:
                    studentInfo['rate attendance'] = str(int(studentInfo['rate attendance']) + 1)
                    ref.child('rate attendance').set(studentInfo['rate attendance'])
   


@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_camera(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/adjustdata', methods=['POST'])
def adjustData():
    return render_template("adjustData.html")

@app.route('/display', methods=['POST'])
def displayData():
    try:
        ref = db.reference('Students')
        data = ref.get()
   
        return render_template('displayData.html', data=data)
    except Exception as e:
        return f'Error: {str(e)}' 

@app.route('/importFile', methods=['POST'])
def importFile():
    return render_template('importfiles.html')

@app.route('/camera', methods=['POST'])
def camera():
    return render_template('camera.html')
    
if __name__ == "__main__":
    app.run(debug=True)