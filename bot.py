from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
import timeit
import re
from selenium.webdriver.common.action_chains import ActionChains
import random
from concurrent.futures import ThreadPoolExecutor
import traceback
from phone import Phone
from chat import Chat
from operation import Operation
from sleep import sleep

# Time which the driver will wait to find component untill timeout exception is raised in seconds
DRIVER_WAIT_TIME = 10

# 1 second in milliseconds
SECOND = 1000

# 1 hour in milliseconds
HOUR = 3600 * SECOND

# Sleep time between searching from 1 component to another in milliseconds
SLEEP_TIME_BETWEEN_COMPONENTS = 10 * SECOND

# Waiting for new message limit before switching to different operation
RETRY_LIMIT = 2

# Time to run the bot until it pauses for SLEEP_BOT_TIME seconds
BOT_WAIT_TIME = 1200

# Time which the bot will sleep every BOT_WAIT_TIME milliseconds in milliseconds
BOT_SLEEP_TIME = SECOND * 60 * 10

# Current running bot link
BOT_LINK = "https://web.telegram.org/#/im?p=@Zcash_click_bot"

# Open chat link pattern
OPEN_CHAT_LINK_PART = "https://web.telegram.org/#/im?p=@"

# Object used to unbuffer the print and show the output during execution of the program
class Unbuffered(object):
   def __init__(self, stream):
       self.stream = stream
   def write(self, data):
       self.stream.write(data)
       self.stream.flush()
   def writelines(self, datas):
       self.stream.writelines(datas)
       self.stream.flush()
   def __getattr__(self, attr):
       return getattr(self.stream, attr)

