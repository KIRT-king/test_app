import cv2
import face_recognition
import getpass
import pickle
import time
import asyncio
import subprocess
import os

# from log_p import create_log

PATH_TO_ENCODINGS_SAVE = "encodings"
CAMERA_ID = 0

cap = cv2.VideoCapture(CAMERA_ID)

global user_name
user_name = input()

# def get_current_user():
#     global username
#     try:
#         result = subprocess.run(['who'], stdout=subprocess.PIPE, text=True)
#         if result.stdout:
#             first_line = result.stdout.splitlines()[0]
#             username = first_line.split()[0]
#             return username
#         else:
#             raise ValueError("Can't define user.")
#     except Exception as e:
#         raise RuntimeError(f"Error during definition: {e}")

async def CompareWithUser(img):
    global user_name
    file_path = PATH_TO_ENCODINGS_SAVE + "/" + user_name + ".pkl"

    faceCurFrame = face_recognition.face_locations(img)
    encodeCurFrame = face_recognition.face_encodings(img, faceCurFrame)

    if not encodeCurFrame:
        print("Ошибка: Лицо не найдено на изображении!")
        return None

    if not os.path.exists(file_path):
        print(f"Ошибка: Файл {file_path} не найден!")
        return None

    with open(file_path, "rb") as f:
        real_encodings = pickle.load(f)

    if not isinstance(real_encodings, list) or len(real_encodings) == 0:
        print("Ошибка: Файл энкодингов пуст или содержит некорректные данные!")
        return None

    user_encoding = encodeCurFrame[0]
    result = face_recognition.compare_faces(real_encodings, user_encoding)
    return result


async def main():
    count = 0
    max_images = 5
    interval = 2
    kol = 0

    start_time = time.time()

    while count < max_images:
        _, img = cap.read()
        imgS = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        if time.time() - start_time >= interval:
            res = await CompareWithUser(imgS)
            print(res)
            if res is not None:
                if res[0]:
                    kol += 1
                    print("good")
                else:
                    kol -= 1
                    print("bad")
                count += 1
            start_time = time.time()

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    if kol < 0:
        # create_log("Session exit")
        import os
        os.system("gnome-session-quit --logout --no-prompt")
    else:
        print("success")
        # create_log("check completed")
        # user_name = getpass.getuser()
        # from db_async.commands import update_user_last_enter
        # await update_user_last_enter(user_name)

    if 'cap' in globals() and cap:
        cap.release()
    cv2.destroyAllWindows()

asyncio.run(main())