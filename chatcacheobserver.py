from chat import *
from os.path import sep

CACHE_FOLDER = "cache" + sep + "chat"

class ChatCacheObserver():
	def get_chat_file(self, current_user):
		return CACHE_FOLDER + sep + current_user

	def cache_joined_channels(self, current_user, chats):
		print("ChatCacheObserver::Caching joined chats for user '", current_user, "'")
		f = open(self.get_chat_file(current_user), "w+")
		for chat in chats:
			print("ChatCacheObserver::Caching chat: ", chat.get_info())
			f.write(chat.get_info())
		f.close()

	def load_chat_from_cache(self, cache_line):
		try:
			print("ChatCacheObserver::Loading from cache: ", cache_line)
			cache_line_parts = cache_line[1:-2].split(",")
			link = cache_line_parts[0].split(":", 1)[1].strip()
			joinedDate = datetime.strptime(cache_line_parts[1].split(":", 1)[1].strip(), "%Y-%m-%d %H:%M:%S.%f")
			leaveDate = datetime.strptime(cache_line_parts[2].split(":", 1)[1].strip(), "%Y-%m-%d %H:%M:%S.%f")
			chat = Chat(link, joinedDate, leaveDate)
			print("ChatCacheObserver::Loaded chat: ", chat.get_info())
			return chat
		except:
			print("ChatCacheObserver::Line ", cache_line, " does not contain valid chat information")
		return None

	def load_chats_from_last_run(self, current_user):
		print("ChatCacheObserver::Loading cached chats for user '", current_user, "'")
		chatsJoined = []
		try:
			f = open(self.get_chat_file(current_user), "r")
			for chat_line in f:
				chat = self.load_chat_from_cache(chat_line)
				if chat != None:
					chatsJoined.append(chat)
			f.close()
		except:
			print("ChatCacheObserver::Error while reading cache")
		return chatsJoined