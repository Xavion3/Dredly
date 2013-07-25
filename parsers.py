#!/usr/bin/env python

from os import sep as pathsep
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
			if not Parser.TYPES['NAME'].match(tmp[0]):
				raise Exception('Invalid name '+tmp[0])

			# Check blocktype and create spot if none
			if blocktype in ['R', 'W']:
				if self.parsers.has_key(name):
					if len(self.parsers[name]) != 2:
						raise Exception('Read/Write block '+name+' already taken by type')
					elif self.parsers[0] != None:
						raise Exception('Read/Write block '+name+' already taken by unknown object')
				else:
					self.parsers[name] = RWBlock(name, self.parsers)
			elif blocktype == 'T':
				if self.parsers.has_key(name):
					if isinstance(self.parsers[name], RWBlock):
						raise Exception('Type block '+name+' already taken by R/W')
					elif self.parsers[0] != None:
						raise Exception('Type block '+name+' already taken by unknown object')
				else:
					self.parsers[name] = [None]
			elif blocktype == 'C':
				if self.parsers.has_key(name):
					if not isinstance(self.parsers[name], RWBlock):
						raise Exception(name+' is used as R/W')
					elif not sum(self.parsers[name].complete):
						raise Exception('R/W block '+name+' used while incomplete')
					elif not self.content.has_key(name):
						self.content[name] = []
				else:
					raise Exception('No R/W block exists for '+name)
			else:
				raise Exception('Invalid block type '+blocktype)

			# Now fill in that spot with out block.
			if blocktype in ['R', 'W']:
				self.parsers[name].parseBlock(block, blocktype)
			elif blocktype == 'C':
				self.conntent[name].append(block)

		
