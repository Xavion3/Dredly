#!/usr/bin/env python

from os import sep as pathsep
from copy import deepcopy
from collections import defaultdict
import re
import xml.etree.ElementTree as ET

##############
# THE PARSER #
##############

class Parser:
	''' The generic parser. '''
	SYS = {'NAME':r'^[a-zA-Z][a-zA-Z0-9_]*$'} # Name, alphanumeric and _ starts with alpha

	def __init__(self, f = None):
		self.parsers = {}
		self.content = {}
		self.xml = []
		if f != None:
			self.parseFile(f)

	##############################
	# Util functions for parsing #
	##############################

	def getBlocks(self, lines, line = 0, ind = 0):
		''' Turns processed lines into blocks. '''
		bits = []
		while line < len(lines):
			if lines[line][0] == ind: # If it's the same level add to list and move on
				bits.append(lines[line])
				line += 1
			elif lines[line][0] < ind: # If it's a lower level return indented bits
				return bits
			elif lines[line][0] > ind: # If it's a higher level change the last line to be of the
				bits[-1] = [bits[-1], self.getBlocks(lines, line, ind+1)] # form [line, [indented lines]]
				while line < len(lines) and lines[line][0] > ind: # Skip to after indented block
					line += 1
		return bits

	def rIn(self, b):
		''' Removes indentation part of lines. '''
		b = b[:] # Prevent direct editing of b
		for i in range(len(b)):
			if type(b[i][0]) == list: # If it's an indented block strip that too
				b[i] = self.rIn(b[i])
			else:
				b[i] = b[i][1]
		return b

	def getFlags(self, s):
		''' Gets the flags from a valid name. '''
		# TODO: (VL) Add error checking to check if it's a name.
		return s.split(':')[1].strip().split('-')

	##########
	# Parser #
	##########

	def parseFile(self, f):
		''' Parses a dredly file. '''
		f.seek(0) # Reset file to start just in case
		# Pull the parts out of the file as blocks
		# Extract the blocks with indentation preserved
		lines = [[len(x)-len(x.lstrip('\t')),str.strip(x)] for x in f if (str.strip(x) and str.strip(x)[0] != '#')] # Process file into list of lines with indentation
		blocks = self.getBlocks(lines)
		
		blocks = self.rIn(blocks) # Strips indentation parts out

		# Now parse the blocks!
		for block in blocks:
			tmp = block[0].split(':')[0].strip().split('-') # Gets name and flag
			name = tmp[0]
			blocktype = 'C' if len(tmp) == 1 else tmp[1] # Gets the R/W/T/C flag, Default to C

			# Check name
			if not re.match(Parser.SYS['NAME'],tmp[0]):
				raise Exception('Invalid name '+tmp[0])

			# Check blocktype and create spot if none
			if blocktype in ['R', 'W']:
				if name in self.parsers:
					if not isinstance(self.parsers[name], RWBlock):
						raise Exception('Read/Write block '+name+' already taken by object')
				else:
					self.parsers[name] = RWBlock(name, self.parsers, self.content)
			elif blocktype == 'T':
				if name in self.parsers:
					if isinstance(self.parsers[name], RWBlock):
						raise Exception('Type block '+name+' already taken by R/W')
					elif self.parsers[0] != None:
						raise Exception('Type block '+name+' already taken by unknown object')
				else:
					self.parsers[name] = [None]
			elif blocktype == 'C':
				if name in self.parsers:
					if not isinstance(self.parsers[name], RWBlock):
						raise Exception(name+' is used as R/W')
					elif not sum(self.parsers[name].complete):
						raise Exception('R/W block '+name+' used while incomplete')
					elif not name in self.content:
						self.content[name] = []
				else:
					raise Exception('No R/W block exists for '+name)
			else:
				raise Exception('Invalid block type '+blocktype)

			# Now fill in that spot with out block.
			if blocktype in ['R', 'W']:
				self.parsers[name].parseBlock(block, blocktype)
			elif blocktype == 'C':
				self.content[name].append(block)

	def createXML(self):
		''' Fills self.xml with the xml. '''
		# Create the xml!
		for p in self.parsers.itervalues():
			if 'FILENAME' in p.flags:
				element = p.parseContent()
				self.xml.append([element, p.flags['FILENAME']])

		
