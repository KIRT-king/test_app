import os
import subprocess
import asyncio
import re

import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import getpass
import face_recognition
import pickle
from tkinter import messagebox

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

CAMERA_ID = 0
NAME = "SECUX"

FONT_SIZE_H1 = 36
FONT_1 = "Arial Bold"

FONT_SIZE_H2 = 36

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_TO_EMOJI_HANDS = os.path.join(CURRENT_DIR, "../resources/emoji/hands.png")
PATH_TO_ENCODINGS_SAVE = os.path.join(CURRENT_DIR, "../encodings")
if not os.path.exists(PATH_TO_EMOJI_HANDS):
    raise FileNotFoundError(f"Файл не найден: {PATH_TO_EMOJI_HANDS}")

corporate_app = None
settings_app = None

def open_corporate():
    global corporate_app
    if corporate_app is None:
        corporate_app = ctk.CTkToplevel(main_app)
    if corporate_app.winfo_exists():
        corporate_app.withdraw()
    else:
        print("Окно уже уничтожено, пропускаем withdraw.")
    main_app.withdraw()
    create_corporate_window()

def open_local():
    main_app.withdraw()
    create_local_window()

def create_local_window():
    global  local_app
    local_app = ctk.CTkToplevel(main_app)
    local_app.title("Корпоративная регистрация")
    local_app.resizable(False, False)

    def return_to_main():
        local_app.destroy()
        main_app.deiconify()

    def get_current_user():
        try:
            result = subprocess.run(['who'], stdout=subprocess.PIPE, text=True)
            if result.stdout:
                first_line = result.stdout.splitlines()[0]
                username = first_line.split()[0]
                return username
            else:
                raise ValueError("Can't define user.")
        except Exception as e:
            raise RuntimeError(f"Error during definition: {e}")

    def create_file(name, data):
        name = "user/" + name
        if not os.path.exists(name):
            try:
                with open(name, 'w') as file:
                    file.write(data)
                print("File created")
                return True
            except Exception as e:
                print(f"File hasn't been created {e}")
                return False
        else:
            return "user_already_exists"

    def create_user_system(full_name : str, username : str, password : str, data):
        try:
            subprocess.run(
                ["useradd", "-m", "-c", full_name, username],
                check=True,
                text=True
            )

            subprocess.run(
                ["bash", "-c", f"echo -e \"{password}\\n{password}\" | passwd {username}"],
                check=True,
                text=True
            )
            create_file(get_current_user(), data)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при выполнении команды: {e}")
            return False
        except Exception as e:
            print(f"Непредвиденная ошибка: {e}")
            return False

    def check_valid_input_user_form(full_name, username, password, check_password, user_real_name, user_last_name, user_post, user_email, user_phone_number):

        only_english_regex = r"^[A-Za-z]+$"
        if (
                not re.match(only_english_regex, full_name) or
                not re.match(only_english_regex, username) or
                not re.match(only_english_regex, user_real_name) or
                not re.match(only_english_regex, user_last_name) or
                not re.match(only_english_regex, user_post)
        ):
            messagebox.showerror("Invalid Format", "Please, use only latin letters")
            return "invalid_letters"


        if len(username) < 3:
            entry_name.delete(0, ctk.END)
            entry_name.configure(placeholder_text="Username is too short (min 3 characters)", placeholder_text_color="red")
            return "short_username"

        if not username.isalnum():
            entry_full_name.delete(0, ctk.END)
            entry_full_name.configure(placeholder_text="Username must contain only letters and numbers",
                                 placeholder_text_color="red")
            return "invalid_username"

        if len(password) < 8:
            entry_password.delete(0, ctk.END)
            entry_check_password.delete(0, ctk.END)
            entry_password.configure(placeholder_text="very short password", placeholder_text_color="red")
            return "short password"

        if password != check_password:
            entry_password.delete(0, ctk.END)
            entry_check_password.delete(0, ctk.END)
            entry_check_password.configure(placeholder_text="passwords are different", placeholder_text_color="red")
            return "passwords are different"

        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if not re.match(email_regex, user_email):
            entry_user_email.delete(0, ctk.END)
            entry_user_email.configure(placeholder_text="Invalid email format", placeholder_text_color="red")
            return "invalid_email"

        phone_regex = r"^\+?[1-9][0-9]{7,14}$"
        if not re.match(phone_regex, user_phone_number):
            entry_user_phone_number.delete(0, ctk.END)
            entry_user_phone_number.configure(placeholder_text="Invalid phone number", placeholder_text_color="red")
            return "invalid_phone_number"

        if not full_name or not username or not password or not check_password or not user_real_name or not user_last_name or not user_post or not user_email or not user_phone_number:
            return "fields_empty"

        return True

    label_full_name = ctk.CTkLabel(local_app, text=f"Полное имя", font=(FONT_1, FONT_SIZE_H2))
    label_name = ctk.CTkLabel(local_app, text=f"Имя пользователя", font=(FONT_1, FONT_SIZE_H2))
    label_password = ctk.CTkLabel(local_app, text=f"Пароль", font=(FONT_1, FONT_SIZE_H2))
    label_check_password = ctk.CTkLabel(local_app, text=f"Пароль(проверка)", font=(FONT_1, FONT_SIZE_H2))
    label_info_user_inputs = ctk.CTkLabel(local_app, text=f"Поля для ввода лич. инф.", font=(FONT_1, FONT_SIZE_H2))
    label_user_name = ctk.CTkLabel(local_app, text=f"Ваше имя", font=(FONT_1, FONT_SIZE_H2))
    label_user_last_name = ctk.CTkLabel(local_app, text=f"Ваша фамилия", font=(FONT_1, FONT_SIZE_H2))
    label_user_post = ctk.CTkLabel(local_app, text=f"Ваша должность", font=(FONT_1, FONT_SIZE_H2))
    label_user_email = ctk.CTkLabel(local_app, text=f"Ваш email", font=(FONT_1, FONT_SIZE_H2))
    label_user_phone_number = ctk.CTkLabel(local_app, text=f"Ваш номер телефона", font=(FONT_1, FONT_SIZE_H2))

    entry_full_name = ctk.CTkEntry(local_app, font=(FONT_1, FONT_SIZE_H2), width=500)
    entry_name = ctk.CTkEntry(local_app, font=(FONT_1, FONT_SIZE_H2), width=500)
    entry_password = ctk.CTkEntry(local_app, font=(FONT_1, FONT_SIZE_H2), width=500)
    entry_check_password = ctk.CTkEntry(local_app, font=(FONT_1, FONT_SIZE_H2), width=500)
    entry_user_name = ctk.CTkEntry(local_app, font=(FONT_1, FONT_SIZE_H2), width=500)
    entry_user_last_name = ctk.CTkEntry(local_app, font=(FONT_1, FONT_SIZE_H2), width=500)
    entry_user_post = ctk.CTkEntry(local_app, font=(FONT_1, FONT_SIZE_H2), width=500)
    entry_user_email = ctk.CTkEntry(local_app, font=(FONT_1, FONT_SIZE_H2), width=500)
    entry_user_phone_number = ctk.CTkEntry(local_app, font=(FONT_1, FONT_SIZE_H2), width=500)

    label_full_name.grid(row=2, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
    entry_full_name.grid(row=2, column=2, columnspan=2, padx=10, pady=10, sticky="w")

    label_name.grid(row=3, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
    entry_name.grid(row=3, column=2, columnspan=2, padx=10, pady=10, sticky="w")

    label_password.grid(row=4, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
    entry_password.grid(row=4, column=2, columnspan=2, padx=10, pady=10, sticky="w")

    label_check_password.grid(row=5, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
    entry_check_password.grid(row=5, column=2, columnspan=2, padx=10, pady=10, sticky="w")

    label_info_user_inputs.grid(row=6, column=0, columnspan=2, padx=(100, 10), pady=(50, 10), sticky="w")

    label_user_name.grid(row=7, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
    entry_user_name.grid(row=7, column=2, columnspan=2, padx=10, pady=10, sticky="w")

    label_user_last_name.grid(row=8, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
    entry_user_last_name.grid(row=8, column=2, columnspan=2, padx=10, pady=10, sticky="w")

    label_user_post.grid(row=9, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
    entry_user_post.grid(row=9, column=2, columnspan=2, padx=10, pady=10, sticky="w")

    label_user_email.grid(row=10, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
    entry_user_email.grid(row=10, column=2, columnspan=2, padx=10, pady=10, sticky="w")

    label_user_phone_number.grid(row=11, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
    entry_user_phone_number.grid(row=11, column=2, columnspan=2, padx=10, pady=10, sticky="w")

    def add_user_local(full_name, username, password, check_password, user_real_name, user_last_name, user_post,
                          user_email, user_phone_number):
        validation_result = check_valid_input_user_form(full_name, username, password, check_password, user_real_name,
                                                        user_last_name, user_post, user_email, user_phone_number)
        print(validation_result)
        if validation_result != True:
            return
        data = f"1\n{username} {user_real_name} {user_last_name} {user_post} {user_email} {user_phone_number}"
        if create_user_system(username, full_name, password, data):
            for widget in local_app.winfo_children():
                widget.destroy()
            second_part(username)
        else:
            messagebox.showerror("User error", "Something went wrong. Try again.")

    def on_button_next_page_click():
        full_name = entry_full_name.get()
        username = entry_name.get()
        password = entry_password.get()
        check_password = entry_check_password.get()
        user_real_name = entry_user_name.get()
        user_last_name = entry_user_last_name.get()
        user_post = entry_user_post.get()
        user_email = entry_user_email.get()
        user_phone_number = entry_user_phone_number.get()

        add_user_local(full_name, username, password, check_password, user_real_name, user_last_name, user_post, user_email, user_phone_number)

    bt_next = ctk.CTkButton(local_app,
                            text="Дальше",
                            font=(FONT_1, FONT_SIZE_H1),
                            command=on_button_next_page_click)
    bt_next.grid(row=12, column=0, columnspan=2, pady=(40, 40), padx=(100, 10), sticky="nswe")

    bt_back = ctk.CTkButton(local_app, text="Назад", font=(FONT_1, FONT_SIZE_H2), command=return_to_main)
    bt_back.grid(row=12, column=0, columnspan=2, pady=(40, 40), padx=(100, 20), sticky="nswe")
    bt_next.grid(row=12, column=2, columnspan=2, pady=(40, 40), padx=(20, 100), sticky="nswe")

    def second_part(username):

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

        def save_face_encodings(image, save_path, user_name):
            img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            face_encoding = face_recognition.face_encodings(img)
            if len(face_encoding) == 1:
                path = save_path + "/" + user_name + ".pkl"
                print(path)
                with open(path, "wb") as f:
                    pickle.dump(face_encoding, f)
                return True
            elif len(face_encoding) > 1:
                messagebox.showerror("Error", "Too many faces")
            else:
                messagebox.showerror("Error", "Detected faces - 0")

        def exit_window():
            local_app.destroy()
            main_app.destroy()

        def capture_photo():
            if cap and cap.isOpened():
                ret, frame_image = cap.read()
                if ret:
                    answer = save_face_encodings(frame_image, PATH_TO_ENCODINGS_SAVE,username)
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
                        success_label.grid(row=0, column=0, pady=(10, 20))
                        cap.release()

        def toggle_camera_action():
            if bt_start.cget("text") == "Сканировать":
                start_camera()
                bt_start.configure(text="Сделать фото", command=capture_photo)
            elif bt_start.cget("text") == "Сделать фото":
                capture_photo()

        frame = ctk.CTkFrame(local_app, width=900, height=900, fg_color="white")
        frame.grid(row=0, column=0, padx=40, pady=(100, 20))
        frame.grid_propagate(False)

        settings_label = ctk.CTkLabel(frame,
                                      text="Нажмите на кнопку ниже",
                                      font=(FONT_1, FONT_SIZE_H1),
                                      text_color="black")
        settings_label.grid(row=0, column=0, pady=(10, 20), sticky="nsew")

        video_label = ctk.CTkLabel(frame, text="")
        video_label.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        bt_start = ctk.CTkButton(local_app,
                                 width=400,
                                 height=20,
                                 text="Сканировать",
                                 font=(FONT_1, FONT_SIZE_H1),
                                 command=toggle_camera_action)
        bt_start.grid(row=2, column=0, pady=50, sticky="nsew")


def create_corporate_window():
    global corporate_app
    corporate_app = ctk.CTkToplevel(main_app)
    corporate_app.title("Корпоративная регистрация")
    corporate_app.resizable(False, False)

    def return_to_main():
        corporate_app.destroy()
        main_app.deiconify()

    def open_settings_window():
        global settings_app, corporate_app
        if settings_app is None:
            settings_app = ctk.CTkToplevel(corporate_app)
        if settings_app.winfo_exists():
            settings_app.withdraw()
        else:
            print("Окно уже уничтожено, пропускаем withdraw.")
        create_settings_window()

    def create_settings_window():
        global settings_app, corporate_app
        settings_app = ctk.CTkToplevel(corporate_app)
        settings_app.title("Настройки ⚙️")
        settings_app.resizable(False, False)

        def return_to_main():
            settings_app.destroy()
            corporate_app.deiconify()

        def check_connection(ip_address):
            import socket
            port = 5432
            try:
                with socket.create_connection((ip_address, port)):
                    bt_server_ip.configure(text = "Active", fg_color = "lime")
            except (socket.timeout, socket.error) as e:
                print(f"Ошибка подключения: {e}")
                bt_server_ip.configure(text = "Disactive", fg_color = "red")

        def open_confirmation_window(db_user, db_user_password, db_ip, db_name):
            print(db_user, db_user_password, db_ip, db_name)
            if db_user != "" and db_user_password != "" and db_ip != "" and db_name != "":
                confirmation_app = ctk.CTkToplevel(settings_app)
                confirmation_app.title("Подтверждение")

                def manage_env_file(db_url):
                    try:
                        parent_dir = os.path.dirname(os.getcwd())
                        env_file_path = os.path.join(parent_dir, ".env")
                        if not os.path.exists(env_file_path):
                            with open(env_file_path, "w") as env_file:
                                env_file.write(f"DATABASE_URL={db_url}\n")
                        else:
                            with open(env_file_path, "r") as env_file:
                                lines = env_file.readlines()
                            lines = [line for line in lines if not line.startswith("DATABASE_URL")]
                            lines.append(f'DATABASE_URL="{db_url}"\n')
                            with open(env_file_path, "w") as env_file:
                                env_file.writelines(lines)

                    except Exception as e:
                        messagebox.showerror("Error", f"Something went wrong: {e}")

                def close_windows(db_user, db_user_password, db_ip, db_name):
                    connection_string = f"postgresql+asyncpg://{db_user}:{db_user_password}@{db_ip}/{db_name}"
                    manage_env_file(connection_string)
                    settings_app.destroy()
                    confirmation_app.destroy()

                def cancel_changes():
                    confirmation_app.destroy()

                label = ctk.CTkLabel(confirmation_app,
                                     text="Вы уверены, что хотите сохранить изменения?",
                                     font=(FONT_1, FONT_SIZE_H2))
                btn_yes = ctk.CTkButton(confirmation_app,
                                        text="Да",
                                        font=(FONT_1, FONT_SIZE_H2),
                                        command=lambda: close_windows(db_user, db_user_password, db_ip, db_name))
                btn_no = ctk.CTkButton(confirmation_app,
                                       text="Нет",
                                       font=(FONT_1, FONT_SIZE_H2),
                                       command=cancel_changes)

                label.grid(row=0, column=0, columnspan=2, pady=20, padx=20)
                btn_yes.grid(row=1, column=0, padx=20, pady=20, sticky="ew")
                btn_no.grid(row=1, column=1, padx=20, pady=20, sticky="ew")
            else:
                messagebox.showerror("Ошибка", "Поля должны быть заполнены")

        label_db_user = ctk.CTkLabel(settings_app,
                                     text = "Имя пользователя в базе данных:",
                                     font = (FONT_1, FONT_SIZE_H2))
        entry_db_user = ctk.CTkEntry(settings_app,
                                    font=(FONT_1, FONT_SIZE_H2),
                                    placeholder_text="postgres"
                                    )
        label_db_user_password = ctk.CTkLabel(settings_app,
                                     text="Пароль пользователя в базе данных:",
                                     font=(FONT_1, FONT_SIZE_H2))
        entry_db_user_password = ctk.CTkEntry(settings_app,
                                     font=(FONT_1, FONT_SIZE_H2)
                                     )
        label_server_ip = ctk.CTkLabel(settings_app,
                                       text="Проверка подключения:",
                                       font=(FONT_1, FONT_SIZE_H2))
        entry_server_ip = ctk.CTkEntry(settings_app,
                                       font=(FONT_1, FONT_SIZE_H2),
                                       placeholder_text="192.168.100.59"
                                       )
        bt_server_ip = ctk.CTkButton(settings_app,
                                     width = 210,
                                     text="Проверить",
                                     font=(FONT_1, FONT_SIZE_H2),
                                     command=lambda : check_connection(entry_server_ip.get()))
        label_db_name = ctk.CTkLabel(settings_app,
                                     text="Название базы данных:",
                                     font=(FONT_1, FONT_SIZE_H2))
        entry_db_name = ctk.CTkEntry(settings_app,
                                     font=(FONT_1, FONT_SIZE_H2))

        bt_save_changes = ctk.CTkButton(settings_app,
                                        text="Сохранить изменения",
                                        font=(FONT_1, FONT_SIZE_H2),
                                        command=lambda: open_confirmation_window(entry_db_user.get(), entry_db_user_password.get(),
                                                                                 entry_server_ip.get(), entry_db_name.get())
                                        )

        label_db_user.grid(row = 0, column = 0, padx = (30, 10), pady = (50, 10), sticky = "w")
        entry_db_user.grid(row = 0, column = 1, padx = (10, 30), pady = (50, 10), sticky = "w", ipadx = 80)
        label_db_user_password.grid(row=1, column=0, padx=(30, 10), pady=(50, 10), sticky="w")
        entry_db_user_password.grid(row=1, column=1, padx=(10, 30), pady=(50, 10), sticky="w", ipadx = 80)
        label_server_ip.grid(row = 2, column = 0, padx = (30, 10), pady = 30, sticky = "w")
        entry_server_ip.grid(row = 2, column = 1, padx = (10, 10), pady = 30, sticky = "NSEW", ipadx = 80)
        bt_server_ip.grid(row = 2, column = 2, padx = (10, 30), pady = 30, sticky = "e")
        label_db_name.grid(row=3, column=0, padx=(30, 10), pady=(50, 10), sticky="w")
        entry_db_name.grid(row=3, column=1, padx=(10, 30), pady=(50, 10), sticky="w", ipadx = 80)
        bt_save_changes.grid(row = 4, column = 0, columnspan = 3, pady = (50, 60), padx = (100, 100), sticky = "NSEW")


    settings_button = ctk.CTkButton(corporate_app,
                                    text = "Настройки ⚙️",
                                    font = (FONT_1, FONT_SIZE_H2),
                                    command=create_settings_window)
    settings_button.grid(row=0, column=3, padx=(10, 5), pady = 30, ipadx = 5)


    #1 part

    label_full_name = ctk.CTkLabel(corporate_app, text = f"Полное имя", font= (FONT_1, FONT_SIZE_H2))
    label_name = ctk.CTkLabel(corporate_app, text = f"Имя пользователя", font= (FONT_1, FONT_SIZE_H2))
    label_password = ctk.CTkLabel(corporate_app, text = f"Пароль", font= (FONT_1, FONT_SIZE_H2))
    label_check_password = ctk.CTkLabel(corporate_app, text = f"Пароль(проверка)", font= (FONT_1, FONT_SIZE_H2))
    label_info_user_inputs = ctk.CTkLabel(corporate_app, text = f"Поля для ввода лич. инф.", font= (FONT_1, FONT_SIZE_H2))
    label_user_name = ctk.CTkLabel(corporate_app, text = f"Ваше имя", font= (FONT_1, FONT_SIZE_H2))
    label_user_last_name = ctk.CTkLabel(corporate_app, text = f"Ваша фамилия", font= (FONT_1, FONT_SIZE_H2))
    label_user_post = ctk.CTkLabel(corporate_app, text = f"Ваша должность", font= (FONT_1, FONT_SIZE_H2))
    label_user_email = ctk.CTkLabel(corporate_app, text = f"Ваш email", font= (FONT_1, FONT_SIZE_H2))
    label_user_phone_number = ctk.CTkLabel(corporate_app, text = f"Ваш номер телефона", font= (FONT_1, FONT_SIZE_H2))

    entry_full_name = ctk.CTkEntry(corporate_app, font= (FONT_1, FONT_SIZE_H2), width= 500)
    entry_name = ctk.CTkEntry(corporate_app, font= (FONT_1, FONT_SIZE_H2), width= 500)
    entry_password = ctk.CTkEntry(corporate_app, font= (FONT_1, FONT_SIZE_H2), width= 500)
    entry_check_password = ctk.CTkEntry(corporate_app, font= (FONT_1, FONT_SIZE_H2), width= 500)
    entry_user_name = ctk.CTkEntry(corporate_app, font= (FONT_1, FONT_SIZE_H2), width= 500)
    entry_user_last_name = ctk.CTkEntry(corporate_app, font= (FONT_1, FONT_SIZE_H2), width= 500)
    entry_user_post = ctk.CTkEntry(corporate_app, font= (FONT_1, FONT_SIZE_H2), width= 500)
    entry_user_email = ctk.CTkEntry(corporate_app, font= (FONT_1, FONT_SIZE_H2), width= 500)
    entry_user_phone_number = ctk.CTkEntry(corporate_app, font= (FONT_1, FONT_SIZE_H2), width= 500)

    label_full_name.grid(row=2, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
    entry_full_name.grid(row=2, column=2, columnspan=2, padx=10, pady=10, sticky="w")

    label_name.grid(row=3, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
    entry_name.grid(row=3, column=2, columnspan=2, padx=10, pady=10, sticky="w")

    label_password.grid(row=4, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
    entry_password.grid(row=4, column=2, columnspan=2, padx=10, pady=10, sticky="w")

    label_check_password.grid(row=5, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
    entry_check_password.grid(row=5, column=2, columnspan=2, padx=10, pady=10, sticky="w")

    label_info_user_inputs.grid(row = 6, column = 0, columnspan=2, padx=(100, 10), pady=(50, 10), sticky="w")

    label_user_name.grid(row=7, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
    entry_user_name.grid(row=7, column=2, columnspan=2, padx=10, pady=10, sticky="w")

    label_user_last_name.grid(row=8, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
    entry_user_last_name.grid(row=8, column=2, columnspan=2, padx=10, pady=10, sticky="w")

    label_user_post.grid(row=9, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
    entry_user_post.grid(row=9, column=2, columnspan=2, padx=10, pady=10, sticky="w")

    label_user_email.grid(row=10, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
    entry_user_email.grid(row=10, column=2, columnspan=2, padx=10, pady=10, sticky="w")

    label_user_phone_number.grid(row=11, column=0, columnspan=2, padx=(100, 10), pady=10, sticky="w")
    entry_user_phone_number.grid(row=11, column=2, columnspan=2, padx=10, pady=10, sticky="w")

    def get_current_user():
        try:
            result = subprocess.run(['who'], stdout=subprocess.PIPE, text=True)
            if result.stdout:
                first_line = result.stdout.splitlines()[0]
                username = first_line.split()[0]
                return username
            else:
                raise ValueError("Can't define user.")
        except Exception as e:
            raise RuntimeError(f"Error during definition: {e}")

    def create_file(name, data):
        name = "user/" + name
        if not os.path.exists(name):
            try:
                with open(name, 'w') as file:
                    file.write(data)
                print("File created")
                return True
            except Exception as e:
                print(f"File hasn't been created {e}")
                return False
        else:
            return "user_already_exists"

    def create_user_system(full_name : str, username : str, password : str, data):
        try:
            subprocess.run(
                ["useradd", "-m", "-c", full_name, username],
                check=True,
                text=True
            )

            subprocess.run(
                ["bash", "-c", f"echo -e \"{password}\\n{password}\" | passwd {username}"],
                check=True,
                text=True
            )
            create_file(get_current_user(), data)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при выполнении команды: {e}")
            return False
        except Exception as e:
            print(f"Непредвиденная ошибка: {e}")
            return False

    def check_valid_input_user_form(full_name, username, password, check_password, user_real_name, user_last_name, user_post, user_email, user_phone_number):

        only_english_regex = r"^[A-Za-z]+$"
        if (
                not re.match(only_english_regex, full_name) or
                not re.match(only_english_regex, username) or
                not re.match(only_english_regex, user_real_name) or
                not re.match(only_english_regex, user_last_name) or
                not re.match(only_english_regex, user_post)
        ):
            messagebox.showerror("Invalid Format", "Please, use only latin letters")
            return "invalid_letters"


        if len(username) < 3:
            entry_name.delete(0, ctk.END)
            entry_name.configure(placeholder_text="Username is too short (min 3 characters)", placeholder_text_color="red")
            return "short_username"

        if not username.isalnum():
            entry_full_name.delete(0, ctk.END)
            entry_full_name.configure(placeholder_text="Username must contain only letters and numbers",
                                 placeholder_text_color="red")
            return "invalid_username"

        if len(password) < 8:
            entry_password.delete(0, ctk.END)
            entry_check_password.delete(0, ctk.END)
            entry_password.configure(placeholder_text="very short password", placeholder_text_color="red")
            return "short password"

        if password != check_password:
            entry_password.delete(0, ctk.END)
            entry_check_password.delete(0, ctk.END)
            entry_check_password.configure(placeholder_text="passwords are different", placeholder_text_color="red")
            return "passwords are different"

        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if not re.match(email_regex, user_email):
            entry_user_email.delete(0, ctk.END)
            entry_user_email.configure(placeholder_text="Invalid email format", placeholder_text_color="red")
            return "invalid_email"

        phone_regex = r"^\+?[1-9][0-9]{7,14}$"
        if not re.match(phone_regex, user_phone_number):
            entry_user_phone_number.delete(0, ctk.END)
            entry_user_phone_number.configure(placeholder_text="Invalid phone number", placeholder_text_color="red")
            return "invalid_phone_number"

        if not full_name or not username or not password or not check_password or not user_real_name or not user_last_name or not user_post or not user_email or not user_phone_number:
            return "fields_empty"

        return True

    async def add_user_db(full_name, username, password, check_password, user_real_name, user_last_name, user_post, user_email, user_phone_number):
        validation_result = check_valid_input_user_form(full_name, username, password, check_password, user_real_name, user_last_name, user_post, user_email, user_phone_number)
        print(validation_result)
        if validation_result != True:
            return

        from db.commands import check_user_exist, create_user
        username_f, email_f = await check_user_exist(username, user_email)

        if username_f:
            messagebox.showerror("User error", "User already exists in the system")
        elif email_f:
            messagebox.showerror("User error", "Email already exists in the system")
        else:
            user_created = await create_user(username, user_real_name, user_last_name, user_post, user_email, user_phone_number)
            if user_created:

                data = f"1\n{username} {user_real_name} {user_last_name} {user_post} {user_email} {user_phone_number}"
                if create_user_system(username, full_name, password, data):
                    for widget in corporate_app.winfo_children():
                        widget.destroy()
                    second_part(username)
                else:
                    messagebox.showerror("User error", "Something went wrong. Try again.")
            else:
                messagebox.showerror("Error", "Failed to create user")

    def on_button_next_page_click():
        full_name = entry_full_name.get()
        username = entry_name.get()
        password = entry_password.get()
        check_password = entry_check_password.get()
        user_real_name = entry_user_name.get()
        user_last_name = entry_user_last_name.get()
        user_post = entry_user_post.get()
        user_email = entry_user_email.get()
        user_phone_number = entry_user_phone_number.get()

        asyncio.run(add_user_db(full_name, username, password, check_password, user_real_name, user_last_name, user_post, user_email, user_phone_number))

    bt_next = ctk.CTkButton(corporate_app,
                             text="Дальше",
                             font=(FONT_1, FONT_SIZE_H1),
                             command=on_button_next_page_click)
    bt_next.grid(row=12, column = 0, columnspan = 2, pady= (40, 40), padx = (100, 10), sticky="nswe")

    bt_back = ctk.CTkButton(corporate_app, text="Назад", font=(FONT_1, FONT_SIZE_H2), command=return_to_main)
    bt_back.grid(row=12, column = 0, columnspan = 2, pady = (40, 40), padx = (100, 20), sticky="nswe")
    bt_next.grid(row=12, column = 2, columnspan = 2, pady = (40, 40), padx = (20, 100), sticky="nswe")

    #2 part
    def second_part(username):

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

        def save_face_encodings(image, save_path, user_name):
            img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            face_encoding = face_recognition.face_encodings(img)
            if len(face_encoding) == 1:
                path = save_path + "/" + user_name + ".pkl"
                print(path)
                with open(path, "wb") as f:
                    pickle.dump(face_encoding, f)
                return True
            elif len(face_encoding) > 1:
                messagebox.showerror("Error", "Too many faces")
            else:
                messagebox.showerror("Error", "Detected faces - 0")

        def exit_window():
            corporate_app.destroy()
            main_app.destroy()

        def capture_photo():
            if cap and cap.isOpened():
                ret, frame_image = cap.read()
                if ret:
                    answer = save_face_encodings(frame_image, PATH_TO_ENCODINGS_SAVE,username)
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
                        success_label.grid(row=0, column=0, pady=(10, 20))
                        cap.release()

        def toggle_camera_action():
            if bt_start.cget("text") == "Сканировать":
                start_camera()
                bt_start.configure(text="Сделать фото", command=capture_photo)
            elif bt_start.cget("text") == "Сделать фото":
                capture_photo()

        frame = ctk.CTkFrame(corporate_app, width=900, height=900, fg_color="white")
        frame.grid(row=0, column=0, padx=40, pady=(100, 20))
        frame.grid_propagate(False)

        settings_label = ctk.CTkLabel(frame,
                                      text="Нажмите на кнопку ниже",
                                      font=(FONT_1, FONT_SIZE_H1),
                                      text_color="black")
        settings_label.grid(row=0, column=0, pady=(10, 20), sticky="nsew")

        video_label = ctk.CTkLabel(frame, text="")
        video_label.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        bt_start = ctk.CTkButton(corporate_app,
                                 width=400,
                                 height=20,
                                 text="Сканировать",
                                 font=(FONT_1, FONT_SIZE_H1),
                                 command=toggle_camera_action)
        bt_start.grid(row=2, column=0, pady=50, sticky="nsew")

main_app = ctk.CTk()
main_app.title("Главное окно")
main_app.resizable(False, False)

global emoji_welcome
emoji_welcome = ctk.CTkImage(
    light_image=Image.open(PATH_TO_EMOJI_HANDS),
    dark_image=Image.open(PATH_TO_EMOJI_HANDS),
    size=(60, 60)
)

label_emoji_welcome1 = ctk.CTkLabel(corporate_app, image=emoji_welcome, text="")
label_emoji_welcome2 = ctk.CTkLabel(corporate_app, image=emoji_welcome, text="")


label_welcome = ctk.CTkLabel(corporate_app, text=f"Добро пожаловать в настройки дистрибутива {NAME}!",
                             font=(FONT_1, FONT_SIZE_H1))

label_emoji_welcome1.grid(row=1, column=0, padx=(40, 10), pady=(50, 50), sticky="e")
label_welcome.grid(row=1, column=1, columnspan=2, padx=(10, 10), pady=(50, 50), sticky="nsew")
label_emoji_welcome2.grid(row=1, column=3, padx=(10, 40), pady=(50, 50), sticky="w")

label_main = ctk.CTkLabel(main_app, text="Выберите режим регистрации", font=(FONT_1, FONT_SIZE_H1))
label_main.grid(row = 2, column = 0, columnspan = 4, padx = (100, 100), pady = (20, 20))

bt_corporate = ctk.CTkButton(main_app, text="Корпоративно", font=(FONT_1, FONT_SIZE_H2), command=open_corporate)
bt_corporate.grid(row = 3, column = 0, columnspan = 2, padx = (50, 20), pady = (20, 100), ipadx = 50)

bt_local = ctk.CTkButton(main_app, text="Локально", font=(FONT_1, FONT_SIZE_H2), command=open_local)
bt_local.grid(row = 3, column = 2, columnspan = 2, padx = (50, 20), pady = (20, 100), ipadx = 50)

main_app.mainloop()

if 'cap' in globals() and cap:
    cap.release()
cv2.destroyAllWindows()
