from botutils import *
from selenium.common.exceptions import StaleElementReferenceException, ElementNotInteractableException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

class Controller():
	def __init__(self, driver):
		self.driver = driver

	def click_ok_popup_button(self):
		try:
			ok_popup_btn = WebDriverWait(self.driver, DRIVER_WAIT_TIME).until(
				EC.presence_of_element_located((By.XPATH, "//button[@class='btn btn-md btn-md-primary']"))
			)
			ok_popup_btn.click()
		except:
			print("Controller::OK Button is not present")
			return False
		print("Controller::Clicking OK button")
		return True

	def click(self, component_type, names, classes = "btn reply_markup_button"):
		try:
			buttons = WebDriverWait(self.driver, DRIVER_WAIT_TIME).until(
				EC.presence_of_all_elements_located((By.XPATH, "//" + component_type + "[@class='" + classes + "']"))
			)
			print("Controller::Searching for ", names)
			print("Controller::Total number of buttons found ", len(buttons))
			for button in reversed(buttons):
				text = button.text
				print("Controller::Processing button ", button.text.encode("utf-8"))
				for name in names:
					if text.strip().find(name.strip()) != -1:
						print("Controller::Clicking '",name.strip(),"' component")
						button.click()
						return True
		except TimeoutException:
			print("Controller::Component ", names, " was not found on the page in the given timeout")
		return False

	def send_text(self, text):
		textArea = WebDriverWait(self.driver, DRIVER_WAIT_TIME).until(
			EC.presence_of_element_located((By.XPATH, "//div[@class='composer_rich_textarea']"))
		)
		textArea.send_keys(text)
		textArea.send_keys(Keys.ENTER)

	def press_escape(self):
		print("Presing escape key..!")
		actions = ActionChains(self.driver)
		actions.send_keys(Keys.ESCAPE)
		actions.perform()

	def is_screen_clear(self, clear = False):
		try:
			popup = WebDriverWait(self.driver, DRIVER_WAIT_TIME / 2).until(
				EC.presence_of_all_elements_located((By.CLASS_NAME, 'error_modal_description'))
			)
			print("Controller::popup with errors found..!")
			if clear:
				self.press_escape()
				print("Controller::Pressing escape..!")
		except TimeoutException:
			return True
		return False

	def popup_exists(self):
		try:
			popup = WebDriverWait(self.driver, DRIVER_WAIT_TIME / 2).until(
				EC.presence_of_all_elements_located((By.CLASS_NAME, "//button[@class='confirm_modal_description']"))
			)
		except:
			print("Controller::Popup is not present")
			return False
		return True

	def click_cancel_popup_button():
		try:
			cancel_popup_btn = WebDriverWait(self.driver, DRIVER_WAIT_TIME).until(
				EC.presence_of_all_elements_located((By.CLASS_NAME, "//button[@class='btn btn-md']"))
			)
			cancel_popup_btn[0].click()
		except:
			print("Controller::Cancel Button is not present")
			return False
		print("Controller::Clicking Cancel button")
		return True

	def is_switch_to_desktop():
		try:
			popup = WebDriverWait(self.driver, DRIVER_WAIT_TIME / 2).until(
				EC.presence_of_all_elements_located((By.CLASS_NAME, "//button[@class='confirm_modal_description']"))
			)
			return popup.text == 'Would you like to switch to desktop version?'
		except:
			print("Controller::Popup is not present")
			return False
		return False

	def is_switch_to_mobile():
		try:
			popup = WebDriverWait(self.driver, DRIVER_WAIT_TIME / 2).until(
				EC.presence_of_all_elements_located((By.CLASS_NAME, "//button[@class='confirm_modal_description']"))
			)
			return popup.text == 'Would you like to switch to mobile version?'
		except:
			print("Controller::Popup is not present")
			return False
		return False

	def switch_screen(self):
		if self.popup_exits():
			if self.is_switch_to_desktop():
				self.click_ok_popup_button()
			if self.is_switch_to_mobile():
				self.click_cancel_popup_button()