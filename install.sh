#!/bin/bash

sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip smbd tshark mc 

cd /home
sudo mkdir ./share

SMB_CONF="/etc/samba/smb.conf"
SHARE_PATH="/home/stickers-printer/input"

sudo mkdir -p $SHARE_PATH
sudo chmod 777 $SHARE_PATH

echo "[PublicShare]
   path = $SHARE_PATH
   browseable = yes
   writable = yes
   guest ok = yes
   create mask = 0777
   directory mask = 0777" | sudo tee -a $SMB_CONF

sudo systemctl restart smbd

PROJECT_DIR="/home/pi/stickers-printer"
sudo rm -rf $PROJECT_DIR
git clone https://github.com/mr12n21/stickers-printer $PROJECT_DIR

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

# Načtení a spuštění služby
sudo systemctl daemon-reload
sudo systemctl enable print_service
sudo systemctl start print_service

echo "Instalace dokončena!"
