from Alchemist import *
class Options_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

		child = None
		try:
			child = list.getChildByName("directory")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__Directory = child
		except (KeyError): self.__Directory = None

	def getParent(self):
		return self.__parent

	def unlink(self):
		if self.__list:
			me = self.__list
			self.__list = None
			me.unlink()
			return self.getParent().delOptions()

	def testDirectory(self, value):
		pass

	def setDirectory(self, value):
		if self.__Directory == None:
			self.__Directory = self.__list.addChild(Data.ADM_TYPE_STRING, "directory")
		return self.__Directory.setValue(value)

	def getDirectory(self):
		if self.__Directory == None: return None
		return self.__Directory.getValue()

	def delDirectory(self):
		if self.__Directory == None: return None
		child = self.__Directory
		self.__Directory = None
		child.unlink()


	def test(self):
		self.testDirectory(self.getDirectory())

		pass

class Logging_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

	def getParent(self):
		return self.__parent

	def unlink(self):
		if self.__list:
			me = self.__list
			self.__list = None
			me.unlink()
			return self.getParent().delLogging()


	def test(self):

		pass

class Controls_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

	def getParent(self):
		return self.__parent

	def unlink(self):
		if self.__list:
			me = self.__list
			self.__list = None
			me.unlink()
			return self.getParent().delControls()


	def test(self):

		pass

class Masters_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

	def getParent(self):
		return self.__parent

	def unlink(self):
		if self.__list:
			me = self.__list
			self.__list = None
			me.unlink()
			return self.getParent().delMasters()

	def testIp(self, value):
		pass

	def setIp(self, pos, value):
		child = self.__list.getChildByIndex(pos)
		return child.setValue(value)

	def getIp(self, pos):
		return self.__list.getChildByIndex(pos).getValue()

	def delIp(self, pos):
		return self.__list.getChildByIndex(pos).unlink()

	def addIp(self):
		self.__list.addChild(Data.ADM_TYPE_STRING, "ip")
		return (self.__list.getNumChildren() - 1)

	def getNumIp(self):
		return self.__list.getNumChildren()

	def moveIp(self, pos1, pos2):
		self.__list.moveChild(self.__list.getChildByIndex(pos1), pos2)

	def test(self):
		for pos in xrange(0, self.getNumIp()): self.testIp(self.getIp(pos))

		pass

class SlaveZone_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

		child = None
		try:
			child = list.getChildByName("name")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__Name = child
		except (KeyError): self.__Name = None

		child = None
		try:
			child = list.getChildByName("file")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__File = child
		except (KeyError): self.__File = None

		child = None
		try:
			child = list.getChildByName("masters")
			if child.getType() != Data.ADM_TYPE_LIST: raise TypeError
			self.__Masters = dnsdata.Masters(child, self)
		except (KeyError): self.__Masters = None

	def getParent(self):
		return self.__parent

	def unlink(self):
		return self.__list.unlink()

	def testName(self, value):
		pass

	def setName(self, value):
		if self.__Name == None:
			self.__Name = self.__list.addChild(Data.ADM_TYPE_STRING, "name")
		return self.__Name.setValue(value)

	def getName(self):
		if self.__Name == None: return None
		return self.__Name.getValue()

	def delName(self):
		if self.__Name == None: return None
		child = self.__Name
		self.__Name = None
		child.unlink()

	def testFile(self, value):
		pass

	def setFile(self, value):
		if self.__File == None:
			self.__File = self.__list.addChild(Data.ADM_TYPE_STRING, "file")
		return self.__File.setValue(value)

	def getFile(self):
		if self.__File == None: return None
		return self.__File.getValue()

	def delFile(self):
		if self.__File == None: return None
		child = self.__File
		self.__File = None
		child.unlink()

	def getMasters(self):
		return self.__Masters

	def delMasters(self):
		if self.__Masters:
			child = self.__Masters
			self.__Masters = None
			child.unlink()

	def createMasters(self):
		child = self.__list.addChild(Data.ADM_TYPE_LIST, "masters")
		self.__Masters = dnsdata.Masters(child, self)
		child.setAnonymous(1)
		return self.__Masters


	def test(self):
		self.testName(self.getName())
		self.testFile(self.getFile())
		if self.getMasters(): self.getMasters().test()

		pass

class SlaveZoneList_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

	def getParent(self):
		return self.__parent

	def unlink(self):
		if self.__list:
			me = self.__list
			self.__list = None
			me.unlink()
			return self.getParent().delSlaveZoneList()

	def getSlaveZone(self, pos):
		return dnsdata.SlaveZone(self.__list.getChildByIndex(pos), self)

	def delSlaveZone(self, pos):
		return self.__list.getChildByIndex(pos).unlink()

	def addSlaveZone(self):
		return dnsdata.SlaveZone(self.__list.addChild(Data.ADM_TYPE_LIST, "slavezone"), self)

	def getNumSlaveZone(self):
		return self.__list.getNumChildren()

	def moveSlaveZone(self, pos1, pos2):
		self.__list.moveChild(self.__list.getChildByIndex(pos1), pos2)


	def test(self):
		for pos in xrange(self.getNumSlaveZone()): self.getSlaveZone(pos).test()

		pass

