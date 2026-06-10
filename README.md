# cupflag

## Локальный запуск

1. Создать виртуальное окружение и установить зависимости:
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt

2. При запуске скриптов из стран, где не работает cloudflare, необходимо использовать прокси.
Заполнить файл proxy.ini

3. Запустить скрипты:
python chalenge_V1.py
python chalenge_V2.py
python chalenge_V3.py

## Запуск в Docker
docker compose build
docker compose up -d

Контейнер будет запущен в фоновом режиме, чтобы можно запустить несколько скриптов внутри одного контейнера. Решение только для демонстрации.

Запустить нужный скрипт внутри контейнера:
docker compose exec main python chalenge_V1.py
docker compose exec main python chalenge_V2.py
docker compose exec main python chalenge_V3.py

Логи скриптов пишутся в папку ./logs/ на хосте