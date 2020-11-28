from botutils import *

class Logger():
	def __init__(self, dir, name):
		self.dir = dir
		self.name = name

	def log(self, msg):
		try:
			f = open(self.dir, "a")
			f.write(current_datetime() + "::" + msg)
			f.close()
		except:
			print("Logger::" + self.name + "::Error while writing to dir '" + self.dir + "'")