class Forwarders_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

	def getParent(self):
		return self.__parent

	def unlink(self):
		if self.__list:
			me = self.__list
			self.__list = None
			me.unlink()
			return self.getParent().delForwarders()

	def testIp(self, value):
		pass

	def setIp(self, pos, value):
		child = self.__list.getChildByIndex(pos)
		return child.setValue(value)

	def getIp(self, pos):
		return self.__list.getChildByIndex(pos).getValue()

	def delIp(self, pos):
		return self.__list.getChildByIndex(pos).unlink()

	def addIp(self):
		self.__list.addChild(Data.ADM_TYPE_STRING, "ip")
		return (self.__list.getNumChildren() - 1)

	def getNumIp(self):
		return self.__list.getNumChildren()

	def moveIp(self, pos1, pos2):
		self.__list.moveChild(self.__list.getChildByIndex(pos1), pos2)

	def test(self):
		for pos in xrange(0, self.getNumIp()): self.testIp(self.getIp(pos))

		pass

class ForwardZone_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

		child = None
		try:
			child = list.getChildByName("name")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__Name = child
		except (KeyError): self.__Name = None

		child = None
		try:
			child = list.getChildByName("forwarders")
			if child.getType() != Data.ADM_TYPE_LIST: raise TypeError
			self.__Forwarders = dnsdata.Forwarders(child, self)
		except (KeyError): self.__Forwarders = None

	def getParent(self):
		return self.__parent

	def unlink(self):
		return self.__list.unlink()

	def testName(self, value):
		pass

	def setName(self, value):
		if self.__Name == None:
			self.__Name = self.__list.addChild(Data.ADM_TYPE_STRING, "name")
		return self.__Name.setValue(value)

	def getName(self):
		if self.__Name == None: return None
		return self.__Name.getValue()

	def delName(self):
		if self.__Name == None: return None
		child = self.__Name
		self.__Name = None
		child.unlink()

	def getForwarders(self):
		return self.__Forwarders

	def delForwarders(self):
		if self.__Forwarders:
			child = self.__Forwarders
			self.__Forwarders = None
			child.unlink()

	def createForwarders(self):
		child = self.__list.addChild(Data.ADM_TYPE_LIST, "forwarders")
		self.__Forwarders = dnsdata.Forwarders(child, self)
		child.setAnonymous(1)
		return self.__Forwarders


	def test(self):
		self.testName(self.getName())
		if self.getForwarders(): self.getForwarders().test()

		pass

class ForwardZoneList_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

	def getParent(self):
		return self.__parent

	def unlink(self):
		if self.__list:
			me = self.__list
			self.__list = None
			me.unlink()
			return self.getParent().delForwardZoneList()

	def getForwardZone(self, pos):
		return dnsdata.ForwardZone(self.__list.getChildByIndex(pos), self)

	def delForwardZone(self, pos):
		return self.__list.getChildByIndex(pos).unlink()

	def addForwardZone(self):
		return dnsdata.ForwardZone(self.__list.addChild(Data.ADM_TYPE_LIST, "forwardzone"), self)

	def getNumForwardZone(self):
		return self.__list.getNumChildren()

	def moveForwardZone(self, pos1, pos2):
		self.__list.moveChild(self.__list.getChildByIndex(pos1), pos2)


	def test(self):
		for pos in xrange(self.getNumForwardZone()): self.getForwardZone(pos).test()

		pass

class HintZone_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

		child = None
		try:
			child = list.getChildByName("name")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__Name = child
		except (KeyError): self.__Name = None

		child = None
		try:
			child = list.getChildByName("file")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__File = child
		except (KeyError): self.__File = None

	def getParent(self):
		return self.__parent

	def unlink(self):
		return self.__list.unlink()

	def testName(self, value):
		pass

	def setName(self, value):
		if self.__Name == None:
			self.__Name = self.__list.addChild(Data.ADM_TYPE_STRING, "name")
		return self.__Name.setValue(value)

	def getName(self):
		if self.__Name == None: return None
		return self.__Name.getValue()

	def delName(self):
		if self.__Name == None: return None
		child = self.__Name
		self.__Name = None
		child.unlink()

	def testFile(self, value):
		pass

	def setFile(self, value):
		if self.__File == None:
			self.__File = self.__list.addChild(Data.ADM_TYPE_STRING, "file")
		return self.__File.setValue(value)

	def getFile(self):
		if self.__File == None: return None
		return self.__File.getValue()

	def delFile(self):
		if self.__File == None: return None
		child = self.__File
		self.__File = None
		child.unlink()


	def test(self):
		self.testName(self.getName())
		self.testFile(self.getFile())

		pass

class HintZoneList_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

	def getParent(self):
		return self.__parent

	def unlink(self):
		if self.__list:
			me = self.__list
			self.__list = None
			me.unlink()
			return self.getParent().delHintZoneList()

	def getHintZone(self, pos):
		return dnsdata.HintZone(self.__list.getChildByIndex(pos), self)

	def delHintZone(self, pos):
		return self.__list.getChildByIndex(pos).unlink()

	def addHintZone(self):
		return dnsdata.HintZone(self.__list.addChild(Data.ADM_TYPE_LIST, "hintzone"), self)

	def getNumHintZone(self):
		return self.__list.getNumChildren()

	def moveHintZone(self, pos1, pos2):
		self.__list.moveChild(self.__list.getChildByIndex(pos1), pos2)


	def test(self):
		for pos in xrange(self.getNumHintZone()): self.getHintZone(pos).test()

		pass

