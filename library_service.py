import requests
import xbmc
import json

class AudioBookShelfLibraryService:
	_instance = None
	HEADERS_TEMPLATE = {
		"Content-Type": "application/json"
	}

	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			cls._instance = super(AudioBookShelfLibraryService, cls).__new__(cls)
		return cls._instance

	def __init__(self, base_url=None, token=None):
		if not hasattr(self, 'initialized'):
			self.token = token
			self.base_url = base_url
			self.headers = self.HEADERS_TEMPLATE.copy()
			self.headers["Authorization"] = "Bearer {}".format(token)
			self.initialized = True

	def get_all_libraries(self):
		url = "{}/api/libraries".format(self.base_url)
		response = requests.get(url, headers=self.headers)
		return response.json()

	def get_library(self, library_id, include_filterdata=False):
		url = "{}/api/libraries/{}".format(self.base_url, library_id)
		params = {}
		if include_filterdata:
			params["include"] = "filterdata"
		
		response = requests.get(url, headers=self.headers, params=params)
		return response.json()

	def get_library_items(self, library_id, limit=None, page=None, sort=None, desc=None, filter=None, minified=None, collapseseries=None, include=None):
		url = "{}/api/libraries/{}/items".format(self.base_url, library_id)
		params = {}
		
		if limit is not None:
			params["limit"] = limit
		if page is not None:
			params["page"] = page
		if sort is not None:
			params["sort"] = sort
		if desc is not None:
			params["desc"] = desc
		if filter is not None:
			params["filter"] = filter
		if minified is not None:
			params["minified"] = minified
		if collapseseries is not None:
			params["collapseseries"] = collapseseries
		if include is not None:
			params["include"] = include
			
		response = requests.get(url, headers=self.headers, params=params)
		return response.json()

	def get_library_item_by_id(self, item_id, expanded=None, include=None, episode=None):
		url = "{}/api/items/{}".format(self.base_url, item_id)
		params = {}
		
		if expanded is not None:
			params["expanded"] = expanded
		if include is not None:
			params["include"] = include
		if episode is not None:
			params["episode"] = episode
		
		response = requests.get(url, headers=self.headers, params=params)
		return response.json()

	def play_library_item_by_id(self, item_id, episode_id=None, device_info=None, force_direct_play=False, force_transcode=False, supported_mime_types=None, media_player="unknown"):
		if episode_id:
			url = "{}/api/items/{}/play/{}".format(self.base_url, item_id, episode_id)
		else:
			url = "{}/api/items/{}/play".format(self.base_url, item_id)

		payload = {
			"forceDirectPlay": force_direct_play,
			"forceTranscode": force_transcode,
			"mediaPlayer": media_player
		}

		if device_info:
			payload["deviceInfo"] = device_info

		if supported_mime_types:
			payload["supportedMimeTypes"] = supported_mime_types

		response = requests.post(url, headers=self.headers, json=payload)

		if response.status_code != 200:
			raise Exception("Error fetching item by ID. Status code: {}".format(response.status_code))

		return response.json()

	def get_file_url(self, iid):
		response = self.play_library_item_by_id(iid, supported_mime_types=["audio/flac", "audio/mpeg", "audio/mp4"])

		full_content_url = None
		if "audioTracks" in response and len(response["audioTracks"]) > 0:
			relative_content_url = response["audioTracks"][0]["contentUrl"]
			full_content_url = "{}{}?token={}".format(self.base_url, relative_content_url, self.token)

		if not full_content_url:
			raise Exception("Content URL not found or empty.")
		return full_content_url  

	def get_media_progress(self, library_item_id, episode_id=None):
		endpoint = "/api/me/progress/{}".format(library_item_id)
		if episode_id:
			endpoint += "/{}".format(episode_id)

		response = requests.get(self.base_url + endpoint, headers=self.headers)
		response.raise_for_status()

		try:
			return response.json()
		except json.JSONDecodeError:
			xbmc.log("Failed to decode JSON. Response content:", xbmc.LOGERROR)
			xbmc.log(response.text, xbmc.LOGDEBUG)
			return {'message': 'Failed to decode JSON'}

	def update_media_progress(self, library_item_id, data, episode_id=None):
		endpoint = "/api/me/progress/{}".format(library_item_id)
		if episode_id:
			endpoint += "/{}".format(episode_id)

		response = requests.patch(self.base_url + endpoint, headers=self.headers, json=data)
		response.raise_for_status()

		try:
			return response.json()
		except json.JSONDecodeError:
			xbmc.log("Ungültige oder leere JSON-Antwort erhalten:", xbmc.LOGERROR)
			return {'message': 'Failed to decode JSON'}

	def get_chapters(self, library_item_id):
		item = self.get_library_item_by_id(library_item_id)
		chapters = item['media']['chapters']
		return chapters

