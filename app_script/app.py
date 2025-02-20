#!/usr/bin/python3
import threading

import customtkinter as ctk
import cv2
from PIL import Image
from tkinter import StringVar
import face_recognition
import os
import pickle
import socket
import pwd
import re
import json
import subprocess
import shutil

from language import Locale

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv, find_dotenv

NAME = "KIRT app"
version = "1.3"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if not os.geteuid() == 0:
        os.execvp("/usr/bin/pkexec", ["/usr/bin/pkexec", CURRENT_DIR+"/"+sys.argv[0].split("/")[-1]])

def user_exists(username):
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False


def check_validation_fills(self):
    only_english_and_numbers_pattern = r"^[A-Za-z0-9]+$"
    password_pattern = r"^[A-Za-z\d!@#$%^&*()_+]{8,}$"
    email_pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    phone_pattern = r"^\+\d{12}$"
    if any(not str(var.get()).strip() for var in self.entry_vars.values()):
        show_notification(self, self.lang.error, self.lang.error_fields_not_fill)
        return False
    elif (
            not re.match(only_english_and_numbers_pattern, str(self.entry_vars["system_user_name"].get())) or
            not re.match(only_english_and_numbers_pattern, str(self.entry_vars["system_user_full_name"].get()))
    ):
        show_notification(self, self.lang.error, self.lang.error_only_latin_letters)
        return False
    elif len(str(self.entry_vars["system_user_name"].get())) < 3:
        show_notification(self, self.lang.error, self.lang.error_system_user_name_short)
        return False
    elif not re.match(password_pattern, str(self.entry_vars["system_password"].get())):
        show_notification(self, self.lang.error, self.lang.error_password_incorrect_type)
        return False
    elif str(self.entry_vars["system_password"].get()) != str(self.entry_vars["system_check_password"].get()):
        show_notification(self, self.lang.error, self.lang.error_system_password_check_different)
        return False
    elif not re.match(email_pattern, str(self.entry_vars["real_user_email"].get())):
        show_notification(self, self.lang.error, self.lang.error_email_incorrect_type)
        return False
    elif not re.match(phone_pattern, str(self.entry_vars["real_user_phone_number"].get())):
        show_notification(self, self.lang.error, self.lang.error_phone_incorrect_type)
        return False
    return True

