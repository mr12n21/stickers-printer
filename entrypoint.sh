#!/bin/bash
set -e
chmod +x /entrypoint.sh
apt-get update
apt-get install -y --no-install-recommends vsftpd
rm -rf /var/lib/apt/lists/*
echo "user:password" | chpasswd
mkdir -p /shared
chown user:user /shared
chmod 755 /shared
# Přepsání vsftpd.conf, aby se vyhnulo interaktivnímu dotazu
echo "Y" | dpkg --configure vsftpd
exec vsftpd /etc/vsftpd.conf