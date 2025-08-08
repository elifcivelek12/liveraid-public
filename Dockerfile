# Python'un resmi imajını temel al
FROM python:3.9-slim

# Çalışma dizinini ayarla
WORKDIR /app

# Bağımlılıkları kopyala ve kur
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarını kopyala
COPY . .


CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 300 app:app
