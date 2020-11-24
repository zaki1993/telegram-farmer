from datetime import datetime, timedelta

class Chat():
	def __init__(self, link, joinDate = datetime.now(), leaveDate = datetime.now()):
		self.link = link
		self.joinDate = joinDate
		self.leaveDate = leaveDate

	def get_info(self):
		return "[Link: " + self.link + ", Join date: " + str(self.joinDate) + ", Leave date: " + str(self.leaveDate) + "]\n"

	def is_expired(self):
		expired = datetime.now() >= self.leaveDate
		print("Chat: ", self.get_info(), " is expired: ", expired)
		return expired
