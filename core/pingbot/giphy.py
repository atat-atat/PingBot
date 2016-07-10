"""
Giphy Module
"""

from urllib.parse import quote_plus
from core import pingbot

async def get_gif(query, index=0, key="dc6zaTOxFJmzC"):
	query = quote_plus(query)
	url = "http://api.giphy.com/v1/gifs/search?q={}&api_key={}".format(query, key)

	resp = await pingbot.WT().async_json_content(url)
	if len(resp["data"]) == 0:
		return None

	return Gif(resp["data"][index]["type"], resp["data"][index]["id"], resp["data"][index]["slug"], resp["data"][index]["url"], resp["data"][index]["bitly_gif_url"], resp["data"][index]["bitly_url"], resp["data"][index]["embed_url"], resp["data"][index]["username"], resp["data"][index]["source"], resp["data"][index]["rating"], resp["data"][index]["content_url"], resp["data"][index]["source_tld"], resp["data"][index]["source_post_url"], resp["data"][index]["is_indexable"], resp["data"][index]["import_datetime"], resp["data"][index]["trending_datetime"], resp["data"][index]["images"])

class Gif:
	def __init__(self, image_type, image_id, slug, url, bitly_gif_url, bitly_url, embed_url, username, source, rating, content_url, source_tld, source_post_url, is_indexable, import_datetime, trending_datetime, images):
		self.image_type = image_type
		self.image_id = image_id
		self.slug = slug
		self.url = url
		self.bitly_gif_url = bitly_gif_url
		self.bitly_url = bitly_url
		self.embed_url = embed_url
		self.username = username
		self.source = source
		self.rating = rating
		self.content_url = content_url
		self.source_tld = source_tld
		self.source_post_url = source_post_url
		self.is_indexable = is_indexable
		self.import_datetime = import_datetime
		self.trending_datetime = trending_datetime
		self.images = images
		#https://media.giphy.com/media/xTk9ZPDCfGw1RALwxq/giphy.gif
		self.direct_embed_url = "https://media.giphy.com/media/{}/giphy.{}".format(self.image_id, self.image_type)