class SOA_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

		child = None
		try:
			child = list.getChildByName("pns")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__PNS = child
		except (KeyError): self.__PNS = None

		child = None
		try:
			child = list.getChildByName("contact")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__Contact = child
		except (KeyError): self.__Contact = None

		child = None
		try:
			child = list.getChildByName("serial")
			if child.getType() != Data.ADM_TYPE_INT: raise TypeError
			self.__Serial = child
		except (KeyError): self.__Serial = None

		child = None
		try:
			child = list.getChildByName("refresh")
			if child.getType() != Data.ADM_TYPE_INT: raise TypeError
			self.__Refresh = child
		except (KeyError): self.__Refresh = None

		child = None
		try:
			child = list.getChildByName("retry")
			if child.getType() != Data.ADM_TYPE_INT: raise TypeError
			self.__Retry = child
		except (KeyError): self.__Retry = None

		child = None
		try:
			child = list.getChildByName("expire")
			if child.getType() != Data.ADM_TYPE_INT: raise TypeError
			self.__Expire = child
		except (KeyError): self.__Expire = None

		child = None
		try:
			child = list.getChildByName("minimum")
			if child.getType() != Data.ADM_TYPE_INT: raise TypeError
			self.__Minimum = child
		except (KeyError): self.__Minimum = None

	def getParent(self):
		return self.__parent

	def unlink(self):
		if self.__list:
			me = self.__list
			self.__list = None
			me.unlink()
			return self.getParent().delSOA()

	def testPNS(self, value):
		pass

	def setPNS(self, value):
		if self.__PNS == None:
			self.__PNS = self.__list.addChild(Data.ADM_TYPE_STRING, "pns")
		return self.__PNS.setValue(value)

	def getPNS(self):
		if self.__PNS == None: return None
		return self.__PNS.getValue()

	def delPNS(self):
		if self.__PNS == None: return None
		child = self.__PNS
		self.__PNS = None
		child.unlink()

	def testContact(self, value):
		pass

	def setContact(self, value):
		if self.__Contact == None:
			self.__Contact = self.__list.addChild(Data.ADM_TYPE_STRING, "contact")
		return self.__Contact.setValue(value)

	def getContact(self):
		if self.__Contact == None: return None
		return self.__Contact.getValue()

	def delContact(self):
		if self.__Contact == None: return None
		child = self.__Contact
		self.__Contact = None
		child.unlink()

	def testSerial(self, value):
		pass

	def setSerial(self, value):
		if self.__Serial == None:
			self.__Serial = self.__list.addChild(Data.ADM_TYPE_INT, "serial")
		return self.__Serial.setValue(value)

	def getSerial(self):
		if self.__Serial == None: return None
		return self.__Serial.getValue()

	def delSerial(self):
		if self.__Serial == None: return None
		child = self.__Serial
		self.__Serial = None
		child.unlink()

	def testRefresh(self, value):
		pass

	def setRefresh(self, value):
		if self.__Refresh == None:
			self.__Refresh = self.__list.addChild(Data.ADM_TYPE_INT, "refresh")
		return self.__Refresh.setValue(value)

	def getRefresh(self):
		if self.__Refresh == None: return None
		return self.__Refresh.getValue()

	def delRefresh(self):
		if self.__Refresh == None: return None
		child = self.__Refresh
		self.__Refresh = None
		child.unlink()

	def testRetry(self, value):
		pass

	def setRetry(self, value):
		if self.__Retry == None:
			self.__Retry = self.__list.addChild(Data.ADM_TYPE_INT, "retry")
		return self.__Retry.setValue(value)

	def getRetry(self):
		if self.__Retry == None: return None
		return self.__Retry.getValue()

	def delRetry(self):
		if self.__Retry == None: return None
		child = self.__Retry
		self.__Retry = None
		child.unlink()

	def testExpire(self, value):
		pass

	def setExpire(self, value):
		if self.__Expire == None:
			self.__Expire = self.__list.addChild(Data.ADM_TYPE_INT, "expire")
		return self.__Expire.setValue(value)

	def getExpire(self):
		if self.__Expire == None: return None
		return self.__Expire.getValue()

	def delExpire(self):
		if self.__Expire == None: return None
		child = self.__Expire
		self.__Expire = None
		child.unlink()

	def testMinimum(self, value):
		pass

	def setMinimum(self, value):
		if self.__Minimum == None:
			self.__Minimum = self.__list.addChild(Data.ADM_TYPE_INT, "minimum")
		return self.__Minimum.setValue(value)

	def getMinimum(self):
		if self.__Minimum == None: return None
		return self.__Minimum.getValue()

	def delMinimum(self):
		if self.__Minimum == None: return None
		child = self.__Minimum
		self.__Minimum = None
		child.unlink()


	def test(self):
		self.testPNS(self.getPNS())
		self.testContact(self.getContact())
		self.testSerial(self.getSerial())
		self.testRefresh(self.getRefresh())
		self.testRetry(self.getRetry())
		self.testExpire(self.getExpire())
		self.testMinimum(self.getMinimum())

		pass

class NS_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

		child = None
		try:
			child = list.getChildByName("host")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__Host = child
		except (KeyError): self.__Host = None

		child = None
		try:
			child = list.getChildByName("appliesto")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__AppliesTo = child
		except (KeyError): self.__AppliesTo = None

	def getParent(self):
		return self.__parent

	def unlink(self):
		return self.__list.unlink()

	def testHost(self, value):
		pass

	def setHost(self, value):
		if self.__Host == None:
			self.__Host = self.__list.addChild(Data.ADM_TYPE_STRING, "host")
		return self.__Host.setValue(value)

	def getHost(self):
		if self.__Host == None: return None
		return self.__Host.getValue()

	def delHost(self):
		if self.__Host == None: return None
		child = self.__Host
		self.__Host = None
		child.unlink()

	def testAppliesTo(self, value):
		pass

	def setAppliesTo(self, value):
		if self.__AppliesTo == None:
			self.__AppliesTo = self.__list.addChild(Data.ADM_TYPE_STRING, "appliesto")
		return self.__AppliesTo.setValue(value)

	def getAppliesTo(self):
		if self.__AppliesTo == None: return None
		return self.__AppliesTo.getValue()

	def delAppliesTo(self):
		if self.__AppliesTo == None: return None
		child = self.__AppliesTo
		self.__AppliesTo = None
		child.unlink()


	def test(self):
		self.testHost(self.getHost())
		self.testAppliesTo(self.getAppliesTo())

		pass

