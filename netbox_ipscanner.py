import pynetbox, urllib3, networkscan, socket, ipaddress
from extras.scripts import Script

TOKEN='xxx'

NETBOXURL='https://your.netbox.address'

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) # disable safety warnings

class IpScan(Script):
    # optional variables in UI here!
    class Meta:
        name = "IP Scanner"
        description = "Scans available prefixes and updates ip addresses in IPAM Module"

    def run(self, data, commit):

        def reverse_lookup(ip):
            '''
            Mini function that does DNS reverse lookup with controlled failure
            '''
            try:
                data = socket.gethostbyaddr(ip)
            except Exception:
                return '' # fails gracefully
            if data[0] == '': # if there is no name
                return ''
            else:
                return data[0]

        nb = pynetbox.api(NETBOXURL, token=TOKEN)
        nb.http_session.verify = False # disable certificate checking

        subnets = nb.ipam.prefixes.all()  # extracts all prefixes, in format x.x.x.x/yy

        for subnet in subnets:
            if str(subnet.status) == 'Reserved': # Do not scan reserved subnets
                self.log_warning(f"Scan of {subnet.prefix} NOT done (is Reserved)")
                continue
            IPv4network = ipaddress.IPv4Network(subnet)
            mask = '/'+str(IPv4network.prefixlen)
            scan = networkscan.Networkscan(subnet)
            scan.run()
            self.log_info(f'Scan of {subnet} done.')

            # extract address info from Netbox
            netbox_addresses = dict()
            for ip in nb.ipam.ip_addresses.filter(parent=str(subnet)):
                netbox_addresses[str(ip)] = ip

            # Routine to mark as DEPRECATED each Netbox entry that does not respond to ping
            for address in IPv4network.hosts(): # for each address of the prefix x.x.x.x/yy...
		        #self.log_debug(f'checking {address}...')
                netbox_address = netbox_addresses.get(str(address)+mask)
                if netbox_address != None: # if the ip exists in netbox // if none exists, leave it to discover
                    if str(netbox_address).rpartition('/')[0] in scan.list_of_hosts_found:  # if he is in the list of "alive"
                        pass # do nothing: It exists in NB and is in the pinged list: ok continue, you will see it later when you cycle the ip addresses that have responded whether to update something
			            #self.log_success(f"L'host {str(netbox_address).rpartition('/')[0]} esiste in netbox ed è stato pingato")
                    else: # if it exists in netbox but is NOT in the list, mark it as deprecated
                        self.log_failure(f"Host {str(netbox_address)} exists in netbox but not responding --> DEPRECATED")
                        nb.ipam.ip_addresses.update([{'id':netbox_address.id, 'status':'deprecated'},])
            ####

            if scan.list_of_hosts_found == []:
                self.log_warning(f'No host found in network {subnet}')
            else:
                self.log_success(f'IPs found: {scan.list_of_hosts_found}')
            for address1 in scan.list_of_hosts_found: # for each ip in the ping list...
                ip_mask=str(address1)+mask
                current_in_netbox = netbox_addresses.get(ip_mask)
                #self.log_debug(f'pinged ip: {address1} mask: {mask} --> {ip_mask} // extracted ip from netbox: {current_in_netbox}')
                if current_in_netbox != None: # the pinged address is already present in the Netbox, mark it as Active and check the name if it has changed
                    if current_in_netbox.status.value != "active":
                        nb.ipam.ip_addresses.update([{'id':current_in_netbox.id, 'status':'active'},])
                    name = reverse_lookup(address1) # name resolution from DNS
                    if current_in_netbox.dns_name.lower() == name.lower(): # the names in Netbox and DNS match, do nothing
                        pass
                    else: # the names in Netbox and in DNS *DO NOT* match --> update Netbox with DNS name
                        self.log_success(f'Name for {address1} updated to {name}')
                        nb.ipam.ip_addresses.update([{'id':current_in_netbox.id, 'dns_name':name},])
                else: # the pinged address is NOT present in Netbox, I have to add it
                    name = reverse_lookup(address1) # name resolution from DNS
                    res = nb.ipam.ip_addresses.create(address=ip_mask, status='active', dns_name=name)
                    if res:
                        self.log_success(f'Added {address1} - {name}')
                    else:
                        self.log_error(f'Adding {address1} - {name} FAILED')