def save_user_data(self):
    user_data = {key: str(var.get()).strip() for key, var in self.entry_vars.items()}
    username = user_data["system_user_name"]
    users_dir = "users"
    os.makedirs(users_dir, exist_ok=True)
    user_file_path = os.path.join(users_dir, f"{username}.json")
    try:
        with open(user_file_path, "w", encoding="utf-8") as file:
            json.dump(user_data, file, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        show_notification(self, self.lang.error, self.lang.error_saving_data)
        return False

def create_user_system(self):
    try:
        username = self.entry_vars["system_user_name"].get().strip()
        full_name = self.entry_vars["system_user_full_name"].get().strip()
        password = self.entry_vars["system_password"].get().strip()

        if not username or not full_name or not password:
            show_notification(self, self.lang.error, self.lang.error_invalid_input)
            return False

        if user_exists(username):
            show_notification(self, self.lang.error, self.lang.error_user_already_exists)
            return False

        subprocess.run(
            ["useradd", "-m", "-c", full_name, username],
            check=True,
            text=True
        )

        process = subprocess.Popen(
            ["passwd", username],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        process.communicate(f"{password}\n{password}\n")
        process.wait()
        print("Пользователь успешно создан")
        return True
    except subprocess.CalledProcessError:
        show_notification(self, self.lang.error, self.lang.error_something_went_wrong)
        return False
    except Exception as e:
        show_notification(self, self.lang.error, self.lang.error_something_went_wrong)
        print(f"Ошибка: {e}")
        return False

def validate_and_continue(self) -> bool:
    from db.commands import check_user_exist

    username_exists, email_exists = check_user_exist(
        str(self.entry_vars["system_user_name"].get().strip()),
        str(self.entry_vars["real_user_email"].get().strip())
    )
    if username_exists:
        show_notification(self, self.lang.error, self.lang.error_user_already_exists)
        return False
    if email_exists:
        show_notification(self, self.lang.error, self.lang.error_email_already_exists)
        return False
    if not check_validation_fills(self):
        return False
    return True

def get_linux_distro():
    distro = ""
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("ID="):
                    distro = line.strip().split("=")[1].strip('"')
                    break
    except Exception:
        pass
    return distro

def ensure_v4l2_ctl_installed():
    if shutil.which("v4l2-ctl") is None:
        distro = get_linux_distro()
        if distro in ["arch", "manjaro"]:
            cmd = ["sudo", "pacman", "-Sy", "--noconfirm", "v4l-utils"]
        elif distro in ["ubuntu", "debian", "pop"]:
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            cmd = ["sudo", "apt-get", "install", "-y", "v4l-utils"]
        elif distro == "fedora":
            cmd = ["sudo", "dnf", "install", "-y", "v4l-utils"]
        else:
            return False
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            return False
    return True

def get_camera_names(self):
    if ensure_v4l2_ctl_installed():
        try:
            output = subprocess.check_output(["v4l2-ctl", "--list-devices"], text=True)
        except Exception as e:
            return False
        devices = []
        lines = output.splitlines()
        for line in lines:
            if line.strip() == "":
                continue
            if not line.startswith("\t"):
                current_device = re.sub(r"\s*\(.*?\)", "", line.strip())
                devices.append(current_device)
        return devices
    else:
        show_notification(self, self.lang.error, self.lang.error_with_v4l2)

def center_window(child, parent):
    child.update_idletasks()
    parent.update_idletasks()

    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()

    child_width = child.winfo_width()
    child_height = child.winfo_height()

    pos_x = parent_x + (parent_width - child_width) // 2
    pos_y = parent_y + (parent_height - child_height) // 2

    child.geometry(f"+{pos_x}+{pos_y}")

def show_notification(self, title: str, message: str):
    Notification(self, title, message)

def show_progress(self, title: str, message: str):
    LoadingWindow(self, title, message)

class Notification(ctk.CTkToplevel):
    def __init__(self, parent, title: str, message: str):
        super().__init__(parent)
        self.title(title)
        image = ctk.CTkImage(light_image=Image.open(f'{CURRENT_DIR}/resources/images/warning.png'), dark_image=Image.open(f'{CURRENT_DIR}/resources/images/warning.png'), size=(80, 80))
        image_label = ctk.CTkLabel(self, text="", image=image)
        label = ctk.CTkLabel(self, text=message)
        exit_button = ctk.CTkButton(self, text="Exit", command=self.destroy)

        image_label.grid(row=0, column=0, padx=15, pady=5, sticky="nsew")
        label.grid(row=0, column=1, padx=15, pady=5, sticky="nsew")
        exit_button.grid(row=1, column=0, columnspan=2, padx=15, pady=5, sticky="nsew")
        self.after(0, lambda: center_window(self, parent))

class LoadingWindow(ctk.CTkToplevel):
    def __init__(self, parent, title: str, message: str):
        super().__init__(parent)
        self.title(title)
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        self.attributes("-topmost", True)
        self.progress = ctk.CTkProgressBar(self, mode = "indeterminate")
        self.loading_label = ctk.CTkLabel(self, text = message)

        self.progress.grid(row = 0, column = 0, padx = (10, 10), pady = (10, 20))
        self.loading_label.grid(row = 1, column = 0, padx = (10, 10), pady = (10, 10))
        self.after(0, lambda: center_window(self, parent))

        self.progress.start()

class SettingsApp(ctk.CTkToplevel):
    def __init__(self, master, language_w):
        super().__init__(master)
        self.language_w = language_w
        self.lang = Locale(language = language_w)
        self.title(f"{self.lang.settings_window_title}")
        self.is_checking = False

        self.label_db_user = ctk.CTkLabel(self, text=self.lang.db_user_label)
        self.entry_db_user = ctk.CTkEntry(self, placeholder_text="postgres")
        self.label_db_user_password = ctk.CTkLabel(self, text=self.lang.db_user_password_label)
        self.entry_db_user_password = ctk.CTkEntry(self, show="*")
        self.label_server_ip = ctk.CTkLabel(self, text=self.lang.server_ip_label)
        self.entry_server_ip = ctk.CTkEntry(self, placeholder_text="192.168.100.59")
        self.label_db_port = ctk.CTkLabel(self, text = self.lang.server_db_port)
        self.entry_db_port = ctk.CTkEntry(self, placeholder_text="5432")
        self.bt_server_ip = ctk.CTkButton(self, text=self.lang.bt_server_ip_text, command=self.__on_check_connection)
        self.label_db_name = ctk.CTkLabel(self, text=self.lang.db_name_label)
        self.entry_db_name = ctk.CTkEntry(self)
        self.bt_save_changes = ctk.CTkButton(self, text=self.lang.bt_save_changes_text, command=self.__on_save_changes)

        self.label_db_user.grid(row = 0, column = 0, sticky = "w", padx = (10, 0), pady = (10, 0))
        self.entry_db_user.grid(row = 0, column = 1, sticky = "nsew", padx = (10, 10), pady = (10, 0))
        self.label_db_user_password.grid(row = 1, column = 0, sticky = "w", padx = (10, 0), pady = (10, 0))
        self.entry_db_user_password.grid(row = 1, column = 1, sticky = "nsew", padx = (10, 10), pady = (10, 0))
        self.label_server_ip.grid(row=2, column=0, sticky="w", padx=(10, 0), pady=(10, 0))
        self.entry_server_ip.grid(row=2, column=1, sticky="nsew", padx=(10, 10), pady=(10, 0))
        self.label_db_port.grid(row=3, column=0, sticky="w", padx=(10, 0), pady=(10, 0))
        self.entry_db_port.grid(row=3, column=1, sticky="nsew", padx=(10, 10), pady=(10, 0))
        self.label_db_name.grid(row=4, column=0, sticky="w", padx=(10, 0), pady=(10, 0))
        self.entry_db_name.grid(row=4, column=1, sticky="nsew", padx=(10, 10), pady=(10, 0))
        self.bt_server_ip.grid(row = 5, column = 0, padx = (10, 0), pady = (15, 10))
        self.bt_save_changes.grid(row = 5, column = 1, padx = (0, 10), pady = (15, 10))


    def __on_check_connection(self):
        if self.is_checking:
            return
        self.is_checking = False
        self.bt_server_ip.configure(text=self.lang.bt_checking_text, fg_color="gray", state="DISABLED")
        self.bt_save_changes.configure(state = "DISABLED")
        self.entry_db_user.configure(state="disabled")
        self.entry_db_user_password.configure(state="disabled")
        self.entry_server_ip.configure(state="disabled")
        self.entry_db_name.configure(state="disabled")
        self.progress_window = None
        self.check_completed = False
        threading.Thread(target=self.__check_connection_thread, daemon=True).start()
        self.after(200, self.__check_show_progress)

    def __check_show_progress(self):
        if not self.check_completed:
            self.progress_window = LoadingWindow(self, self.lang.loading, self.lang.loading_wait)

    def __check_connection_thread(self):
        ip_address = self.entry_server_ip.get()
        port = self.entry_db_port.get()
        try:
            with socket.create_connection((ip_address, port), timeout=5):
                status = ("lime", self.lang.status_active)
        except (socket.timeout, socket.error):
            status = ("#a3544e", self.lang.status_inactive)

        self.check_completed = True
        self.after(0, self.__update_button_status, status)

    def __update_button_status(self, status):
        if self.progress_window:
            self.progress_window.destroy()
        color, text = status
        self.bt_server_ip.configure(text=text, fg_color=color, state="NORMAL")
        self.bt_save_changes.configure(state="NORMAL")
        self.entry_db_user.configure(state="normal")
        self.entry_db_user_password.configure(state="normal")
        self.entry_server_ip.configure(state="normal")
        self.entry_db_name.configure(state="normal")

        self.is_checking = False

    def __on_save_changes(self):
        db_user = self.entry_db_user.get()
        db_user_password = self.entry_db_user_password.get()
        db_ip = self.entry_server_ip.get()
        db_port = self.entry_db_port.get()
        db_name = self.entry_db_name.get()

        if db_user and db_user_password and db_ip and db_port and db_name:
            self.__open_confirmation_window(db_user, db_user_password, db_ip, db_port, db_name)
        else:
            if db_user == "":
                self.entry_db_user.configure(text_color="red", placeholder_text=self.lang.error_fill_in_the_fild)
            if db_user_password == "":
                self.entry_db_user_password.configure(text_color="red", placeholder_text=self.lang.error_fill_in_the_fild)
            if db_ip == "":
                self.entry_server_ip.configure(text_color="red", placeholder_text=self.lang.error_fill_in_the_fild)
            if db_port == "":
                self.entry_server_ip.configure(text_color="red", placeholder_text=self.lang.error_fill_in_the_fild)
            if db_name == "":
                self.entry_db_name.configure(text_color="red", placeholder_text=self.lang.error_fill_in_the_fild)

    def __open_confirmation_window(self, db_user, db_user_password, db_ip, db_port, db_name):
        ConfirmationWindow(self, db_user, db_user_password, db_ip, db_port, db_name, self.language_w)

class ConfirmationWindow(ctk.CTkToplevel):
    def __init__(self, parent, db_user, db_user_password, db_ip, db_port, db_name, language_ww):
        super().__init__(parent)
        self.title("")
        self.db_user = db_user
        self.db_user_password = db_user_password
        self.db_ip = db_ip
        self.db_name = db_name
        self.db_port = db_port
        self.lang = Locale(language=language_ww)
        self.after(10, lambda: center_window(self, parent))

        self.label = ctk.CTkLabel(self, text=self.lang.confirm_text)
        self.btn_yes = ctk.CTkButton(self, text=self.lang.yes, command=self.on_yes)
        self.btn_no = ctk.CTkButton(self, text=self.lang.no, command=self.on_no)

        self.label.grid(row=0, column=0, columnspan=2, pady=20, padx=20)
        self.btn_yes.grid(row=1, column=0, padx=20, pady=20, sticky="ew")
        self.btn_no.grid(row=1, column=1, padx=20, pady=20, sticky="ew")

    def on_yes(self):
        async_connection_string = f'"postgresql+asyncpg://{self.db_user}:{self.db_user_password}@{self.db_ip}:{self.db_port}/{self.db_name}"'
        sync_connection_string = f'"postgresql+psycopg2://{self.db_user}:{self.db_user_password}@{self.db_ip}:{self.db_port}/{self.db_name}"'
        self.manage_env_file(async_connection_string, sync_connection_string)
        self.master.destroy()
        self.destroy()

    def on_no(self):
        self.destroy()

    def manage_env_file(self, async_db_url, sync_db_url):
        try:
            env_file_path = os.path.join(os.getcwd(), ".env")
            if not os.path.exists(env_file_path):
                with open(env_file_path, "w") as env_file:
                    env_file.write(f"DATABASE_URL_ASYNC={async_db_url}\n")
                    env_file.write(f"DATABASE_URL={sync_db_url}\n")
            else:
                with open(env_file_path, "r") as env_file:
                    lines = env_file.readlines()
                lines = [line for line in lines if not line.startswith("DATABASE_URL")]
                lines.append(f"DATABASE_URL_ASYNC={async_db_url}\n")
                lines.append(f"DATABASE_URL={sync_db_url}\n")
                with open(env_file_path, "w") as env_file:
                    env_file.writelines(lines)
        except Exception as e:
            show_notification(self, self.lang.error, f"Something went wrong: {e}")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{NAME}")
        self.geometry("400x400")
        self.scaling = 1
        self.cap = None
        self.type = None
        self.language = "en"
        self.lang = Locale(language="en")
        self.available_cameras = get_camera_names(self)
        if not self.available_cameras:
            show_notification(self, self.lang.error, self.lang.error_no_camera)
            self.available_cameras = ["Нет доступных камер | There are no cameras available"]
        self.selected_camera = StringVar(value=self.available_cameras[0])
        self.camera_index = 0
        # ctk.set_widget_scaling(self.scaling)
        ctk.set_appearance_mode("dark")

        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()


        self.entry_vars = {
            "system_user_name": StringVar(),
            "system_user_full_name": StringVar(),
            "system_password": StringVar(),
            "system_check_password": StringVar(),
            "real_user_name": StringVar(),
            "real_user_last_name": StringVar(),
            "real_user_post": StringVar(),
            "real_user_email": StringVar(),
            "real_user_phone_number": StringVar()
        }

        img = Image.open(f"{CURRENT_DIR}/resources/images/ogon.png")
        img_ctk = ctk.CTkImage(light_image=img, size = (80, 80))
        img_label = ctk.CTkLabel(self, text = "", image = img_ctk)
        label_welcome = ctk.CTkLabel(self, text=f"Welcome to {NAME}")
        ui_scaling_label = ctk.CTkLabel(self, text="Масштабирование | UI Scaling")
        self.ui_scaling = ctk.CTkOptionMenu(self, values=["80%", "100%", "125%", "150%", "200%"], command=self.__ui_scaling_handler)
        self.__set_initial_ui_scaling()
        self.language = ctk.StringVar(value = "ru")
        language_label = ctk.CTkLabel(self, text = "Выберите язык | Choose language")
        language_radio_1 = ctk.CTkRadioButton(self, text = "руc | ru", variable=self.language, value = "ru")
        language_radio_2 = ctk.CTkRadioButton(self, text = "англ | en", variable = self.language, value = "en")
        bt_next_page = ctk.CTkButton(self, text="Следующая страница | Next page", command=self.page_variant_app)

        self.grid_columnconfigure(0, weight = 1)
        self.grid_columnconfigure(1, weight = 1)

        img_label.grid(row = 0, column = 0, columnspan = 2, pady = (20, 10))
        label_welcome.grid(row = 1, column = 0, columnspan = 2, padx = (10, 10))
        ui_scaling_label.grid(row = 2, column = 0, columnspan = 2, padx = (10, 10))
        self.ui_scaling.grid(row = 3, column = 0, columnspan = 2, pady = (10, 10), padx = (10, 10))
        language_label.grid(row = 4, column = 0, columnspan = 2, padx = (10, 10))
        language_radio_1.grid(row = 5, column = 0, padx = (10, 0), pady = (10, 10))
        language_radio_2.grid(row = 5, column = 1, padx = (0, 10), pady = (10, 10))
        bt_next_page.grid(row = 6, column = 0, columnspan = 2, pady = (25, 10), padx = (10, 10))

    def __set_initial_ui_scaling(self):
        print(self.screen_width, self.screen_height)
        if self.screen_width >= 5120 and self.screen_height >= 2880:
            initial_scaling = "200%"
        elif self.screen_width >= 3840 and self.screen_height >= 2400:
            initial_scaling = "150%"
        elif self.screen_width >= 2560 and self.screen_height >= 1440:
            initial_scaling = "125%"
        elif self.screen_width >= 1920 and self.screen_height >= 1080:
            initial_scaling = "100%"
        else:
            initial_scaling = "80%"

        self.__ui_scaling_handler(initial_scaling)
        self.ui_scaling.set(initial_scaling)

    def __ui_scaling_handler(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        print(self.scaling * new_scaling_float)
        ctk.set_widget_scaling(self.scaling * new_scaling_float)
        ctk.set_window_scaling(self.scaling * new_scaling_float)

    def page_variant_app(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.lang = Locale(language = self.language.get())
        label_variant_app = ctk.CTkLabel(self, text=self.lang.label_variant_app)
        button_local_app = ctk.CTkButton(self, text=self.lang.button_local_app, command=self.__page_first_reg_local)
        button_corp_app = ctk.CTkButton(self, text=self.lang.button_corp_app, command=self.__page_first_reg_corp)

        label_variant_app.grid(row = 0, column= 0, columnspan = 2, pady = (20, 10))
        button_local_app.grid(row = 1, column = 0, padx = (10, 0))
        button_corp_app.grid(row = 1, column = 1, padx = (0, 10))

    def __page_first_reg_local(self):
        for widget in self.winfo_children():
            widget.destroy()
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.type = "local"
        self.geometry("400x460")
        label_system_user_name = ctk.CTkLabel(self, text=self.lang.system_user_name)
        label_system_user_full_name = ctk.CTkLabel(self, text=self.lang.system_user_full_name)
        label_system_password = ctk.CTkLabel(self, text=self.lang.system_password)
        label_system_check_password = ctk.CTkLabel(self, text=self.lang.system_check_password)
        label_info_user_inputs = ctk.CTkLabel(self, text=self.lang.info_user_inputs)
        label_real_user_name = ctk.CTkLabel(self, text=self.lang.real_user_name)
        label_real_user_last_name = ctk.CTkLabel(self, text=self.lang.real_user_last_name)
        label_real_user_post = ctk.CTkLabel(self, text=self.lang.real_user_post)
        label_real_user_email = ctk.CTkLabel(self, text=self.lang.real_user_email)
        label_real_user_phone_number = ctk.CTkLabel(self, text=self.lang.real_user_phone_number)

        self.entry_system_user_name = ctk.CTkEntry(self, textvariable=self.entry_vars["system_user_name"])
        self.entry_system_user_full_name = ctk.CTkEntry(self, textvariable=self.entry_vars["system_user_full_name"])
        self.entry_system_password = ctk.CTkEntry(self, show="*", textvariable=self.entry_vars["system_password"])
        self.entry_system_check_password = ctk.CTkEntry(self, show="*", textvariable=self.entry_vars["system_check_password"])
        self.entry_real_user_name = ctk.CTkEntry(self, textvariable=self.entry_vars["real_user_name"])
        self.entry_real_user_last_name = ctk.CTkEntry(self, textvariable=self.entry_vars["real_user_last_name"])
        self.entry_real_user_post = ctk.CTkEntry(self, textvariable=self.entry_vars["real_user_post"])
        self.entry_real_user_email = ctk.CTkEntry(self, textvariable=self.entry_vars["real_user_email"])
        self.entry_real_user_phone_number = ctk.CTkEntry(self, textvariable=self.entry_vars["real_user_phone_number"])

        bt_previous_page = ctk.CTkButton(self, text=self.lang.previous_page, command=self.page_variant_app)
        bt_second_reg_local = ctk.CTkButton(self, text=self.lang.next_page, command=self.__check_page_second_reg_local)

        label_system_user_name.grid(row=0, column=0, sticky="nw", padx=(10, 10), pady=(0, 10))
        self.entry_system_user_name.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        label_system_user_full_name.grid(row=1, column=0, sticky="nw", padx=(10, 10), pady=(0, 10))
        self.entry_system_user_full_name.grid(row=1, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        label_system_password.grid(row=2, column=0, sticky="nw", padx=(10, 10), pady=(0, 10))
        self.entry_system_password.grid(row=2, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        label_system_check_password.grid(row=3, column=0, sticky="nw", padx=(10, 10), pady=(0, 10))
        self.entry_system_check_password.grid(row=3, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        label_info_user_inputs.grid(row=4, column=0, columnspan=2, padx=10, pady=10)
        label_real_user_name.grid(row=5, column=0, sticky="nw", padx=(10, 10), pady=(0, 10))
        self.entry_real_user_name.grid(row=5, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        label_real_user_last_name.grid(row=6, column=0, sticky="nw", padx=(10, 10), pady=(0, 10))
        self.entry_real_user_last_name.grid(row=6, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        label_real_user_post.grid(row=7, column=0, sticky="nw", padx=(10, 10), pady=(0, 10))
        self.entry_real_user_post.grid(row=7, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        label_real_user_email.grid(row=8, column=0, sticky="nw", padx=(10, 10), pady=(0, 10))
        self.entry_real_user_email.grid(row=8, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        label_real_user_phone_number.grid(row=9, column=0, sticky="nw", padx=(10, 10), pady=(0, 10))
        self.entry_real_user_phone_number.grid(row=9, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        bt_previous_page.grid(row=10, column=0, padx=(10, 10), pady=(20, 10))
        bt_second_reg_local.grid(row=10, column=1, padx=(10, 10), pady=(20, 10))

    def __check_page_second_reg_local(self):
        if user_exists(self.entry_vars["system_user_name"].get()):
            show_notification(self, self.lang.error, self.lang.error_user_already_exists)
        else:
            if check_validation_fills(self):
                self.available_cameras = get_camera_names(self)
                if not self.available_cameras:
                    self.available_cameras = ["Нет доступных камер | There are no cameras available"]
                self.__page_second_reg_local()

    def __page_second_reg_local(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.geometry("400x500")
        label_info_scan = ctk.CTkLabel(self, text = self.lang.process_scanning)
        self.image_label_cv2 = ctk.CTkLabel(self, text="")
        self.info_label_cv2 = ctk.CTkLabel(self, text="")
        self.camera_dropdown = ctk.CTkComboBox(
            self,
            values=self.available_cameras,
            variable=self.selected_camera,
            command=self.on_camera_selected
        )
        if self.available_cameras == ["Нет доступных камер | There are no cameras available"]:
            self.bt_start_scan = ctk.CTkButton(self, text=self.lang.begin, command=self.__toggle_camera, state = "disabled")
        else:
            self.bt_start_scan = ctk.CTkButton(self, text=self.lang.begin, command=self.__toggle_camera)
        bt_previous_page = ctk.CTkButton(self, text=self.lang.previous_page, command=self.__page_first_reg_local)

        label_info_scan.grid(row = 0, column = 0, columnspan = 2, padx = (10, 10), pady = (10, 10))
        self.image_label_cv2.grid(row = 1, column = 0, columnspan = 2, padx = (10, 10), pady = (10, 10))
        self.info_label_cv2.grid(row = 2, column = 0, columnspan = 2, padx = (10, 10), pady = (5, 10))
        self.camera_dropdown.grid(row = 3, column = 0, columnspan = 2, padx = (10, 10), pady = (5, 5), sticky = "ew")
        bt_previous_page.grid(row = 4, column = 0, padx = (10, 0), pady = (10, 10))
        self.bt_start_scan.grid(row = 4, column = 1, padx = (0, 10), pady = (10, 10))

    def on_camera_selected(self, event=None):
        selected = self.selected_camera.get()
        if selected == "Нет доступных камер | There are no cameras available":
            self.camera_index = None
            self.info_label_cv2.configure(text = self.lang.error_no_camera, text_color="red")
        else:
            self.camera_index = self.available_cameras.index(selected)

    def __toggle_camera(self):
        if self.bt_start_scan.cget("text") == self.lang.begin:
            self.bt_start_scan.configure(text=self.lang.scan)
            self.__start_camera()
        elif self.bt_start_scan.cget("text") == self.lang.scan:
            if self.__capture_photo():
                self.bt_start_scan.configure(text=self.lang.complete)
        elif self.bt_start_scan.cget("text") == self.lang.complete:
            if self.cap is not None and self.cap.isOpened():
                self.cap.release()
                self.cap = None
            if self.type == "local":
                if save_user_data(self) and create_user_system(self):
                    self.__last_page()
                self.__last_page()
            elif self.type == "corp":
                from db.commands import create_user
                if create_user(
                    username=str(self.entry_vars["system_user_name"].get().strip()),
                    name=str(self.entry_vars["real_user_name"].get().strip()),
                    lastname=str(self.entry_vars["real_user_last_name"].get().strip()),
                    post=str(self.entry_vars["real_user_post"].get().strip()),
                    email=str(self.entry_vars["real_user_email"].get().strip()),
                    phone_number=str(self.entry_vars["real_user_phone_number"].get().strip())
                ) and create_user_system(self):
                    self.__last_page()

    def __start_camera(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        def update_frame():
            if self.cap is not None and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    frame = cv2.resize(frame, (300, 300))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                    video_frame = ctk.CTkImage(light_image=img, size=(300, 300))

                    self.image_label_cv2.configure(image=video_frame)
                    self.image_label_cv2.image = video_frame

                self.image_label_cv2.after(10, update_frame)

        update_frame()

    def __capture_photo(self) -> bool:
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame)
                if face_locations:
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    if len(face_encodings) == 1:
                        encoding = face_encodings[0]
                        if not os.path.exists("encodings"):
                            os.makedirs("encodings")
                        username = self.entry_vars["system_user_name"].get()
                        file_path = os.path.join("encodings", f"{username}.pkl")
                        with open(file_path, "wb") as f:
                            pickle.dump([encoding], f)
                        self.info_label_cv2.configure(text = self.lang.success_face_recognition, text_color="lime")
                        return True
                    elif len(face_encodings) > 1:
                        self.info_label_cv2.configure(text = self.lang.error_too_many_faces, text_color="red")
                        return False
                else:
                    self.info_label_cv2.configure(text = self.lang.error_face_not_detected, text_color="red")
                    return False

    def __page_first_reg_corp(self):
        for widget in self.winfo_children():
            widget.destroy()
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        self.type = "corp"
        self.geometry("400x500")

        bt_setting_server_connection = ctk.CTkButton(self, text = self.lang.settings_server_connection, command=self.__settings_server_connection)

        label_system_user_name = ctk.CTkLabel(self, text=self.lang.system_user_name)
        label_system_user_full_name = ctk.CTkLabel(self, text=self.lang.system_user_full_name)
        label_system_password = ctk.CTkLabel(self, text=self.lang.system_password)
        label_system_check_password = ctk.CTkLabel(self, text=self.lang.system_check_password)
        label_info_user_inputs = ctk.CTkLabel(self, text=self.lang.info_user_inputs)
        label_real_user_name = ctk.CTkLabel(self, text=self.lang.real_user_name)
        label_real_user_last_name = ctk.CTkLabel(self, text=self.lang.real_user_last_name)
        label_real_user_post = ctk.CTkLabel(self, text=self.lang.real_user_post)
        label_real_user_email = ctk.CTkLabel(self, text=self.lang.real_user_email)
        label_real_user_phone_number = ctk.CTkLabel(self, text=self.lang.real_user_phone_number)

        self.entry_system_user_name = ctk.CTkEntry(self, textvariable=self.entry_vars["system_user_name"])
        self.entry_system_user_full_name = ctk.CTkEntry(self, textvariable=self.entry_vars["system_user_full_name"])
        self.entry_system_password = ctk.CTkEntry(self, show="*", textvariable=self.entry_vars["system_password"])
        self.entry_system_check_password = ctk.CTkEntry(self, show="*", textvariable=self.entry_vars["system_check_password"])
        self.entry_real_user_name = ctk.CTkEntry(self, textvariable=self.entry_vars["real_user_name"])
        self.entry_real_user_last_name = ctk.CTkEntry(self, textvariable=self.entry_vars["real_user_last_name"])
        self.entry_real_user_post = ctk.CTkEntry(self, textvariable=self.entry_vars["real_user_post"])
        self.entry_real_user_email = ctk.CTkEntry(self, textvariable=self.entry_vars["real_user_email"])
        self.entry_real_user_phone_number = ctk.CTkEntry(self, textvariable=self.entry_vars["real_user_phone_number"])

        bt_previous_page = ctk.CTkButton(self, text=self.lang.previous_page, command=self.page_variant_app)
        bt_second_reg_corp = ctk.CTkButton(self, text=self.lang.next_page, command=self.__check_page_second_reg_corp)

        bt_setting_server_connection.grid(row = 0, column = 1, sticky = "e", padx = (0, 5), pady = (10, 0))
        label_system_user_name.grid(row=1, column=0, sticky="nw", padx=(10, 10), pady=(0, 10))
        self.entry_system_user_name.grid(row=1, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        label_system_user_full_name.grid(row=2, column=0, sticky="nw", padx=(10, 10), pady=(0, 10))
        self.entry_system_user_full_name.grid(row=2, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        label_system_password.grid(row=3, column=0, sticky="nw", padx=(10, 10), pady=(0, 10))
        self.entry_system_password.grid(row=3, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        label_system_check_password.grid(row=4, column=0, sticky="nw", padx=(10, 10), pady=(0, 10))
        self.entry_system_check_password.grid(row=4, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        label_info_user_inputs.grid(row=5, column=0, columnspan=2, padx=10, pady=10)
        label_real_user_name.grid(row=6, column=0, sticky="nw", padx=(10, 10), pady=(0, 10))
        self.entry_real_user_name.grid(row=6, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        label_real_user_last_name.grid(row=7, column=0, sticky="nw", padx=(10, 10), pady=(0, 10))
        self.entry_real_user_last_name.grid(row=7, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        label_real_user_post.grid(row=8, column=0, sticky="nw", padx=(10, 10), pady=(0, 10))
        self.entry_real_user_post.grid(row=8, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        label_real_user_email.grid(row=9, column=0, sticky="nw", padx=(10, 10), pady=(0, 10))
        self.entry_real_user_email.grid(row=9, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        label_real_user_phone_number.grid(row=10, column=0, sticky="nw", padx=(10, 10), pady=(0, 10))
        self.entry_real_user_phone_number.grid(row=10, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        bt_previous_page.grid(row=11, column=0, padx=(10, 10), pady=(20, 10))
        bt_second_reg_corp.grid(row=11, column=1, padx=(10, 10), pady=(20, 10))

    def __settings_server_connection(self):
        SettingsApp(self, self.language.get())

    def __check_db_connection(self, database_url, timeout=2):
        from sqlalchemy import create_engine, inspect
        from sqlalchemy.exc import SQLAlchemyError
        try:
            engine = create_engine(database_url, connect_args={"connect_timeout": timeout})
            with engine.connect() as conn:
                inspector = inspect(engine)
                tables = inspector.get_table_names()
            engine.dispose()
            return True
        except SQLAlchemyError:
            return False

    def __check_page_second_reg_corp(self):
        if user_exists(self.entry_vars["system_user_name"].get()):
            show_notification(self, self.lang.error, self.lang.error_user_already_exists)
            return

        load_dotenv(find_dotenv())
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            show_notification(self, self.lang.error,self.lang.error_no_connection_string)
            return

        if not self.__check_db_connection(database_url):
            show_notification(self, self.lang.error, self.lang.error_cant_connect)
            return

        if validate_and_continue(self):
            self.available_cameras = get_camera_names(self)
            if not self.available_cameras:
                self.available_cameras = ["Нет доступных камер | There are no cameras available"]
            self.__page_second_reg_corp()

    def __page_second_reg_corp(self):
        for widget in self.winfo_children():
            widget.destroy()
        label_info_scan = ctk.CTkLabel(self, text = self.lang.process_scanning)
        self.image_label_cv2 = ctk.CTkLabel(self, text="")
        self.info_label_cv2 = ctk.CTkLabel(self, text="")
        self.camera_dropdown = ctk.CTkComboBox(
            self,
            values=self.available_cameras,
            variable=self.selected_camera,
            command=self.on_camera_selected
        )
        if self.available_cameras == ["Нет доступных камер | There are no cameras available"]:
            self.bt_start_scan = ctk.CTkButton(self, text=self.lang.begin, command=self.__toggle_camera, state="disabled")
        else:
            self.bt_start_scan = ctk.CTkButton(self, text=self.lang.begin, command=self.__toggle_camera)
        bt_previous_page = ctk.CTkButton(self, text=self.lang.previous_page, command=self.__page_first_reg_corp)

        label_info_scan.grid(row = 0, column = 0, columnspan = 2, padx = (10, 10), pady = (10, 10))
        self.image_label_cv2.grid(row = 1, column = 0, columnspan = 2, padx = (10, 10), pady = (10, 10))
        self.info_label_cv2.grid(row = 2, column = 0, columnspan = 2, padx = (10, 10), pady = (5, 10))
        self.camera_dropdown.grid(row=3, column=0, columnspan=2, padx=(10, 10), pady=(5, 5), sticky="ew")
        bt_previous_page.grid(row = 4, column = 0, padx = (10, 0), pady = (10, 10))
        self.bt_start_scan.grid(row = 4, column = 1, padx = (0, 10), pady = (10, 10))

    def __last_page(self):
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
            self.cap = None
        for widget in self.winfo_children():
            widget.destroy()
        label_last_page = ctk.CTkLabel(self, text = self.lang.last_page_label)
        img_2 = Image.open("resources/images/ogon.png")
        img_2_ctk = ctk.CTkImage(light_image=img_2, size=(80, 80))
        img_2_label = ctk.CTkLabel(self, text="", image=img_2_ctk)

        label_last_page.grid(row = 0, column = 0, columnspan = 2, padx = (10, 10), pady = (20, 20))
        img_2_label.grid(row = 1, column = 0, columnspan = 2, padx = (10, 10), pady = (20, 20))


if __name__ == '__main__':
    App().mainloop()