class NSList_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

	def getParent(self):
		return self.__parent

	def unlink(self):
		if self.__list:
			me = self.__list
			self.__list = None
			me.unlink()
			return self.getParent().delNSList()

	def getNS(self, pos):
		return dnsdata.NS(self.__list.getChildByIndex(pos), self)

	def delNS(self, pos):
		return self.__list.getChildByIndex(pos).unlink()

	def addNS(self):
		return dnsdata.NS(self.__list.addChild(Data.ADM_TYPE_LIST, "ns"), self)

	def getNumNS(self):
		return self.__list.getNumChildren()

	def moveNS(self, pos1, pos2):
		self.__list.moveChild(self.__list.getChildByIndex(pos1), pos2)


	def test(self):
		for pos in xrange(self.getNumNS()): self.getNS(pos).test()

		pass

class PTR_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

		child = None
		try:
			child = list.getChildByName("ip")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__Ip = child
		except (KeyError): self.__Ip = None

		child = None
		try:
			child = list.getChildByName("host")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__Host = child
		except (KeyError): self.__Host = None

	def getParent(self):
		return self.__parent

	def unlink(self):
		return self.__list.unlink()

	def testIp(self, value):
		pass

	def setIp(self, value):
		if self.__Ip == None:
			self.__Ip = self.__list.addChild(Data.ADM_TYPE_STRING, "ip")
		return self.__Ip.setValue(value)

	def getIp(self):
		if self.__Ip == None: return None
		return self.__Ip.getValue()

	def delIp(self):
		if self.__Ip == None: return None
		child = self.__Ip
		self.__Ip = None
		child.unlink()

	def testHost(self, value):
		pass

	def setHost(self, value):
		if self.__Host == None:
			self.__Host = self.__list.addChild(Data.ADM_TYPE_STRING, "host")
		return self.__Host.setValue(value)

	def getHost(self):
		if self.__Host == None: return None
		return self.__Host.getValue()

	def delHost(self):
		if self.__Host == None: return None
		child = self.__Host
		self.__Host = None
		child.unlink()


	def test(self):
		self.testIp(self.getIp())
		self.testHost(self.getHost())

		pass

class PTRList_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

	def getParent(self):
		return self.__parent

	def unlink(self):
		if self.__list:
			me = self.__list
			self.__list = None
			me.unlink()
			return self.getParent().delPTRList()

	def getPTR(self, pos):
		return dnsdata.PTR(self.__list.getChildByIndex(pos), self)

	def delPTR(self, pos):
		return self.__list.getChildByIndex(pos).unlink()

	def addPTR(self):
		return dnsdata.PTR(self.__list.addChild(Data.ADM_TYPE_LIST, "ptr"), self)

	def getNumPTR(self):
		return self.__list.getNumChildren()

	def movePTR(self, pos1, pos2):
		self.__list.moveChild(self.__list.getChildByIndex(pos1), pos2)


	def test(self):
		for pos in xrange(self.getNumPTR()): self.getPTR(pos).test()

		pass

class MReverseZone_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

		child = None
		try:
			child = list.getChildByName("name")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__Name = child
		except (KeyError): self.__Name = None

		child = None
		try:
			child = list.getChildByName("file")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__File = child
		except (KeyError): self.__File = None

		child = None
		try:
			child = list.getChildByName("soa")
			if child.getType() != Data.ADM_TYPE_LIST: raise TypeError
			self.__SOA = dnsdata.SOA(child, self)
		except (KeyError): self.__SOA = None

		child = None
		try:
			child = list.getChildByName("nslist")
			if child.getType() != Data.ADM_TYPE_LIST: raise TypeError
			self.__NSList = dnsdata.NSList(child, self)
		except (KeyError): self.__NSList = None

		child = None
		try:
			child = list.getChildByName("ptrlist")
			if child.getType() != Data.ADM_TYPE_LIST: raise TypeError
			self.__PTRList = dnsdata.PTRList(child, self)
		except (KeyError): self.__PTRList = None

	def getParent(self):
		return self.__parent

	def unlink(self):
		return self.__list.unlink()

	def testName(self, value):
		pass

	def setName(self, value):
		if self.__Name == None:
			self.__Name = self.__list.addChild(Data.ADM_TYPE_STRING, "name")
		return self.__Name.setValue(value)

	def getName(self):
		if self.__Name == None: return None
		return self.__Name.getValue()

	def delName(self):
		if self.__Name == None: return None
		child = self.__Name
		self.__Name = None
		child.unlink()

	def testFile(self, value):
		pass

	def setFile(self, value):
		if self.__File == None:
			self.__File = self.__list.addChild(Data.ADM_TYPE_STRING, "file")
		return self.__File.setValue(value)

	def getFile(self):
		if self.__File == None: return None
		return self.__File.getValue()

	def delFile(self):
		if self.__File == None: return None
		child = self.__File
		self.__File = None
		child.unlink()

	def getSOA(self):
		return self.__SOA

	def delSOA(self):
		if self.__SOA:
			child = self.__SOA
			self.__SOA = None
			child.unlink()

	def createSOA(self):
		child = self.__list.addChild(Data.ADM_TYPE_LIST, "soa")
		self.__SOA = dnsdata.SOA(child, self)
		return self.__SOA

	def getNSList(self):
		return self.__NSList

	def delNSList(self):
		if self.__NSList:
			child = self.__NSList
			self.__NSList = None
			child.unlink()

	def createNSList(self):
		child = self.__list.addChild(Data.ADM_TYPE_LIST, "nslist")
		self.__NSList = dnsdata.NSList(child, self)
		child.setAnonymous(1)
		return self.__NSList

	def getPTRList(self):
		return self.__PTRList

	def delPTRList(self):
		if self.__PTRList:
			child = self.__PTRList
			self.__PTRList = None
			child.unlink()

	def createPTRList(self):
		child = self.__list.addChild(Data.ADM_TYPE_LIST, "ptrlist")
		self.__PTRList = dnsdata.PTRList(child, self)
		child.setAnonymous(1)
		return self.__PTRList


	def test(self):
		self.testName(self.getName())
		self.testFile(self.getFile())
		if self.getSOA(): self.getSOA().test()
		if self.getNSList(): self.getNSList().test()
		if self.getPTRList(): self.getPTRList().test()

		pass

