from os import listdir
from os.path import isfile, join, sep

CACHE_FOLDER = "cache"

class CacheObeserver():
	def __init__(self):
		self.cacheArray = []

	def load(self, fileList):
		self.cacheArray = [(self.unwrap(file), self.loadfile(CACHE_FOLDER + sep + file)) for file in fileList]
		print(self.cacheArray)

	def observe(self):
		fileList = [f for f in listdir("cache") if isfile(join("cache", f))]
		if len(fileList) != len(self.cacheArray):
			self.load(fileList)

	def unwrap(self, fileName):
		return fileName

	def loadfile(self, fileName):
		print("Loading file: ", fileName)
		with open(fileName, 'r') as file:
   			return file.read()

CacheObeserver().observe()