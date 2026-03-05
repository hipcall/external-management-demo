# Python 3.11 slim sürümünü baz alıyoruz
FROM python:3.11-slim

# Uygulama klasörünü oluştur ve oraya geç
WORKDIR /app
RUN mkdir -p /app/data

# Gerekli kütüphaneleri kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyala
COPY . .

# Giriş betiğine çalışma izni ver
RUN chmod +x /app/entrypoint.sh

# Flask'ın çalışacağı portu belirt
EXPOSE 5000

# Uygulamayı giriş betiği ile başlat
ENTRYPOINT ["/app/entrypoint.sh"]
