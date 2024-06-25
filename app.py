import marqo
import os
from git import Repo
import shutil
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk

nltk.download('punkt')
nltk.download('stopwords')

def clone_repo(repo_url, repo_path, username, password):
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    Repo.clone_from(repo_url, repo_path, env={"GIT_ASKPASS": "echo", "GIT_USERNAME": username, "GIT_PASSWORD": password})

def preprocess_text(text):
    text = re.sub(r'\W', ' ', text)
    text = text.lower()
    stop_words = set(stopwords.words('russian'))
    tokens = word_tokenize(text)
    filtered_text = ' '.join([word for word in tokens if word not in stop_words])
    return filtered_text

def index_documents(repo_url, repo_path, base_url, username, password):
    # Клонируем репозиторий
    clone_repo(repo_url, repo_path, username, password)
    
    mq = marqo.Client(url='http://marqo:8882')

    # Удаляем индекс, если он существует
    try:
        mq.index("my-markdown-index").delete()
    except:
        pass

    # Создаем новый индекс с подходящей моделью
    settings = {
        "treatUrlsAndPointersAsImages": False,
        #"model": "sentence-transformers/stsb-xlm-r-multilingual",
        "model": "hf/multilingual-e5-large",
        "normalizeEmbeddings": True,
    }
    mq.create_index("my-markdown-index", settings_dict=settings)

    # Рекурсивно обходим все папки и файлы в клонированном репозитории
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

if __name__ == '__main__':
    repo_url = 'https://0717376:GCXPO89msv@gitlab.muravskiy.com/0717376/requirements.git'
    repo_path = os.path.expanduser("~/Desktop/repository")
    base_url = 'https://gitlab.muravskiy.com/0717376/requirements/blob/main'  # URL к репозиторию на GitLab
    index_documents(repo_url, repo_path, base_url, '0717376', 'GCXPO89msv')