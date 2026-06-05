FROM python:3.10-slim

RUN pip install --no-cache-dir watchdog Pyro5

WORKDIR /app

COPY . .

# O banco de dados será criado pelo código, mas garantimos que o diretório existe
RUN mkdir -p data

CMD ["python", "main.py"]
