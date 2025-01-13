import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import getpass
import face_recognition
import pickle
from tkinter import messagebox

CAMERA_ID = 0
NAME = "SECUX"
FONT_SIZE_H1 = 36
FONT_1 = "Arial Bold"

PATH_TO_EMOJI_HANDS = "emoji/hands.png"
PATH_TO_ENCODINGS_SAVE = "encodings"

def start_camera():
    global cap, photo
    cap = cv2.VideoCapture(CAMERA_ID)

    def update_frame():
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)

                video_frame = ctk.CTkImage(light_image=img, size=(900, 900))
                video_label.configure(image=video_frame)
            video_label.after(10, update_frame)

    update_frame()

def exit_window():
    app.destroy()


def save_face_encodings(image, save_path):
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    face_encoding = face_recognition.face_encodings(img)
    if len(face_encoding) == 1:
        user_name = getpass.getuser()
        path = save_path + "/" + user_name + ".pkl"
        print(path)
        with open(path, "wb") as f:
            pickle.dump(face_encoding, f)
        return True
    elif len(face_encoding) > 1:
        messagebox.showerror("Error", "Too many faces")
    else:
        messagebox.showerror("Error", "Detected faces - 0")

def capture_photo():
    if cap and cap.isOpened():
        ret, frame_image = cap.read()
        if ret:
            answer = save_face_encodings(frame_image, PATH_TO_ENCODINGS_SAVE)
            print(answer)
            if answer:
                for widget in frame.winfo_children():
                    widget.destroy()
                frame.configure(fg_color="white")
                bt_start.configure(text = "Выход", command=exit_window)

                success_label = ctk.CTkLabel(frame,
                                             text="Фотография успешно сделана!",
                                             font=(FONT_1, FONT_SIZE_H1),
                                             text_color="green")
                success_label.pack(expand=True)

                cap.release()


def toggle_camera_action():
    if bt_start.cget("text") == "Сканировать":
        start_camera()
        bt_start.configure(text="Сделать фото", command=capture_photo)
    elif bt_start.cget("text") == "Сделать фото":
        capture_photo()

app = ctk.CTk()
app.geometry("1200x1200")
app.resizable(False, False)
app.title("Registaration Script")

emoji_welcome = ctk.CTkImage(light_image=Image.open(PATH_TO_EMOJI_HANDS),
                             dark_image=Image.open(PATH_TO_EMOJI_HANDS),
                             size=(60, 60))

label_emoji_welcome1 = ctk.CTkLabel(app, image=emoji_welcome, text="")
label_emoji_welcome2 = ctk.CTkLabel(app, image=emoji_welcome, text="")
label_emoji_welcome1.place(x=25, y=40)
label_emoji_welcome2.place(x=1115, y=40)

label_welcome = ctk.CTkLabel(app, text=f"Добро пожаловать в настройки дистрибутива {NAME}!",
                             font=(FONT_1, FONT_SIZE_H1))
label_welcome.pack(padx=40, pady=40)

frame = ctk.CTkFrame(app, width=900, height=900, fg_color="white")
frame.pack(padx=40)
frame.pack_propagate(False)

settings_label = ctk.CTkLabel(frame,
                              text="Нажмите на кнопку ниже",
                              font=(FONT_1, FONT_SIZE_H1),
                              text_color="black")
settings_label.pack(expand=True)

video_label = ctk.CTkLabel(frame, text="")
video_label.pack(fill="both", expand=True)

bt_start = ctk.CTkButton(app,
                         width=400,
                         height=20,
                         text="Сканировать",
                         font=(FONT_1, FONT_SIZE_H1),
                         command=toggle_camera_action)
bt_start.pack(pady=30)
app.mainloop()

if 'cap' in globals() and cap:
    cap.release()
cv2.destroyAllWindows()
