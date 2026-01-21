FROM python:3.10-slim

# working directory
WORKDIR /code

# Install dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc

# Copy requirements dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .