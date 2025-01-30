import customtkinter as ctk
from PIL import Image
from screeninfo import get_monitors

screen_info = get_monitors()[0]
screen_width = screen_info.width
screen_height = screen_info.height

app_width = int(screen_width * 0.1)
app_height = int(screen_height * 0.1)
x_position = int((screen_width - app_width) / 2)
y_position = int((screen_height - app_height) / 2)


NAME = "KIRT app"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{NAME}")
        self.geometry(f"{app_width}x{app_height}+{x_position}+{y_position}")
        ctk.set_appearance_mode("dark")

        label_welcome = ctk.CTkLabel(self, text=f"Welcome to {NAME}")
        ui_scaling_label = ctk.CTkLabel(self, text="Масштабирование | UI Scaling")
        ui_scaling = ctk.CTkOptionMenu(self, values=["80%", "100%", "125%", "150%", "200%"], command=self.__ui_scaling_handler)
        ui_scaling.set("100%")
        bt_next_page = ctk.CTkButton(self, text = "Next page", command = self.page_variant_app)

        self.grid_columnconfigure((0, 2), weight = 1)
        self.grid_columnconfigure(1, weight = 2)

        label_welcome.grid(row=0, column = 1, padx = (15, 15), pady = (15, 15))
        ui_scaling_label.grid(row=1, column = 1, padx = (15, 15))
        ui_scaling.grid(row=2, column = 1, padx = (15, 15))
        bt_next_page.grid(row = 3, column = 1, padx = (15, 15), pady = (30, 15))

    def __ui_scaling_handler(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)
        ctk.set_window_scaling(new_scaling_float)

    def page_variant_app(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.grid_rowconfigure(0, weight = 3)
        self.grid_rowconfigure(1, weight= 1)
        label_variant_app = ctk.CTkLabel(self, text="Выберите режим регистрации")
        button_corp_app = ctk.CTkButton(self, text=f"Corporate app", command=self.__page_first_reg_corp)
        button_local_app = ctk.CTkButton(self, text=f"Local app", command=self.__page_first_reg_local)
        label_variant_app.grid(row = 0, column = 0, columnspan = 2)
        button_corp_app.grid(row=1, column=0)
        button_local_app.grid(row=1, column=1)

    def __page_first_reg_local(self):
        for widget in self.winfo_children():
            widget.destroy()

        label_system_user_name = ctk.CTkLabel(self,         text=f"Имя пользователя")
        label_system_user_full_name = ctk.CTkLabel(self,    text=f"Полное имя")
        label_system_password = ctk.CTkLabel(self,          text=f"Пароль")
        label_system_check_password = ctk.CTkLabel(self,    text=f"Пароль(проверка)")
        label_info_user_inputs = ctk.CTkLabel(self,         text=f"Поля для ввода лич. инф.")
        label_real_user_name = ctk.CTkLabel(self,           text=f"Ваше имя")
        label_real_user_last_name = ctk.CTkLabel(self,      text=f"Ваша фамилия")
        label_real_user_post = ctk.CTkLabel(self,           text=f"Ваша должность")
        label_real_user_email = ctk.CTkLabel(self,          text=f"Ваш email")
        label_real_user_phone_number = ctk.CTkLabel(self,   text=f"Ваш номер телефона")

        entry_system_user_name = ctk.CTkEntry(self)
        entry_system_user_full_name = ctk.CTkEntry(self)
        entry_system_password = ctk.CTkEntry(self, show = "*")
        entry_system_check_password = ctk.CTkEntry(self, show = "*")
        entry_real_user_name = ctk.CTkEntry(self)
        entry_real_user_last_name = ctk.CTkEntry(self)
        entry_real_user_post = ctk.CTkEntry(self)
        entry_real_user_email = ctk.CTkEntry(self)
        entry_real_user_phone_number = ctk.CTkEntry(self)

        self.grid_columnconfigure((0, 1), weight = 1)
        self.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8, 9), weight = 1)

        label_system_user_name.grid(row = 0, column = 0, sticky = "w", padx = (10, 10), pady = (10, 10))
        entry_system_user_name.grid(row = 0, column = 1, sticky = "ew", padx = (0, 10), pady = (10, 10))
        label_system_user_full_name.grid(row = 1, column = 0, sticky = "w", padx = (10, 10), pady = (0, 10))
        entry_system_user_full_name.grid(row = 1, column = 1, sticky = "ew", padx = (0, 10), pady = (10, 10))
        label_system_password.grid(row = 2, column = 0, sticky = "w", padx = (10, 10), pady = (0, 10))
        entry_system_password.grid(row = 2, column = 1, sticky = "ew", padx = (0, 10), pady = (10, 10))
        label_system_check_password.grid(row = 3, column = 0, sticky = "w", padx = (10, 10), pady = (0, 10))
        entry_system_check_password.grid(row = 3, column = 1, sticky = "ew", padx = (0, 10), pady = (10, 10))
        label_info_user_inputs.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        label_real_user_name.grid(row=5, column=0, sticky="w", padx = (10, 10), pady = (0, 10))
        entry_real_user_name.grid(row=5, column=1, sticky="ew", padx = (0, 10), pady = (10, 10))
        label_real_user_last_name.grid(row=6, column=0, sticky="w", padx = (10, 10), pady = (0, 10))
        entry_real_user_last_name.grid(row=6, column=1, sticky="ew", padx = (0, 10), pady = (10, 10))
        label_real_user_post.grid(row=7, column=0, sticky="w", padx = (10, 10), pady = (0, 10))
        entry_real_user_post.grid(row=7, column=1, sticky="ew", padx = (0, 10), pady = (10, 10))
        label_real_user_email.grid(row=8, column=0, sticky="w", padx = (10, 10), pady = (0, 10))
        entry_real_user_email.grid(row=8, column=1, sticky="ew", padx = (0, 10), pady = (10, 10))
        label_real_user_phone_number.grid(row=9, column=0, sticky="w", padx = (10, 10), pady = (0, 10))
        entry_real_user_phone_number.grid(row=9, column=1, sticky="ew", padx = (0, 10), pady = (10, 10))


    def __page_second_reg_local(self):
        pass
    def __page_first_reg_corp(self):
        pass
    def __page_second_reg_corp(self):
        pass

if __name__ == "__main__":
    App().mainloop()