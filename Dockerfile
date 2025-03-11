# Используем официальный образ Python
FROM python:3.10

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файлы проекта
COPY requirements.txt /app/
COPY . /app/

# Устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Запуск приложения
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "mis_backend.wsgi:application"]
