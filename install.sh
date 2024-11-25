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
        echo "Soubor $pdf_file neexistuje!"
        return 1
    fi

    echo "Tisknu PDF soubor: $pdf_file"
    
    lp -d "$TICKET_PRINTER_NAME" "$pdf_file"
    
    if [ $? -eq 0 ]; then
        echo "Tisk dokončen. Mazání souboru..."
        rm "$pdf_file"
        echo "Soubor byl smazán."
    else
        echo "Chyba při tisku souboru $pdf_file!"
        return 1
    fi
}

cleanup_old_pdfs() {
    echo "Mazání souborů PDF starších než $PDF_AGE_LIMIT dní..."
    find "$PDF_DIR" -type f -name "*.pdf" -mtime +$PDF_AGE_LIMIT -exec rm {} \;
    echo "Soubory starší než $PDF_AGE_LIMIT dní byly smazány."
}

check_and_restart_smb() {
    echo "Kontroluji dostupnost SMB serveru..."
    
    if ! smbclient -L //localhost -U "$USER%$PASSWORD" &> /dev/null; then
        echo "SMB server není dostupný. Restartuji Samba službu..."
        sudo systemctl restart smbd
        echo "Samba služba byla restartována."
    else
        echo "SMB server je dostupný."
    fi
}

main() {
    if [ ! -d "$SMB_SHARE_DIR" ]; then
        setup_smb_share
    fi    
    check_and_restart_smb
    
    echo "Procházím PDF soubory v adresáři $PDF_DIR..."
    for pdf_file in "$PDF_DIR"/*.pdf; do
        if [ -f "$pdf_file" ]; then
            print_pdf "$pdf_file"
        fi
    done
    
    cleanup_old_pdfs
}

main