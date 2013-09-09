#!/usr/bin/env python

import os
import shutil
import zipfile
import xml.etree.ElementTree as ET
import Tkinter as tk
import tkFileDialog as tkFD

import parsers

DREDLY_EXTENSIONS = ['inf', 'dredly', 'drd']

def call(func, *args, **kwargs):
	return lambda: func(*args, **kwargs)

class App(object):
	def __init__(self):
		self.root = tk.Tk()
		self.root.title('Dredly')
		self.mainloop = self.root.mainloop

		self.parser = parsers.Parser()
		self.tmp_path = os.path.join(os.path.curdir,'tmp')

		self.active_tab = -1
		self.tab_frame = tk.Frame(self.root, bd='3', relief='groove')
		self.tab_frame.pack(side = tk.TOP, expand=1, fill=tk.X)
		self.tabs = []
		self.frames = []

		self.make_tabs(['Dredly'])
		self.activate_tab(0)
		self.create_main(self.frames[0])

	def make_tabs(self, tabs):
		'''Create tabs from a list of strings.'''
		offset = len(self.tabs)
		for i in xrange(len(tabs)):
			self.tabs.append(tk.Button(self.tab_frame, text = tabs[i]))
			self.tabs[-1].pack(side = tk.LEFT)
			self.tabs[-1].configure(command = call(self.activate_tab, i+offset))
			self.frames.append(tk.Frame(self.root))

	def activate_tab(self, tab):
		'''Activate tab from index passed in.'''
		if tab != self.active_tab:
			self.frames[self.active_tab].pack_forget()
			self.frames[tab].pack(side = tk.TOP)
			self.active_tab = tab

	def quit(self):
		self.root.destroy()

	def create_main(self, frame):
		''' Creates the main tab. '''
		tk.Label(frame, text='Load Syntax Definition').pack(side = tk.TOP)
		tk.Button(frame, text='Load Syntax Definition', command=self.test).pack(side = tk.TOP)
		tk.Label(frame, text='Compile to XML').pack(side = tk.TOP)
		tk.Button(frame, text='Compile to XML').pack(side = tk.TOP)

	def test(self):
		return tkFD.askdirectory()

	def makeZip(self, dest):
		'''dest = path to write to
		   Makes a zip out of a given folder at the destination.'''
		zf = zipfile.ZipFile(dest, 'w')
		for root, dirs, files in os.walk(self.tmp_path):
			for filename in files:
				zf.write(os.path.join(root, filename))
		zf.close()

	def parseFolder(self, path):
		'''Parses a folder with the parser.'''
		if os.path.isdir(path):
			for root, dirs, files in os.walk(path):
				for filename in files:
					if filename.split('.')[-1] in DREDLY_EXTENSIONS: # If it's a dredly file then parse
						f = open(os.path.join(root, filename), 'r')
						self.parser.parseFile(f)
						f.close()
		elif os.path.isfile(path):
			f = open(os.path.join(root, filename), 'r')
			self.parser.parseFile(f)
			f.close()
		else:
			print 'Unknown path type. WTFF?'
	
	def export(self, path):
		'''Exports the current data as XML.'''
		try:
			os.mkdir(self.tmp_path)
		except OSError:
			shutil.rmtree(self.tmp_path)
			os.mkdir(self.tmp_path)
		# Now that you've parsed everything make the xml
		self.parser.createXML()
		for f in self.parser.xml:
			if f[0] != None: # If there is xml, skips if it was empty.
				ET.ElementTree(f[0]).write(os.path.join(self.tmp_path, f[1]))
		makeZip(self.tmp_path)
		shutil.rmtree(self.tmp_path)

def main():
	app = App()
	app.mainloop()

if __name__ == '__main__':
        main()
