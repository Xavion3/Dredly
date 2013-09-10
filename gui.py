#!/usr/bin/env python

import Tkinter as tk

class App:
	def __init__(self, master):
		self.master = master

		frame = tk.Frame(master, bd='3')
		frame.pack()

		self.button = tk.Button(frame, text='QUIT', fg='red', command=self.master.destroy)
		self.button.pack(side=tk.LEFT)

		self.hi_there = tk.Button(frame, text='Hello', command=self.say_hi)
		self.hi_there.pack(side=tk.LEFT)

	def say_hi(self):
		print 'hi there'

		# Labels
		# self.labels = []
		# self.labels.append({})
		# self.labels[0]['data'] = tk.StringVar()
		# self.labels[0]['data'].set('Dredly Compiler')
		# self.labels[0]['obj'] = tk.Label(self, textvariable=self.labels[0]['data'], height=0)

		# Text Inputs
		# self.entries = []
		# for i in xrange(1):
		# 	self.entries.append({'data':tk.StringVar(None)})
		# 	self.entries[i]['obj'] = tk.Entry(self, textvariable=self.entries[i]['data'])
		# self.entries[0]['data'].set('Mod name')
		# self.initUI()

	# def initUI(self):
	# 	self.pack(fill=tk.BOTH, expand=1)
	# 	self.labels[0]['obj'].pack()
	# 	self.entries[0]['obj'].pack()

def main():
	root = Tkinter.Tk()
	root.title('Dredly Compiler')
	root.geometry('250x300+600+300')
	app = App(root)
	root.mainloop()