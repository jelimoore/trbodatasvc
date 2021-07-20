def id2ip(cai, id):
	'''Returns the IP of a radio given the CAI and ID'''
	return (str(cai)+"."+str((id >> 16) & 0xff) +'.'+ str((id >> 8) & 0xff) + '.' + str(id & 0xff))

def ip2id(ipaddr):
	'''Returns the ID of the radio given the IP'''
	a, b, c, d = ipaddr.split('.')
	return ((int(b) << 16) + (int(c) << 8 ) + int(d))

def ip2cai(ipaddr):
	'''Returns the CAI of the radio net given the IP'''
	a, b, c, d = ipaddr.split('.')
	return int(a)