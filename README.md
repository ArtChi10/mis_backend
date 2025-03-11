# MIS Backend

Проект представляет собой backend для системы управления медицинскими консультациями.

## Технологии

- Django + Django REST Framework
- PostgreSQL
- Docker
- JWT (аутентификация)
- Flake8 (линтер) + pytest (тестирование)

## Установка и запуск

### 1. Клонирование репозитория
```bash
git clone https://github.com/YOUR_USERNAME/mis_backend.git
cd mis_backend
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Запуск через Docker
```bash
docker-compose up -d --build
```

### 4. Применение миграций и создание суперпользователя
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

## API-документация

Доступна по адресу:
- Swagger: [`http://127.0.0.1:8000/api/docs/`](http://127.0.0.1:8000/api/docs/)

## Тестирование
```bash
pytest
```

## Линтер и форматирование
- Проверка кода с Flake8:
```bash
flake8
```
- Автоформатирование с autopep8:
```bash
autopep8 --in-place --aggressive --aggressive core/
```

### 3. Добавление в репозиторий  
```bash
git add README.md
git commit -m "Add README"
git push origin main
```
