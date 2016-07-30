import aiohttp, requests, asyncio, youtube_dl, re, urllib.request, urllib.parse, urllib.error, imgurpython
from imgurpython import ImgurClient
from core import pingbot
from bs4 import BeautifulSoup, Tag
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
				raise pingbot.errors.PingBotError("An error has occurred while executing web_get; No url provided.")
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
				raise pingbot.errors.PingBotError("An error has occurred while executing web_get; No url provided.")
			else:
				url = self._url

		if not url.startswith('http'): 
			raise pingbot.errors.PingBotError("An error has occurred while executing web_get; Bad link.")

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
				raise pingbot.errors.PingBotError("An error has occurred while executing div_get; No URL provided.")
			else:
				url = self._url
		if query == None:
			if self._query == None:
				raise pingbot.errors.PingBotError("An error has occurred while executing div_get; No query provided.")
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
				raise pingbot.errors.PingBotError("An error has occurred while executing async_resp_content; No URL provided.")
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
				raise pingbot.errors.PingBotError("An error has occurred while executing async_resp_content; No URL provided.")
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
				raise pingbot.errors.PingBotError("An error has occurred while executing async_save_image; No URL provided.")
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

	async def retrieve_html_images(self, url, **kwargs):
		"""
		Extract HTML img tags or meta image tags from a website, or tumblr blog.
		"""
		is_tumblr_link = kwargs.get('tumblr', False)
		#resp = await self.async_url_content(url)
		resp = urllib.request.urlopen(url) #aiohttp isnt too good with redirecting URLs, and since most of the time users would most likely provide the random link of a tumblr blog, i will just use urllib for now

		soup = BeautifulSoup(resp, "html.parser")
		images = []
		image = {}

		img_list = soup.findAll('meta', {"property":'og:image'})
		for og_image in img_list:
			if not og_image.get('content'):
				continue

			image = {'url': og_image['content']}
			next = og_image.nextSibling.nextSibling # calling once returns end of line char '\n'

			if next and isinstance(next, Tag) and next.get('property', '').startswith('og:image:'):
				dimension = next['content']
				prop = next.get('property').rsplit(':')[-1]
				image[prop] = dimension

				next = next.nextSibling.nextSibling
				if next and isinstance(next, Tag) and next.get('property', '').startswith('og:image:'):
					dimension = next['content']
					prop = next.get('property').rsplit(':')[-1]
					image[prop] = dimension

			if not is_tumblr_link:
				if 'srvcs.tumblr' not in image['url'] and 'avatar' not in image['url'] and image['url'].startswith('/'.join(url.split('/')[:3])):
					images.append(image['url'])
			else:
				if 'srvcs.tumblr' not in image['url'] and 'avatar' not in image['url']:
					images.append(image['url'])

		for img in soup.findAll('img'):
			if not is_tumblr_link:
				if 'gravatar' not in img.get('src') and 'srvcs.tumblr' not in img.get('src') and 'avatar' not in img.get('src') and img.get('src').startswith('/'.join(url.split('/')[:3])):
					images.append(img.get('src'))
			else:
				if 'gravatar' not in img.get('src') and 'srvcs.tumblr' not in img.get('src') and 'avatar' not in img.get('src'):
					images.append(img.get('src'))

		for ima in images:
			if 'img.youtube' in ima:
				images.remove(ima)

		return images

	def return_subreddit_result(self, subreddit, sort=None):
		"""
		Returns a random item from a subreddit.
		"""
		config = pingbot.Config("./user/config/bot.json").load_json()
		imgur_clientid = config['imgur']['client_id']
		imgur_clientsecret = config['imgur']['client_secret']
		imgur_client = ImgurClient(imgur_clientid, imgur_clientsecret)
		if sort != None:
			try:
				result = imgur_client.subreddit_gallery(subreddit, sort=sort)
				return result
			except IndexError:
				return None
		else:
			try:
				result = imgur_client.subreddit_gallery(subreddit)
				return result
			except IndexError:
				return None