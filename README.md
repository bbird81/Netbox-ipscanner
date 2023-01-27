# Netbox-ipscanner
ip scan script for populating IPAM module in Netbox

# Usage
1. Add required modules (ipcalc and networkscan) in netbox environment by adding them in local_requirements.txt, something like:
```
sudo sh -c "echo 'ipcalc' >> /opt/netbox/local_requirements.txt"
sudo sh -c "echo 'networkscan' >> /opt/netbox/local_requirements.txt"
sudo /opt/netbox/upgrade.sh
sudo systemctl restart netbox netbox-rq
```
2. Copy the script in netbox script directory (usually /opt/netbox/netbox/scripts/).
3. Create a token in Netbox webgui and copy/paste it in variable TOKEN at line #4, so the script can write the DB using netbox API.
4. Replace 'https://your.netbox.address' with your server address @line 27.

That's all, you are ready to go :)

# What it does exactly?
Reads the prefixes in IPAM module and for each subnet makes a ping scan. Every responding address is added into the ip address IPAM module with DNS resolution. If an address exists in Netbox but is not pingable, it is marked as "Deprecated"; if DNS resolution is changed then it's updated.
Subnets marked as "Reserved" are not scanned.
