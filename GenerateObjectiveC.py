import re
import pprint
import string
import plistlib
import xml.dom.minidom
from xml.dom.minidom import Node

class VarProperties:
	def __init__(self, node):
		self.constName = node.getAttribute("name")
		self.varType = node.getAttribute("type")
		self.varValue = node.getAttribute("value")
			
	def setProperties(self):
		self.setPropertyNames()
		
	def setPropertyNames(self):
		self.setVariableName()
		self.setConstVarName()
			
	def setVariableName(self):
		varName = string.capwords(self.constName, '_').replace('_', '')
		self.varName = varName[:1].lower() + varName[1:]
		
	def setConstVarName(self):
		self.constVarName = 'k' + string.capwords(self.constName, '_').replace('_', '')
		
	def getPropertyConstName(self):
		return self.constName
		
	def getPropertyValue(self):
		return self.varValue
		
	def getDeclaration(self):
		# int variable;
		return '{0} {1};'.format(self.varType, self.varName)
	
	def getPrintDeclaration(self):
		return '\t{0}\n'.format(self.getDeclaration())
		
	def getProperty(self):
		# @property (readonly) int variable;
		if (self.varType == 'NSMutableArray'):
			headerProperty = '@property (readonly, assign) {0}* {1};\n'.format(self.varType, self.varName)
		else:
			headerProperty = '@property (readonly) {0} {1};\n'.format(self.varType, self.varName)
		return headerProperty
	
	def getSynthesize(self):
		# @synthesize vairable;
		return '@synthesize {0};\n'.format(self.varName)
	
	def getConstDeclaration(self):
		# static NSString* const kGameConfigurationFileName = @"GameConfiguration";
		return 'static NSString* const {0} = @"{1}";\n'.format(self.constVarName, self.constName)
	
	def getAssignCommand(self):
		# enemiesEnabled = [[configuration objectForKey:kEnableEnemies] boolValue];
		# upImpulseToApply = [[configuration objectForKey:kUpImpulseToApply] intValue];
		# maxStrengthShortSwipe = [[configuration objectForKey:kMaxStrengthShortSwipe] floatValue];
		# wiresPosition = [configuration objectForKey:kWiresPosition];
		if (self.varType == 'NSMutableArray'):
			assignCommand = '{0} = [configuration objectForKey:{1}];\n'.format(self.varName, self.constVarName)
		else:
			assignCommand = '{0} = [[configuration objectForKey:{1}] {2}Value];\n'.format(self.varName, self.constVarName, self.varType)
		return assignCommand

class Goc:
	def __init__(self):
		self.gocDeclareStart = '[[[gocDeclareStart]]]'
		self.gocDeclareEnd = '[[[gocDeclareEnd]]]'
		self.gocPropertyStart = '[[[gocPropertyStart]]]'
		self.gocPropertyEnd = '[[[gocPropertyEnd]]]'
		self.gocSynthesizeStart = '[[[gocSynthesizeStart]]]'
		self.gocSynthesizeEnd = '[[[gocSynthesizeEnd]]]'
		self.gocAssignStart = '[[[gocAssignStart]]]'
		self.gocAssignEnd = '[[[gocAssignEnd]]]'
		
	def isBeginSpecLine(self, line):
		return string.find(line, self.gocDeclareStart) >= 0
		
	def isEndOutputLine(self, line):
		return string.find(line, self.gocDeclareEnd) >= 0
		
def isBeginSpecLine(s):
    return string.find(s, '[[[gocDeclareStart]]]') >= 0

def isEndOutputLine(s):
	return string.find(s, '[[[gocDeclareEnd]]]') >= 0

def main():
	
	# Get the properties XML
	doc = xml.dom.minidom.parse("properties.xml")
	
	mapping = {}
	
	# For each property create object of VarProperties
	for node in doc.getElementsByTagName("property"):
		varProps = VarProperties(node)
		varProps.setProperties()
		mapping[propName] = varProps
	
	# Open the header file
	headerFile = open("SettingsManager.h", "r+")
	headerFull = headerFile.read()
	headerFile.seek(0)
	
	# Open the implementation file
	implementFile = open("SettingsManager.m", "r")
	implementationFull = implementationFile.read()
	implementationFile.seek(0)
	
	# Open the plist file
	plistProperties = plistlib.readPlist("GameConfiguration.plist")
	for key, varProp in mapping.iteritems():
		if varProp.getPropertyConstName() not in plistProperties:
			plistProperties[varProp.getPropertyConstName()] = varProp.getPropertyValue()
	plistlib.writePlist(plistProperties, "GameConfiguration.plist")
	
	# Create the generic objective-c object
	gocObject = Goc(headerFull, implementationFull)
	
	line = headerFile.readline()
	outputStream = ''
	counter = 0
	while line:
		# Build the output stream
		outputStream += line
		if gocObject.isBeginSpecLine(line):
			# Get regular expression re.findall(r'gocDeclareStart.+gocDeclareEnd', headerFull, re.DOTALL)
			match = re.findall(r'gocDeclareStart.+gocDeclareEnd', headerFull, re.DOTALL)
			for key, varProp in mapping.iteritems():
				if (varProp.getDeclaration() not in match[0]):
					outputStream += varProp.getPrintDeclaration()
		line = headerFile.readline()
		
	headerFile.seek(0)
	headerFile.write(outputStream)
	
	if headerFile:
		headerFile.close()
	if implementFile:
		implementFile.close()
	
# Standard boilerplate to call the main() function.
if __name__ == '__main__':
  main()