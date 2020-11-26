class LocalStorage:
    def __init__(self, driver) :
        self.driver = driver

    def set_json(self, json):
        self.driver.execute_script("var data = JSON.parse(JSON.stringify(" + json + "));" \
            "Object.keys(data).forEach(function (k) {" \
            "localStorage.setItem(k, data[k]);" \
            "});")

    def clear(self):
        print("LocalStorage::Clearing localStorage")
        self.driver.execute_script("window.localStorage.clear();")

    def get(self):
        print("LocalStorage::", self.driver.execute_script("return localStorage;"))