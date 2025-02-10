import os
import subprocess
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_command(command_list):
    try:
        subprocess.run(command_list, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка: {e}")


def install_docker():
    print("🔹 Проверяем, установлен ли Docker...")
    if subprocess.run(["docker", "--version"], capture_output=True).returncode != 0:
        print("⬇️  Устанавливаем Docker...")
        run_command(["sudo", "apt", "update"])
        run_command(["sudo", "apt", "install", "-y", "docker.io"])
    else:
        print("✅ Docker уже установлен!")


def install_postgres_image():
    print("🔹 Проверяем, загружен ли образ PostgreSQL...")
    images = subprocess.getoutput("docker images")
    if "postgres" not in images:
        print("⬇️  Загружаем образ PostgreSQL...")
        run_command(["docker", "pull", "postgres"])
    else:
        print("✅ Образ PostgreSQL уже загружен!")


def get_user_input():
    db_name = input("Введите имя базы данных: ")
    user = input("Введите имя пользователя: ")
    password = input("Введите пароль: ")
    host = input("Введите адрес хоста (по умолчанию localhost): ") or "localhost"
    port = input("Введите порт (по умолчанию 5432): ") or "5432"
    container_name = input("Введите имя контейнера (по умолчанию postgresql): ") or "postgresql"
    create_tables_answer = input("Желаете ли вы создать таблицы? (Y/n) ")
    return db_name, user, password, host, port, container_name, create_tables_answer


def run_postgres_container(db_name, user, password, port, container_name):
    while True:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True, text=True
        )
        containers = result.stdout.splitlines()
        if container_name in containers:
            container_name = input(
                f"Контейнер с именем '{container_name}' уже существует. Введите другое имя контейнера: "
            ).strip()
        else:
            break

    while True:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Ports}}"],
            capture_output=True, text=True
        )
        ports_list = result.stdout.splitlines()
        if any(f":{port}->" in mapping for mapping in ports_list):
            port = input(f"Порт '{port}' уже используется. Введите другой порт: ").strip()
        else:
            break

    print("🚀 Запускаем контейнер PostgreSQL...")
    command = [
        "docker", "run", "-d",
        "--name", container_name,
        "-e", f"POSTGRES_DB={db_name}",
        "-e", f"POSTGRES_USER={user}",
        "-e", f"POSTGRES_PASSWORD={password}",
        "-p", f"{port}:5432",
        "postgres"
    ]
    run_command(command)
    print("⏳ Ожидание запуска контейнера...")
    time.sleep(5)
    return port, container_name


def generate_connection_string(user, password, port, db_name, host="localhost"):
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"


def check_connection(connection_string, create_tables_answer: str):
    if create_tables_answer.lower() in ["yes", "y", ""]:
        print("🔹 Проверяем подключение к PostgreSQL и создаем таблицы...")
        try:
            engine = create_engine(connection_string)
            with engine.connect() as conn:
                print("✅ Успешное подключение к базе данных!")
            try:
                Base = declarative_base()
                from sqlalchemy import Column, Integer, String
                class User(Base):
                    __tablename__ = "users"

                    id = Column(Integer, primary_key=True, autoincrement=True)
                    username = Column(String(50), nullable=False, unique=True)
                    name = Column(String(100), nullable=False)
                    lastname = Column(String(100), nullable=False)
                    post = Column(String(150))
                    email = Column(String(255), nullable=False, unique=True)
                    phone_number = Column(String(20))
                    status = Column(String(100), nullable=False)
                    last_check = Column(String(50), nullable=False)
                Base.metadata.create_all(engine)
                print("✅ Таблицы успешно созданы!")
            except Exception as e:
                print(f"❌ Ошибка при создании таблиц: {e}")
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
    else:
        print("🔹 Проверяем подключение к PostgreSQL...")
        try:
            engine = create_engine(connection_string)
            with engine.connect() as conn:
                print("✅ Успешное подключение к базе данных!")
        except Exception as e:
            print(f"Ошибка подключения: {e}")


if __name__ == "__main__":
    install_docker()
    install_postgres_image()

    db_name, user, password, host, port, container_name, create_tables_answer = get_user_input()
    port, container_name = run_postgres_container(db_name, user, password, port, container_name)

    connection_string = generate_connection_string(user, password, port, db_name, host)
    print(f"🔗 Ваша строка подключения: {connection_string}")
    check_connection(connection_string, create_tables_answer)
