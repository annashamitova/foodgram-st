
## **Подготовка фронтенда**
Перейдите в папку infra и выполните команду:
```sh
docker-compose up  
```
Контейнер frontend (описанный в docker-compose.yml) соберёт необходимые файлы для фронтенда и завершит работу.

Фронтенд web-приложения: http://localhost
Спецификация API: http://localhost/api/docs/

## **Используемые технологии**
- **СУБД**: PostgreSQL
- **Backend**: Django 3.2.16, Django REST Framework 3.12.4
- **Infrastructure**: Docker, Nginx, Gunicorn
- **CI/CD**: GitHub Actions

 
## **Локальный запуск**

### **1. Клонирование репозитория**
```sh
git clone https://github.com/annashamitova/foodgram-st
```
### **2. Переменные окружения**
Проект использует:
```ini
DEBUG
SECRET_KEY
DB_NAME
DB_USER
DB_PASSWORD
DB_HOST
DB_PORT
DOCKER_USERNAME # Необходим для загрузки образов бекенда и фронтенда
```
### **3. Запуск проекта в Docker**
```sh
docker-compose up -d --build
```
После сборки проект будет доступен по адресу: http://localhost:80

### **4. Доступ к административной панели Django**

Доступна через Gunicorn: http://localhost:8000/admin

Импорт данных из json-фикстуры:
```sh
python manage.py fill_ingredients
```


### **5. Docker Hub**
Образ проекта: https://hub.docker.com/repositories/annashamitova