class Bot:

	def get_chat_file(self):
		return "chat_" + self.phone.phoneNumber + ".cache"

	def cache_joined_channels(self):
		print("Caching joined channels")
		f = open(self.get_chat_file(), "w+")
		for chat in self.chatsJoined:
			print("Cached chat: ", chat.get_info())
			f.write(chat.get_info())
		f.close()

	def load_chat_from_cache(self, cache_line):
		try:
			print("Parsing line: ", cache_line)
			cache_line_unwrapped = cache_line[1:-2]
			print("Unwrapped line: ", cache_line_unwrapped)
			cache_line_parts = cache_line_unwrapped.split(",")
			link = cache_line_parts[0].split(":", 1)[1].strip()
			joinedDate = datetime.strptime(cache_line_parts[1].split(":", 1)[1].strip(), "%Y-%m-%d %H:%M:%S.%f")
			leaveDate = datetime.strptime(cache_line_parts[2].split(":", 1)[1].strip(), "%Y-%m-%d %H:%M:%S.%f")
			chat = Chat(link, joinedDate, leaveDate)
			print("Serialized chat: ", chat.get_info())
			return chat
		except:
			print("Line ", cache_line, " does not contain valid chat information")
		return None

	def load_chats_from_last_run(self):
		print("Loading cached chats..!")
		chatsJoined = []
		try:
			f = open(self.get_chat_file(), "r")
			for chat_line in f:
				chat = self.load_chat_from_cache(chat_line)
				if chat != None:
					chatsJoined.append(chat)
			f.close()
			print(len(chatsJoined), " chats loaded from cache..!")
		except:
			print("Error while reading cache")
		return chatsJoined

	def reset(self):
		self.waitingForTasksRetry = 0
		# Variable to check whether the bot has changed the operation
		self.isOperationInitialized = False
		# Limit of how many chats the bot can join in a row
		self.joinLimit = 20
		# Limit of how many sites the bot can visit in a row
		self.visitLimit = 40
		# Limit of how many runs the bot can wait until it switches the operation
		self.retryLimit = 5
		# Variable to count how many chats the bot has joined
		self.joinedChatsCount = 0
		# Variable to count how many sites the bo has visited
		self.visitedSitesCount = 0

	def __init__(self, driver, operation, currency, phone):
		print("Initializing bot..!")
		self.phone = phone
		self.CHATS_CACHE_FILE = "chats.cache" + "_" + self.phone.phoneNumber
		self.driver = driver
		self.operation = operation
		self.currency = currency
		self.chatsJoined = self.load_chats_from_last_run()
		self.reset()

	def close_tab(self):
		self.driver.switch_to.window(self.driver.window_handles[1])
		self.driver.close()
		self.driver.switch_to.window(self.driver.window_handles[0])

	def refresh(self, channel_link = BOT_LINK):
		print("Refreshing link ", channel_link)
		self.driver.get(channel_link)
		self.driver.refresh()

	def get_last_message(self):
		try:
			messages = WebDriverWait(self.driver, DRIVER_WAIT_TIME).until(
				EC.presence_of_all_elements_located((By.XPATH, "//div[@class='im_message_text']"))
			)
			return messages[len(messages) - 1].text
		except TimeoutException:
			return None

	def change_operation(self, new_operation):
		print("Changing operation..!")
		self.operation = new_operation
		self.isOperationInitialized = False
		self.refresh()
		self.waitingForTasksRetry = 0
		sleep(SLEEP_TIME_BETWEEN_COMPONENTS)

	def click_ok_popup_button(self):
		try:
			ok_popup_btn = WebDriverWait(self.driver, DRIVER_WAIT_TIME).until(
				EC.presence_of_element_located((By.XPATH, "//button[@class='btn btn-md btn-md-primary']"))
			)
			ok_popup_btn.click()
		except:
			print("OK Button is not present")
			return False
		print("Clicking OK button")
		return True

	def click(self, component_type, names, classes = "btn reply_markup_button"):
		try:
			buttons = WebDriverWait(self.driver, DRIVER_WAIT_TIME).until(
				EC.presence_of_all_elements_located((By.XPATH, "//" + component_type + "[@class='" + classes + "']"))
			)
			print("Searching for ", names)
			print("Total number of buttons found ", len(buttons))
			for button in reversed(buttons):
				text = button.text
				print("Processing button ", button.text.encode("utf-8"))
				for name in names:
					if text.strip().find(name.strip()) != -1:
						print("Clicking '",name.strip(),"' component")
						button.click()
						return True
		except TimeoutException:
			print("Component ", names, " was not found on the page in the given timeout")
		return False

	def send_text(self, text):
		textArea = WebDriverWait(self.driver, DRIVER_WAIT_TIME).until(
			EC.presence_of_element_located((By.XPATH, "//div[@class='composer_rich_textarea']"))
		)
		textArea.send_keys(text)
		textArea.send_keys(Keys.ENTER)

	def start_join_channel(self):
		return self.send_text("/join")

	def start_visit_sites(self):
		return self.send_text("/visit")

	def start_message_bots(self):
		return self.click_button_by_name(["Message bots"])

	def click_button_by_name(self, names):
		return self.click("button", names)

	def click_link_by_name(self, names):
		return self.click("a", names)

	def skip_channel(self):
		return self.click_button_by_name(["Skip"])

	def open_joining_channel(self):
		return self.click_link_by_name(["Go to channel", "Go to group"])

	def validate_join_chats(self):
		print("Validate joining chats")
		message = self.get_last_message().strip()
		if message != None:
			print("Validating message: ", message.encode("utf-8"));
			result = True
			if message.find("We cannot find you") != -1 or message.find("You already completed this task") != -1:
				self.skip_channel()
				result = False
			elif message.find("There is a new chat for you to join") != -1 or message.find("Sorry, that task is no longer valid") != -1 or message.find("There is a new chat for you to join") != -1:
				self.start_join_channel()
				sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
				result = False
			elif message.find("Sorry, there are no new ads available.") != -1 or message.find("Join chats") != -1:
				print("Waiting for new tasks")
				sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
				result = False
				self.waitingForTasksRetry += 1
				print("RETRY: ", self.waitingForTasksRetry," from JOIN")
				if self.waitingForTasksRetry % RETRY_LIMIT == 0:
					self.change_operation(Operation.VISIT)
		else:
			result = False
		if result == False:
			sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
			self.open_channel(BOT_LINK)
		
		print("Validation is: ", result)
		
		return result

	def join_openned_channel(self):
		return self.click("a", ["JOIN"], "btn btn-primary im_start_btn")

	def open_channel(self, channel_link = BOT_LINK):
		self.refresh(channel_link)

	def get_hours_untill_reward(self):
		messages = WebDriverWait(self.driver, DRIVER_WAIT_TIME).until(
			EC.presence_of_all_elements_located((By.CLASS_NAME, 'im_message_text'))
		)
		for message in reversed(messages):
			print("Processing message: ", message.text.encode("utf-8"))
			if message.text.find("You must stay in the channel for at least") != -1 or message.text.find("You must stay in the group for at least") != -1:
				return int(re.search('at least (.+?) hour', message.text).group(1).strip())

	def init_operation(self):
		if (self.operation == Operation.JOIN):
			self.start_join_channel()
		elif (self.operation == Operation.VISIT):
			self.start_visit_sites()
		else:
			self.start_message_bots()
		self.isOperationInitialized = True
		print("Initializing operation")

	def is_bot_joined_success(self):
		sleep(SLEEP_TIME_BETWEEN_COMPONENTS / 2)
		return self.get_last_message().find("We cannot find you") == -1

	def join_chats(self, channel_url = None):
		if self.validate_join_chats():
			sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
			if self.open_joining_channel():
				sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
				# The bot update to have a link on the chats as well
				if self.click_ok_popup_button():
					sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
					# Get current url. It would be something like that https://t.me/Jizzax_Zomin_bozor
					if len(self.driver.window_handles) < 2:
						self.skip_channel()
						sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
						self.refresh()
					else:
						self.driver.switch_to.window(self.driver.window_handles[1])
						print("Current url is ", self.driver.current_url)
						chatUrlNameParts = self.driver.current_url.split("/")
						print("URL parts are", chatUrlNameParts)
						chatUrlName = chatUrlNameParts[len(chatUrlNameParts) - 1].strip()
						print("Extracted chat name", chatUrlName)
						self.close_tab()
						sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
						self.open_channel(OPEN_CHAT_LINK_PART + chatUrlName)
						sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
						channel_url = OPEN_CHAT_LINK_PART + chatUrlName
						if self.join_openned_channel():
							sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
				else:
					channel_url = self.driver.current_url
					if self.join_openned_channel():
						sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
				self.open_channel(BOT_LINK)
				sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
				if self.click_button_by_name(["Joined"]):
					sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
					if self.is_bot_joined_success() and channel_url != None:
						hoursUntillReward = self.get_hours_untill_reward()
						if hoursUntillReward != None:
							print("Hours untill reward '", hoursUntillReward, "'")
							joinDate = datetime.now()
							leaveDate = joinDate + timedelta(hours = hoursUntillReward)
							chat = Chat(channel_url, joinDate, leaveDate)
							self.chatsJoined.append(chat)
							print("Joined channel: ", chat.get_info())
							self.joinedChatsCount += 1
							print("You have joined ", self.joinedChatsCount, " chats in total")
							if self.joinedChatsCount % self.joinLimit == 0:
								self.change_operation(Operation.VISIT)
						else:
							self.change_operation(Operation.VISIT)

	def open_site(self):
		print("Openning site")
		return self.click_link_by_name(["Go to website"])

	def validate_visit_sites(self):
		print("Validate visiting sites")
		message = self.get_last_message().strip()
		print("Validating message: ", message.encode("utf-8"));
		result = True
		if message.find("Sorry, there are no new ads available.") != -1:
			print("Waiting for new tasks")
			sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
			result = False
			self.waitingForTasksRetry += 1
			print("RETRY: ", self.waitingForTasksRetry," from VISIT")
			if self.waitingForTasksRetry % RETRY_LIMIT == 0:
				self.change_operation(Operation.JOIN)
		
		if result == False:
			sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
			self.open_channel(BOT_LINK)
		
		print("Validation is: ", result)
		
		return result

	def extract_sleep_time(self, message):
		messages = WebDriverWait(self.driver, DRIVER_WAIT_TIME).until(
			EC.presence_of_all_elements_located((By.CLASS_NAME, 'im_message_text'))
		)
		sleepTime = 0
		for message in reversed(messages):
			print("Processing message: ", message.text.encode("utf-8"))
			if message.text.find("Please stay on the site for at least") != -1:
				regex = re.search('Please stay on the site for at least (.+?) seconds', message.text)
				print("Regex result is ", regex)
				sleepTime = int(regex.group(1)) * SECOND
				break
			elif message.text.find("You must stay on the site for") != -1:
				regex = re.search('You must stay on the site for (.+?) seconds to get your reward', message.text)
				print("Regex result is ", regex)
				sleepTime = int(regex.group(1)) * SECOND
				break
		return sleepTime

	def visit_sites(self):
		if self.validate_visit_sites():
			sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
			if self.open_site():
				sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
				if self.click_ok_popup_button():
					sleep(2 * SLEEP_TIME_BETWEEN_COMPONENTS - SECOND)
					siteSleepTimeUntillReward = self.extract_sleep_time(self.get_last_message())
					if siteSleepTimeUntillReward != 0:
						sleep(siteSleepTimeUntillReward)
					self.close_tab()
					if siteSleepTimeUntillReward != 0:
						self.visitedSitesCount += 1
						print("You have visited ", self.visitedSitesCount, " sites in total")
						if self.visitedSitesCount % self.visitLimit == 0:
							self.change_operation(Operation.JOIN)
					else:
						self.skip_channel()

	def message_bots(self):
		print("Messaging bots")

	def wait_for_login(self):
		WebDriverWait(self.driver, 5 * 60).until(
			EC.text_to_be_present_in_element((By.XPATH, "//div[@class='im_history_not_selected vertical-aligned']"), "Please select a chat to start messaging")
		)
		print("Login successfull")

	def login(self):
		# Set phone country input field
		phone_country = WebDriverWait(self.driver, DRIVER_WAIT_TIME).until(
		    EC.presence_of_element_located((By.NAME, "phone_country"))
		)
		phone_country.clear()
		phone_country.send_keys(self.phone.phoneCountry)
		print("Set phone country number")
		sleep(2000)

		# Set phone number input field
		phone_number = WebDriverWait(self.driver, DRIVER_WAIT_TIME).until(
		    EC.presence_of_element_located((By.NAME, "phone_number"))
		)
		phone_number.send_keys(self.phone.phoneNumber)
		phone_number.send_keys(Keys.ENTER)
		print("Set phone number")
		sleep(2000)

		# Click OK confirm button
		self.click_ok_popup_button()
		print("Confirm the number")
		sleep(2000)

		print("Logging in as: ", self.phone.phoneCountry, self.phone.phoneNumber)

		# Wait for the user to enter the SMS code and confirm the login
		self.wait_for_login()
		# Open ZEC click bot
		self.refresh()

	def open_current_channel_options(self):
		all_peers_info = WebDriverWait(self.driver, DRIVER_WAIT_TIME).until(
			EC.presence_of_all_elements_located((By.CLASS_NAME, 'tg_head_btn'))
		)
		all_peers_info[len(all_peers_info) - 1].click()

	def leave_current_channel(self):
		print("Leaving current channel..!")
		try:
			if self.click("a", ["Leave"], 'md_modal_list_peer_action pull-right') == False:
				self.click("a", ["Leave channel"], 'md_modal_section_link')
				return True
		except:
			print("Channel already is left")
		return False

	def press_escape(self):
		print("Presing escape key..!")
		actions = ActionChains(self.driver)
		actions.send_keys(Keys.ESCAPE)
		actions.perform()

	def is_screen_clear(self):
		try:
			popup = WebDriverWait(self.driver, DRIVER_WAIT_TIME / 2).until(
				EC.presence_of_all_elements_located((By.CLASS_NAME, 'error_modal_description'))
			)
			print("popup with errors found..!")
			self.press_escape()
			print("Pressing escape..!")
		except TimeoutException:
			return True
		return False

	def leave_chat(self, chat):
		print("Leaving chat: " + chat.get_info())
		self.open_channel(chat.link)
		sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
		# If the chat is valid leave it from the webpage otherwise just remove it from the list
		if self.is_screen_clear():
			print("Chat is valid..Continue processing..!")
			self.open_current_channel_options()
			sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
			if self.leave_current_channel():
				sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
				if self.click_ok_popup_button():
					sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
		# After everything runs successfully in the telegram, remove it here as well
		print("Removing chat from the collection..!")
		self.chatsJoined.remove(chat)

	def run_bot(self):
		# Leave all channels which are expired
		print("Check if there are expired chats and leave them...!")
		has_any_expired_channel = False
		for chat in self.chatsJoined:
			if chat.is_expired():
				self.leave_chat(chat)
				print("Chat removed successfully..!")
				has_any_expired_channel = True
		if has_any_expired_channel:
			self.open_channel(BOT_LINK)
			sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
		# Process with the operation
		if self.isOperationInitialized == False:
			self.init_operation()
			sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
		if self.operation == Operation.JOIN:
			self.join_chats()
		elif self.operation == Operation.VISIT:
			self.visit_sites()
		else:
			self.message_bots()

	def run(self):
		self.driver.get("https://web.telegram.org/#/login")

		try:
			self.login()
			sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
			runs = 0
			# Variable to define the starting time of the program
			start_time = timeit.default_timer()
			while True:
				try:
					if self.is_screen_clear() == False:
						raise Exception("Screen has some errors..!")
					print("===========================================================")
					# TODO try and catch exception 
					#try:
					self.run_bot()
					runs+=1
					time_upto_last_run = timeit.default_timer()
					print("Running for '", runs, "'' runs for '", (time_upto_last_run - start_time), "' seconds")
					# Sleep the bot every BOT_WAIT_TIME seconds for BOT_SLEEP_TIME seconds and then refresh
					if (time_upto_last_run - start_time) >= BOT_WAIT_TIME:
						sleep(BOT_SLEEP_TIME)
						start_time = timeit.default_timer()
						self.refresh()
					else:
						sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
				except Exception as e:
					print("Some critical error appeared on the screen..! Sleeping for some time and then try again untill error is not present..!")
					print(repr(e))
					traceback.print_exc()
					sleep(HOUR)
					self.refresh()
				print("===========================================================")

		finally:
			print("Closing the driver")
			self.driver.quit()
			self.cache_joined_channels()



# Unbuffer the print in order to show the data during the executing of the program
# instead of when the program finishes
import sys
sys.stdout = Unbuffered(sys.stdout)