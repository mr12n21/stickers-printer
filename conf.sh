#!/bin/bash

LOG_FILE="/var/log/stickers_printer_setup.log"
exec > >(tee -a "$LOG_FILE") 2>&1
echo "Starting setup at $(date)"

SMB_IP="192.168.0.10"
SMB_SHARE="stitky"
MOUNT_POINT="/mnt/data"
PROJECT_DIR="/home/pi/stitky"

configure_smb_share() {
    local ip_address="$1"
    local share_name="$2"
    local mount_point="$3"

    echo "Installing cifs-utils..."
    sudo apt install -y cifs-utils || exit 1

    echo "Creating mount point at $mount_point..."
    sudo mkdir -p "$mount_point"
    sudo chmod 777 "$mount_point"

    local fstab_entry="//$ip_address/$share_name $mount_point cifs guest,uid=pi,gid=pi,file_mode=0777,dir_mode=0777,nounix 0 0"
    if ! grep -Fxq "$fstab_entry" /etc/fstab; then
        echo "$fstab_entry" | sudo tee -a /etc/fstab
    fi

    echo "Mounting SMB share..."
    sudo mount -a
    if mountpoint -q "$mount_point"; then
        echo "SMB share mounted successfully."
    else
        echo "Mounting failed."
        exit 1
    fi
}

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root. Use sudo."
    exit 1
fi

echo "Adding user 'pi' to 'lp' group for printer access..."
usermod -aG lp pi

echo "Installing base packages..."
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git || exit 1

configure_smb_share "$SMB_IP" "$SMB_SHARE" "$MOUNT_POINT"

cd "$PROJECT_DIR" || { echo "Project directory not found!"; exit 1; }

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv || exit 1
fi

echo "Installing Python requirements..."
source venv/bin/activate
pip install pyyaml pdfplumber pillow watchdog brother_ql
deactivate

START_SCRIPT="$PROJECT_DIR/start_print_service.sh"
echo "Creating start script..."
cat << 'EOF' > "$START_SCRIPT"
#!/bin/bash
sudo chmod 666 /dev/usb/lp0
cd /home/pi/stitky
source venv/bin/activate
python3 app.py
EOF

chmod +x "$START_SCRIPT"
chown pi:pi "$START_SCRIPT"

SERVICE_FILE="/etc/systemd/system/stickers-printer.service"
echo "Creating systemd service file..."
cat << EOF > "$SERVICE_FILE"
[Unit]
Description=Stickers Printer Service
After=network-online.target

[Service]
ExecStart=$START_SCRIPT
WorkingDirectory=$PROJECT_DIR
Restart=always
User=pi
Group=pi

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading and enabling systemd service..."
systemctl daemon-reload
systemctl enable stickers-printer.service
systemctl start stickers-printer.service
systemctl status stickers-printer.service --no-pager

echo "Setup complete at $(date)!"
