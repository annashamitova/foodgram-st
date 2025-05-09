Находясь в папке infra, выполните команду docker-compose up. При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.

По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.

## **Стек**
- **СУБД**: PostgreSQL
- **Backend**: Django 3.2.16, Django REST Framework 3.12.4
- **Infrastructure**: Docker, Nginx, Gunicorn
- **CI/CD**: GitHub Actions


## **Запуск проекта локально**

### **1. Клонировать репозиторий**
```sh
git clone https://github.com/annashamitova/foodgram-st
```
### **2. Переменные окружения**
Проект читает
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
### **3. Запустить проект в Docker**
```sh
docker-compose up -d --build
```
Проект будет доступ по адресу [localhost:80](http://localhost:80)
### **3. Django админка**
доступна прямо через gunicorn по адресу [localhost:8000/admin](http://localhost:8000/admin)

Для импорта продуктов из json-фикстуры
```sh
python manage.py fill_ingredients
```


### **3. Docker Hub**
https://hub.docker.com/repositories/annashamitova





## **Запуск проекта в Docker**
Перейдите в папку infra и выполните команду:
