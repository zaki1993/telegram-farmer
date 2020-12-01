from os import listdir
from os.path import isfile, join, sep

CACHE_FOLDER = "cache" + sep + "user"

class UserCacheObserver():
	def __init__(self):
		print("UserCacheObserver::Initializing user observer..!")
		self.cacheArray = []
		self.next = 0

	def load(self, fileList):
		self.cacheArray = [(self.unwrap(file), self.__load_file__(CACHE_FOLDER + sep + file)) for file in fileList]

	def observe(self):
		print("UserCacheObserver::Observing the cache..!")
		fileList = [f for f in listdir(CACHE_FOLDER) if isfile(join(CACHE_FOLDER, f))]
		if len(fileList) != len(self.cacheArray):
			self.load(fileList)

	def unwrap(self, fileName):
		return fileName

	def __load_file__(self, fileName):
		print("UserCacheObserver::Loading file: ", fileName)
		with open(fileName, 'r', encoding="utf8") as file:
   			return file.read()

	def pick_next(self):
		if len(self.cacheArray) == 0:
			self.observe()
		if len(self.cacheArray) == 0:
			return None
		if self.next >= len(self.cacheArray):
			self.next = 0
		context = self.cacheArray[self.next]
		self.next += 1
		return context