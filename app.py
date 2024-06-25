import os
import sys
import marqo
from git import Repo
import shutil
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
import socket
import subprocess

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

def get_env_variable(var_name):
    value = os.getenv(var_name)
    if value is None:
        raise EnvironmentError(f"Переменная окружения {var_name} не установлена")
    return value.strip()

def check_network(host):
    try:
        # Попытка разрешить DNS
        ip = socket.gethostbyname(host)
        print(f"DNS resolution for {host}: {ip}")

        # Попытка пинга
        result = subprocess.run(['ping', '-c', '4', host], capture_output=True, text=True)
        print(f"Ping result for {host}:\n{result.stdout}")

        # Попытка установить TCP-соединение
        sock = socket.create_connection((host, 443), timeout=10)
        sock.close()
        print(f"TCP connection to {host}:443 successful")
        return True
    except Exception as e:
        print(f"Network check failed for {host}: {str(e)}")
        return False

def clone_repo(repo_url, repo_path, username, password):
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    
    print(f"Attempting to clone repository from {repo_url} to {repo_path}")
    
    # Попробуем использовать Git напрямую через subprocess для более подробного вывода
    git_command = [
        "git",
        "clone",
        "--verbose",
        f"https://{username}:{password}@{repo_url.split('://')[1]}",
        repo_path
    ]
    
    try:
        result = subprocess.run(git_command, capture_output=True, text=True, check=True)
        print("Git clone output:")
        print(result.stdout)
        print("Git clone successful")
    except subprocess.CalledProcessError as e:
        print("Git clone failed. Error output:")
        print(e.stderr)
        raise Exception(f"Failed to clone repository: {e}")

if __name__ == '__main__':
    try:
        repo_url = get_env_variable('REPO_URL')
        repo_path = get_env_variable('REPO_PATH')
        base_url = get_env_variable('BASE_URL')
        username = get_env_variable('GIT_USERNAME')
        password = get_env_variable('GIT_PASSWORD')

        index_documents(repo_url, repo_path, base_url, username, password)
    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")
        sys.exit(1)