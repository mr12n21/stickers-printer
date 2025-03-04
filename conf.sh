#!/bin/bash

sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip smbd tshark mc nmap

cd /home/pi

PROJECT_DIR="/home/pi/"
sudo rm -rf $PROJECT_DIR
git clone https://github.com/mr12n21/stickers-printer $PROJECT_DIR

sudo mkdir -p $SHARE_PATH
sudo chmod 777 $SHARE_PATH

cd $PROJECT_DIR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

deactivate

SERVICE_FILE="/etc/systemd/system/print_service.service"
echo "[Unit]
Description=Python Print Service
After=network.target

[Service]
ExecStart=/home/pi/stickers-printer/venv/bin/python /home/pi/stickers-printer/main.py
WorkingDirectory=/home/pi/stickers-printer
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target" | sudo tee $SERVICE_FILE

sudo systemctl daemon-reload
sudo systemctl enable print_service
sudo systemctl start print_service

echo "Instalace dokončena!"
