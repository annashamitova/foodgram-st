FROM python:3.9

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt --no-cache-dir

RUN mkdir -p /app/static

CMD ["sh", "-c", "cd foodgram && python manage.py migrate --noinput && python manage.py fill_ingredients && python manage.py collectstatic --noinput && gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 100"]
