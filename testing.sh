#!/bin/bash

LOG_FILE="/var/log/stickers_printer_setup.log"
exec > >(tee -a "$LOG_FILE") 2>&1
echo "Starting setup at $(date)"

SMB_IP="192.168.1.100"
SMB_USER="smbuser"
SMB_PASS="smbpass"
SMB_SHARE="shared_folder"
PROJECT_DIR="/home/pi/stickers-printer"
SHARE_PATH="/mnt/network_storage"
REPO_URL="https://github.com/mr12n21/stickers-printer.git"

configure_smb_share() {
    local ip_address="$1"
    local username="$2"
    local password="$3"
    local share_name="$4"
    local mount_point="/home/pracovni/$share_name"

    echo "Installing cifs-utils..."
    sudo apt install -y cifs-utils || { echo "Failed to install cifs-utils"; exit 1; }

    echo "Creating mount point at $mount_point..."
    sudo mkdir -p "$mount_point" || { echo "Failed to create mount point"; exit 1; }
    sudo chmod 777 "$mount_point"

    local cred_file="/home/pi/.smbcredentials"
    echo "Writing credentials to $cred_file..."
    echo "username=$username" | sudo tee "$cred_file" || { echo "Failed to write username"; exit 1; }
    echo "password=$password" | sudo tee -a "$cred_file" || { echo "Failed to write password"; exit 1; }
    sudo chmod 600 "$cred_file"

    local fstab_entry="//$ip_address/$share_name $mount_point cifs credentials=$cred_file,uid=pi,gid=pi,file_mode=0777,dir_mode=0777 0 0"
    if ! grep -Fxq "$fstab_entry" /etc/fstab; then
        echo "Adding SMB share to /etc/fstab..."
        echo "$fstab_entry" | sudo tee -a /etc/fstab || { echo "Failed to update fstab"; exit 1; }
    fi

    echo "Mounting SMB share from $ip_address..."
    sudo mount -a
    if mountpoint -q "$mount_point"; then
        echo "SMB share mounted successfully at $mount_point!"
    else
        echo "Error in mounting SMB share"
        exit 1
    fi
}

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root. Use sudo."
    exit 1
fi

echo "Updating system and installing dependencies..."
apt update && apt upgrade -y || { echo "Failed to update system"; exit 1; }
apt install -y python3 python3-pip mc nmap || { echo "Failed to install packages"; exit 1; }

cd /home/pi || { echo "Failed to change to /home/pi"; exit 1; }
echo "Removing old project directory if it exists..."
rm -rf "$PROJECT_DIR"
echo "Cloning repository from $REPO_URL..."
git clone "$REPO_URL" "$PROJECT_DIR" || { echo "Failed to clone repository"; exit 1; }

configure_smb_share "$SMB_IP" "$SMB_USER" "$SMB_PASS" "$SMB_SHARE"

echo "Setting up share path at $SHARE_PATH..."
mkdir -p "$SHARE_PATH" || { echo "Failed to create $SHARE_PATH"; exit 1; }
chmod 777 "$SHARE_PATH"

cd "$PROJECT_DIR" || { echo "Failed to change to $PROJECT_DIR"; exit 1; }
echo "Creating virtual environment..."
python3 -m venv venv || { echo "Failed to create venv"; exit 1; }
source venv/bin/activate
echo "Installing Python requirements..."
pip install -r requirements.txt || { echo "Failed to install requirements"; exit 1; }
deactivate

START_SCRIPT="$PROJECT_DIR/start_print_service.sh"

chmod +x "$START_SCRIPT"
chown pi:pi "$START_SCRIPT"

SERVICE_FILE="/etc/systemd/system/print_service.service"
echo "Creating systemd service file at $SERVICE_FILE..."
echo "[Unit]
Description=Python Print Service
After=network.target

[Service]
ExecStart=$START_SCRIPT
WorkingDirectory=$PROJECT_DIR
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target" | tee "$SERVICE_FILE" || { echo "Failed to create service file"; exit 1; }

systemctl daemon-reload || { echo "Failed to reload systemd"; exit 1; }
systemctl enable print_service || { echo "Failed to enable service"; exit 1; }
systemctl start print_service || { echo "Failed to start service"; exit 1; }

systemctl status print_service --no-pager

echo "Setup complete at $(date)!"