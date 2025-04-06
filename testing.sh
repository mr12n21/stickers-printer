#!/bin/bash

set -e

echo "Instaluji potřebné balíčky..."
sudo apt update && sudo apt install -y \
  python3 \
  python3-pip \
  python3-venv \
  git \
  cifs-utils

# --- 2. Klonování GitHub repozitáře ---
REPO_URL=""
DEST_DIR="./"

echo "Klonuji repozitář..."
git clone $REPO_URL $DEST_DIR

# --- 3. Připojení k SMB disku (anonymně) ---
SMB_SHARE="//192.168.1.100/public/stitky"
MOUNT_POINT="/mnt/smb_share"

echo "Připojuji SMB disk (anonymně)..."
sudo mkdir -p $MOUNT_POINT

# Záznam do /etc/fstab pro automatické připojení bez přihlašování
echo "$SMB_SHARE $MOUNT_POINT cifs guest,uid=1000,iocharset=utf8,vers=3.0,nofail 0 0" | sudo tee -a /etc/fstab

# Ruční mount hned teď
sudo mount -a

# --- 4. Vytvoření a aktivace virtuálního prostředí + instalace závislostí ---
cd $DEST_DIR
echo "Vytvářím virtuální prostředí..."
python3 -m venv venv
source venv/bin/activate

echo "Instaluji Python knihovny..."
pip install --upgrade pip
pip install -r requirements.txt

# --- 5. Vytvoření systemd služby pro spuštění Python skriptu po startu ---
SERVICE_NAME="myproject.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"

echo "Vytvářím systemd službu..."
sudo tee $SERVICE_PATH > /dev/null <<EOL
[Unit]
Description=Spuštění Python skriptu po startu
After=network-online.target
Wants=network-online.target

[Service]
User=pracovni
WorkingDirectory=$DEST_DIR
ExecStart=$DEST_DIR/venv/bin/python3 $DEST_DIR/main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOL

sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo "Hotovo! SMB disk i Python skript se automaticky spustí po restartu."
