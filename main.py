#!/usr/bin/env python

import sys, os
import zipfile

import parsers
import gui

def makeZip(path):
	if path.endswith('.zip'):
		path = path[:-4]
	zf = zipfile.ZipFile(os.path.basename(path)+'.zip', 'w')
	for root, dirs, files in os.walk(path):
		for filename in files:
			zf.write(os.path.join(root, filename))
			print root, filename
	zf.close()
		
def parse(filename, tmp):
	''' Parses a given file. '''
	try:
		f = open(filename, 'r')
	except IOError, e:
		print 'File not found'
		raise e
	parsers
	f.close()
	ET.ElementTree(data).write(os.path.join(tmp,loc))

def parseFolder(path, tmp_path = os.path.join(os.path.curdir,'tmp')):
	os.mkdir(tmp_path)
	os.mkdir(os.path.join(tmp_path,'mod'))
	os.mkdir(os.path.join(tmp_path,'sprites'))
	os.mkdir(os.path.join(tmp_path,'items'))
	for root, dirs, files in os.walk(path):
		for filename in files:
			if filename.split('.')[-1] in VALID_EXTENSIONS:
				parse(os.path.join(root, filename), tmp_path)
			else:
				print filename
				print root
				shutil.copy(os.path.join(root,filename), # The file to be copied
					os.path.join(tmp_path,root.split(path)[1].partition(os.sep)[2],filename)) # Gets the equivalent location
	return tmp_path

def main():
	gui.main()