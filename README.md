# Netbox-ipscanner
ip scan script for populating IPAM module in Netbox

# Usage
1. Add required modules (ipcalc and networkscan) in netbox environment by adding them in local_requirements.txt, something like:
```
sudo sh -c "echo 'ipcalc' >> /opt/netbox/local_requirements.txt"
sudo sh -c "echo 'networkscan' >> /opt/netbox/local_requirements.txt"
sudo sh -c "echo 'pynetbox' >> /opt/netbox/local_requirements.txt"
sudo /opt/netbox/upgrade.sh
sudo systemctl restart netbox netbox-rq
```
2. Copy the script in netbox script directory (usually /opt/netbox/netbox/scripts/).
3. Create a token in Netbox webgui and copy/paste it in variable TOKEN @ line #4, so the script can write the DB using netbox API.
4. Replace 'https://your.netbox.address' with your server address in variable NETBOXURL @ line #6.

That's all, you are ready to go :)

# What it does exactly?
1. Reads the prefixes in IPAM module and for each subnet makes a ping scan.
2. Every responding address is added into the ip address IPAM module with DNS resolution.
4. If an address exists in Netbox but is not pingable, it is marked as "Deprecated", if DNS resolution is changed then it's updated.
5. Subnets marked as "Reserved" are not scanned.
