#!/usr/bin/env python

import sys
import os
import shutil
import zipfile
import xml.etree.ElementTree as ET

import parsers
import gui

DREDLY_EXTENSIONS = ['inf', 'dredly']

def makeZip(path):
	''' Makes a zip out of a given folder with the same name as the folder.
	    It creates in the directory this was run out of. '''
	if not os.path.isdir(path):
		raise ValueError('Must be a directory')
	zf = zipfile.ZipFile(os.path.join(os.path.curdir, os.path.basename(path)+'.zip'), 'w')
	for root, dirs, files in os.walk(path):
		for filename in files:
			zf.write(os.path.join(root, filename))
			# print root, filename
	zf.close()

def parseFolder(path, parser, tmp_path = os.path.join(os.path.curdir,'tmp')):
	try:
		os.mkdir(tmp_path)
	except OSError:
		shutil.rmtree(tmp_path)
		os.mkdir(tmp_path)
	# TODO: (M) Make it generate foldres based on content instead.
	os.mkdir(os.path.join(tmp_path,'mod'))
	os.mkdir(os.path.join(tmp_path,'sprites'))
	os.mkdir(os.path.join(tmp_path,'items'))
	for root, dirs, files in os.walk(path):
		for filename in files:
			if filename.split('.')[-1] in DREDLY_EXTENSIONS: # If it's a dredly file then parse
				# print "Parsing", filename
				f = open(os.path.join(root, filename), 'r')
				parser.parseFile(f)
			else: # Else just copy
				# print filename
				# print root
				shutil.copy(os.path.join(root,filename), # The file to be copied
					os.path.join(tmp_path,root.split(path)[1].partition(os.sep)[2],filename)) # Gets the equivalent location
	# Now that you've parsed everything make the xml
	parser.createXML()
	for f in parser.xml:
		ET.ElementTree(f[0]).write(os.path.join(tmp_path, f[1]))
	makeZip(tmp_path)
	shutil.rmtree(tmp_path)

def main():
	#gui.main()
	# Parse the syntax.
	f = open('./dredly/curSyntax.dredly', 'r')
	global Parser
	Parser = parsers.Parser(f)
	# Now run it on the test mod!
	parseFolder('dredly/test_mod',Parser)
