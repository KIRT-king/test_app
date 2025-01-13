import cv2
import face_recognition
import getpass
import pickle
import time

from log_p import create_log


PATH_TO_ENCODINGS_SAVE = "encodings"
CAMERA_ID = 0

cap = cv2.VideoCapture(CAMERA_ID)

def CompareWithUser(img):
    user_name = getpass.getuser()
    file_path = PATH_TO_ENCODINGS_SAVE + "/" + user_name + ".pkl"

    faceCurFrame = face_recognition.face_locations(img)
    encodeCurFrame = face_recognition.face_encodings(img, faceCurFrame)
    if faceCurFrame:

        with open(file_path, "rb") as f:
            real_encodings = pickle.load(f)
        user_encoding = encodeCurFrame[0]
        result = face_recognition.compare_faces(real_encodings, user_encoding)
        return result

count = 0
max_images = 5
interval = 2
kol = 0

import time

start_time = time.time()

while count < max_images:
    _, img = cap.read()
    imgS = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    if time.time() - start_time >= interval:
        res = CompareWithUser(imgS)
        print(res)
        if res is not None:
            if res[0]:
                kol += 1
            else:
                kol -= 1
            count += 1
        start_time = time.time()

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

if kol < 0:
    create_log("Session exit")
    import os
    os.system("gnome-session-quit --logout --no-prompt")
else:
    create_log("check completed")

if 'cap' in globals() and cap:
    cap.release()
cv2.destroyAllWindows()