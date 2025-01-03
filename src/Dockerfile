FROM python:3.12

# Установим системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Установим Poetry
RUN pip install poetry

# Установим переменную окружения для работы Poetry
# (Poetry по умолчанию использует виртуальные окружения, но мы отключим это
# для совместимости с контейнером)
ENV POETRY_VIRTUALENVS_CREATE=false

# Установим рабочую директорию
WORKDIR /app

# Скопируем описание зависимостей
COPY pyproject.toml poetry.lock* /app/

# Установим зависимости приложения
RUN poetry install --no-root

# Копируем оставшийся код приложения в контейнер
COPY . /app/

# Команда для запуска приложения (сначала миграции, потом запуск)
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]