FROM python:3.11-slim

RUN apt-get update -y && apt-get install -y awscli

WORKDIR /app

# Copy setup.py and requirements first (both needed)
COPY setup.py .
COPY requirements.txt .

# Now install - this will work with -e .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

EXPOSE 8080
CMD ["python", "app.py"]