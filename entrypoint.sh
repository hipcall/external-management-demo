#!/bin/bash
# Seed dosyasını ana veritabanı dosyasına kopyala (sıfırla)
echo "Restoring database from seed in data/ directory..."
cp /app/data/database.db.seed /app/data/database.db
# Uygulamayı başlat
echo "Starting application..."
exec python app.py
