import core.pingbot, aiohttp, requests, asyncio, youtube_dl, re, urllib.request, urllib.parse, urllib.error
from bs4 import BeautifulSoup
from html.entities import name2codepoint

class WT:
	"""
	An arsenal of tools for web scraping/in general web stuff (includes async stuff too.)
	"""
	def __init__(self, url = None, query = None):
		self._url = url
		self._query = query

	def url_content(self, url = None):
		if url == None:
			if self._url == None:
				raise core.pingbot.errors.PingBotError("An error has occurred while executing web_get; No url provided.")
			else:
				url = self._url
		req = urllib.request.Request(url)
		with urllib.request.urlopen(req) as response:
			return response.read()

	def web_get(self, url = None):
		"""
		Code from JordanKinsley's PinkiePyBot

		https://github.com/JordanKinsley/PinkiePyBot
		"""
		if url == None:
			if self._url == None:
				raise core.pingbot.errors.PingBotError("An error has occurred while executing web_get; No url provided.")
			else:
				url = self._url

		if not url.startswith('http'): 
			raise core.pingbot.errors.PingBotError("An error has occurred while executing web_get; Bad link.")

		opener = urllib.request.build_opener()
		opener.addheaders = [('User-agent', 'Mozilla/5.0')]
		u = opener.open(url)
		_bytes = u.read()
		try:
			_bytes = _bytes.decode('utf-8')
		except UnicodeDecodeError:
			_bytes = _bytes.decode('ISO-8859-1')
		u.close()
		return _bytes


	def div_set(self, url, query):
		self._url = url
		self._query = query

	def div_get(self, dtype, content, query = None, url=None): #ripped straight from original div_get function (ill change this a bit later.)
		if url == None:
			if self._url == None:
				raise core.pingbot.errors.PingBotError("An error has occurred while executing div_get; No URL provided.")
			else:
				url = self._url
		if query == None:
			if self._query == None:
				raise core.pingbot.errors.PingBotError("An error has occurred while executing div_get; No query provided.")
			else:
				query = self._query

		try:
			r = requests.get(url+"{}".format(query))
			soup = BeautifulSoup(r.content, "html.parser")
			outcome = soup.find("div",attrs={dtype:content}).text
		except AttributeError as e:
			return
		return outcome

	def dl_youtube(self, url, **kwargs):
		_format = kwargs.get('format', 'bestaudio/best')
		_extractaudio = kwargs.get('extractaudio', True)
		_audioformat = kwargs.get('audioformat', "mp3")
		_outtmpl = kwargs.get('outtmpl', '%(id)s')
		_noplaylist = kwargs.get('noplaylist', True)
		_no_dl = kwargs.get('no_dl', False)
		_no_resp = kwargs.get('no_resp', False)
		options = {
			'format': _format, # choice of quality
			'extractaudio' : _extractaudio,      # only keep the audio
			'audioformat' : _audioformat,      # convert to mp3
			'outtmpl': _outtmpl,        # name the file the ID of the video
			'noplaylist' : _noplaylist,        # only download single song, not playlist
		}
		with youtube_dl.YoutubeDL(options) as ydl:
			r = ydl.extract_info(url, download=False)
			if _no_dl == False:
				ydl.download([url])
		if _no_resp == False:
			return r

	async def async_url_content(self, url=None):
		"""
		Load content from a website.
		"""
		if url == None:
			if self._url == None:
				raise core.pingbot.errors.PingBotError("An error has occurred while executing async_resp_content; No URL provided.")
			else:
				url = self._url
		async with aiohttp.get(url) as r:
			response = await r.read()
			return response

	async def async_json_content(self, url=None):
		"""
		Load JSON content from a website.
		"""
		if url == None:
			if self._url == None:
				raise core.pingbot.errors.PingBotError("An error has occurred while executing async_resp_content; No URL provided.")
			else:
				url = self._url

		async with aiohttp.get(url) as r:
			response = await r.json()
			return response

	async def async_save_image(self, file, url=None):
		"""
		Save content from a URL as image.
		"""
		if url == None:
			if self._url == None:
				raise core.pingbot.errors.PingBotError("An error has occurred while executing async_save_image; No URL provided.")
			else:
				url = self._url

		content = await self.async_url_content(url)
		with open(file, 'wb') as f:
			f.write(content)

	async def search_youtube(self, query, **kwargs):
		index = kwargs.get('index', 0)
		url = "https://www.youtube.com/results?search_query=" + query
		url = url.replace(" ", "%20")
		response = await self.async_url_content(url)
		soup = BeautifulSoup(response, "html.parser")
		vids = soup.findAll(attrs={'class':'yt-uix-tile-link'})
		vid = vids[index]
		video = 'https://www.youtube.com' + vid['href']
		return video

