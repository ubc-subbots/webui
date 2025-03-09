FROM --platform=linux/arm64/v8 python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN apt-get update && apt-get install -y util-linux ffmpeg && \
    pip install -r requirements.txt

# Copy backend files
COPY . .

# Copy frontend files
COPY ./frontend /frontend

CMD ["python", "main.py"]