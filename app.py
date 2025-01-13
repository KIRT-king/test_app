import os

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

FONT_SIZE_H2 = 36


PATH_TO_EMOJI_HANDS = "emoji/hands.png"
PATH_TO_ENCODINGS_SAVE = "encodings"

def exit_window():
    app.destroy()

app = ctk.CTk()
app.geometry("1200x1200")
app.resizable(False, False)
app.title("Registaration Script")

emoji_welcome = ctk.CTkImage(light_image=Image.open(PATH_TO_EMOJI_HANDS),
                             dark_image=Image.open(PATH_TO_EMOJI_HANDS),
                             size=(60, 60))

label_emoji_welcome1 = ctk.CTkLabel(app, image=emoji_welcome, text="")
label_emoji_welcome2 = ctk.CTkLabel(app, image=emoji_welcome, text="")


label_welcome = ctk.CTkLabel(app, text=f"Добро пожаловать в настройки дистрибутива {NAME}!",
                             font=(FONT_1, FONT_SIZE_H1))

label_emoji_welcome1.grid(row=0, column=0, padx=(40, 10), pady=(20, 50), sticky="e")
label_welcome.grid(row=0, column=1, columnspan=2, padx=(10, 10), pady=(20, 50), sticky="nsew")
label_emoji_welcome2.grid(row=0, column=3, padx=(10, 40), pady=(20, 50), sticky="w")



#1 part

label_full_name = ctk.CTkLabel(app, text = f"Полное имя", font= (FONT_1, FONT_SIZE_H2))
label_name = ctk.CTkLabel(app, text = f"Имя пользователя", font= (FONT_1, FONT_SIZE_H2))
label_password = ctk.CTkLabel(app, text = f"Пароль", font= (FONT_1, FONT_SIZE_H2))
label_check_password = ctk.CTkLabel(app, text = f"Пароль(проверка)", font= (FONT_1, FONT_SIZE_H2))

entry_full_name = ctk.CTkEntry(app, font= (FONT_1, FONT_SIZE_H2), width= 500)
entry_name = ctk.CTkEntry(app, font= (FONT_1, FONT_SIZE_H2), width= 500)
entry_password = ctk.CTkEntry(app, font= (FONT_1, FONT_SIZE_H2), width= 500)
entry_check_password = ctk.CdTkEntry(app, font= (FONT_1, FONT_SIZE_H2), width= 500)

label_full_name.grid(row=1, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
entry_full_name.grid(row=1, column=2, columnspan=2, padx=10, pady=10, sticky="w")

label_name.grid(row=2, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
entry_name.grid(row=2, column=2, columnspan=2, padx=10, pady=10, sticky="w")

label_password.grid(row=3, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
entry_password.grid(row=3, column=2, columnspan=2, padx=10, pady=10, sticky="w")

label_check_password.grid(row=4, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
entry_check_password.grid(row=4, column=2, columnspan=2, padx=10, pady=10, sticky="w")

def create_new_user(full_name, username, password, check_password):
    command = f"useradd -m {username} -c \"{full_name}\""
    os.system(command)
    command = f"echo -e \"{password}\\n{password}\" | passwd {username}"
    os.system(command)
    return True

def on_button_next_page_click():
    full_name = entry_full_name.get()
    username = entry_name.get()
    password = entry_password.get()
    check_password = entry_check_password.get()
    f = True
    if len(password) < 8:
        f = False
        entry_password.configure(placeholder_text="very short password", placeholder_text_color="red")
    if password != check_password:
        f = False
        entry_password.delete(0, ctk.END)
        entry_check_password.delete(0, ctk.END)
        entry_check_password.configure(placeholder_text="passwords are different", placeholder_text_color="red")
    if full_name != "" and username != "" and password != "" and check_password != "":
        if f:
            if create_new_user(full_name, username, password, check_password):
                for widget in app.winfo_children():
                    widget.destroy()
                second_part()
        else:
            print("Пароли не совпадают.")
    else:
        print("Данные не введены")

bt_next = ctk.CTkButton(app,
                         width=400,
                         height=20,
                         text="Дальше",
                         font=(FONT_1, FONT_SIZE_H1),
                         command=on_button_next_page_click)
bt_next.place(x = 400, y = 600)

#2 part
def second_part():

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
                    bt_start.configure(text="Выход", command=exit_window)

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

    frame = ctk.CTkFrame(app, width=900, height=900, fg_color="white")
    frame.pack(padx=40, pady = (100, 20))
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


print("hello world")