import time

def sleep(ms):
	timenow = datetime.now()
	print("Sleeping for: ", ms, " ms. Sleep is from ", str(timenow), "to", str(timenow + timedelta(hours = ms / 1000 / 3600)))
	time.sleep(ms / 1000)