class MReverseZoneList_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

	def getParent(self):
		return self.__parent

	def unlink(self):
		if self.__list:
			me = self.__list
			self.__list = None
			me.unlink()
			return self.getParent().delMReverseZoneList()

	def getMReverseZone(self, pos):
		return dnsdata.MReverseZone(self.__list.getChildByIndex(pos), self)

	def delMReverseZone(self, pos):
		return self.__list.getChildByIndex(pos).unlink()

	def addMReverseZone(self):
		return dnsdata.MReverseZone(self.__list.addChild(Data.ADM_TYPE_LIST, "mreversezone"), self)

	def getNumMReverseZone(self):
		return self.__list.getNumChildren()

	def moveMReverseZone(self, pos1, pos2):
		self.__list.moveChild(self.__list.getChildByIndex(pos1), pos2)


	def test(self):
		for pos in xrange(self.getNumMReverseZone()): self.getMReverseZone(pos).test()

		pass

class A_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

		child = None
		try:
			child = list.getChildByName("host")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__Host = child
		except (KeyError): self.__Host = None

		child = None
		try:
			child = list.getChildByName("ip")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__Ip = child
		except (KeyError): self.__Ip = None

	def getParent(self):
		return self.__parent

	def unlink(self):
		return self.__list.unlink()

	def testHost(self, value):
		pass

	def setHost(self, value):
		if self.__Host == None:
			self.__Host = self.__list.addChild(Data.ADM_TYPE_STRING, "host")
		return self.__Host.setValue(value)

	def getHost(self):
		if self.__Host == None: return None
		return self.__Host.getValue()

	def delHost(self):
		if self.__Host == None: return None
		child = self.__Host
		self.__Host = None
		child.unlink()

	def testIp(self, value):
		pass

	def setIp(self, value):
		if self.__Ip == None:
			self.__Ip = self.__list.addChild(Data.ADM_TYPE_STRING, "ip")
		return self.__Ip.setValue(value)

	def getIp(self):
		if self.__Ip == None: return None
		return self.__Ip.getValue()

	def delIp(self):
		if self.__Ip == None: return None
		child = self.__Ip
		self.__Ip = None
		child.unlink()


	def test(self):
		self.testHost(self.getHost())
		self.testIp(self.getIp())

		pass

class AList_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

	def getParent(self):
		return self.__parent

	def unlink(self):
		if self.__list:
			me = self.__list
			self.__list = None
			me.unlink()
			return self.getParent().delAList()

	def getA(self, pos):
		return dnsdata.A(self.__list.getChildByIndex(pos), self)

	def delA(self, pos):
		return self.__list.getChildByIndex(pos).unlink()

	def addA(self):
		return dnsdata.A(self.__list.addChild(Data.ADM_TYPE_LIST, "a"), self)

	def getNumA(self):
		return self.__list.getNumChildren()

	def moveA(self, pos1, pos2):
		self.__list.moveChild(self.__list.getChildByIndex(pos1), pos2)


	def test(self):
		for pos in xrange(self.getNumA()): self.getA(pos).test()

		pass

class CNAME_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

		child = None
		try:
			child = list.getChildByName("alias")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__Alias = child
		except (KeyError): self.__Alias = None

		child = None
		try:
			child = list.getChildByName("host")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__Host = child
		except (KeyError): self.__Host = None

	def getParent(self):
		return self.__parent

	def unlink(self):
		return self.__list.unlink()

	def testAlias(self, value):
		pass

	def setAlias(self, value):
		if self.__Alias == None:
			self.__Alias = self.__list.addChild(Data.ADM_TYPE_STRING, "alias")
		return self.__Alias.setValue(value)

	def getAlias(self):
		if self.__Alias == None: return None
		return self.__Alias.getValue()

	def delAlias(self):
		if self.__Alias == None: return None
		child = self.__Alias
		self.__Alias = None
		child.unlink()

	def testHost(self, value):
		pass

	def setHost(self, value):
		if self.__Host == None:
			self.__Host = self.__list.addChild(Data.ADM_TYPE_STRING, "host")
		return self.__Host.setValue(value)

	def getHost(self):
		if self.__Host == None: return None
		return self.__Host.getValue()

	def delHost(self):
		if self.__Host == None: return None
		child = self.__Host
		self.__Host = None
		child.unlink()


	def test(self):
		self.testAlias(self.getAlias())
		self.testHost(self.getHost())

		pass

