import logging
import os

DEFAULT_LOG_FILE = "/var/log/my_program.log"

def setup_logger(log_path=""):
    log_file = log_path if log_path else DEFAULT_LOG_FILE

    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

def create_log(path: str, message: str):
    setup_logger(path)
    logging.info(message)