from discord.ext import commands
from core import pingbot
from core.pingbot.messages import text
import asyncio
import feedparser
import discord

class Feeds:
	def __init__(self, bot):
		self.bot = bot
		self.last_feed = {}

	@commands.command(name="add_feed", aliases=["add-feed"], pass_context=True)
	@pingbot.permissions.has_permissions(manage_server=True)
	async def _add_feed_link(self, ctx, rss_url : str):
		"""
		🗣 Adds an RSS link to the feeds list.

		--------------------
		  USAGE: add_feed <rss url>
		EXAMPLE: add_feed http://myanimelist.net/rss/news.xml
		--------------------
		"""
		feeds_json = pingbot.Config('./user/cogs/feeds/feeds.json').load_json()
		d = feedparser.parse(rss_url)
		if 'bozo_exception' in d:
			await text("Invalid URL or data.", emoji="failure")
			return

		if ctx.message.server.id not in feeds_json:
			feeds_json[ctx.message.server.id] = {}
			feeds_json[ctx.message.server.id]["feeds"] = {}

		if ctx.message.channel.id not in feeds_json[ctx.message.server.id]["feeds"]:
			feeds_json[ctx.message.server.id]["feeds"][ctx.message.channel.id] = []
			feeds_json[ctx.message.server.id]["feeds"][ctx.message.channel.id].append(rss_url)
			pingbot.Config("./user/cogs/feeds/feeds.json").write_json(feeds_json)
			await text(pingbot.get_message("feed_added"), emoji="success")
			return

		if rss_url in feeds_json[ctx.message.server.id]["feeds"][ctx.message.channel.id]:
			await text(pingbot.get_message("feed_already_added"), emoji="failure")
			return
		else:
			feeds_json[ctx.message.server.id]["feeds"][ctx.message.channel.id].append(rss_url)
			await text(pingbot.get_message("feed_added"), emoji="success")

		pingbot.Config("./user/cogs/feeds/feeds.json").write_json(feeds_json)

	@commands.command(name="rem_feed", aliases=["rem-feed"], pass_context=True, no_pm=True)
	@pingbot.permissions.has_permissions(manage_server=True)
	async def _remove_feed_link(self, ctx, rss_url : str):
		"""
		🗣 Removes an RSS link from the feeds list.

		--------------------
		  USAGE: rem_feed <rss url>
		EXAMPLE: rem_feed http://myanimelist.net/rss/news.xml
		--------------------
		"""
		feeds_json = pingbot.Config('./user/cogs/feeds/feeds.json').load_json()
		if ctx.message.server.id not in feeds_json:
			feeds_json[ctx.message.server.id] = {}
			feeds_json[ctx.message.server.id]["feeds"] = {}

		if ctx.message.channel.id not in feeds_json[ctx.message.server.id]["feeds"]:
			pingbot.Config("./user/cogs/feeds/feeds.json").write_json(feeds_json)
			await text(pingbot.get_message("feed_remove_not_found"), emoji="failure")
			return

		if rss_url in self.last_feed:
			self.last_feed.pop(rss_url)

		if rss_url in feeds_json[ctx.message.server.id]["feeds"][ctx.message.channel.id]:
			feeds_json[ctx.message.server.id]["feeds"][ctx.message.channel.id].remove(rss_url)
			await text(pingbot.get_message("feed_remove_success"), emoji="success")
		else:
			await text(pingbot.get_message("feed_remove_not_found"), emoji="failure")
			return

		pingbot.Config("./user/cogs/feeds/feeds.json").write_json(feeds_json)

	@commands.command(name="feeds", aliases=["show-feeds", "show_feeds"], pass_context=True, no_pm=True)
	@pingbot.permissions.has_permissions(send_messages=True)
	async def list_feeds(self, ctx):
		"""
		🗣 Returns a list of feeds that have been assigned to the channel.

		--------------------
		  USAGE: feeds
		EXAMPLE: feeds
		--------------------
		"""
		feeds_json = pingbot.Config('./user/cogs/feeds/feeds.json').load_json()
		if ctx.message.server.id not in feeds_json:
			await text(pingbot.get_message("no_feeds_assigned_server"), emoji="failure")
			return

		if ctx.message.channel.id not in feeds_json[ctx.message.server.id]["feeds"]:
			await text(pingbot.get_message("no_feeds_assigned_channel"), emoji="failure")
			return
		elif len(feeds_json[ctx.message.server.id]["feeds"][ctx.message.channel.id]) == 0:
			await text(pingbot.get_message("no_feeds_assigned_channel"), emoji="failure")
			return

		await text("**These feeds have been assigned:** {}".format(', '.join(feeds_json[ctx.message.server.id]["feeds"][ctx.message.channel.id])), no_bold=True, emoji="success")

	async def auto_feed(self):
		"""
		Outputs RSS feed.
		"""
		await self.bot.wait_until_ready()
		while not self.bot.is_closed:
			try:
				feeds_json = pingbot.Config('./user/cogs/feeds/feeds.json').load_json()
				#nested for loops seem pretty ugly, but ill use this method for now
				for server in feeds_json:
					for channel in feeds_json[server]["feeds"]:
						for rss_url in feeds_json[server]["feeds"][channel]:
							d = feedparser.parse(rss_url)
							if 'bozo_exception' in d: #if rss url is invalid
								await self.bot.send_message(discord.Object(channel), "Error while retrieving data from URL: '{}'".format(rss_url))
							else:
								entry_link = d["entries"][0]["link"]
								entry_summary = d["entries"][0]["summary"]
								entry_title = d["entries"][0]["title_detail"]["value"]
								entry_website_title = d["feed"]["title"]

								#if len(entry_summary) > 200 and "<" in entry_summary:
								#exterminate the ugly html tags
								entry_summary = entry_summary.strip("<p>")
								entry_summary = entry_summary.strip("</p>")
								entry_summary = entry_summary.strip("<em>")
								entry_summary = entry_summary.strip("</em>")
								entry_summary = entry_summary.strip("<span style=")
								entry_summary = entry_summary.strip('"font-weight: 400;">')
								entry_summary = entry_summary.replace("<strong>", "**")
								entry_summary = entry_summary.replace("</strong>", "**")
								#not the most efficient system but it works for now
								if len(entry_summary) > 200:
									entry_summary = entry_summary[:210] + "..."

								if "=" in entry_summary or "<" in entry_summary or ">" in entry_summary: #if a gross html tag managed to rear its head in, then dont show the summary
									fmt = "**{} ({})** - {}".format(entry_title, entry_website_title, entry_link)
								else:
									fmt = "**{} ({})**:\n{} - {}".format(entry_title, entry_website_title, entry_summary, entry_link)
								
								if rss_url not in self.last_feed:
									self.last_feed[rss_url] = entry_title
									await text(fmt, no_mention=True, channel=channel, emoji="new_feed", no_bold=True)
								elif self.last_feed[rss_url] != entry_title:
									self.last_feed[rss_url] = entry_title
									await text(fmt, no_mention=True, channel=channel, emoji="new_feed", no_bold=True)
			except Exception as e:
				pingbot.Utils().cprint("red", "LOOP_ERROR@feeds! {}".format(pingbot.errors.get_traceback()))
							
			await asyncio.sleep(200) #since im too lazy to make an async version of feedparser, trying to parse an rss feed will usually pause the bot for a little bit, so this shouldn't be too frequent

	async def feed_server_remove(self, server):
		"""
		on_server_remove listener
		"""
		feeds_json = pingbot.Config('./user/cogs/feeds/feeds.json').load_json()
		if server.id in feeds_json:
			feeds_json.pop(server.id)
			pingbot.Config("./user/cogs/feeds/feeds.json").write_json(feeds_json)

	async def feed_channel_remove(self, channel):
		"""
		on_channel_delete listener
		"""
		feeds_json = pingbot.Config('./user/cogs/feeds/feeds.json').load_json()
		if channel.server.id in feeds_json:
			if channel.id in feeds_json[channel.server.id]["feeds"]:
				feeds_json[channel.server.id]["feeds"].pop(channel.id)
				pingbot.Config("./user/cogs/feeds/feeds.json").write_json(feeds_json)

def setup(bot):
	bot.add_listener(Feeds(bot).feed_server_remove, "on_server_remove")
	bot.add_listener(Feeds(bot).feed_channel_remove, "on_channel_delete")
	bot.add_cog(Feeds(bot))
