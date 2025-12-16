FROM python:3.10

# Install FFmpeg for screenshot extraction
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt --no-cache-dir
RUN chmod +x start.sh
CMD ["python3", "main.py"]
