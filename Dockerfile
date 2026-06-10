# --- Этап 1: Сборка (Build stage) ---
FROM python:3.14-slim AS builder

# Устанавливаем uv для сверхбыстрой установки зависимостей
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /build

# Устанавливаем системные зависимости для компиляции
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем только файлы зависимостей для кеширования слоев
COPY requirements.txt .
# Устанавливаем зависимости в системное окружение (site-packages)
RUN uv pip install --no-cache --system -r requirements.txt


# --- Этап 2: Финальный образ (Runtime stage) ---
FROM python:3.14-slim

# Оптимизация Python и настройка таймзоны
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TZ=Europe/Moscow

# Устанавливаем tzdata для таймзоны и создаем пользователя (без root)
RUN apt-get update && apt-get install -y --no-install-recommends tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 1000 appuser && useradd -r -u 1000 -g appuser appuser

WORKDIR /app

# Копируем только установленные пакеты из первого этапа
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем исходный код и меняем владельца на appuser
COPY --chown=appuser:appuser . .

# Переключаемся на пользователя
USER appuser
