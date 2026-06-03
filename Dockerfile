FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: run the CLI viz so there's something to see immediately
CMD ["python3", "rl.py", "viz"]
