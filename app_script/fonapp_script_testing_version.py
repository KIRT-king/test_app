import cv2
from tkinter import messagebox
import subprocess
import pickle
import face_recognition
import time

from log import create_log
from utils import print_name

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


PATH_TO_ENCODINGS_SAVE = "encodings"
PATH_TO_LOGS_SAVE = "logs" #you can put nothing, I mean "" and your logs will be saved in system dir or put not - they will not be saved anywhere

#log messages
CHECK_SUCCESS = "The checking was successful"
CHECK_FAILED = "The checking was failed"

CAMERA_ID = 0
KOL_IMAGES = 5 #how many photos will take script
INTERVAL = 2 #interval between photos

def find_active_camera_index():
    global CAMERA_ID
    for i in range(1, 11):
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                CAMERA_ID = i
                break
        except Exception:
            pass

    if CAMERA_ID == 0:
        messagebox.showerror("Ошибка | Error", "Камера не найдена\nCamera has not been found")

def get_current_user():
    # try:
    #     result = subprocess.run(['who'], stdout=subprocess.PIPE, text=True)
    #     if result.stdout:
    #         first_line = result.stdout.splitlines()[0]
    #         username = first_line.split()[0]
    #         return username
    #     else:
    #         raise ValueError("Can't define user.")
    # except Exception as e:
    #     raise RuntimeError(f"Error during definition: {e}")
    import getpass
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        return sudo_user
    try:
        import psutil
        users = psutil.users()
        for user in users:
            if user.name != "root":
                return user.name
        if users:
            return users[0].name
    except ImportError:
        print("psutil не установлен. Для более корректного определения активного пользователя установите psutil.")
    return getpass.getuser()

def CompareWithUser(img, user_name):
    file_path = PATH_TO_ENCODINGS_SAVE + "/" + user_name + ".pkl"
    encodeCurFrame = face_recognition.face_encodings(img)
    if not encodeCurFrame:
        return None
    with open(file_path, "rb") as f:
        real_encodings = pickle.load(f)
    if not isinstance(real_encodings, list) or len(real_encodings) == 0:
        return None
    user_encoding = encodeCurFrame[0]
    res = face_recognition.compare_faces(real_encodings, user_encoding)
    return res

def main():
    print_name()
    try:
        cap = cv2.VideoCapture(CAMERA_ID)
        if cap.isOpened():
            pass
        else:
            find_active_camera_index()

        start_time = time.time()
        count = 0
        kol = 0
        no_face_start_time = None
        print(get_current_user())
        user_name = input("Введите имя пользователя для сравнения: ")
        logs_save = input("Введите путь к файлу, в который нужно сохранить логи (press Enter/not/default): ")
        global PATH_TO_LOGS_SAVE
        if logs_save == "not":
            PATH_TO_LOGS_SAVE = "not"
        elif logs_save == "":
            PATH_TO_LOGS_SAVE = ""

        while count < KOL_IMAGES:
            _, img = cap.read()
            imgS = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            current_time = time.time()
            if time.time() - start_time >= INTERVAL:
                res = CompareWithUser(imgS, user_name)
                if res is None:
                    if no_face_start_time is None:
                        no_face_start_time = current_time
                    elif current_time - no_face_start_time >= 15:
                        print("Блокировка: Лицо не обнаружено более 15 секунд!")
                        if PATH_TO_LOGS_SAVE != "not":
                            create_log(PATH_TO_LOGS_SAVE, "BLOCKED: no face detected for 15 seconds")
                        cap.release()
                        sys.exit()
                else:
                    no_face_start_time = None
                    if res[0]:
                        kol += 1
                        print("good")
                    else:
                        kol -= 1
                        print("bad")
                    count += 1
                start_time = time.time()

        if kol < 0:
            cap.release()
            if PATH_TO_LOGS_SAVE != "not":
                create_log(PATH_TO_LOGS_SAVE, CHECK_FAILED)
            print("The owner isn't you!")
        else:
            cap.release()
            env_file_path = os.path.join(os.getcwd(), ".env")
            if os.path.exists(env_file_path):
                from db.commands import update_user_last_enter, test_db_connection
                print(test_db_connection())
                try:
                    print(user_name)
                    update_user_last_enter(user_name)
                except:
                    print("Connect to db!")
            if PATH_TO_LOGS_SAVE != "not":
                create_log(PATH_TO_LOGS_SAVE, CHECK_SUCCESS)
            print("Owner is similar to you")
    except Exception as e:
        print(f"Trouble {e}")

main()