#!/usr/bin/env python

import os, shutil
import re
import xml.etree.ElementTree as ET

VALID_EXTENSIONS = ['.inf', '.dredly']

##############################
# Util Functions for Parsers #
##############################
def getFlags(s):
	''' Gets the flags from a valid name. '''
	# TODO: Add error checking to check if it's a name.
	return s.split(':')[1].strip().split('-')

def getInName(s, check):
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
		if len(stack) == stack.count(check) and not s[i] in ['(', '|', ')']:
			# parts[-1] += s[i]
			part += s[i]
		elif s[i] == '(':
			stack.append(0)
		elif s[i] == '|':
			stack[-1] += 1
		elif s[i] == ')':
			if len(stack[:-1]) == stack[:1].count(check) and stack.pop(-1) < check:
				# check = -2
				# parts.pop(-1)
				raise IndexError('Part not in range for name')
	# check += 1
	return part

def parseName(s):
	''' Turns a dredly name into a valid regex string. '''
	pattern = ''
	blank = []
	for i in range(len(s)):
		if not s[i] in ['(', '|', ')']:
			pattern += s[i]
			continue
		if s[i] == '|':
			if s[i-1] in ['('] or s[i+1] in ['|', ')']:
				blank[-1] = True
			else:
				pattern += '|'
		if s[i] == ')':
			pattern += ')'
			if blank.pop(-1):
				pattern += '?'
		if s[i] == '(':
			pattern += '('
			blank.append(False)
	return pattern

##############
# THE PARSER #
##############

class Parser:
	''' The generic parser. '''
	def __init__(self):
		self.parsers = {}

	def make_parsers(self, f):
		''' Generates parsers from a syntax file. '''
		f.seek(0) # Reset file to start just in case
		# Pull the parsers out of the file as blocks
		# Extract the blocks with indentation preserved
		lines = [[len(x)-len(x.lstrip('\t')),str.strip(x)] for x in f] # Process file into list of lines with indentation
		def getBlocks(line): # Created to allow for recursion
			bits = [lines[line]]
			line += 1 # Process first line to simplify indentation checking
			while line < len(lines):
				if lines[line][0] == bits[0][0]: # If it's the same level add to list and move on
					bits.append(lines[line])
					line += 1
				elif lines[line][0] < bits[0][0]: # If it's a lower level return indented bits
					return bits
				elif lines[line][0] > bits[0][0]: # If it's a higher level change the last line to be
					bits[-1] = [bits[-1],getBlocks(line)] # of the form [line, [indented lines]]
					while line < len(lines) and lines[line][0] > bits[0][0]: # Skip to after indented block
						line += 1
			return bits
		blocks = getBlocks(0)
		def rIn(b): # Created to allow for recursion
			b = b[:] # Prevent direct editing of b
			for i in range(len(b)):
				if type(b[i][0]) == list: # If it's an indented block strip that too
					b[i] = rIn(b[i])
				else:
					b[i] = b[i][1]
			return b
		blocks = rIn(blocks) # Strips indentation parts out

	def addParser(self, syntax):
		''' Creates a parser from a syntax block. '''
		# Get basic info
		name = syntax[0].split('-')[0]
		flag = syntax[0].split(':')[0].split('-')[1] # Gets the R/W/T flag
		if flag in ['R', 'W']: # If it's a macro then init if the first scanned
			if not self.parsers.has_key(name):
				self.parsers[name] = [None, None]
		elif flag in ['T']: # If it's a type just add one.
			self.parsers[name] = None
		else:
			raise Exception('Invalid Syntax Type: ' + flag)

		# Actual parsing begins now
		indentation = 1
		stack = [1]
		parser = []
		l = lambda:syntax[stack[-1]] # Gets next line according to stack
		getIn = lambda s:len(s)-len(s.lstrip('\t')) # 
		while True:
			i = getIn(l())
			if indentation == i:
				pass

	def parseObj(self, block):
		''' Turns a list into a parser by recursively calling itself. '''
		# Progress
		# - Nums
		# - Simple strings
		# - String lists
		# - macros
		# output format
		f = getFlags(block[0])
		if f[0] == 'NUM':
			pass
		if not (f[0] in ['STR'] and 'strict' in f):
			pass
		e = []
		for l in [x.lstrip('\t') for x in block[1:]]:
			e.append(parseName(l))
		return [f, e]

	def parse(self, f):
		if type(block) == str:
			block = block.split('\n')
		f.close()
		ET.ElementTree(data).write(os.path.join(self.path,loc))

	def parseFolder(self, path):
		self.path = os.path.join(os.path.curdir,'tmp')
		os.mkdir(self.path)
		os.mkdir(os.path.join(self.path,'mod'))
		os.mkdir(os.path.join(self.path,'sprites'))
		os.mkdir(os.path.join(self.path,'items'))
		for root, dirs, files in os.walk(path):
			for filename in files:
				if filename.split('.')[-1] in ['inf', 'dredly']:
					self.parse(os.path.join(root, filename))
				else:
					print filename
					print root
					shutil.copy(os.path.join(root,filename), # The file to be copied
						os.path.join(self.path,root.split(path)[1].partition(os.sep)[2],filename)) # Gets the equivalent location
		shutil.rmtree(self.path)


def InfoParser(f):
	lines = [str.strip(line) for line in f.readlines()]
	loc = os.path.join('mod','mod.xml')
	data = ET.Element('dredmormod')
	ET.SubElement(data, 'revision', {'text':lines[0]})
	ET.SubElement(data, 'author', {'text':lines[1]})
	ET.SubElement(data, 'name', {'text':lines[2]})
	ET.SubElement(data, 'description', {'text':lines[3]})
	ET.SubElement(data, 'info', {'totalconversion':'0'})
	for p in lines[4].split(','):
		ET.SubElement(data, 'require', {'expansion':p})
	return loc, data

