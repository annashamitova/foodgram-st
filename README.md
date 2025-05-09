Запуск проекта в Docker
Перейдите в папку infra и выполните команду:

sh
docker-compose up  
Контейнер frontend (описанный в docker-compose.yml) соберёт необходимые файлы для фронтенда и завершит работу.

Доступ к приложению:

Фронтенд: http://localhost

Документация API: http://localhost/api/docs/

Используемые технологии
База данных: PostgreSQL

Бэкенд: Django 3.2.16 + DRF 3.12.4

Инфраструктура: Docker, Nginx, Gunicorn

CI/CD: GitHub Actions

Локальная установка
1. Клонирование репозитория
sh
git clone https://github.com/annashamitova/foodgram-st  
2. Настройка переменных окружения
Проект использует следующие переменные:

ini
DEBUG  
SECRET_KEY  
DB_NAME  
DB_USER  
DB_PASSWORD  
DB_HOST  
DB_PORT  
DOCKER_USERNAME  # Для загрузки образов бэкенда и фронтенда  
3. Запуск в Docker
sh
docker-compose up -d --build  
После сборки проект будет доступен по адресу:
👉 http://localhost:80

4. Админ-панель Django
Доступна через Gunicorn:
🔗 http://localhost:8000/admin

Импорт данных из фикстур:

sh
python manage.py fill_ingredients  
5. Docker Hub
Образы проекта:
📦 https://hub.docker.com/repositories/annashamitova
