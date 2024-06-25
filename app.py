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
    
    print("Проверка сетевого подключения...")
    host = repo_url.split('//')[1].split('/')[0]
    if not check_network(host):
        raise Exception(f"Не удалось установить сетевое подключение с {host}")

    print(f"Клонирование репозитория из {repo_url} в {repo_path}")
    try:
        Repo.clone_from(repo_url, repo_path, env={
            "GIT_ASKPASS": "echo",
            "GIT_USERNAME": username,
            "GIT_PASSWORD": password,
            "GIT_HTTP_LOW_SPEED_LIMIT": "1000",
            "GIT_HTTP_LOW_SPEED_TIME": "60"
        })
        print("Репозиторий успешно клонирован")
    except Exception as e:
        print(f"Ошибка при клонировании: {str(e)}")
        raise

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