class CNAMEList_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

	def getParent(self):
		return self.__parent

	def unlink(self):
		if self.__list:
			me = self.__list
			self.__list = None
			me.unlink()
			return self.getParent().delCNAMEList()

	def getCNAME(self, pos):
		return dnsdata.CNAME(self.__list.getChildByIndex(pos), self)

	def delCNAME(self, pos):
		return self.__list.getChildByIndex(pos).unlink()

	def addCNAME(self):
		return dnsdata.CNAME(self.__list.addChild(Data.ADM_TYPE_LIST, "cname"), self)

	def getNumCNAME(self):
		return self.__list.getNumChildren()

	def moveCNAME(self, pos1, pos2):
		self.__list.moveChild(self.__list.getChildByIndex(pos1), pos2)


	def test(self):
		for pos in xrange(self.getNumCNAME()): self.getCNAME(pos).test()

		pass

class MX_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

		child = None
		try:
			child = list.getChildByName("priority")
			if child.getType() != Data.ADM_TYPE_INT: raise TypeError
			self.__Priority = child
		except (KeyError): self.__Priority = None

		child = None
		try:
			child = list.getChildByName("host")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__Host = child
		except (KeyError): self.__Host = None

		child = None
		try:
			child = list.getChildByName("appliesto")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__AppliesTo = child
		except (KeyError): self.__AppliesTo = None

	def getParent(self):
		return self.__parent

	def unlink(self):
		return self.__list.unlink()

	def testPriority(self, value):
		pass

	def setPriority(self, value):
		if self.__Priority == None:
			self.__Priority = self.__list.addChild(Data.ADM_TYPE_INT, "priority")
		return self.__Priority.setValue(value)

	def getPriority(self):
		if self.__Priority == None: return None
		return self.__Priority.getValue()

	def delPriority(self):
		if self.__Priority == None: return None
		child = self.__Priority
		self.__Priority = None
		child.unlink()

	def testHost(self, value):
		pass

	def setHost(self, value):
		if self.__Host == None:
			self.__Host = self.__list.addChild(Data.ADM_TYPE_STRING, "host")
		return self.__Host.setValue(value)

	def getHost(self):
		if self.__Host == None: return None
		return self.__Host.getValue()

	def delHost(self):
		if self.__Host == None: return None
		child = self.__Host
		self.__Host = None
		child.unlink()

	def testAppliesTo(self, value):
		pass

	def setAppliesTo(self, value):
		if self.__AppliesTo == None:
			self.__AppliesTo = self.__list.addChild(Data.ADM_TYPE_STRING, "appliesto")
		return self.__AppliesTo.setValue(value)

	def getAppliesTo(self):
		if self.__AppliesTo == None: return None
		return self.__AppliesTo.getValue()

	def delAppliesTo(self):
		if self.__AppliesTo == None: return None
		child = self.__AppliesTo
		self.__AppliesTo = None
		child.unlink()


	def test(self):
		self.testPriority(self.getPriority())
		self.testHost(self.getHost())
		self.testAppliesTo(self.getAppliesTo())

		pass

class MXList_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

	def getParent(self):
		return self.__parent

	def unlink(self):
		if self.__list:
			me = self.__list
			self.__list = None
			me.unlink()
			return self.getParent().delMXList()

	def getMX(self, pos):
		return dnsdata.MX(self.__list.getChildByIndex(pos), self)

	def delMX(self, pos):
		return self.__list.getChildByIndex(pos).unlink()

	def addMX(self):
		return dnsdata.MX(self.__list.addChild(Data.ADM_TYPE_LIST, "mx"), self)

	def getNumMX(self):
		return self.__list.getNumChildren()

	def moveMX(self, pos1, pos2):
		self.__list.moveChild(self.__list.getChildByIndex(pos1), pos2)


	def test(self):
		for pos in xrange(self.getNumMX()): self.getMX(pos).test()

		pass

