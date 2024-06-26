FROM python:3.10-slim

RUN apt-get update && apt-get install -y git iputils-ping net-tools cron
RUN apt-get upgrade -y git

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN echo "marqo" >> /etc/hosts

# Объявляем аргументы сборки
ARG REPO_URL
ARG REPO_PATH
ARG BASE_URL
ARG GIT_USERNAME
ARG GIT_PASSWORD
ARG MARQO_URL

# Устанавливаем переменные окружения
ENV REPO_URL=${REPO_URL}
ENV REPO_PATH=${REPO_PATH}
ENV BASE_URL=${BASE_URL}
ENV GIT_USERNAME=${GIT_USERNAME}
ENV GIT_PASSWORD=${GIT_PASSWORD}
ENV MARQO_URL=${MARQO_URL}

# Создаем скрипт для загрузки переменных окружения
RUN echo '#!/bin/bash' > /load_env.sh && \
    echo 'printenv | sed "s/^\(.*\)$/export \1/g" > /env.sh' >> /load_env.sh && \
    chmod +x /load_env.sh

# Модифицируем cron-задачу для использования переменных окружения
RUN echo "0 * * * * . /env.sh; /usr/local/bin/python /app/app.py >> /var/log/cron.log 2>&1" > /etc/cron.d/indexer-cron
RUN chmod 0644 /etc/cron.d/indexer-cron
RUN crontab /etc/cron.d/indexer-cron
RUN touch /var/log/cron.log

# Создаем скрипт для запуска приложения и cron
RUN echo '#!/bin/bash' > /start.sh && \
    echo '/load_env.sh' >> /start.sh && \
    echo 'python /app/app.py &' >> /start.sh && \
    echo 'cron' >> /start.sh && \
    echo 'tail -f /var/log/cron.log' >> /start.sh && \
    chmod +x /start.sh

# Запускаем скрипт для старта приложения и cron
CMD ["/start.sh"]