apt-get update
apt-get install -y samba
useradd -m user
echo -e "password\npassword" | smbpasswd -a user
mkdir -p /shared
chown user:user /shared
chmod 755 /shared
smbd --foreground --no-process-group