class RWBlock:
	''' A parsed read/write block for use with content parsing. '''
	TYPES = {'INT':r'^[-+]?[0-9]+$', # Integer, postive or negative
	         'FLOAT':r'^[-+]?[0-9]*\.?[0-9]+$', # Floating point number, postive or negative
	         'STR':r'^[^:]*$', # String, no restrictions
	         'BOOL':r'^(0|1|TRUE|FALSE)$'} # Boolean, 0, 1, true, or false

	def __init__(self, name, parsers):
		''' Creates the block. '''
		self.name = name
		self.parsers = parsers
		self.complete = [False, False]
		self.flags = {}
		self.read = {}
		self.write = {}
		self.neededContent = [self.name]

	def getFlags(self, s):
		''' Gets the flags from a valid name. '''
		# TODO: (VL) Add error checking to check if it's a name.
		# TODO: (L) Figure out why I've got two copies of this.
		return s.split(':')[1].strip().split('-')

	def parseName(self, s):
		''' Turns a dredly name into a valid regex string. 
		    Returns false if invalid. '''
		# TODO: (M) Error checking, particularly in relevance to balancing brackets
		# Current errors
		# - Fails if encountering unmatched end bracket
		# - Fails if starting with an unescaped |
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
			# if (not s[i] in ['(', '|', ')']) or (i >= 1 and s[i-1] == '\\'): # Non special or escaped
			# 	pattern += s[i]
			# 	continue # Skip to next char to avoid accidently going thorugh with following if's
			# if s[i] == '|': # Or separator
			# 	if s[i-1] in ['(', '|'] or s[i+1] in ['|', ')']: # Matches (|, ||, and |) to check for blanks
			# 		blank[-1] = True
			# 		if re.search(r'\(\|*$', pattern) or re.search(r'^\|*\)', s[i:]) and s[i-1] != '|': # If it's not at the start or the end add if the first of a group
			# 			pattern += '|'
			# 	else: # If isn't a blank then whatevs
			# 		pattern += '|'
			# if s[i] == ')':
			# 	pattern += ')'
			# 	if blank.pop(-1): # Check if the current bracket pair had a blank while removing it from the list
			# 		pattern += '?'
			# if s[i] == '(':
			# 	pattern += '('
			# 	blank.append(False) # Assume no blanks and start another set of brackets
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
					parsedBlock[name] = self.parsers[varType[1:]]
			elif type(i) == list:
				flags = map(str.upper, self.getFlags(i[0]))
				varType, flags = flags[0], flags[1:]
				name = i[0].split(':')[0]
				if varType == 'STR':
					parsedBlock[name] = [varType, flags, i[1]]
		if self.name == (block[0].split(':')[0].split('-')[0]):
			self.read = parsedBlock
			self.complete[0] = True
		else:
			return parsedBlock

	def parseWrite(self, block):
		''' Parses a block for use. '''
		parsedBlock = {}
		for i in block[1]:
			if type(i) == str:
				# Special first
				if i[0] == '!':
					if i.startswith('!FILENAME'):
						self.flags['FILENAME'] = i.split('=')[1].replace('/',pathsep)
					elif i.startswith('!NAME'):
						# TODO: (H) Add functionality for !NAME
						print '!NAME flag is currently unhandled.\nSkipping...'
					else:
						raise Exception('Unknown special attribute.')
				elif i[0] == '@':
					self.neededContent.append(i[1:])
				elif i.find(':') != -1:
					name, attrs = i.split(':')
					name, flags = name.split('-')[0], name.split('-')[1:]
					if attrs:
						attrs = attrs.split('=')
						attrs = {attrs[0]:attrs[1]}
					parsedBlock[name] = [flags, attrs, {}]
				elif i.find('=') != -1:
					pass #TODO: (VH) Attributes of parent class
				else:
					raise Exception('Line "'+i+'" not attribute or tag. Unable to parse.')
			elif type(i) == list:
				if i[0][0] == '!':
					if i[0].startswith('!NAME'):
						# TODO: (H) Add functionality for !NAME
						print '!NAME flag is currently unhandled.\nSkipping...'
					else:
						raise Exception('Unknown special attribute: '+i[0])
				else:
					name = i[0].split(':')[0]
					parsedBlock[name] = [[],{},self.parseWrite(i)]
		if self.name == (block[0].split(':')[0].split('-')[0]):
			self.write = parsedBlock
			self.complete[1] = True
		else:
			return parsedBlock

	def parseContent(self, content):
		''' Parses content using the read and write blocks. Generates a file if required. '''
		# First get the relevant blocks.
		useContent = {}
		for i in self.neededContent:
			if i in content:
				useContent[i] = content[i][:]
		# Now parse for reading
		pContent = self.__parseContentRead__(useContent)
		# Now for writing.
		element = self.__parseContentWrite__(pContent)
		# TODO: (VH) Macros! (@blah)
		return element

	def __parseContentRead__(self, useContent):
		''' Parses the content using the read info. '''
		pContent = dict.fromkeys(self.read)
		for k in pContent:
			pContent[k] = []
		for i in useContent:
			for block in useContent[i]:
				for attr in block[1]:
					if type(attr) == str:
						attr = map(str.strip,attr.split(':')) # TODO: (VL) Allow for colons in strings.
						if attr[1][0] == attr[1][-1] and attr[1][0] in ['"',"'"]:
							attr[1] = attr[1][1:-1]
						for j in self.read:
							if re.search(self.parseName(j), attr[0]):
								if self.read[j][0] == 'BOOL' and re.search(self.TYPES['BOOL'], attr[1], re.I):
									pContent[j].append(attr[1])
								elif self.read[j][0] == 'NUM':
									pass # TODO: (VH) Numbers!
								elif self.read[j][0] == 'STR':
									if not 'MULTI' in self.read[j][1]:
										attr[1] = attr[1].replace('\n', ' ')
									if 'STRICT' in self.read[j][1]:
										reFlags = 0
										if 'CI' in self.read[j][1] and not 'CS' in self.read[j][1]:
											reFlags |= re.I
										for s in self.read[j][2]:
											if re.search(self.parseName(s), attr[1], reFlags):
												pContent[j].append(s)
												break
									else:
										if re.search(self.TYPES['STR'], attr[1]):
											pContent[j].append(attr[1])
								break
		return pContent

	def __parseContentWrite__(self, pContent, writeRules = None, parElement = None):
		''' Parses the read content into xml. '''
		if writeRules == None:
			writeRules = self.write
		elif writeRules == {}:
			return {}
		if parElement == None:
			parElement = ET.Element(writeRules.keys()[0])
			self.__parseContentWrite__(pContent, writeRules[parElement.tag][2], parElement)
			return parElement
		else:
			for tag in writeRules:
				eleT = ET.Element(tag) # Create the blank template
				eles = []
				# Now for attributes.
				tagAttribs = writeRules[tag][1]
				tagNum = 1
				for i in tagAttribs:
					if tagAttribs[i].find('$') != -1 or tagAttribs[i].find('!') != -1:
						attrName = tagAttribs[i][1:].split('?')[0].split('>')[0]
						for j in pContent:
							if re.search(j, attrName):
								tagNum = max(tagNum, len(pContent[j]))
						if tagNum == 0:
							raise Exception('Attr "'+attrName+'" not found in read list.')
				# if not tagNum:
				# 	eles.append(eleT.copy())
				# 	eles[-1].attrib = tagAttribs
				# else:
				for i in tagAttribs:
					attrName = tagAttribs[i][1:].split('?')[0].split('>')[0]
					for j in xrange(tagNum):
						eles.append(eleT.copy())
						if tagAttribs[i][0] == '$':
							for k in pContent:
								if re.search(k, attrName):
									attrName = k
									break
							if tagAttribs[i].find('?i') != -1: # If it's a special one.
								ind = str(self.read[attrName][2].index(pContent[attrName][j]))
								eles[-1].attrib[i] = ind
							elif tagAttribs[i].find('>') != -1:
								ind = int(tagAttribs[i])
								eles[-1].attrib[i] = self.getInName(pContent[attrName][j],ind)
							else:
								eles[-1].attrib[i] = pContent[attrName][j]
						else:
							eles[-1].attrib[i] = tagAttribs[i]

				# Finally add sub tags before adding them to the parent element
				for e in eles:
					self.__parseContentWrite__(pContent, writeRules[tag][2], e)
					parElement.append(e)

# Currently retained only as xml lib reference
# 	lines = [str.strip(line) for line in f.readlines()]
# 	loc = os.path.join('mod','mod.xml')
# 	data = ET.Element('dredmormod')
# 	ET.SubElement(data, 'revision', {'text':lines[0]})
# 	ET.SubElement(data, 'author', {'text':lines[1]})
# 	ET.SubElement(data, 'name', {'text':lines[2]})
# 	ET.SubElement(data, 'description', {'text':lines[3]})
# 	ET.SubElement(data, 'info', {'totalconversion':'0'})
# 	for p in lines[4].split(','):
# 		ET.SubElement(data, 'require', {'expansion':p})
# 	ET.ElementTree(data).write(os.path.join(path/to/write/to,loc))

