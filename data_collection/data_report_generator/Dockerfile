FROM python:3.13-alpine

COPY . /app
WORKDIR /app

RUN apk add --no-cache git make musl-dev gcc

RUN pip install -r /app/requirements.txt

CMD ["python3", "-u", "/app/main.py"]