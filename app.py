import os
import sys
import marqo
from git import Repo
import shutil
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
import subprocess

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

def get_env_variable(var_name):
    value = os.getenv(var_name)
    if value is None:
        raise EnvironmentError(f"Переменная окружения {var_name} не установлена")
    return value.strip()

def clone_repo(repo_url, repo_path, username, password):
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    
    print(f"Attempting to clone repository from {repo_url} to {repo_path}")
    
    # Попытка 1: HTTPS с отключенной проверкой SSL
    git_command_1 = [
        "git", "-c", "http.sslVerify=false",
        "clone", "--verbose",
        f"https://{username}:{password}@{repo_url.split('://')[1]}",
        repo_path
    ]
    
    # Попытка 2: Git протокол
    git_command_2 = [
        "git",
        "clone", "--verbose",
        f"git@{repo_url.split('://')[1].replace('/', ':')}",
        repo_path
    ]
    
    # Попытка 3: HTTPS с увеличенным таймаутом
    git_command_3 = [
        "git", "-c", "http.lowSpeedLimit=1000", "-c", "http.lowSpeedTime=60",
        "clone", "--verbose",
        f"https://{username}:{password}@{repo_url.split('://')[1]}",
        repo_path
    ]
    
    commands = [git_command_1, git_command_2, git_command_3]
    
    for i, command in enumerate(commands, 1):
        try:
            print(f"Attempt {i}: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=120)
            print("Git clone output:")
            print(result.stdout)
            print("Git clone successful")
            return
        except subprocess.CalledProcessError as e:
            print(f"Attempt {i} failed. Error output:")
            print(e.stderr)
        except subprocess.TimeoutExpired:
            print(f"Attempt {i} timed out after 120 seconds")
    
    raise Exception("Failed to clone repository after all attempts")

def preprocess_text(text):
    text = re.sub(r'\W', ' ', text)
    text = text.lower()
    stop_words = set(stopwords.words('russian'))
    tokens = word_tokenize(text)
    filtered_text = ' '.join([word for word in tokens if word not in stop_words])
    return filtered_text

def index_documents(repo_url, repo_path, base_url, username, password):
    try:
        clone_repo(repo_url, repo_path, username, password)
        
        mq = marqo.Client(url=get_env_variable('MARQO_URL'))

        try:
            mq.index("my-markdown-index").delete()
            print("Existing index deleted successfully")
        except Exception as e:
            print(f"Error deleting index (this may be normal if the index doesn't exist): {str(e)}")

        settings = {
            "treatUrlsAndPointersAsImages": False,
            "model": "hf/multilingual-e5-large",
            "normalizeEmbeddings": True,
        }
        mq.create_index("my-markdown-index", settings_dict=settings)
        print("New index created successfully")

        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        content = f.read()
                        preprocessed_content = preprocess_text(content)
                        relative_path = os.path.relpath(file_path, repo_path)
                        document_url = f"{base_url}/{relative_path.replace(os.path.sep, '/')}"
                        mq.index("my-markdown-index").add_documents([
                            {
                                "Title": file,
                                "Content": preprocessed_content,
                                "URL": document_url
                            }
                        ], tensor_fields=["Content"])
                    print(f"Indexed document: {file}")
        print("Индексация завершена успешно")
    except Exception as e:
        print(f"Произошла ошибка при индексации: {str(e)}")
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