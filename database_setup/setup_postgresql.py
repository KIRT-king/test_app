import os
import subprocess
import time
from sqlalchemy import create_engine


def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка: {e}")


def install_docker():
    print("🔹 Проверяем, установлен ли Docker...")
    if subprocess.run("docker --version", shell=True).returncode != 0:
        print("⬇️  Устанавливаем Docker...")
        run_command("sudo apt update && sudo apt install -y docker.io")
    else:
        print("✅ Docker уже установлен!")


def install_postgres_image():
    print("🔹 Проверяем, загружен ли образ PostgreSQL...")
    if "postgres" not in subprocess.getoutput("docker images"):
        print("⬇️  Загружаем образ PostgreSQL...")
        run_command("docker pull postgres")
    else:
        print("✅ Образ PostgreSQL уже загружен!")


def get_user_input():
    db_name = input("Введите имя базы данных: ")
    user = input("Введите имя пользователя: ")
    password = input("Введите пароль: ")
    port = input("Введите порт (по умолчанию 5432): ") or "5432"
    return db_name, user, password, port


def run_postgres_container(db_name, user, password, port):
    print("🚀 Запускаем контейнер PostgreSQL...")
    run_command(
        f"docker run -d --name postgresql -e POSTGRES_DB={db_name} -e POSTGRES_USER={user} -e POSTGRES_PASSWORD={password} -p {port}:5432 postgres")

    print("⏳ Ожидание запуска контейнера...")
    time.sleep(5)


def generate_connection_string(user, password, port, db_name):
    return f"postgresql+psycopg2://{user}:{password}@localhost:{port}/{db_name}"


def check_connection(connection_string):
    print("🔹 Проверяем подключение к PostgreSQL через SQLAlchemy...")
    try:
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            print("✅ Успешное подключение к базе данных!")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")


if __name__ == "__main__":
    install_docker()
    install_postgres_image()

    db_name, user, password, port = get_user_input()
    run_postgres_container(db_name, user, password, port)

    connection_string = generate_connection_string(user, password, port, db_name)
    print(f"🔗 Ваша строка подключения: {connection_string}")

    check_connection(connection_string)
