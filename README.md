# cupflag

## Требования

- Python 3.11+
- Установленные зависимости из requirements.txt
- Прокси при запуске из региона, где недоступен Cloudflare

## Локальный запуск

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

Запустить нужный скрипт:
python chalenge_V1.py
python chalenge_V2.py
python chalenge_V3.py
```

## Прокси

Использовать файл `proxy.ini`, пример в `proxy.ini.example`

## Логи
Логи пишутся в папку `./logs/`

## Запуск в Docker

```bash
docker compose build
docker compose up -d
```

Контейнер запускается в фоне и ожидает команды для запуска нужного скрипта.
Запустить нужный скрипт внутри:

```bash
docker compose exec main python chalenge_V1.py
docker compose exec main python chalenge_V2.py
docker compose exec main python chalenge_V3.py
```
Логи доступны на хосте в папке `./logs/`.

## Структура проекта

```
.
├── chalenge_V1.py 
├── chalenge_V2.py       
├── chalenge_V3.py  
├── credentials.py   
├── requirements.txt
├── proxy.ini.example
├── Dockerfile
├── docker-compose.yml
└── WRITEUP.md
```
