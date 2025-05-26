#!/bin/bash

# Čekání na tiskárnu
while [ ! -e /dev/usb/lp0 ]; do
  sleep 1
done

# Oprávnění pro tiskárnu
chmod 666 /dev/usb/lp0

# Aktivace virtuálního prostředí a spuštění Python skriptu

cd /home/camp/stickers-printer/
source ./venv/bin/activate
pip install -r requirements.txt
python3 app.py
