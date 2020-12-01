import configparser
from operation import Operation
from os.path import sep
from botutils import uniquefy_list

class User():
	def __init__(self, phone, data, balance):
		self.phone = phone
		self.data = data
		self.balance = balance
		self.__load_config__()
		self.__validate__()

	def __load_config__(self):
		if self.phone != None:
			self.config = configparser.ConfigParser()
			self.config.read("ini" + sep + self.phone + ".ini")

	def __validate__(self):
		if self.data == None:
			raise Exception("User context is empty...!")

	def on_cache(self, currentBalance):
		return '{0:.8f}'.format(currentBalance - self.balance);

	@property
	def active(self):
		if self.config.has_section('CONFIG'):
			return self.config.get('CONFIG', 'active') == 'True'
		return True
	
	@property
	def allowed_operations(self):
		if self.config.has_section('CONFIG'):
			return self.__operations_from_string__(self.config.get('CONFIG', 'allowed_operations'))
		else:
			return [Operation.JOIN, Operation.VISIT, Operation.MESSAGE]
	
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

	def __operations_from_string__(self, str):
		return uniquefy_list([self.__operation_from_string__(s) for s in str.split(',')])

	def __operation_from_string__(self, str):
		if str in [oper.name for oper in Operation]:
			return Operation[str]
		return Operation.VISIT
	
	def __str__(self):
		return "[" + self.phone + "]"