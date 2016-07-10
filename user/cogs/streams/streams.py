from core import pingbot
from core.pingbot.messages import text
from discord.ext import commands
import discord
import asyncio

class Streams:
	def __init__(self, bot):
		self.bot = bot

		self.twitch_stream_alerts = {}

	@commands.group(pass_context=True)
	@pingbot.permissions.has_permissions()
	async def twitch(self, ctx):
		"""
		📺 Twitch stream management commands and channel viewer.

		--------------------
		  USAGE: twitch <subcommand or username>
		EXAMPLE: twitch add_alert / twitch maxpiewalker
		--------------------
		"""
		if ctx.invoked_subcommand is None:
			if ctx.subcommand_passed is None:
				await text(pingbot.get_message("twitch_no_subcommand_or_username"), emoji="failure")
				return
			username = ctx.subcommand_passed

			if not await self.stream_exists('twitch', username):
				await text(pingbot.get_message("twitch_unknown_user"), emoji="failure")
				return

			twitch_channel = await self.stream_return_channel('twitch', username)
			channel_url = "https://www.twitch.tv/{}".format(username)
			is_online = await self.stream_is_on('twitch', username)

			if twitch_channel["game"]:
				game = twitch_channel["game"]
			else:
				game = "Nothing."

			if twitch_channel["product_path"]:
				products_url = "https://www.twitch.tv/products/{}/ticket".format(username)
			else:
				products_url = "No products."

			fmt = """```xl
    Name: {} ({})
 Playing: {}
Products: {}
	Live: {}
		  {}```""".format(twitch_channel["display_name"], twitch_channel["name"], game, products_url, is_online, channel_url)
			await text(fmt)

	@twitch.command(pass_context=True, name="add_alert", aliases=["add_stream"])
	async def twitch_add_stream_alert(self, ctx, username : str):
		"""
		📺 Receive notifications when a Twitch.tv channel goes live.

		--------------------
		  USAGE: twitch add_alert <username>
		EXAMPLE: twitch add_alert maxpiewalker
		--------------------
		"""

		author = ctx.message.author
		server = ctx.message.server
		channel = ctx.message.channel

		if ctx.message.channel.is_private:
			if not await self.stream_exists('twitch', username):
				await text(pingbot.get_message("twitch_unknown_user"), emoji="failure")
				return
			twitch_json = pingbot.Config("./user/cogs/streams/twitch_channels.json").load_json()
			section_name = author.id + "_member"
			if section_name not in twitch_json:
				twitch_json[section_name] = {}
				twitch_json[section_name]["streams"] = []
				twitch_json[section_name]["streams"].append(username)
			elif username not in twitch_json[section_name]["streams"]:
				twitch_json[section_name]["streams"].append(username)

			pingbot.Config("./user/cogs/streams/twitch_channels.json").write_json(twitch_json)

			await text(pingbot.get_message("twitch_alert_add_success_pm"), channel=author, no_mention=True, emoji="success")
		else:
			twitch_json = pingbot.Config("./user/cogs/streams/twitch_channels.json").load_json()

			if not pingbot.permissions._has_permissions(ctx, manage_channels=True, manage_roles=True, manage_server=True):
				await text(pingbot.get_message("no_permission"), emoji="failure")
				return

			if not await self.stream_exists('twitch', username):
				await text(pingbot.get_message("twitch_unknown_user"), emoji="failure")
				return

			if server.id not in twitch_json:
				twitch_json[server.id] = {}
				twitch_json[server.id]["streams"] = {}
				twitch_json[server.id]["streams"][channel.id] = []
				twitch_json[server.id]["streams"][channel.id].append(username)
			elif channel.id not in twitch_json[server.id]["streams"]:
				twitch_json[server.id]["streams"][channel.id] = []
				twitch_json[server.id]["streams"][channel.id].append(username)
			elif username not in twitch_json[server.id]["streams"][channel.id]:
				twitch_json[server.id]["streams"][channel.id].append(username)
			elif username in twitch_json[server.id]["streams"][channel.id]:
				await text(pingbot.get_message("twitch_alert_exists"), emoji="failure")
				return

			pingbot.Config("./user/cogs/streams/twitch_channels.json").write_json(twitch_json)

			await text(pingbot.get_message("twitch_alert_add_success"), emoji="success")

	@twitch.command(pass_context=True, name="del_alert", aliases=["rem_alert, del_stream, rem_stream"])
	async def twitch_remove_stream_alert(self, ctx, username : str):
		"""
		📺 Stop receiving notifications about a twitch channel.

		--------------------
		  USAGE: twitch del_alert <username>
		EXAMPLE: twitch del_alert maxpiewalker
		--------------------
		"""
		author = ctx.message.author
		server = ctx.message.server
		channel = ctx.message.channel

		twitch_json = pingbot.Config("./user/cogs/streams/twitch_channels.json").load_json()

		if channel.is_private:
			section_name = author.id + "_member"
			if section_name not in twitch_json:
				await text(pingbot.get_message("twitch_no_alerts_pm"), emoji="failure")
				return

			if username not in twitch_json[section_name]["streams"]:
				await text(pingbot.get_message("twitch_unknown_user"), emoji="failure")
				return

			twitch_json[section_name]["streams"].remove(username)
			pingbot.Config("./user/cogs/streams/twitch_channels.json").write_json(twitch_json)
			await text(pingbot.get_message("twitch_alert_remove_success_pm"), emoji="success")
		else:
			if server.id not in twitch_json:
				await text(pingbot.get_message("twitch_no_alerts"), emoji="failure")
				return

			if channel.id not in twitch_json[server.id]["streams"]:
				await text(pingbot.get_message("twitch_no_alerts"), emoji="failure")
				return

			if username not in twitch_json[server.id]["streams"][channel.id]:
				await text(pingbot.get_message("twitch_unknown_user"), emoji="failure")
				return

			twitch_json[server.id]["streams"][channel.id].remove(username)
			pingbot.Config("./user/cogs/streams/twitch_channels.json").write_json(twitch_json)
			await text(pingbot.get_message("twitch_alert_remove_success"), emoji="success")

	@twitch.command(pass_context=True, name="streams")
	async def twitch_list_streams(self, ctx):
		"""
		📺 Lists all twitch channel notifications that have been set in the channel.

		--------------------
		  USAGE: twitch streams
		EXAMPLE: twitch streams
		----
		"""

		author = ctx.message.author
		server = ctx.message.server
		channel = ctx.message.channel

		twitch_json = pingbot.Config("./user/cogs/streams/twitch_channels.json").load_json()

		if channel.is_private:
			section_name = author.id + "_member"
			if section_name not in twitch_json:
				await text(pingbot.get_message("twitch_no_alerts_pm"), no_mention=True, channel=author, emoji="failure")
				return

			if len(twitch_json[section_name]["streams"]) == 0:
				await text(pingbot.get_message("twitch_no_alerts_pm"), no_mention=True, channel=author, emoji="failure")
				return

			await text(pingbot.get_message("twitch_list_streams").format(', '.join(twitch_json[section_name]["streams"])), no_mention=True, channel=author, emoji="success", no_bold=True)
		else:
			if server.id not in twitch_json:
				await text(pingbot.get_message("twitch_no_alerts"), emoji="failure")
				return

			if channel.id not in twitch_json[server.id]["streams"]:
				await text(pingbot.get_message("twitch_no_alerts"), emoji="failure")
				return

			if len(twitch_json[server.id]["streams"][channel.id]) == 0:
				await text(pingbot.get_message("twitch_no_alerts"), emoji="failure")
				return

			await text(pingbot.get_message("twitch_list_streams").format(', '.join(twitch_json[server.id]["streams"][channel.id])), no_bold=True, emoji="success")

	@commands.command()
	async def show_raw_stream(self):
		await self.bot.say(self.twitch_stream_alerts)

	async def stream_return_channel(self, stream_type, username):
		if stream_type.lower() == "twitch":
			url = "https://api.twitch.tv/channels/{}".format(username)
			resp = await pingbot.WT().async_json_content(url)
			return resp

	async def stream_is_on(self, stream_type, username):
		if stream_type.lower() == "twitch":
			url = "https://api.twitch.tv/kraken/streams?channel={}".format(username)
			resp = await pingbot.WT().async_json_content(url)
			return len(resp["streams"]) > 0

	async def stream_exists(self, stream_type, username):
		if stream_type.lower() == "twitch":
			url = "https://api.twitch.tv/channels/{}".format(username)
			resp = await pingbot.WT().async_json_content(url)
			return not "error" in resp

	async def stream_check(self):
		"""
		The stream check loop.
		"""
		await self.bot.wait_until_ready()
		while True:
			try:
				twitch_json = pingbot.Config("./user/cogs/streams/twitch_channels.json").load_json()
				fmt = "**{} is now live!**\n**Playing {}!**\n{}"

				for server in twitch_json:
					if server.endswith("_member"):
						channel = discord.Object(server.strip("_member"))
						for stream in twitch_json[server]["streams"]:
							twitch_channel = "https://www.twitch.tv/{}".format(stream)
							game = await self.stream_return_channel('twitch', stream)
							game = game["game"]

							if await self.stream_is_on('twitch', stream):

								if server not in self.twitch_stream_alerts:
									self.twitch_stream_alerts[server] = {}
									self.twitch_stream_alerts[server][stream] = True

									await text(fmt.format(stream, game, twitch_channel), channel=channel, no_mention=True, no_bold=True)
								elif stream not in self.twitch_stream_alerts[server]:
									self.twitch_stream_alerts[server][stream] = True

									await text(fmt.format(stream, game, twitch_channel), channel=channel, no_mention=True, no_bold=True)
								elif self.twitch_stream_alerts[server][stream] != True:
									self.twitch_stream_alerts[server][stream] = True

									await text(fmt.format(stream, game, twitch_channel), channel=channel, no_mention=True, no_bold=True)
							else:
								if server not in self.twitch_stream_alerts:
									self.twitch_stream_alerts[server] = {}
									self.twitch_stream_alerts[server][stream] = False
								else:
									self.twitch_stream_alerts[server][stream] = False
					else:
						for channel in twitch_json[server]["streams"]:
							for stream in twitch_json[server]["streams"][channel]:
								twitch_channel = "https://www.twitch.tv/{}".format(stream)
								game = await self.stream_return_channel('twitch', stream)
								game = game["game"]

								if await self.stream_is_on('twitch', stream):
									if server not in self.twitch_stream_alerts:
										self.twitch_stream_alerts[server] = {}
										self.twitch_stream_alerts[server][stream] = True
										await text(fmt.format(stream, game, twitch_channel), channel=discord.Object(channel), no_mention=True, no_bold=True)
									elif stream not in self.twitch_stream_alerts[server]:
										self.twitch_stream_alerts[server][stream] = True
										await text(fmt.format(stream, game, twitch_channel), channel=discord.Object(channel), no_mention=True, no_bold=True)
									elif self.twitch_stream_alerts[server][stream] != True:
										self.twitch_stream_alerts[server][stream] = True
										await text(fmt.format(stream, game, twitch_channel), channel=discord.Object(channel), no_mention=True, no_bold=True)
								else:
									if server not in self.twitch_stream_alerts:
										self.twitch_stream_alerts[server] = {}
										self.twitch_stream_alerts[server][stream] = False
									else:
										self.twitch_stream_alerts[server][stream] = False
			except Exception as e:
				pingbot.Utils().cprint("red", "LOOP_ERROR@streams! {}".format(pingbot.errors.get_traceback()))

			await asyncio.sleep(30)

	async def stream_server_remove(self, server):
		"""
		on_server_remove listener.
		"""
		twitch_json = pingbot.Config("./user/cogs/streams/twitch_channels.json").load_json()
		if server.id in twitch_json:
			twitch_json.pop(server.id)

			pingbot.Config("./user/cogs/streams/twitch_channels.json").write_json(twitch_json)

	async def stream_channel_remove(self, channel):
		"""
		on_channel_delete listener.
		"""
		twitch_json = pingbot.Config("./user/cogs/streams/twitch_channels.json").load_json()
		if channel.server.id in twitch_json:
			if channel.id in twitch_json[channel.server.id]["streams"]:
				twitch_json[channel.server.id]["streams"].pop(channel.id)

				pingbot.Config("./user/cogs/streams/twitch_channels.json").write_json(twitch_json)

def setup(bot):
	bot.add_listener(Streams(bot).stream_server_remove, "on_server_remove")
	bot.add_listener(Streams(bot).stream_channel_remove, "on_channel_delete")
	bot.add_cog(Streams(bot))