FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && 

apt-get update && 

apt-get install -y --no-install-recommends libcups2 libusb-1.0-0 && 

apt-get clean && 

rm -rf /var/lib/apt/lists/*
COPY printer_service.py .
CMD ["python", "printer_service.py"]