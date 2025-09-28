import requests

class AudioBookShelfService:
	def __init__(self, base_url):
		self.base_url = base_url

	def login(self, username, password):
		url = "{}/login".format(self.base_url)
		payload = {
			"username": username,
			"password": password
		}
		return self._post(url, payload).get("user")

	def logout(self, socketId=None):
		url = "{}/logout".format(self.base_url)
		payload = {}
		if socketId:
			payload["socketId"] = socketId
		self._post(url, payload)

	def initialize_server(self, new_root_username, new_root_password=""):
		url = "{}/init".format(self.base_url)
		payload = {
			"newRoot": {
				"username": new_root_username,
				"password": new_root_password
			}
		}
		self._post(url, payload)

	def server_status(self):
		url = "{}/status".format(self.base_url)
		return self._get(url)        

	def ping(self):
		url = "{}/ping".format(self.base_url)
		return self._get(url)

	def healthcheck(self):
		url = "{}/healthcheck".format(self.base_url)
		self._get(url)

	def _post(self, url, payload=None):
		headers = {"Content-Type": "application/json"}
		response = requests.post(url, headers=headers, json=payload)
		response.raise_for_status()
		return response.json()

	def _get(self, url):
		response = requests.get(url)
		response.raise_for_status()
		return response.json()
