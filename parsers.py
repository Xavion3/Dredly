#!/usr/bin/env python

import os, shutil
import re
import xml.etree.ElementTree as ET

##############
# THE PARSER #
##############

class Parser:
	''' The generic parser. '''
	TYPES = {'INT':r'^[-+]?[0-9]+$', # Integer, postive or negative
	         'FLOAT':r'^[-+]?[0-9]*\.?[0-9]+$', # Floating point number, postive or negative
	         'STR':r'^.*$', # String, no restrictions
	         'BOOL':r'^(0|1|TRUE|FALSE)$'} # Boolean, 0, 1, true, or false
	SYS = {'NAME':r'^[a-zA-Z][a-zA-Z0-9_]*$'} # Name, alphanumeric and _ starts with alpha

	def __init__(self):
		self.parsers = {}
		self.content = {}

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
				bits[-1] = [bits[-1],getBlocks(lines, line, ind+1)] # form [line, [indented lines]]
				while line < len(lines) and lines[line][0] > ind: # Skip to after indented block
					line += 1
		return bits

	def rIn(self, b):
		''' Removes indentation part of lines. '''
		b = b[:] # Prevent direct editing of b
		for i in range(len(b)):
			if type(b[i][0]) == list: # If it's an indented block strip that too
				b[i] = rIn(b[i])
			else:
				b[i] = b[i][1]
		return b

	def getFlags(self, s):
		''' Gets the flags from a valid name. '''
		# TODO: Add error checking to check if it's a name.
		return s.split(':')[1].strip().split('-')

	def getInName(self, s, check):
		''' Gets an option from a multi-option name. 
		    check is index for option to get from name s'''
		# Commented code shows how to swap to getting all options instead of just one. 
		# parts = []
		# check = 0
		part = ''
		stack = []
	# while check >= 0:
		parts.append('')
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
				if len(stack[:-1]) == stack[:1].count(check) and stack.pop(-1) < check: # If a level stopped before it should've error
					# check = -2
					# parts.pop(-1)
					raise IndexError('Part not in range for name')
		# check += 1
		return part

	def parseName(self, s):
		''' Turns a dredly name into a valid regex string. 
		    Returns false if invalid. '''
		# TODO: Error checking, particularly in relevance to balancing brackets
		# Current errors
		# - Fails if encountering unmatched end bracket
		# - Fails if starting with an unescaped |
		pattern = ''
		blank = []
		for i in range(len(s)):
			if (not s[i] in ['(', '|', ')']) or (i >= 1 and s[i-1] == '\\'): # Non special or escaped
				pattern += s[i]
				continue # Skip to next char to avoid accidently going thorugh with following if's
			if s[i] == '|': # Or separator
				if s[i-1] in ['(', '|'] or s[i+1] in ['|', ')']: # Matches (|, ||, and |) to check for blanks
					blank[-1] = True
					if re.search(r'\(\|*$', pattern) or re.search(r'^\|*\)', s[i:]) and s[i-1] != '|': # If it's not at the start or the end add if the first of a group
						pattern += '|'
				else: # If isn't a blank then whatevs
					pattern += '|'
			if s[i] == ')':
				pattern += ')'
				if blank.pop(-1): # Check if the current bracket pair had a blank while removing it from the list
					pattern += '?'
			if s[i] == '(':
				pattern += '('
				blank.append(False) # Assume no blanks and start another set of brackets
		return pattern

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
					self.parsers[name] = RWBlock(name)
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
					elif self.parsers[name].complete:
						raise Exception('R/W block '+name+' used while incomplete')
					elif not self.content.has_key(name):
						self.content[name] = []
				else:
					raise Exception('No R/W block exists for '+name)
			else:
				raise Exception('Invalid block type '+blocktype)

			# Now fill in that spot with out block.
			if blocktype == 'R':
				self.parsers[name].parseRead(block)
			elif blocktype == 'W':
				self.parsers[name].parseWrite(block)

	# def parseMacro(self, block):
	# 	''' Turns a macro block into a macro by recursively calling itself. '''
	# 	# Progress
	# 	# - Nums
	# 	# - Simple strings
	# 	# - String lists
	# 	# - macros
	# 	for attr in block:
	# 		if type(attr) == list:
	# 	if f[0] == 'NUM':
	# 		pass
	# 	if not (f[0] in ['STR'] and 'strict' in f):
	# 		pass
	# 	e = []
	# 	for l in [x.lstrip('\t') for x in block[1:]]:
	# 		e.append(parseName(l))
	# 	return [f, e]
	# Obselete maybe?
		
class RWBlock:
	''' A parsed read/write block for use with content parsing. '''

	def __init__(self, name):
		''' Creates the block. '''
		self.name = name
		self.complete = False
		self.flags = []
		self.read = {}
		self.write = {}

	def parseRead(self, block):
		''' Parses a read block for use. '''
		if self.read:
			raise Exception('Read block '+self.name+' already exists. Cannot overwrite.')
		

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

