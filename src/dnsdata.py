from Alchemist import *
from FileBlackBox import *
import sys
import os.path
import re
import string

from dnsdata_base import *
import gettext
_=gettext.gettext

# Hmm is this really needed?
true = (1==1)
false = not true

hname_re = re.compile('^[a-zA-Z0-9.\-]+$')

ip_re = re.compile('^([0-2]?[0-9]?[0-9])\\.([0-2]?[0-9]?[0-9])\\.([0-2]?[0-9]?[0-9])\\.([0-2]?[0-9]?[0-9])(?:\\.in-addr\\.arpa\\.?)?$')

revip_re = re.compile('^([0-2]?[0-9]?[0-9])(?:\\.([0-2]?[0-9]?[0-9]))?(?:\\.([0-2]?[0-9]?[0-9])\\.)?(?:\\.([0-2]?[0-9]?[0-9]))?(?:\\.in-addr\\.arpa)$')

class TestError(Exception):
	def __init__(self, args=None):
		#raise Error("Here with args" + args)
		self.args = args

	#def __str__(self):
		#return Exception.__str__(self)

def checkIpNum(value):
	try:
		m = ip_re.match(value)
		if not m:
			return false
		nums = m.groups()
		if not nums or ( nums and ( len(nums) != 4 )) :
			return false
		
		for i in xrange(0, 4):
			if nums[i] == None:
				return false
			num = int(nums[i])
			if (num < 0) or (num > 255):
				return false
	except TypeError:
		return false
	
	return true


def checkRevIpNum(value):
	try:
		m = revip_re.match(value)
		if not m:
			return false
		nums = m.groups()
		
		if not nums: return false
		
		#print len(nums), " matching groups!", nums
		for i in xrange(0, len(nums)):
			if nums[i] == None:
				continue
			num = int(nums[i])
			if (num < 0) or (num > 255):
				return false
	except TypeError:
		return false
	
	return true

def checkTTL(ttl):
	if ttl < 0:
		return false
	return true
	# add more TTL checking code here

