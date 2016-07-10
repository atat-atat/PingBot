"""
Based off of MALnet_bot by Eskat0n : https://github.com/Eskat0n/MALnet_bot
"""
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus
from urllib.request import HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler, build_opener, install_opener, urlopen

def authorize(username, password):
	pass_manager = HTTPPasswordMgrWithDefaultRealm()
	pass_manager.add_password(None, 'http://myanimelist.net/api', username, password)

	auth_handler = HTTPBasicAuthHandler(pass_manager)

	opener = build_opener(auth_handler)
	install_opener(opener)

def mal_search(entry_type, term):
	parameter = quote_plus(term)
	url = "http://myanimelist.net/api/{}/search.xml?q={}".format(entry_type, parameter)

	response = urlopen(url).read().decode()
	if len(response) == 0:
		return None

	return ET.fromstring(response)

def get_anime(title):
	resp = mal_search('anime', title)

	if resp == None:
		return None

	return AnimeEntry(
		entry_id=resp[0].find('id').text,
		title=resp[0].find('title').text,
		english=resp[0].find('english').text,
		synonyms=resp[0].find('synonyms').text,
		episodes=resp[0].find('episodes').text,
		score=resp[0].find('score').text,
		entry_type=resp[0].find('type').text,
		status=resp[0].find('status').text,
		start_date=resp[0].find('start_date').text,
		end_date=resp[0].find('end_date').text,
		synopsis=resp[0].find('synopsis').text,
		image=resp[0].find('image').text)

class AnimeEntry:
	"""
	Code based on Eskat0n's MALnet_bot

	ttps://github.com/Eskat0n/MALnet_both
	"""
	def __init__(self, entry_id, title, english, synonyms, episodes, score, entry_type, status, start_date, end_date, synopsis, image):
		self._id = entry_id
		self.title = title
		self.english = english
		self.synonyms = synonyms
		self.episodes = episodes
		self.score = score
		self.entry_type = entry_type
		self.status = status
		self.start_date = start_date
		self.end_date = end_date
		self.synopsis = synopsis
		self.image = image