class MForwardZone_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

		child = None
		try:
			child = list.getChildByName("name")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__Name = child
		except (KeyError): self.__Name = None

		child = None
		try:
			child = list.getChildByName("file")
			if child.getType() != Data.ADM_TYPE_STRING: raise TypeError
			self.__File = child
		except (KeyError): self.__File = None

		child = None
		try:
			child = list.getChildByName("soa")
			if child.getType() != Data.ADM_TYPE_LIST: raise TypeError
			self.__SOA = dnsdata.SOA(child, self)
		except (KeyError): self.__SOA = None

		child = None
		try:
			child = list.getChildByName("alist")
			if child.getType() != Data.ADM_TYPE_LIST: raise TypeError
			self.__AList = dnsdata.AList(child, self)
		except (KeyError): self.__AList = None

		child = None
		try:
			child = list.getChildByName("nslist")
			if child.getType() != Data.ADM_TYPE_LIST: raise TypeError
			self.__NSList = dnsdata.NSList(child, self)
		except (KeyError): self.__NSList = None

		child = None
		try:
			child = list.getChildByName("cnamelist")
			if child.getType() != Data.ADM_TYPE_LIST: raise TypeError
			self.__CNAMEList = dnsdata.CNAMEList(child, self)
		except (KeyError): self.__CNAMEList = None

		child = None
		try:
			child = list.getChildByName("mxlist")
			if child.getType() != Data.ADM_TYPE_LIST: raise TypeError
			self.__MXList = dnsdata.MXList(child, self)
		except (KeyError): self.__MXList = None

	def getParent(self):
		return self.__parent

	def unlink(self):
		return self.__list.unlink()

	def testName(self, value):
		pass

	def setName(self, value):
		if self.__Name == None:
			self.__Name = self.__list.addChild(Data.ADM_TYPE_STRING, "name")
		return self.__Name.setValue(value)

	def getName(self):
		if self.__Name == None: return None
		return self.__Name.getValue()

	def delName(self):
		if self.__Name == None: return None
		child = self.__Name
		self.__Name = None
		child.unlink()

	def testFile(self, value):
		pass

	def setFile(self, value):
		if self.__File == None:
			self.__File = self.__list.addChild(Data.ADM_TYPE_STRING, "file")
		return self.__File.setValue(value)

	def getFile(self):
		if self.__File == None: return None
		return self.__File.getValue()

	def delFile(self):
		if self.__File == None: return None
		child = self.__File
		self.__File = None
		child.unlink()

	def getSOA(self):
		return self.__SOA

	def delSOA(self):
		if self.__SOA:
			child = self.__SOA
			self.__SOA = None
			child.unlink()

	def createSOA(self):
		child = self.__list.addChild(Data.ADM_TYPE_LIST, "soa")
		self.__SOA = dnsdata.SOA(child, self)
		return self.__SOA

	def getAList(self):
		return self.__AList

	def delAList(self):
		if self.__AList:
			child = self.__AList
			self.__AList = None
			child.unlink()

	def createAList(self):
		child = self.__list.addChild(Data.ADM_TYPE_LIST, "alist")
		self.__AList = dnsdata.AList(child, self)
		child.setAnonymous(1)
		return self.__AList

	def getNSList(self):
		return self.__NSList

	def delNSList(self):
		if self.__NSList:
			child = self.__NSList
			self.__NSList = None
			child.unlink()

	def createNSList(self):
		child = self.__list.addChild(Data.ADM_TYPE_LIST, "nslist")
		self.__NSList = dnsdata.NSList(child, self)
		child.setAnonymous(1)
		return self.__NSList

	def getCNAMEList(self):
		return self.__CNAMEList

	def delCNAMEList(self):
		if self.__CNAMEList:
			child = self.__CNAMEList
			self.__CNAMEList = None
			child.unlink()

	def createCNAMEList(self):
		child = self.__list.addChild(Data.ADM_TYPE_LIST, "cnamelist")
		self.__CNAMEList = dnsdata.CNAMEList(child, self)
		child.setAnonymous(1)
		return self.__CNAMEList

	def getMXList(self):
		return self.__MXList

	def delMXList(self):
		if self.__MXList:
			child = self.__MXList
			self.__MXList = None
			child.unlink()

	def createMXList(self):
		child = self.__list.addChild(Data.ADM_TYPE_LIST, "mxlist")
		self.__MXList = dnsdata.MXList(child, self)
		child.setAnonymous(1)
		return self.__MXList


	def test(self):
		self.testName(self.getName())
		self.testFile(self.getFile())
		if self.getSOA(): self.getSOA().test()
		if self.getAList(): self.getAList().test()
		if self.getNSList(): self.getNSList().test()
		if self.getCNAMEList(): self.getCNAMEList().test()
		if self.getMXList(): self.getMXList().test()

		pass

class MForwardZoneList_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

	def getParent(self):
		return self.__parent

	def unlink(self):
		if self.__list:
			me = self.__list
			self.__list = None
			me.unlink()
			return self.getParent().delMForwardZoneList()

	def getMForwardZone(self, pos):
		return dnsdata.MForwardZone(self.__list.getChildByIndex(pos), self)

	def delMForwardZone(self, pos):
		return self.__list.getChildByIndex(pos).unlink()

	def addMForwardZone(self):
		return dnsdata.MForwardZone(self.__list.addChild(Data.ADM_TYPE_LIST, "mforwardzone"), self)

	def getNumMForwardZone(self):
		return self.__list.getNumChildren()

	def moveMForwardZone(self, pos1, pos2):
		self.__list.moveChild(self.__list.getChildByIndex(pos1), pos2)


	def test(self):
		for pos in xrange(self.getNumMForwardZone()): self.getMForwardZone(pos).test()

		pass

