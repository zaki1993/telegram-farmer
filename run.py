import sys
from phone import Phone
from bot import Bot
from operation import Operation
from selenium import webdriver
import random

useragent = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
			 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
			 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36',
			 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
			 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36']

def start_bot(phone):
	profile = webdriver.FirefoxProfile()
	randomuseragent = random.choice(useragent)
	print("user agent is", randomuseragent)
	profile.set_preference("general.useragent.override", randomuseragent)
	Bot(webdriver.Firefox(profile), Operation.VISIT, "ZEC", phone).run()

def start():
	myPhone = Phone(sys.argv[1], sys.argv[2])
	start_bot(myPhone)

start()