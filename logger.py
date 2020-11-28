from botutils import *

class Logger():
	def __init__(self, dir, name):
		self.dir = dir
		self.name = name
		print("Initializing logger '" + name + "'")

	def log(self, msg):
		try:
			f = open(self.dir, "a")
			f.write(self.name + "::" + current_datetime() + "::" + msg)
			f.close()
		except Exception as e:
			print(repr(e))
			print("Logger::" + self.name + "::Error while writing to dir '" + self.dir + "'")