class RWBlock:
	''' A parsed read/write block for use with content parsing. '''
	TYPES = {'INT':r'^[-+]?[0-9]+$', # Integer, postive or negative
	         'FLOAT':r'^[-+]?[0-9]*\.?[0-9]+$', # Floating point number, postive or negative
	         'STR':r'^[^:]*$', # String, no restrictions
	         'BOOL':r'^(0|1|TRUE|FALSE)$'} # Boolean, 0, 1, true, or false

	def __init__(self, name, parsers, content):
		''' Creates the block. '''
		self.name = name
		self.parsers = parsers
		self.content = content
		self.complete = [False, False]
		self.flags = {}
		self.read = {}
		self.write = {}
		self.macrosNeeded = []

	def getFlags(self, s):
		''' Gets the flags from a valid name. '''
		# TODO: (VL) Add error checking to check if it's a name.
		# TODO: (L) Figure out why I've got two copies of this.
		return s.split(':')[1].strip().split('-')

	def parseName(self, s):
		''' Turns a dredly name into a valid regex string. 
		    Returns false if invalid. '''
		# TODO: (M) Error checking, particularly in relevance to balancing brackets
		pattern = '^'
		blank = []
		for i in range(len(s)):
			if i >= 1 and s[i-1] == '\\':
				if s[i] == 'n':
					pattern = pattern[:-1] + '\n'
				else:
					pattern = pattern[:-1] + s[i]
			else:
				pattern += s[i]
		pattern += '$'
		return pattern

	def getInName(self, s, check):
		''' Gets an option from a multi-option name. 
		    check is index for option to get from name s'''
		# Commented code shows how to swap to getting all options instead of just one. 
		# parts = []
		# check = 0
		part = ''
		stack = []
	# while check >= 0:
		#parts.append('')
		for i in range(len(s)):
			if (len(stack) == stack.count(check) and # If it's at the right part in the all sets of brackets
			((not s[i] in ['(', '|', ')']) or (i >= 1 and s[i-1] == '\\'))): # Non special or escaped
				# parts[-1] += s[i]
				part += s[i]
			elif s[i] == '(': # Start new level in stack
				stack.append(0)
			elif s[i] == '|': # Next part in stack
				stack[-1] += 1
			elif s[i] == ')':
				if stack.pop(-1) < check and len(stack) == stack.count(check): # If a level stopped before it should've error
					# check = -2
					# parts.pop(-1)
					raise IndexError('Part not in range for name')
		# check += 1
		return part

	def parseBlock(self, block, blocktype):
		''' Interface function, redirects to correct parsing function. '''
		if blocktype == 'R':
			if self.complete[0]:
				raise Exception('Read block '+self.name+' already exists. Cannot overwrite.')
			else:
				self.parseRead(block)
		elif blocktype == 'W':
			if self.complete[1]:
				raise Exception('Write block '+self.name+' already exists. Cannot overwrite.')
			else:
				self.parseWrite(block)

	def parseRead(self, block):
		''' Parses a block for use. '''
		parsedBlock = {}
		for i in block[1]:
			if type(i) == str:
				flags = map(str.upper, self.getFlags(i))
				varType, flags = flags[0], flags[1:]
				name = i.split(':')[0]
				if varType in ['NUM', 'BOOL', 'STR']:
					parsedBlock[name] = [varType, flags]
				elif varType[0] == '@':
					print 'Macro found in read block. Be careful.'
					parsedBlock[name] = self.parsers[varType[1:]]
			elif type(i) == list:
				flags = map(str.upper, self.getFlags(i[0]))
				varType, flags = flags[0], flags[1:]
				name = i[0].split(':')[0]
				if varType == 'STR': # Strict string.
					parsedBlock[name] = [varType, flags, i[1]]
				else: # Object
					parsedBlock[name] = ['OBJ', flags, self.parseRead(i)]
		if self.name == (block[0].split(':')[0].split('-')[0]):
			self.read = parsedBlock
			self.complete[0] = True
		else:
			return parsedBlock

	def parseWrite(self, block, outermost = True):
		''' Parses a block for use. '''
		parsedBlock = defaultdict(list)
		parsedAttrs = {}
		parsedFlags = []
		for i in block[1]:
			if type(i) == str:
				# Special first
				if i[0] == '!':
					if i.startswith('!FILENAME'):
						self.flags['FILENAME'] = i.split('=')[1].replace('/',pathsep)
					elif i.startswith('!NAME'):
						parsedAttrs['!NAME'] = i.split('=')[1]
					else:
						parsedFlags.append(i)
						print 'Unknown special attribute:', i
					# 	raise Exception('Unknown special attribute.')
				elif i[0] == '@':
					self.macrosNeeded.append(i[1:])
					parsedBlock[i[1:]].append([[i],{},{}])
				elif i.find(':') != -1:
					attribs = {}
					name, attrs = i.split(':')
					name, flags = name.split('-')[0], name.split('-')[1:]
					for attr in [x for x in attrs.split(',') if x]:
						attr = attr.split('=')
						attribs[attr[0]] = attr[1]
					parsedBlock[name].append([flags, attribs, {}])
				elif i.find('=') != -1:
					name, attr = i.split('=')
					parsedAttrs[name] = attr
				else:
					raise Exception('Line "'+i+'" not attribute or tag. Unable to parse.')
			elif type(i) == list:
				if i[0][0] == '!' and i[0][1:7] != 'OBJECT':
					if i[0].startswith('!NAME'):
						# TODO: (H) Add functionality for !NAME
						print '!NAME flag is currently unhandled.\nSkipping...'
					else:
						raise Exception('Unknown special attribute: '+i[0])
				else:
					name, flags = i[0].split(':')
					flags = map(str.strip, flags.split('-'))
					if flags and not flags[0]:
						flags.pop(0)
					pw = self.parseWrite(i, False)
					parsedBlock[name].append([flags+pw[0], pw[1], pw[2]])
		if outermost:
			self.write = parsedBlock
			self.complete[1] = True
		else:
			return parsedFlags, parsedAttrs, parsedBlock

	def parseContent(self):
		''' Parses content using the read and write blocks. Generates a file if required. '''
		# First get the relevant blocks.
		print '\nSTARTING: '+self.name
		try:
			useContent = deepcopy(self.content[self.name])
		except KeyError:
			useContent = False # If there is none of the tag
		macros = False
		for m in self.macrosNeeded:
			if m in self.content:
				macros = True
				break
		if not (useContent or macros): # If there is none of the tag and no macros.
			return
		# Now parse for reading
		if useContent:
			pContent = self.__parseContentRead__(useContent)
		else:
			pContent = [{}]
		# Now for writing.
		elements = []
		for c in pContent:
			elements.extend(self.__parseContentWrite__([c]))
		if not elements:
			return None
		elif 'FILENAME' in self.flags:
			return elements[0]
		else:
			return elements

	def __parseContentRead__(self, useContent, readRules = None):
		''' Parses the content using the read info. '''
		if readRules == None:
			readRules = self.read
		pContent = []
		for i in xrange(len(useContent)):
			pContent.append(dict.fromkeys(readRules))
			for k in pContent[-1]:
				pContent[-1][k] = []
			self.__parseContentReadBlock__(useContent[i], readRules, pContent[-1])
		return pContent

	def __parseContentReadBlock__(self, block, readRules, pContent):
		# print '---B---'
		# print block
		# print readRules
		for attr in block[1]:
			if type(attr) == str:
				attr = map(str.strip,attr.split(':')) # TODO: (VL) Allow for colons in strings.
				if attr[1][0] == attr[1][-1] and attr[1][0] in ['"',"'"]:
					attr[1] = attr[1][1:-1]
				for j in readRules:
					if re.search(self.parseName(j), attr[0], re.I):
						if readRules[j][0] == 'BOOL':
							if not re.search(self.TYPES['BOOL'], attr[1], re.I):
								raise TypeError('Value:'+attr[1]+' not a valid boolean.')
							if attr[1].upper() == 'TRUE':
								attr[1] = '1'
							else:
								attr[1] = '0'
							pContent[j].append(attr[1])
						elif readRules[j][0] == 'NUM':
							if 'INT' in readRules[j] and not re.search(self.TYPES['INT'],attr[1]):
								raise TypeError('Value:'+attr[1]+' not a valid integer.')
							elif not re.search(self.TYPES['FLOAT'], attr[1]):
								raise TypeError('Value:'+attr[1]+' not a valid float.')
							val = float(attr[1])
							for f in readRules[j]:
								if 'CAP' in f:
									low, high = f.split('=')[1].split('/')
									if (low and float(low) > val) or (high and float(high) < val) or (not low and not high):
										raise ValueError('Value:' + attr[1] + ' not in range ('+str(low)+','+str(high)+')')
							pContent[j].append(attr[1])
						elif readRules[j][0] == 'STR':
							if not 'MULTI' in readRules[j][1]:
								attr[1] = attr[1].replace('\\n', ' ')
							if 'STRICT' in readRules[j][1]:
								reFlags = 0
								if 'CI' in readRules[j][1] and not 'CS' in readRules[j][1]:
									reFlags |= re.I
								for s in readRules[j][2]:
									if re.search(self.parseName(s), attr[1], reFlags):
										pContent[j].append(s)
										break
							else:
								if re.search(self.TYPES['STR'], attr[1]):
									pContent[j].append(attr[1])
						else:
							print "Unknown type: " + readRules[j][0]
						break
			elif type(attr) == list:
				attrName = attr[0].split(':')[0].strip()
				for j in readRules:
					if re.search(self.parseName(j), attrName, re.I):
						obj = dict.fromkeys(readRules[j][2])
						for k in obj:
							obj[k] = []
						self.__parseContentReadBlock__(attr, readRules[j][2], obj)
						pContent[j].append(obj)
		# print '---E---'

	def __getTagNum__(self, tag, writeRules, scope, block = None):
		tagNum = 0
		scope = deepcopy(scope)
		if block is not None:
			block = [block]
		else:
			block = writeRules[tag]
		for p in block:
			tagAttribs = p[1]
			if p[0]:
				if p[0][0][0] == '$':
					objName = p[0][0][1:]
					writeCopy = deepcopy(writeRules[tag])
					writeCopy[writeCopy.index(p)][0] = []
					writeCopy = {tag:writeCopy}
					for t in xrange(len(self.sg(scope, objName))):
						tagNum = max(tagNum, self.__getTagNum__(tag, writeCopy, [self.sg(scope, objName)[t]] + scope))
					return tagNum
				elif p[0][0][0] == '@':
					tagNum = 1
			attrs = False
			const = False
			for i in tagAttribs:
				if tagAttribs[i].find('!') != -1 or tagAttribs[i].find('$') != -1:
					attrName = tagAttribs[i][1:].split('?')[0].split('>')[0]
					k, N = self.getAttrName(scope, attrName)
					tagNum = max(tagNum, N)
					attrs = True
				elif i: 
					const = True
			if const and not attrs: # If there was a constant value and no variable values
				tagNum = max(tagNum, 1)
			for t in p[2]: # If any of the children would appear make this appear.
				if tagNum >= 1:
					break
				tagNum = max(tagNum, 1 & self.__getTagNum__(t, p[2], scope))
		return tagNum

	def getAttrName(self, scope, name):
		for s in scope:
			for i in s:
				if re.search(self.parseName(i), name, re.I):
					return i, len(s[i])
		print name, scope[0]
		raise KeyError('Attr "'+name+'" not found in list.')

	def sg(self, scope, key):
		''' Gets the value from the scope. '''
		for s in scope:
			if key in s:
				return s[key]
		print scope, key
		raise KeyError(str(key))

	def __parseContentWrite__(self, scope, writeRules = None, parElement = None, pars = []):
		''' Parses the read content into xml. '''
		# print '--B--'
		if writeRules == None:
			writeRules = self.write
		elif writeRules == {}:
			return {}
		elements = []
		for tag in writeRules:
			for p in writeRules[tag]:
				eleT = ET.Element(tag) # Create the blank template
				eles = []
				# First check if it calls a block.
				if p[0]:
					# if self.name=='test':
					# 	print 'S',p[0]
					ref = filter(lambda x:x[0]=='$',p[0])
					if ref: # If there is a object reference
						objName = ref[0][1:]
						objName, tagNum = self.getAttrName(scope, objName)
						flags = deepcopy(p[0])
						flags.remove(ref[0])
						# if self.name=='test':print 'F',flags
						writeCopy = deepcopy(writeRules[tag])
						writeCopy[writeCopy.index(p)][0] = flags
						writeCopy = {tag:writeCopy}
						for j in xrange(tagNum):
							eles.append(eleT.copy())
							self.__parseContentWrite__([self.sg(scope, objName)[j]] + scope, writeCopy, eles[-1], pars + [objName])
							if len(eles[-1]):# and tag == list(eles[-1])[0].tag:
								eles = eles[:-1] + list(eles[-1])
						if tag == '!OBJECT':
							parElement.extend(eles)
						elif parElement == None:
							elements.extend(eles)
						else:
							parElement.extend(eles)
						continue # Skip the rest of the loop
					elif p[0][0][0] == '@': # If there is a macro.
						result = self.parsers[p[0][0][1:]].parseContent()
						eles.extend(result)
						if parElement == None: # I wonder if this will work?
							if len(eles) != 1:
								raise Exception("Serious Problem")
							return eles[0]
						else:
							parElement.extend(eles)
						continue # Skip the rest of the loop
					elif p[0][0][0] == '!':
						print 'Y',p[0]
					else:
						print 'Skipping...'
				# Now for attributes.
				tagNum = self.__getTagNum__(tag, writeRules, scope, p)
				tagAttribs = p[1]
				for j in xrange(tagNum):
					eles.append(eleT.copy())
					for i in tagAttribs:
						attr = self.__parseContentWriteAttr__(tagAttribs[i], scope, pars, j)
						if attr:
							if i == '!NAME':
								eles[-1].tag = attr
							else:
								eles[-1].attrib[i] = attr
						else:
							continue
				# Finally add sub tags before adding them to the parent element
				for e in eles:
					self.__parseContentWrite__(scope, p[2], e, pars)
				if parElement == None:
					elements.extend(eles)
				else:
					if tag == '!OBJECT':
						for e in eles:
							parElement.extend(list(e))
					else:
						parElement.extend(eles)
		return elements

	def __parseContentWriteAttr__(self, attrValue, scope, pars, j = 0):
		''' Creates an attribute. '''
		attrName = attrValue[1:].split('?')[0].split('>')[0]
		if attrValue[0] == '$':
			attrName, N = self.getAttrName(scope, attrName)			
			if N == 0:
				return # If the attr wasn't used skip it.
			if attrValue.find('?i') != -1: # If it's a special one.
				useRead = self.read
				for par in pars:
					useRead = useRead[par][2]
				ind = str(useRead[attrName][2].index(self.sg(scope, attrName)[j]))
				return ind
			elif attrValue.find('>') != -1:
				ind = attrValue.split('>')[1]
				if ind.isdigit():
					ind = int(ind)
					return self.getInName(self.sg(scope, attrName)[j],ind)
				else:
					raise TypeError('Index: '+str(ind)+' not integer.')
			else:
				# print tag, eles, i, attrName, j, pContent, writeRules
				return self.sg(scope, attrName)[j]
		else:
			return attrValue