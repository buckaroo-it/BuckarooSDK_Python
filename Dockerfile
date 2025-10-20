FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .

RUN pip install --root-user-action=ignore -r requirements.txt

CMD ["tail", "-f", "/dev/null"]
