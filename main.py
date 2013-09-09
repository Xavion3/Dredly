#!/usr/bin/env python

DEBUG = True # This is key.

import sys
import os
import shutil
import zipfile
import xml.etree.ElementTree as ET

import parsers
import gui

def main():
	gui.main()
	# # Parse the syntax.
	# if not DEBUG:
	# 	path = raw_input('Please enter syntax filepath:')
	# else:
	# 	path = './dredly syntax/tests/test.drd'
	# f = open(path, 'r')
	# global Parser
	# Parser = parsers.Parser(f)
	# # Now run it on the test mod!
	# if not DEBUG:
	# 	path = raw_input('Please enter mod filepath:')
	# else:
	# 	path = './dredly syntax/tests/content'
	# parseFolder(path, Parser)
