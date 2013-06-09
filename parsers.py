#!/usr/bin/env python

import os, shutil
import re
import xml.etree.ElementTree as ET

VALID_EXTENSIONS = ['.inf', '.dredly']

##############################
# Util Functions for Parsers #
##############################
def getInName(s, check):
	''' Gets an option from a name. '''
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
	# Parses a Name/Str into valid regex and opt list
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

def parseList(block):
	f = block[0].split(':')[1]
	e = []
	for l in [x.lstrip('\t') for x in block[1:]]:
		e.append(parseName(l))
	return [f, e]

##############
# THE PARSER #
##############

class Parser:
	''' The generic parser. '''
	def __init__(self):
		self.parsers = {}

	def make_parsers(self, f):
		''' Generates parsers from a syntax file. '''
		f.seek(0) # Reset file to start
		# Get version
		ver=f.readline().strip()[1:].split(' ')
		print 'You are using version ' + ver[0] + ' of ' + ver[1]

		# Pull the parsers out of the file as blocks
		block = []
		for l in [str.rstrip(x) for x in f]: # Auto remove the end newlines without damaging indentation
			if not l or l[0].isaplha(): # If it's a newline or a top-level name then add block to list and reset tracker
				self.addParser(block)
				block = []
				continue
			block.append(l)
		if block: # If it didn't end in a new line the final block would normally be skipped
			self.addParser(block)

	def addParser(self, syntax):
		''' Creates a parser from a syntax block. '''
		# Get basic info
		name = syntax[0].split('-')[0]
		flag = syntax[0].split(':')[0].split('-')[1]
		if flag in ['R', 'W']: # If it's a macro then init if the first scanned
			if not self.parsers.has_key(name):
				self.parsers[name] = [None, None]
		elif flag in ['T']: # If it's a type just parse it now.
			self.parsers[name] = parseList(syntax)
		else:
			raise Exception('Invalid Syntax Type: ' + flag)

		# Actual parsing begins now
		indentation = 1
		stack = [1]
		parser = []
		l = lambda:syntax[stack[-1]]
		getIn = lambda s:len(s)-len(s.lstrip('\t'))
		while True:
			i = getIn(l())
			if indentation == i:



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
