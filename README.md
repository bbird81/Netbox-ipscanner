# Netbox-ipscanner
ip scan script for populating IPAM module in Netbox

# Usage
add required modules in netbox environment and then copy the script in netbox script directory (usually /opt/netbox/netbox/scripts/)... you are ready to go :)

# What it does exactly?
Reads the prefixes in IPAM module and for each subnet makes a ping scan. Every responding address is added into the ip address IPAM module with DNS resolution. If an address exists in Netbox but is not pingable, it is marked as "Deprecated"; if DNS resolution is changed then it's updated.
Subnets marked as "Reserved" are not scanned.
