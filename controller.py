class Controller():
	def __init__(self, driver):
		self.driver = driver

	def send_text(self, text):
		textArea = WebDriverWait(self.driver, DRIVER_WAIT_TIME).until(
			EC.presence_of_element_located((By.XPATH, "//div[@class='composer_rich_textarea']"))
		)
		textArea.send_keys(text)
		textArea.send_keys(Keys.ENTER)