class Options(Options_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		Options_base.__init__(self, list, parent)
		if not self.getDirectory():
			self.setDirectory("/var/named")

	def write(self, fh):
		pass

	def testDirectory(self, dir):
		if not os.path.isabs(dir):
			raise TestError, _("Directory ") + dir + _(" does not begin with a slash!")
		if not os.dir.isdir(dir):
			raise TestError, _("Directory ") + dir + _(" is not an existing directory!")
		# FIXME
		# more checks for valid path here
		
class Logging(Logging_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		Logging_base.__init__(self, list, parent)

class Controls(Controls_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		Controls_base.__init__(self, list, parent)

class Masters(Masters_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		Masters_base.__init__(self, list, parent)

	def testIp(self, value):
		if not checkIpNum(value):
			raise TestError, _("Master ") + value + _(" is not a valid IP address.")

	def test(self):
		Masters_base.test(self)
 		num = self.getNumIp()
 		if num:
 			names = []
 			for i in xrange(0, num):
 				names.append(self.getIp(i))
 			for i in xrange(0, num-1):
 				for j in xrange(i+1, num):
 					if names[j] == names[i]:
 						raise TestError, _("Master ") + names[i] + _(" is defined twice.")
class SlaveZone(SlaveZone_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		SlaveZone_base.__init__(self, list, parent)

	def testName(self, value):
		if not hname_re.match(value):
			raise TestError, _("Slave zone name ") + value + _(" is not a valid domain name.")
		
	
class SlaveZoneList(SlaveZoneList_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		SlaveZoneList_base.__init__(self, list, parent)

class Forwarders(Forwarders_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		Forwarders_base.__init__(self, list, parent)

	def testIp(self, value):
		if not checkIpNum(value):
			raise TestError, _("Forwarder ") + value + _(" is not a valid Ip address.")	
		
class HintZone(HintZone_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		HintZone_base.__init__(self, list, parent)

class HintZoneList(HintZoneList_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		HintZoneList_base.__init__(self, list, parent)

class SOA(SOA_base):
	def __init__(self, list=None, parent=None):
		if list == None: return
		SOA_base.__init__(self, list, parent)
		if not self.getSerial(): self.setSerial(1)
		if not self.getRefresh(): self.setRefresh(28800)
		if not self.getRetry():	self.setRetry(7200)
		if not self.getExpire(): self.setExpire(604800)
		if not self.getMinimum(): self.setMinimum(86400)
		if not self.getContact(): self.setContact("root@localhost")
		if not self.getPNS(): self.setPNS("@")

	def testPNS(self, value):
		if not value:
			raise TestError, _("Primary Nameserver not defined.")
		
		if ((len(value) == 1) and value == "@"):
			return

		#print "testPNS on " + value
		if not ((len(value) > 1) and value[-1] == '.'):
			raise TestError, _("Primary Nameserver `") + value + _("' has no . at the end. You must use a full hostname.")
		if not hname_re.match(value):
			raise TestError, _("Primary Nameserver `") + value + _("' is not a valid hostname or IP address.")
		
		
	def updateSerial(self):
		ser = self.getSerial()
		if ser == None:
			ser = 0
		ser = ser+1
		self.setSerial(ser)

	def test(self):
		SOA_base.test(self)
		
		if self.getRefresh() < self.getRetry():
			raise TestError, _("Refresh value should be bigger than Retry")
		# FIXME
		# add more tests here


	def testSerial(self, value):
		if value <= 0:
			raise TestError, _("Serial number must be >= 1.")

	def testRefresh(self, value):
		if not checkTTL(value):
			raise TestError, _("Refresh value must be >= 0.")

	def testRetry(self, value):
		if not checkTTL(value):
			raise TestError, _("Retry value must be >= 0.")

	def testExpire(self, value):
		if not checkTTL(value):
			raise TestError, _("Expire value must be >= 0.")

	def testMinimum(self, value):
		if not checkTTL(value):
			raise TestError, _("Minimum value must be >= 0.")

	def setContact(self, value):
		if value:
			l = len(value)
			if l:
				value = string.replace(value, '@', '.')
		SOA_base.setContact(self, value)

	def getContact(self):
		value = SOA_base.getContact(self)
		if value:
			l = len(value)
			if l:
				value = string.replace(value, '.', '@', 1)
		return value

class PTR(PTR_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		PTR_base.__init__(self, list, parent)
		if not self.getHost(): self.setHost(_("NewHost"))
		if not self.getIp(): self.setIp("1")

	def testHost(self, value):
		if not value:
			raise TestError, _("PTR hostname not defined")
		
		if not ((len(value) > 1) and value[-1] == '.'):
			raise TestError, _("PTR hostname `") + value + _("' has no . at the end. You must use a full hostname.")

		if not hname_re.match(value):
			raise TestError, value + _(" is not a valid hostname.")
		
	def testIp(self, value):
		try:
			num = int(value)
			if num < 0 or num > 255:
				raise RangeError
		except:
			raise TestError, value + _(" must be in the range 0..255.")
			
class PTRList(PTRList_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		PTRList_base.__init__(self, list, parent)

	def test(self):
		PTRList_base.test(self)
		num = self.getNumPTR()
		if num:
			names = []
			for i in xrange(0, num):
				item = self.getPTR(i)
				item.test()
				names.append(item.getIp())
			for i in xrange(0, num-1):
				for j in xrange(i+1, num):
					if names[j] == names[i]:
						raise TestError, _("IP ") + names[i] + _(" is defined twice.")
		
class A(A_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		A_base.__init__(self, list, parent)
		if not self.getHost(): self.setHost(_("NewHost"))
		if not self.getIp(): self.setIp("0.0.0.0")

	def testHost(self, value):
		if not (hname_re.match(value) or value == '@'):
			raise TestError, value + _(" is not a valid hostname.")
		
	def testIp(self, value):
		if not checkIpNum(value):
			raise TestError, value + _(" is not a valid IP address.")

class AList(AList_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		AList_base.__init__(self, list, parent)

	def test(self):
		AList_base.test(self)
# 		num = self.getNumA()
# 		if num:
# 			names = []
# 			for i in xrange(0, num):
# 				item = self.getA(i)
# 				item.test()
# 				names.append(item.getHost())
# 			for i in xrange(0, num-1):
# 				for j in xrange(i+1, num):
# 					if names[j] == names[i]:
# 						raise TestError, _("Hostname ") + names[i] + _(" is defined twice.")
			
class NS(NS_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		NS_base.__init__(self, list, parent)
		if not self.getHost(): self.setHost(_("NewHost"))
		if not self.getAppliesTo(): self.setAppliesTo("@")


	def testHost(self, value):
		if not hname_re.match(value):
			raise TestError, _("Nameserver ") + value + _(" is not a valid hostname.")
		

	def testAppliesTo(self, value):
		if value != "@" and not hname_re.match(value):
			raise TestError, value + _(" is not a valid host or domain name.")

class NSList(NSList_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		NSList_base.__init__(self, list, parent)
		
	def test(self):
		NSList_base.test(self)
		num = self.getNumNS()
		if num:
			names = []
			for i in xrange(0, num):
				item = self.getNS(i)
				item.test()
				names.append((item.getHost(), item.getAppliesTo()))
			for i in xrange(0, num-1):
				for j in xrange(i+1, num):
					if names[j] == names[i]:
						raise TestError, _("Nameserver ") + names[i][0] + _(" is defined twice for ") + names[i][1] + "."

class CNAME(CNAME_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		CNAME_base.__init__(self, list, parent)
		if not self.getHost(): self.setHost(_("New"))
		if not self.getAlias(): self.setAlias(_("New"))

	def testHost(self, value):
		if not hname_re.match(value):
			raise TestError, value + _(" is not a valid hostname.")

	def testAlias(self, value):
		if not hname_re.match(value):
			raise TestError, value + _(" is not a valid hostname.")
	
class CNAMEList(CNAMEList_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		CNAMEList_base.__init__(self, list, parent)

	def test(self):
		CNAMEList_base.test(self)
		num = self.getNumCNAME()
		if num:
			names = []
			for i in xrange(0, num):
				item = self.getCNAME(i)
				item.test()
				names.append(item.getAlias())
			for i in xrange(0, num-1):
				for j in xrange(i+1, num):
					if names[j] == names[i]:
						raise TestError, _("Alias ") + names[i] + _(" is defined twice.")

class MX(MX_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		MX_base.__init__(self, list, parent)
		if not self.getPriority(): self.setPriority(0)
		if not self.getHost(): self.setHost(_("NewHost"))
		if not self.getAppliesTo(): self.setAppliesTo("@")

	def testHost(self, value):
		if not hname_re.match(value):
			raise TestError, value + _(" is not a valid hostname.")
		
class MXList(MXList_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		MXList_base.__init__(self, list, parent)

	def test(self):
		MXList_base.test(self)

class ForwardZone(ForwardZone_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		ForwardZone_base.__init__(self, list, parent)
		if not self.getName(): self.setName(_("<New Forward Zone>"))
		if not self.getForwarders(): self.createForwarders()
	
	def testName(self, value):
		if not hname_re.match(value):
			raise TestError, _("Forward zone name ") + value + _(" is not a valid domain name.")
		
class ForwardZoneList(ForwardZoneList_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		ForwardZoneList_base.__init__(self, list, parent)

	def test(self):
		ForwardZoneList_base.test(self)
		num = self.getNumForwardZone()
		if num:
			names = []
			for i in xrange(0, num):
				zone = self.getForwardZone(i)
				zone.test()
				names.append(zone.getName())
			for i in xrange(0, num-1):
				for j in xrange(i+1, num):
					if names[j] == names[i]:
						raise TestError, _("Zone ") + names[i] + _(" is defined twice.")

class MReverseZone(MReverseZone_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		MReverseZone_base.__init__(self, list, parent)
		if not self.getSOA(): self.createSOA()
		if not self.getNSList(): self.createNSList()
		if not self.getPTRList(): self.createPTRList()
		if not self.getName(): self.setName(_("<New Reverse Zone>"))
		
	def testName(self, value):
		if not checkRevIpNum(value):
			raise TestError, _("Reverse zone name `") + value + _("' is not the end of a reverse IP address.")

	def test(self):
		MReverseZone_base.test(self)
		if (not self.getNSList()) or self.getNSList().getNumNS() < 1:
			raise TestError, _("Reverse zone `") + self.getName() + _("' must list at least one name server") 

class MReverseZoneList(MReverseZoneList_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		MReverseZoneList_base.__init__(self, list, parent)

	def test(self):
		MReverseZoneList_base.test(self)
		num = self.getNumMReverseZone()
		if num:
			names = []
			for i in xrange(0, num):
				zone = self.getMReverseZone(i)
				zone.test()
				names.append(zone.getName())
			for i in xrange(0, num-1):
				for j in xrange(i+1, num):
					if names[j] == names[i]:
						raise TestError, _("Reverse zone ") + names[i] + _(" is defined twice.")

  
class MForwardZone(MForwardZone_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		MForwardZone_base.__init__(self, list, parent)		
		if not self.getSOA(): self.createSOA()
		if not self.getMXList(): self.createMXList()
		if not self.getNSList(): self.createNSList()
		if not self.getAList(): self.createAList()
		if not self.getCNAMEList(): self.createCNAMEList()
		if not self.getName(): self.setName(_("<New Zone>"))


	def testName(self, value):
		if not hname_re.match(value):
			raise TestError, _("Forward zone name ") + value + _(" is not a valid domain name.")
		
	def test(self):
		MForwardZone_base.test(self)
		
			
class MForwardZoneList(MForwardZoneList_base):
	def __init__(self, list = None, parent = None):
		if list == None: return
		MForwardZoneList_base.__init__(self, list, parent)

	def test(self):
		MForwardZoneList_base.test(self)
		num = self.getNumMForwardZone()
		names = []
		if num:
			for i in xrange(0, num):
				zone = self.getMForwardZone(i)
				zone.test()
				names.append(zone.getName())
				pass
			for i in xrange(0, num-1):
				for j in xrange(i+1, num):
					if names[j] == names[i]:
						raise TestError, _("Zone ") + names[i] + _(" is defined twice.")


class DNS(DNS_base):
	def __init__(self, list = None):
		if list == None:
			p = "/etc/alchemist/switchboard/dns.switchboard.adl"
			if os.path.exists("dns.switchboard.adl"):
				p = "dns.switchboard.adl"
			swb = Alchemist.Switchboard(file_path=p)
			input_set = swb.readNamespaceCfg('dns').getChildByName('input_set')
			output_set = swb.readNamespaceCfg('dns').getChildByName('output_set')
			local_box_entry = input_set.getChildByName('local')
			self.local_box = Alchemist.getBox(local_box_entry.getChildByName('box'))
			named_box_entry = output_set.getChildByName('namedconf')
			self.named_box = Alchemist.getBox(named_box_entry.getChildByName('box'))
			zone_box_entry = output_set.getChildByName('zoneconf')
			self.zone_box = Alchemist.getBox(zone_box_entry.getChildByName('box'))
			self.ctx = self.local_box.read()
			self.list = self.ctx.getDataRoot().getChildByIndex(0)
			
		DNS_base.__init__(self, self.list, None)

	def saveLocal(self):
		self.local_box.write(self.ctx)

	def saveBind(self):
		self.zone_box.write(self.ctx)
		self.named_box.write(self.ctx)


if __name__ == '__main__':
	gettext.bindtextdomain("bindconf", "/usr/share/locale")
	gettext.textdomain("bindconf")
	for ip in ["1.1.1.1", "256.1.1.1", "1.1.1.256"]:		
		if checkIpNum(ip):
			print ip, "is valid"
		else:
			print ip, "is not valid"
	for host in [ "/&%9583djfgfg", "445456-sdh.de", "fg-dfg.dr", "dfghdf.dfg.dfgdf"]:
		if not hname_re.match(host):
			print host + " not valid"
	for value in ["1.1.1.1", "1.1.1.1.", "redhat.de.", "test", "1kjsdf"]:
		if checkIpNum(value):
			print value + " seems to be an IP address. Please add a . at the end!"
		if not hname_re.match(value) and not ((len(value) > 1) and value[-1] == '.' and checkIpNum(value[:-1])):
			print value + " is not a valid IP address."

	soa = SOA()
	for host in [ "/&%9583djfgfg", "445456-sdh.de", "fg-dfg.dr", "dfghdf.dfg.dfgdf"]:
		try:
			soa.testPNS(host)
		except TestError, e:
			print e.args

	zone = MReverseZone()
	for host in [ "1.1.1.in-addr.arpa", "256.1.1.in-addr.arpa", "1.1.1.", "dfghdf.dfg.dfgdf"]:
		try:
			zone.testName(host)
		except TestError, e:
			print e.args
	
