from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.keys import Keys
from usercacheobserver import UserCacheObserver
from chatcacheobserver import ChatCacheObserver
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
from localstorage import LocalStorage
from operation import Operation
from selenium import webdriver
from logger import Logger
from user import *
from botutils import *
from chat import Chat
from controller import Controller
import numpy as np
import traceback
import timeit
import random
import sys
import re

DEBUG = True

TIME_UNTIL_NEXT_USER = 600

class Bot:
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

	def __init__(self, driver, operation, currency):
		print("Initializing bot..!")
		self.driver = driver
		self.controller = Controller(driver)
		self.operation = operation
		self.currency = currency
		self.userObserver = UserCacheObserver()
		self.chatCache = ChatCacheObserver()
		self.storage = LocalStorage(self.driver)
		self.currentUser = None
		self.chatsJoined = None
		self.logger = Logger("log.log", "BotLogger")
		self.balanceLogger = Logger("balance.log", "BalanceLogger")

	def set_user(self, user):
		print ("Bot::Switching to user: ", user)
		self.currentUser = user

	def close_tab(self):
		self.driver.switch_to.window(self.driver.window_handles[1])
		self.driver.close()
		self.driver.switch_to.window(self.driver.window_handles[0])

	def refresh(self, channel_link = BOT_LINK):
		print("Bot::Refreshing link ", channel_link)
		self.driver.get(channel_link)
		self.driver.refresh()
		sleep(SLEEP_TIME_BETWEEN_COMPONENTS)

	def get_last_message(self):
		try:
			messages = WebDriverWait(self.driver, DRIVER_WAIT_TIME).until(
				EC.presence_of_all_elements_located((By.XPATH, "//div[@class='im_message_text']"))
			)
			msg = messages[len(messages) - 1].text
			return msg
		except TimeoutException:
			return None

	def change_operation(self, new_operation):
		if new_operation not in self.currentUser.allowed_operations:
			new_operation = random_from_list(np.setdiff1d([self.operation], self.currentUser.allowed_operations))
			if new_operation == None:
				new_operation = Operation.VISIT
		print("Bot::Changing operation..!")
		self.operation = new_operation
		self.isOperationInitialized = False
		self.refresh()
		self.waitingForTasksRetry = 0
		sleep(SLEEP_TIME_BETWEEN_COMPONENTS)

	def start_join_channel(self):
		return self.controller.send_text("/join")

	def start_visit_sites(self):
		return self.controller.send_text("/visit")

	def start_message_bots(self):
		return self.click_button_by_name(["Message bots"])

	def click_button_by_name(self, names):
		return self.controller.click("button", names)

	def click_link_by_name(self, names):
		return self.controller.click("a", names)

	def skip_channel(self):
		return self.click_button_by_name(["Skip"])

	def open_joining_channel(self):
		return self.click_link_by_name(["Go to channel", "Go to group"])

	def validate_join_chats(self):
		print("Bot::Validate joining chats")
		message = self.get_last_message().strip()
		if message != None:
			print("Bot::Validating message: ", message.encode("utf-8"));
			result = True
			if message.find("We cannot find you") != -1 or message.find("You already completed this task") != -1:
				self.skip_channel()
				result = False
			elif message.find("There is a new chat for you to join") != -1 or message.find("Sorry, that task is no longer valid") != -1 or message.find("There is a new chat for you to join") != -1:
				self.start_join_channel()
				sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
				result = False
			elif message.find("Sorry, there are no new ads available.") != -1 or message.find("Join chats") != -1:
				print("Bot::Waiting for new tasks")
				sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
				result = False
				self.waitingForTasksRetry += 1
				print("Bot::RETRY: ", self.waitingForTasksRetry," from JOIN")
				if self.waitingForTasksRetry % RETRY_LIMIT == 0:
					self.change_operation(Operation.VISIT)
		else:
			result = False
		if result == False:
			sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
			self.open_channel(BOT_LINK)
		
		print("Bot::Validation is: ", result)
		
		return result

	def join_openned_channel(self):
		return self.controller.click("a", ["JOIN"], "btn btn-primary im_start_btn")

	def open_channel(self, channel_link = BOT_LINK):
		self.refresh(channel_link)

	def get_hours_untill_reward(self):
		messages = WebDriverWait(self.driver, DRIVER_WAIT_TIME).until(
			EC.presence_of_all_elements_located((By.CLASS_NAME, 'im_message_text'))
		)
		for message in reversed(messages):
			print("Bot::Processing message: ", message.text.encode("utf-8"))
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
		print("Bot::Initializing operation")

	def is_bot_joined_success(self):
		sleep(SLEEP_TIME_BETWEEN_COMPONENTS / 2)
		return self.get_last_message().find("We cannot find you") == -1

	def join_chats(self, channel_url = None):
		if self.validate_join_chats():
			sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
			if self.open_joining_channel():
				sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
				# The bot update to have a link on the chats as well
				if self.controller.click_ok_popup_button():
					sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
					# Get current url. It would be something like that https://t.me/Jizzax_Zomin_bozor
					if len(self.driver.window_handles) < 2:
						self.skip_channel()
						sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
						self.refresh()
					else:
						self.driver.switch_to.window(self.driver.window_handles[1])
						print("Bot::Current url is ", self.driver.current_url)
						chatUrlNameParts = self.driver.current_url.split("/")
						print("Bot::URL parts are", chatUrlNameParts)
						chatUrlName = chatUrlNameParts[len(chatUrlNameParts) - 1].strip()
						print("Bot::Extracted chat name", chatUrlName)
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
							print("Bot::Hours untill reward '", hoursUntillReward, "'")
							joinDate = datetime.now()
							leaveDate = joinDate + timedelta(hours = hoursUntillReward)
							chat = Chat(channel_url, joinDate, leaveDate)
							self.chatsJoined.append(chat)
							print("Bot::Joined channel: ", chat.get_info())
							self.joinedChatsCount += 1
							print("Bot::You have joined ", self.joinedChatsCount, " chats in total")
							if self.joinedChatsCount % self.joinLimit == 0:
								self.change_operation(Operation.VISIT)
						else:
							self.change_operation(Operation.VISIT)

	def open_site(self):
		print("Bot::Openning site")
		return self.click_link_by_name(["Go to website"])

	def validate_visit_sites(self):
		print("Bot::Validate visiting sites")
		message = self.get_last_message().strip()
		print("Bot::Validating message: ", message.encode("utf-8"));
		result = True
		if message.find("Sorry, there are no new ads available.") != -1:
			print("Bot::Waiting for new tasks")
			sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
			result = False
			self.waitingForTasksRetry += 1
			print("Bot::RETRY: ", self.waitingForTasksRetry," from VISIT")
			if self.waitingForTasksRetry % RETRY_LIMIT == 0:
				self.change_operation(Operation.JOIN)
		
		if result == False:
			sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
			self.open_channel(BOT_LINK)
		
		print("Bot::Validation is: ", result)
		
		return result

	def extract_sleep_time(self, message):
		messages = WebDriverWait(self.driver, DRIVER_WAIT_TIME).until(
			EC.presence_of_all_elements_located((By.CLASS_NAME, 'im_message_text'))
		)
		sleepTime = 0
		for message in reversed(messages):
			print("Bot::Processing message: ", message.text.encode("utf-8"))
			if message.text.find("Please stay on the site for at least") != -1:
				regex = re.search('Please stay on the site for at least (.+?) seconds', message.text)
				print("Bot::Regex result is ", regex)
				sleepTime = int(regex.group(1)) * SECOND
				break
			elif message.text.find("You must stay on the site for") != -1:
				regex = re.search('You must stay on the site for (.+?) seconds to get your reward', message.text)
				print("Bot::Regex result is ", regex)
				sleepTime = int(regex.group(1)) * SECOND
				break
		return sleepTime

	def visit_sites(self):
		if self.validate_visit_sites():
			sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
			if self.open_site():
				sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
				if self.controller.click_ok_popup_button():
					sleep(2 * SLEEP_TIME_BETWEEN_COMPONENTS - SECOND)
					siteSleepTimeUntillReward = self.extract_sleep_time(self.get_last_message())
					if siteSleepTimeUntillReward != 0:
						sleep(siteSleepTimeUntillReward)
					self.close_tab()
					if siteSleepTimeUntillReward != 0:
						self.visitedSitesCount += 1
						print("Bot::You have visited ", self.visitedSitesCount, " sites in total")
						if self.visitedSitesCount % self.visitLimit == 0:
							self.change_operation(Operation.JOIN)
					else:
						self.skip_channel()

	def message_bots(self):
		print("Bot::Messaging bots")

	def open_current_channel_options(self):
		all_peers_info = WebDriverWait(self.driver, DRIVER_WAIT_TIME).until(
			EC.presence_of_all_elements_located((By.CLASS_NAME, 'tg_head_btn'))
		)
		all_peers_info[len(all_peers_info) - 1].click()

	def leave_current_channel(self):
		print("Bot::Leaving current channel..!")
		try:
			if self.controller.click("a", ["Leave"], 'md_modal_list_peer_action pull-right') == False:
				self.controller.click("a", ["Leave channel"], 'md_modal_section_link')
				return True
		except:
			print("Bot::Channel already is left")
		return False

	def get_balance(self):
		try:
			if self.controller.is_screen_clear(False) == False:
				return -1.0
			print("Bot::getting current balance")
			self.controller.send_text("/balance")
			sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
			message = self.get_last_message()
			return float(re.search('Available balance: (.+?) ZEC', message).group(1)) if message.find("Available balance") != -1 else 0.0
		except:
			return -1.0
	def leave_chat(self, chat):
		print("Bot::Leaving chat: " + chat.get_info())
		self.open_channel(chat.link)
		sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
		# If the chat is valid leave it from the webpage otherwise just remove it from the list
		if self.controller.is_screen_clear():
			print("Bot::Chat is valid..Continue processing..!")
			self.open_current_channel_options()
			sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
			if self.leave_current_channel():
				sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
				if self.controller.click_ok_popup_button():
					sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
		print("Bot::Removing chat from the collection..!")
		self.chatsJoined.remove(chat)

	def run_bot(self):
		print("Bot::Check if there are expired chats and leave them...!")
		has_any_expired_channel = False
		for chat in self.chatsJoined:
			if chat.is_expired():
				self.leave_chat(chat)
				print("Bot::Chat removed successfully..!")
				has_any_expired_channel = True
		if has_any_expired_channel:
			self.open_channel(BOT_LINK)
			sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
		if self.isOperationInitialized == False:
			self.init_operation()
			sleep(SLEEP_TIME_BETWEEN_COMPONENTS)
		if self.operation == Operation.JOIN:
			self.join_chats()
		elif self.operation == Operation.VISIT:
			self.visit_sites()
		else:
			self.message_bots()

	def cache_balance(self, newBalance):
		self.balanceLogger.log("Total balance earned from user " + self.currentUser.phone + " in this run = " + self.currentUser.on_cache(newBalance) + "\n")

	def cache(self):
		if self.currentUser != None:
			print("Bot::caching user data")
			self.cache_balance(self.get_balance())
			self.chatCache.cache_joined_channels(self.currentUser.phone, self.chatsJoined)

	def switch_user(self, context):
		try:
			self.cache()
		except:
			print("Exception while caching..!")
		phone, data = context
		self.refresh()
		self.storage.clear()
		self.storage.set_json(data)
		if DEBUG: self.storage.get()
		self.chatsJoined = self.chatCache.load_chats_from_last_run(phone)
		self.reset()
		self.refresh()
		balance = self.get_balance()
		if balance != -1.0: self.set_user(User(phone, data, balance))

	def __user_active__(self):
		return self.currentUser != None and self.currentUser.active

	def start(self):
		print("Bot::Starting the bot..!")
		try:
			firstRun = True
			runs = 0
			start_time = timeit.default_timer()
			while True:
				self.userObserver.observe()
				current_time = timeit.default_timer()
				if firstRun or current_time - start_time >= TIME_UNTIL_NEXT_USER or not self.__user_active__():
					self.switch_user(self.userObserver.pick_next())
					start_time = timeit.default_timer()
					firstRun = False
				if self.__user_active__():
					if DEBUG: print(current_time - start_time, " untill next user. Current time is", TIME_UNTIL_NEXT_USER)
					try:
						if self.controller.is_screen_clear() == False:
							raise Exception("Screen has some errors..!")
						print("===========================================================")
						self.run_bot()
						runs += 1
						time_upto_last_run = timeit.default_timer()
						print("Bot::Running for '", runs, "'' runs for '", (time_upto_last_run - start_time), "' seconds")
						print("===========================================================")
					except Exception as e:
						print("Bot::Some critical error appeared on the screen..! Sleeping for some time and then try again untill error is not present..!")
						print(repr(e))
						traceback.print_exc()
						self.switch_user(self.userObserver.pick_next())
						start_time = timeit.default_timer()
		finally:
			print("Bot::Closing the driver")
			self.driver.quit()
			self.cache()

def prepare_driver():
	driver = webdriver.Chrome()
	driver.maximize_window()
	return driver

def buffer():
	sys.stdout = Unbuffered(sys.stdout)

buffer()
driver = prepare_driver()
print("Starting..!")
Bot(driver, Operation.VISIT, "ZEC").start()
