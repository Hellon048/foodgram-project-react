FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
COPY db.json .
RUN pip3 install -r requirements.txt --no-cache-dir
COPY . .
CMD ["gunicorn", "food_gram.wsgi:application", "--bind", "0:8000" ]