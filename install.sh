#!/bin/bash

SMB_SHARE_DIR="/home/pi/smb_share"
PDF_DIR="$SMB_SHARE_DIR/pdf_files"
TICKET_PRINTER_NAME="MiniPrinter"
USER="pi"
PASSWORD="pi_password"
PDF_AGE_LIMIT=7

setup_smb_share() {
    echo "setup smb share..."
    sudo apt-get update
    sudo apt-get install -y samba samba-common-bin

    if [ ! -d "$SMB_SHARE_DIR" ]; then
        mkdir -p "$SMB_SHARE_DIR"
        mkdir -p "$PDF_DIR"
    fi

    sudo bash -c "cat >> /etc/samba/smb.conf <<EOL

[public_share]
   path = $SMB_SHARE_DIR
   available = yes
   valid users = $USER
   read only = no
   browsable = yes
   public = yes
   writable = yes
EOL"
    sudo systemctl restart smbd
    echo "smb is setup"
}

print_pdf() {
    local pdf_file="$1"
    
    if [ ! -f "$pdf_file" ]; then
        echo "file $pdf_file error"
        return 1
    fi

    echo "printing pdf: $pdf_file"
    
    lp -d "$TICKET_PRINTER_NAME" "$pdf_file"
    
    if [ $? -eq 0 ]; then
        echo "print is complet"
        rm "$pdf_file"
        echo "file is remove"
    else
        echo "error print: $pdf_file!"
        return 1
    fi
}

cleanup_old_pdfs() {
    echo "remove file with expirtation $PDF_AGE_LIMIT"
    find "$PDF_DIR" -type f -name "*.pdf" -mtime +$PDF_AGE_LIMIT -exec rm {} \;
    echo "file is remove $PDF_AGE_LIMIT"
}

check_and_restart_smb() {
    echo "control smb"
    
    if ! smbclient -L //localhost -U "$USER%$PASSWORD" &> /dev/null; then
        echo "restart smb service"
        sudo systemctl restart smbd
        echo "complet"
    else
        sudo systemctl status smdb
    fi
}

main() {
    if [ ! -d "$SMB_SHARE_DIR" ]; then
        setup_smb_share
    fi    
    check_and_restart_smb
    
    echo "look to $PDF_DIR"
    for pdf_file in "$PDF_DIR"/*.pdf; do
        if [ -f "$pdf_file" ]; then
            print_pdf "$pdf_file"
        fi
    done
    
    cleanup_old_pdfs
}

main