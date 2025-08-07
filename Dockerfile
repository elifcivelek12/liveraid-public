# Python'un resmi imajını temel al
FROM python:3.9-slim

# Çalışma dizinini ayarla
WORKDIR /app

# Bağımlılıkları kopyala ve kur
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarını kopyala
COPY . .

# Uygulamayı çalıştırmak için Gunicorn'u kullan
# PORT ortam değişkeni Cloud Run tarafından otomatik olarak sağlanır
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app