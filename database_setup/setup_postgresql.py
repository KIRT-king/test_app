import os
import subprocess
import psycopg2
import configparser
import typer

app = typer.Typer()

CONFIG_PATH = "db_config.ini"  # Путь к файлу конфигурации


def create_env_file(db_name: str, user: str, password: str, host: str = "localhost", port: str = "5432"):
    env_content = f"""DB_NAME={db_name}
DB_USER={user}
DB_PASSWORD={password}
DB_HOST={host}
DB_PORT={port}
"""
    with open(".env", "w") as env_file:
        env_file.write(env_content)

    print(".env файл успешно создан.")


def run_command(command: str):
    process = subprocess.run(command, check=True, capture_output=True, text=True)
    if process.returncode != 0:
        typer.echo(f"Ошибка: {process.stderr}")
    else:
        typer.echo(process.stdout)


def get_command_operator():
    distro = ""
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("ID="):
                    distro = line.strip().split("=")[1].strip('"')
                    break
    except Exception:
        pass
    if distro in ["arch", "manjaro"]:
        return "pacman"
    elif distro in ["ubuntu", "debian", "pop"]:
        return "apt-get"
    elif distro == "fedora":
        return "dnf"
    else:
        return None


@app.command()
def install_postgres():
    typer.echo("Устанавливаем PostgreSQL...")
    cmd_operator = get_command_operator()
    if cmd_operator is None:
        cmd_operator = input("Введите используемый менеджер пакетов (dnf/apt-get/pacman): ")
    run_command(f"sudo {cmd_operator} install -y postgresql postgresql-contrib")


@app.command()
def setup_db(
    db_name: str = typer.Option(..., prompt="Введите название базы данных"),
    user: str = typer.Option(..., prompt="Введите имя пользователя"),
    password: str = typer.Option(
        ..., prompt="Введите пароль", hide_input=True, confirmation_prompt=True
    ),
):
    try:
        conn = psycopg2.connect(dbname="postgres", user="postgres", password="admin")
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute(f"CREATE DATABASE {db_name};")
        cur.execute(f"CREATE USER {user} WITH ENCRYPTED PASSWORD '{password}';")
        cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {user};")

        cur.close()
        conn.close()
        typer.echo(f"База данных '{db_name}' и пользователь '{user}' успешно созданы.")

        config = configparser.ConfigParser()
        config["DATABASE"] = {
            "DB_NAME": db_name,
            "USER": user,
            "PASSWORD": password,
            "HOST": "localhost",
            "PORT": "5432"
        }
        with open(CONFIG_PATH, "w") as configfile:
            config.write(configfile)
        typer.echo(f"Конфигурационный файл '{CONFIG_PATH}' создан.")

        create_env_file(db_name, user, password)

    except Exception as e:
        typer.echo(f"Ошибка при настройке БД: {e}")


if __name__ == "__main__":
    app()
