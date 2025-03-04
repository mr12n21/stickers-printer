#!/bin/bash

configure_smb_share() {
    local ip_address="$1"
    local username="$2"
    local password="$3"
    local share_name="$4"
    local mount_point="/mnt/$share_name"

    sudo apt install -y cifs-utils
    echo "Creating mount point at $mount_point..."
    sudo mkdir -p "$mount_point"
    sudo chmod 777 "$mount_point"

    local cred_file="/home/pi/.smbcredentials"
    echo "username=$username" | sudo tee "$cred_file"
    echo "password=$password" | sudo tee -a "$cred_file"
    sudo chmod 600 "$cred_file"

    local fstab_entry="//$ip_address/$share_name $mount_point cifs credentials=$cred_file,uid=pi,gid=pi,file_mode=0777,dir_mode=0777 0 0"
    if ! grep -Fxq "$fstab_entry" /etc/fstab; then
        echo "$fstab_entry" | sudo tee -a /etc/fstab
    fi

    echo "Mounting SMB share from $ip_address..."
    sudo mount -a
    if mountpoint -q "$mount_point"; then
        echo "SMB share mounted successfully at $mount_point!"
    else
        echo "error in mounting SMB share"
        exit 1
    fi
}

sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip mc nmap

PROJECT_DIR="/home/pi/"
SHARE_PATH="/mnt/network_storage"

cd /home/pi
sudo rm -rf "$PROJECT_DIR/stickers-printer"

echo "SMB:"
read -p "Enter the IP address of the SMB server (e.g., 192.168.1.100): " smb_ip
read -p "Enter the SMB username: " smb_user
read -s -p "Enter the SMB password: " smb_pass
echo ""
read -p "Enter the SMB share name: " data

if [[ -z "$smb_ip" || -z "$smb_user" || -z "$smb_pass" || -z "$smb_share" ]]; then
    echo "Error: All fields (IP, username, password, share name) are required!"
    exit 1
fi

configure_smb_share "$smb_ip" "$smb_user" "$smb_pass" "$smb_share"

sudo mkdir -p "$SHARE_PATH"
sudo chmod 777 "$SHARE_PATH"

cd "$PROJECT_DIR/stickers-printer"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate

START_SCRIPT="/home/pi/stickers-printer/start_print_service.sh"
echo "Creating start script at $START_SCRIPT..."
echo "#!/bin/bash
# Path to the project directory
PROJECT_DIR=\"/home/pi/stickers-printer\"

# Activate the virtual environment
source \"\$PROJECT_DIR/venv/bin/activate\"

# Run the Python application
exec \"\$PROJECT_DIR/venv/bin/python\" \"\$PROJECT_DIR/main.py\"
" | sudo tee "$START_SCRIPT"

sudo chmod +x "$START_SCRIPT"
sudo chown pi:pi "$START_SCRIPT"

SERVICE_FILE="/etc/systemd/system/print_service.service"
echo "Creating systemd service file at $SERVICE_FILE..."
echo "[Unit]
Description=Python Print Service
After=network.target

[Service]
ExecStart=/home/pi/stickers-printer/start_print_service.sh
WorkingDirectory=/home/pi/stickers-printer
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target" | sudo tee "$SERVICE_FILE"

sudo systemctl daemon-reload
sudo systemctl enable print_service
sudo systemctl start print_service

sudo systemctl status print_service --no-pager

echo "Setup complete! The service should now start automatically on boot."