class DNS_base:
	def __init__(self, list, parent):
		self.__list = list
		self.__parent = parent

		child = None
		try:
			child = list.getChildByName("options")
			if child.getType() != Data.ADM_TYPE_LIST: raise TypeError
			self.__Options = dnsdata.Options(child, self)
		except (KeyError): self.__Options = None

		child = None
		try:
			child = list.getChildByName("logging")
			if child.getType() != Data.ADM_TYPE_LIST: raise TypeError
			self.__Logging = dnsdata.Logging(child, self)
		except (KeyError): self.__Logging = None

		child = None
		try:
			child = list.getChildByName("controls")
			if child.getType() != Data.ADM_TYPE_LIST: raise TypeError
			self.__Controls = dnsdata.Controls(child, self)
		except (KeyError): self.__Controls = None

		child = None
		try:
			child = list.getChildByName("slavezonelist")
			if child.getType() != Data.ADM_TYPE_LIST: raise TypeError
			self.__SlaveZoneList = dnsdata.SlaveZoneList(child, self)
		except (KeyError): self.__SlaveZoneList = None

		child = None
		try:
			child = list.getChildByName("forwardzonelist")
			if child.getType() != Data.ADM_TYPE_LIST: raise TypeError
			self.__ForwardZoneList = dnsdata.ForwardZoneList(child, self)
		except (KeyError): self.__ForwardZoneList = None

		child = None
		try:
			child = list.getChildByName("hintzonelist")
			if child.getType() != Data.ADM_TYPE_LIST: raise TypeError
			self.__HintZoneList = dnsdata.HintZoneList(child, self)
		except (KeyError): self.__HintZoneList = None

		child = None
		try:
			child = list.getChildByName("mreversezonelist")
			if child.getType() != Data.ADM_TYPE_LIST: raise TypeError
			self.__MReverseZoneList = dnsdata.MReverseZoneList(child, self)
		except (KeyError): self.__MReverseZoneList = None

		child = None
		try:
			child = list.getChildByName("mforwardzonelist")
			if child.getType() != Data.ADM_TYPE_LIST: raise TypeError
			self.__MForwardZoneList = dnsdata.MForwardZoneList(child, self)
		except (KeyError): self.__MForwardZoneList = None

	def getParent(self):
		return self.__parent

	def unlink(self):
		if self.__list:
			me = self.__list
			self.__list = None
			me.unlink()
			return self.getParent().delDNS()

	def getOptions(self):
		return self.__Options

	def delOptions(self):
		if self.__Options:
			child = self.__Options
			self.__Options = None
			child.unlink()

	def createOptions(self):
		child = self.__list.addChild(Data.ADM_TYPE_LIST, "options")
		self.__Options = dnsdata.Options(child, self)
		return self.__Options

	def getLogging(self):
		return self.__Logging

	def delLogging(self):
		if self.__Logging:
			child = self.__Logging
			self.__Logging = None
			child.unlink()

	def createLogging(self):
		child = self.__list.addChild(Data.ADM_TYPE_LIST, "logging")
		self.__Logging = dnsdata.Logging(child, self)
		return self.__Logging

	def getControls(self):
		return self.__Controls

	def delControls(self):
		if self.__Controls:
			child = self.__Controls
			self.__Controls = None
			child.unlink()

	def createControls(self):
		child = self.__list.addChild(Data.ADM_TYPE_LIST, "controls")
		self.__Controls = dnsdata.Controls(child, self)
		return self.__Controls

	def getSlaveZoneList(self):
		return self.__SlaveZoneList

	def delSlaveZoneList(self):
		if self.__SlaveZoneList:
			child = self.__SlaveZoneList
			self.__SlaveZoneList = None
			child.unlink()

	def createSlaveZoneList(self):
		child = self.__list.addChild(Data.ADM_TYPE_LIST, "slavezonelist")
		self.__SlaveZoneList = dnsdata.SlaveZoneList(child, self)
		child.setAnonymous(1)
		return self.__SlaveZoneList

	def getForwardZoneList(self):
		return self.__ForwardZoneList

	def delForwardZoneList(self):
		if self.__ForwardZoneList:
			child = self.__ForwardZoneList
			self.__ForwardZoneList = None
			child.unlink()

	def createForwardZoneList(self):
		child = self.__list.addChild(Data.ADM_TYPE_LIST, "forwardzonelist")
		self.__ForwardZoneList = dnsdata.ForwardZoneList(child, self)
		child.setAnonymous(1)
		return self.__ForwardZoneList

	def getHintZoneList(self):
		return self.__HintZoneList

	def delHintZoneList(self):
		if self.__HintZoneList:
			child = self.__HintZoneList
			self.__HintZoneList = None
			child.unlink()

	def createHintZoneList(self):
		child = self.__list.addChild(Data.ADM_TYPE_LIST, "hintzonelist")
		self.__HintZoneList = dnsdata.HintZoneList(child, self)
		child.setAnonymous(1)
		return self.__HintZoneList

	def getMReverseZoneList(self):
		return self.__MReverseZoneList

	def delMReverseZoneList(self):
		if self.__MReverseZoneList:
			child = self.__MReverseZoneList
			self.__MReverseZoneList = None
			child.unlink()

	def createMReverseZoneList(self):
		child = self.__list.addChild(Data.ADM_TYPE_LIST, "mreversezonelist")
		self.__MReverseZoneList = dnsdata.MReverseZoneList(child, self)
		child.setAnonymous(1)
		return self.__MReverseZoneList

	def getMForwardZoneList(self):
		return self.__MForwardZoneList

	def delMForwardZoneList(self):
		if self.__MForwardZoneList:
			child = self.__MForwardZoneList
			self.__MForwardZoneList = None
			child.unlink()

	def createMForwardZoneList(self):
		child = self.__list.addChild(Data.ADM_TYPE_LIST, "mforwardzonelist")
		self.__MForwardZoneList = dnsdata.MForwardZoneList(child, self)
		child.setAnonymous(1)
		return self.__MForwardZoneList


	def test(self):
		if self.getOptions(): self.getOptions().test()
		if self.getLogging(): self.getLogging().test()
		if self.getControls(): self.getControls().test()
		if self.getSlaveZoneList(): self.getSlaveZoneList().test()
		if self.getForwardZoneList(): self.getForwardZoneList().test()
		if self.getHintZoneList(): self.getHintZoneList().test()
		if self.getMReverseZoneList(): self.getMReverseZoneList().test()
		if self.getMForwardZoneList(): self.getMForwardZoneList().test()

		pass

import dnsdata
