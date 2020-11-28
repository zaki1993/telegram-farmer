class User():
	def __init__(self, phone, data, balance):
		self.phone = phone
		self.data = data
		self.balance = balance
		self.__validate__()

	def __validate__(self):
		if self.data == None:
			raise Exception("User context is empty...!")


	def on_cache(self, currentBalance):
		return '{0:.8f}'.format(currentBalance - self.balance);

	@property
	def balance(self):
		return self._balance
	
	@property
	def phone(self):
		return self._phone
	
	@property
	def data(self):
		return self._data

	@phone.setter
	def phone(self, value):
		self._phone = value

	@data.setter
	def data(self, value):
		self._data = value

	@balance.setter
	def balance(self, value):
		self._balance = value
	
	def __str__(self):
		return "[" + self.phone + "]"