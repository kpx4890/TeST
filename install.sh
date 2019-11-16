#!/bin/bash
sudo apt update && sudo apt upgrade
sudo apt install -y hostapd dnsmasq
sudo mkdir -p /TeslaCam/ && sudo cp ./httpsServer.py /TeslaCam && sudo cp wallpaper.jpg /TeslaCam &&  openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes && sudo cp ./server.pem /TeslaCam

chmod +x ./subzero.sh && sudo cp ./subzero.sh /usr/local/bin
(sudo crontab -l 2>/dev/null; echo "@reboot /usr/local/bin/subzero.sh") | crontab -

sudo mv /etc/dhcpcd.conf /etc/dhcpcd.bak
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.bak
sudo mv /etc/hostapd/hostapd.conf /etc/hostapd/hostapd.bak
sudo mv /etc/network/interfaces /etc/network/interfaces.bak

sudo cp ./interfaces /etc/network/
sudo cp ./dhcpcd.conf /etc/
sudo cp ./dnsmasq.conf /etc/
sudo cp ./hostapd.conf /etc/hostapd/
echo "DAEMON_CONF=\"/etc/hostapd/hostapd.conf\"" | sudo tee -a /etc/default/hostapd
sudo systemctl unmask hostapd
sudo ldconfig
sudo systemctl enable hostapd
sudo systemctl start hostapd
sudo systemctl enable dnsmasq
