import time
from datetime import datetime, timedelta

# Time which the driver will wait to find component untill timeout exception is raised in seconds
DRIVER_WAIT_TIME = 10

# 1 second in milliseconds
SECOND = 1000

# 1 minute in milliseconds
MINUTE = 60 * SECOND

# 1 hour in milliseconds
HOUR = 60 * MINUTE

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

def current_datetime():
	return datetime.today().strftime("%m/%d/%Y, %H:%M:%S")

def sleep(ms):
	timenow = datetime.now()
	print("Sleeping for: ", ms, " ms. Sleep is from ", str(timenow), "to", str(timenow + timedelta(hours = ms / 1000 / 3600)))
	time.sleep(ms / 1000)

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
