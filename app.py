import os
import sys
import marqo
from git import Repo
import shutil
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

def get_env_variable(var_name):
    value = os.getenv(var_name)
    if value is None:
        raise EnvironmentError(f"Переменная окружения {var_name} не установлена")
    return value

def clone_repo(repo_url, repo_path, username, password):
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    auth_repo_url = repo_url.replace('http://', f'http://{username}:{password}@')
    Repo.clone_from(auth_repo_url, repo_path)

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
        except:
            pass

        settings = {
            "treatUrlsAndPointersAsImages": False,
            "model": "hf/multilingual-e5-large",
            "normalizeEmbeddings": True,
        }
        mq.create_index("my-markdown-index", settings_dict=settings)

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
        print("Индексация завершена успешно")
    except Exception as e:
        print(f"Произошла ошибка при индексации: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        repo_url = get_env_variable('REPO_URL')
        repo_path = get_env_variable('REPO_PATH')
        base_url = get_env_variable('BASE_URL')
        username = get_env_variable('GIT_USERNAME')
        password = get_env_variable('GIT_PASSWORD')

        index_documents(repo_url, repo_path, base_url, username, password)
    except EnvironmentError as e:
        print(f"Ошибка: {str(e)}")
        sys.exit(1)