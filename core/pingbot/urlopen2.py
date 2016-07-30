try:
	import urlparse
	from urllib import urlencode
	import urllib2 as urllib
except ImportError: # For Python 3
	import urllib.parse as urlparse
	from urllib.parse import urlencode
	import urllib

import json

try:
	import aiohttp
	import asyncio
	async_allowed = True
except ImportError:
	async_allowed = False

def urlparams(url, params):

	url_parts = list(urlparse.urlparse(url))
	query = dict(urlparse.parse_qsl(url_parts[4]))
	query.update(params)

	url_parts[4] = urlencode(query)

	return urlparse.urlunparse(url_parts)

def _urlopen(url, **kwargs):
	headers = kwargs.get('headers', None)
	params = kwargs.get('params', None)

	if headers != None:
		if params != None:
			url = urlparams(url, params=params)

		req = urllib.request.Request(url, headers=headers)

		resp = urllib.request.urlopen(req)
		return resp
	else:
		if params != None:
			url = urlparams(url, params=params)
		resp = urllib.request.urlopen(url)
		return resp

class urlopen:
	def __init__(self, url, **kwargs):
		self.url = url
		self.return_data = _urlopen(url, **kwargs)

	def __repr__(self):
		return self.return_data

	@property
	def json(self):
		return json.loads(self.return_data.read().decode())

	@property
	def string(self):
		return self.return_data.read().decode()

if async_allowed:
	class async_urlopen_class:
		async def _init_(self, url, **kwargs):
			headers = kwargs.get('headers', None)
			params = kwargs.get('params', None)

			if params != None:
				url = urlparams(url, params)
			print(url)

			async with aiohttp.ClientSession() as session:
					async with session.post(url, headers=headers) as resp:
						r = await resp.json()
			return r
		
	async def async_urlopen(url, **kwargs):
		return await async_urlopen_class()._init_(url, **kwargs)

	async def async_urlopen2(url, **kwargs):
		headers = kwargs.get('headers')
		params = kwargs.get('params')
		url = urlparams(url, params)

		print(url)

		async with aiohttp.ClientSession() as session:
			async with session.post(url, headers=headers) as resp:
				r = await resp.json()
		return r