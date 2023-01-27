import pynetbox, urllib3, networkscan, socket, ipaddress
from extras.scripts import Script

TOKEN='xxx'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #disattiva i warning di sicurezza

class IpScan(Script):
    #optional variables in UI here!
    class Meta:
        name = "IP Scanner"
        description = "Scans available prefixes and updates ip addresses in IPAM Module"
    
    def run(self, data, commit):

        def reverse_lookup(ip):
            '''
            Mini funzione che fa reverse lookup DNS con fallimento controllato
            '''
            try:
                data = socket.gethostbyaddr(ip)
            except Exception:
                return '' #fails gracefully
            if data[0] == '': #se non c'è nome
                return ''
            else:
                return data[0]

        nb = pynetbox.api('https://your.netbox.address', token=TOKEN)
        nb.http_session.verify = False #disattiva il check del certificato

        subnets = nb.ipam.prefixes.all() #estrae tutti i prefissi, in formato x.x.x.x/yy

        for subnet in subnets:
            if str(subnet.status) == 'Reserved': #Do not scan reserved subnets
                self.log_warning(f"Scansione di {subnet.prefix} NON eseguita (is Reserved)")
                continue
            IPv4network = ipaddress.IPv4Network(subnet)
            mask = '/'+str(IPv4network.prefixlen)
            scan = networkscan.Networkscan(subnet)
            scan.run()
            self.log_info(f'Scansione di {subnet} eseguita.')
	    
            #Routine per marcare come DEPRECATED ogni entry in Netbox che non risponda al ping
            for address in IPv4network.hosts(): #per ogni indirizzo della prefix x.x.x.x/yy...
		        #self.log_debug(f'checking {address}...')
                netbox_address = nb.ipam.ip_addresses.get(address=address) #estrai da Netbox le info sull'indirizzo
                if netbox_address != None: #se l'ip esiste in netbox // se non esiste chissene, lascia fare alla discover
                    if str(netbox_address).rpartition('/')[0] in scan.list_of_hosts_found: #se è nella lista dei "vivi"
                        pass #do nothing: Esiste in NB ed è nella lista dei pingati: ok prosegui, te la vedrai dopo quando cicli gli ip che hanno risposto se aggiornare qualcosa
			            #self.log_success(f"L'host {str(netbox_address).rpartition('/')[0]} esiste in netbox ed è stato pingato")
                    else: #se esiste in netbox ma NON è nella lista, marca come deprecato
                        self.log_failure(f"L'host {str(netbox_address)} esiste in netbox ma non risponde --> DEPRECATO")
                        nb.ipam.ip_addresses.update([{'id':netbox_address.id, 'status':'deprecated'},])
            ####

            if scan.list_of_hosts_found == []:
                self.log_warning(f'No host found in network {subnet}')
            else:
                self.log_success(f'IPs found: {scan.list_of_hosts_found}')
            for address1 in scan.list_of_hosts_found: #per ciascun ip nella lista dei pingati...
                ip_mask=str(address1)+mask
                current_in_netbox = nb.ipam.ip_addresses.get(address=ip_mask) #estrai i dati attuali in Netbox relativi all'ip
                #self.log_debug(f'ip pingato: {address1} mask: {mask} --> {ip_mask} // ip estratto da netbox: {current_in_netbox}')
                if current_in_netbox != None: #l'indirizzo pingato è già presente in Netbox, marchiamo come Active e verifichiamo il nome se è cambiato
                    nb.ipam.ip_addresses.update([{'id':current_in_netbox.id, 'status':'active'},])
                    name = reverse_lookup(address1) #risoluzione del nome dal DNS
                    if current_in_netbox.dns_name == name: #i nomi in Netbox e nel DNS coincidono, non fare niente
                        pass
                    else: #i nomi in Netbox e nel DNS *NON* coincidono --> aggiorna Netbox con il nome DNS
                        self.log_success(f'Nome per {address1} aggiornato in {name}')
                        nb.ipam.ip_addresses.update([{'id':current_in_netbox.id, 'dns_name':name},])
                else: #l'indirizzo pingato NON è presente in Netbox, lo devo aggiungere
                    name = reverse_lookup(address1)
                    res = nb.ipam.ip_addresses.create(address=ip_mask, status='active', dns_name=name)
                    if res:
                        self.log_success(f'Aggiunto {address1} - {name}')
                    else:
                        self.log_error(f'Aggiunta di {address1} {name} FALLITA')
