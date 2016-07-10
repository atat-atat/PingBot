from core import pingbot
from core.pingbot.messages import text, whisper
from discord.ext import commands
import __main__
import sys
import os
import json
import asyncio
import discord
import user.cogs.nsfw.nsfw
import importlib
import random
import datetime

config = pingbot.Config().load_json("./user/config/bot.json")
emoji = pingbot.Config().load_json("./core/data/emoji.json")
sysmsg = pingbot.Config().load_json("./core/data/messages.json")
no_perm = sysmsg['no_permission']

class System:
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True, name="close", aliases=["exit", "logout"], hidden=True)
	async def _close(self, ctx):
		"""
		⭐ Closes the bot.

		--------------------
		  USAGE: close
		EXAMPLE: close
		--------------------
		"""
		await pingbot.Utils(self.bot, ctx.message).text(":wave:", no_mention=True)
		self.bot.logout()
		sys.exit()

	@commands.command(name="reload-system", aliases=["reload_system"], pass_context=True, hidden=True)
	async def reload_sys_cog(self, ctx):
		"""
		⭐ Reloads the system cog.

		--------------------
		  USAGE: reload-system
		EXAMPLE: reload-system
		--------------------
		"""
		if not pingbot.permissions.can_mm(ctx.message.author) and not pingbot.permissions.is_serv_owner(ctx.message.author, ctx) and not pingbot.permissions.is_bot_owner(ctx.message.author):
			await text(no_perm, emoji=emoji["failure"])
			return
		try:
			self.bot.unload_extension('core.data.system')
			self.bot.load_extension('core.data.system')
		except Exception as e:
			await text("`{}`: `{}`".format(type(e).__name__, str(e)), emoji=emoji["failure"])
			return
		await text("Successfully reloaded system cog.", emoji=pingbot.get_emoji("robot"))

	@commands.command(pass_context=True, name="setup-server", aliases=["setup_server"], hidden=True, no_pm=True)
	async def _setup_server(self, ctx):
		pingbot.Utils().setup_server_section(ctx.message.server)
		await pingbot.Utils(self.bot, ctx.message).text("Successfully set the server up.", emoji=emoji["success"])

	@commands.command(pass_context=True, name="server-checkup", aliases=["server_checkup"], hidden=True, no_pm=True)
	async def _checkup_server(self, ctx):
		pingbot.Utils().server_checkup(ctx.message.server)
		await pingbot.Utils(self.bot, ctx.message).text("Successfully completed server checkup.", emoji=emoji["success"])

	@commands.command(pass_context=True, name="eval", hidden=True)
	async def _eval(self, ctx, *, code : str):
		"""
		⭐ Evaluates a line of code.

		--------------------
		  USAGE: eval <line of code>
		EXAMPLE: eval 1 + 1
		--------------------
		"""
		if not pingbot.permissions.can_mm(ctx.message.author) and not pingbot.permissions.is_serv_owner(ctx.message.author, ctx) and not pingbot.permissions.is_bot_owner(ctx.message.author):
			await pingbot.Utils(self.bot, ctx.message).text(no_perm, emoji=emoji["failure"])
			return
		try:
			result = eval(code)
			result = "```py\n{}\n```".format(result)
		except:
			result = "```py\n{}\n```".format(pingbot.errors.get_traceback())
		await pingbot.Utils(self.bot, ctx.message).text(result, no_bold=True)

	@_eval.error
	async def eval_error(self, error, ctx):
		await pingbot.Utils(self.bot, ctx.message).text("""ERROR: ```xl
{}
```""".format(pingbot.Errors().get_traceback(*sys.exc_info())))

	@commands.command(pass_context=True)
	async def join(self, ctx, invite : discord.Invite):
		"""
		⭐ Joins a server.

		--------------------
		  USAGE: join <invite link>
		EXAMPLE: join http://discord.gg/abcde
		--------------------
		"""
		if self.bot.user.bot:
			try:
				await pingbot.Utils(self.bot, ctx.message).text("I am unable to join invite links, please use the link {} to invite me to your server.".format(discord.utils.oauth_url(self.bot.client_id, perms)), emoji=emoji['failure'])
			except IndexError:
				await pingbot.Utils(self.bot, ctx.message).text("I am unable to join invite links.", emoji=emoji['failure'])
		else:
			await self.bot.accept_invite(invite)
			await pingbot.Utils(self.bot, ctx.message).text("Successfully joined server!", emoji=emoji['success'])

	@join.error
	async def join_error(self, error, ctx):
		if self.bot.user.bot:
			try:
				await pingbot.Utils(self.bot, ctx.message).text("I am unable to join invite links, please use the link https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=54 to invite me to your server.".format(config['client_id']), emoji=emoji['failure'])
			except IndexError:
				await pingbot.Utils(self.bot, ctx.message).text("I am unable to join invite links.", emoji=emoji['failure'])
			return
		if isinstance(error, discord.errors.HTTPException):
			await pingbot.Utils(self.bot, ctx.message).text("Failed to accept the invite.", emoji=emoji["failure"])

	@commands.command(pass_context=True)
	async def leave(self, ctx):
		"""
		⭐ Leaves the current server.

		--------------------
		  USAGE: leave
		EXAMPLE: leave
		--------------------
		"""
		if not pingbot.permissions.can_mm(ctx.message.author) and not pingbot.permissions.is_serv_owner(ctx.message.author, ctx) and not pingbot.permissions.is_bot_owner(ctx.message.author):
			await pingbot.Utils(self.bot, ctx.message).text(no_perm, emoji=emoji["failure"])
			return

		await pingbot.Utils(self.bot, ctx.message).text("Good night.", emoji=":wave:")
		await self.bot.leave_server(ctx.message.server)

	@commands.group(name="cogs", aliases=["cog"], pass_context=True)
	async def _cog(self, ctx):
		"""
		⭐ Shows the cogs that have been loaded.

		--------------------
		  USAGE: cogs
		EXAMPLE: cogs
		--------------------
		"""
		if ctx.invoked_subcommand == None:
			if not pingbot.permissions.can_mm(ctx.message.author) and not pingbot.permissions.is_serv_owner(ctx.message.author, ctx) and not pingbot.permissions.is_bot_owner(ctx.message.author):
				await pingbot.Utils(self.bot, ctx.message).text(no_perm, emoji=emoji["failure"])
				return

			found_cogs = []
			for file in os.listdir('./user/cogs'): #cycle through each file in the /cogs/ directory.
				if os.path.isfile('./user/cogs/{0}/{0}.py'.format(file)):
					if os.path.isfile('./user/cogs/{0}/{0}_info.json'.format(file)):
						cog_info = pingbot.Config('./user/cogs/{0}/{0}_info.json'.format(file)).load_json()
						try:
							cog_version = cog_info["version"]
						except KeyError:
							cog_version = "Unknown"
						try:
							cog_name = cog_info["name"]
						except KeyError:
							cog_name = "Unknown"
						try:
							cog_author = cog_info["author"]
						except KeyError:
							cog_author = "Unknown"
						try:
							cog_description = cog_info["description"]
						except KeyError:
							cog_description = "Unknown"
					else:
						cog_version = "Unknown"
						cog_name = "Unknown"
						cog_author = "Unknown"
						cog_description = "Unknown"

					found_cogs.append("- {} : {} ({}/{})".format(cog_name, cog_description, cog_author, cog_version))

			if len(found_cogs) <= 0:
				await pingbot.Utils(self.bot, ctx.message).text("No cogs were found.", emoji=emoji["failure"])
				return

			await pingbot.Utils(self.bot, ctx.message).text("I found {} cogs from the directory...\n{}".format(len(found_cogs), '\n'.join(found_cogs)), emoji=emoji["channel_update"])

	@_cog.command(name="load", pass_context=True)
	async def _cog_load(self, ctx, cog : str):
		"""
		⭐ Loads a cog.

		--------------------
		  USAGE: cogs load <cog>
		EXAMPLE: cogs load fun
		--------------------
		"""
		if not pingbot.permissions.can_mm(ctx.message.author) and not pingbot.permissions.is_serv_owner(ctx.message.author, ctx) and not pingbot.permissions.is_bot_owner(ctx.message.author):
				await pingbot.Utils(self.bot, ctx.message).text(no_perm, emoji=emoji["failure"])
				return

		if '.' in cog:
			load_cog = cog
		elif '/' in cog:
			load_cog = cog.replace('/', '.')
		else:
		#if '.' not in cog:
			if not os.path.isfile('./user/cogs/{0}/{0}.py'.format(cog)):
				await pingbot.Utils(self.bot, ctx.message).text("Sorry, I was unable to find that cog!\nIf you are certain that it exists, try providing the full directory.", emoji=emoji["failure"])
				return
			else:
				load_cog = 'user.cogs.{0}.{0}'.format(cog)

		if load_cog in self.bot.extensions:
			await pingbot.Utils(self.bot, ctx.message).text("I have already loaded that cog!\nUse `reload` to reload a/all cogs.", emoji=emoji["failure"])
			return

		try:
			self.bot.load_extension(load_cog)
		except:
			await pingbot.Utils(self.bot, ctx.message).text("""```xl
[UNEXPECTED ERROR]: {}
```""".format(pingbot.Errors().get_traceback(*sys.exc_info())))
			pingbot.Errors().set_new_error("""```xl
		{}```""".format(pingbot.Errors().get_traceback(*sys.exc_info())))
			return

		await pingbot.Utils(self.bot, ctx.message).text("Successfully loaded {}!".format(load_cog), emoji=emoji["success"])

	@_cog_load.error
	async def cog_load_error(self, error, ctx):
		if isinstance(error, commands.MissingRequiredArgument):
			await pingbot.Utils(self.bot, ctx.message).text("You must provide the cog!", emoji=emoji["failure"])

	@_cog.command(name="unload", pass_context=True)
	async def _cog_unload(self, ctx, cog : str):
		"""
		⭐ Unloads a cog.

		--------------------
		  USAGE: cogs unload <cog>
		EXAMPLE: cogs unload fun
		--------------------
		"""
		if not pingbot.permissions.can_mm(ctx.message.author) and not pingbot.permissions.is_serv_owner(ctx.message.author, ctx) and not pingbot.permissions.is_bot_owner(ctx.message.author):
				await pingbot.Utils(self.bot, ctx.message).text(no_perm, emoji=emoji["failure"])
				return

		if '.' in cog:
			load_cog = cog
		elif '/' in cog:
			load_cog = cog.replace('/', '.')
		else:
			if not os.path.isfile('./user/cogs/{0}/{0}.py'.format(cog)):
				await pingbot.Utils(self.bot, ctx.message).text("Sorry, I was unable to find that cog!\nIf you are certain that it exists, try providing the full directory.", emoji=emoji["failure"])
				return
			else:
				load_cog = "user.cogs.{0}.{0}".format(cog)

		if load_cog not in self.bot.extensions:
			await pingbot.Utils(self.bot, ctx.message).text("I have never loaded that cog before.\nUse `cog load` to load a cog.", emoji=emoji["failure"])
			return

		try:
			self.bot.unload_extension(load_cog)
		except:
			await pingbot.Utils(self.bot, ctx.message).text("""```xl
[UNEXPECTED ERROR]: {}
```""".format(pingbot.Errors().get_traceback(*sys.exc_info())))
			pingbot.Errors().set_new_error("""```xl
		{}```""".format(pingbot.Errors().get_traceback(*sys.exc_info())))
			return

		await pingbot.Utils(self.bot, ctx.message).text("Successfully unloaded {}!".format(load_cog), emoji=emoji["success"])

	@commands.command(name="info")
	async def bot_info(self):
		"""
		⭐ Returns information about the bot.

		--------------------
		  USAGE: info
		EXAMPLE: info
		--------------------
		"""
		perms = discord.Permissions.none()
		perms.read_messages = True
		perms.send_messages = True
		perms.manage_roles = True
		perms.ban_members = True
		perms.kick_members = True
		perms.manage_messages = True
		perms.embed_links = True
		perms.read_message_history = True
		perms.attach_files = True
		fmt = """```xl
{}

Library: discord.py -- https://github.com/Rapptz/discord.py
Version: {}

Name: {}
ID: {}
Invite: {}
Uptime: {}

Cogs: {}
Commands: {}```""".format(self.bot.description, "Test", self.bot.user.name, self.bot.user.id, discord.utils.oauth_url(self.bot.client_id, perms), self.bot_uptime(), len(self.bot.extensions.keys()), len(self.bot.commands.keys()))
		await text(fmt)

	@commands.group(name="bot", pass_context=True)
	async def _bot(self, ctx):
		"""
		⭐ Bot management command.

		--------------------
		  USAGE: bot <optional: subcommand>
		EXAMPLE: bot
		--------------------
		"""
		
		if ctx.invoked_subcommand is None:
			perms = discord.Permissions.none()
			perms.read_messages = True
			perms.send_messages = True
			perms.manage_roles = True
			perms.ban_members = True
			perms.kick_members = True
			perms.manage_messages = True
			perms.embed_links = True
			perms.read_message_history = True
			perms.attach_files = True
			fmt = """```xl
{}

Library: discord.py -- https://github.com/Rapptz/discord.py
Version: {}

Name: {}
ID: {}
Invite: {}
Uptime: {}

Cogs: {}
Commands: {}```""".format(self.bot.description, "Test", self.bot.user.name, self.bot.user.id, discord.utils.oauth_url(self.bot.client_id, perms), self.bot_uptime(), len(self.bot.extensions.keys()), len(self.bot.commands.keys()))
			await text(fmt)

	@_bot.command(name="name", aliases=["change_name", "change-name"], pass_context=True)
	async def bot_name(self, ctx, *, name: str):
		"""
		⭐ Change the bot's username.

		--------------------
		  USAGE: bot name <username>
		EXAMPLE: bot name Bot2
		--------------------
		"""
		if not pingbot.permissions.is_bot_owner(ctx.message.author):
			await pingbot.Utils(self.bot, ctx.message).text(no_perm, emoji=pingbot.get_emoji("failure"))
			return

		if len(name) <= 2:
			await text("That name is too short. Names must be between 2 to 32 characters long.", emoji=pingbot.get_emoji("failure"))
			return
		elif len(name) > 32:
			await text("That name is too long. Names must be between 2 to 32 characters long.", emoji=pingbot.get_emoji("failure"))
			return

		await self.bot.edit_profile(username=name)
		config = pingbot.Config("./user/config/bot.json").load_json()
		config["username"] = name
		pingbot.Config("./user/config/bot.json").write_json(config)
		await text("Successfully changed my name to `{}`!".format(name), emoji=pingbot.get_emoji("member_update_game"))

	@_bot.command(name="game", aliases=["change_game", "change-game"], pass_context=True)
	async def bot_game(self, ctx, *, name : str):
		"""
		⭐ Change the bot's game name.

		--------------------
		  USAGE: bot game <name>
		EXAMPLE: bot game Hearthstone
		--------------------
		"""
		if not pingbot.permissions.is_bot_owner(ctx.message.author):
			await text(no_perm, emoji=pingbot.get_emoji("failure"))
			return

		await self.bot.change_status(game=discord.Game(name=name))
		await text("Successfully changed my currently playing game to `{}`!".format(name), emoji=pingbot.get_emoji("success"))

	@_bot.command(name="append_game", aliases=["add_game"], pass_context=True)
	async def bot_append_game(self, ctx, *, name : str):
		"""
		⭐ Adds a game to the bot's list of random currently-playing games.
		--------------------
		  USAGE: bot append_game <name>
		EXAMPLE: bot append_game Hearthstone
		--------------------
		"""
		if not pingbot.permissions.is_bot_owner(ctx.message.author):
			await text(no_perm, emoji=pingbot.get_emoji("failure"))
			return

		bot_json = pingbot.Config("./user/config/bot.json").load_json()
		if name in bot_json["games"]:
			await text("That game has already been added!\nUse `remove_game` to remove a game.", emoji=pingbot.get_emoji("failure"))
			return
		bot_json["games"].append(name)
		pingbot.Config("./user/config/bot.json").write_json(bot_json)
		await text("Successfully added game: `{}`".format(name), emoji=pingbot.get_emoji("member_update_game"))

	@_bot.command(name="remove_game", aliases=["rem_game", "del_game", "delete_game"], pass_context=True)
	async def bot_remove_game(self, ctx, *, name : str):
		"""
		⭐ Removes a game from the bot's list of random currently-playing games.

		--------------------
		  USAGE: bot remove_game <name>
		EXAMPLE: bot remove_game Hearthstone
		--------------------
		"""
		if not pingbot.permissions.is_bot_owner(ctx.message.author):
			await text(no_perm, emoji=pingbot.get_emoji("failure"))
			return

		bot_json = pingbot.Config("./user/config/bot.json").load_json()
		if name not in bot_json["games"]:
			await text("That game has never been added to the list.\nUse `append_game` to add a game.", emoji=pingbot.get_emoji("failure"))
			return
		bot_json["games"].remove(name)
		pingbot.Config("./user/config/bot.json").write_json(bot_json)
		await text("Successfully removed game.".format(name), emoji=pingbot.get_emoji("member_update_game"))

	@_bot.command(name="random_game", pass_context=True)
	async def bot_random_game(self, ctx):
		"""
		⭐ Changes the currently-playing game to a random game from the list.

		--------------------
		  USAGE: bot random_game
		EXAMPLE: bot random_game
		--------------------
		"""
		if not pingbot.permissions.is_bot_owner(ctx.message.author):
			await text(no_perm, emoji=pingbot.get_emoji("failure"))
			return
		bot_json = pingbot.Config("./user/config/bot.json").load_json()
		game = random.choice(bot_json["games"])
		await self.bot.change_status(game=discord.Game(name=game))
		await text("I am now playing, `{}`".format(game), emoji=pingbot.get_emoji("member_update_game"))

	@_bot.command(name="avatar", aliases=["change_avatar"], pass_context=True)
	async def bot_avatar(self, ctx, url : str):
		"""
		⭐ Changes the bot's avatar.

		--------------------
		  USAGE: bot avatar <url>
		EXAMPLE: bot avatar http://i.imgur.com/I2ncbqu.jpg
		--------------------
		"""
		if not pingbot.permissions.is_bot_owner(ctx.message.author):
			await text(no_perm, emoji=pingbot.get_emoji("failure"))
			return
		if url.lower() == "none":
			avatar = None
		else:
			try:
				avatar = await pingbot.WT().async_url_content(url)
			except ValueError:
				await text("That url is invalid.", emoji=pingbot.get_emoji("failure"))
				return
		try:
			if self.bot.user.bot:
				await self.bot.edit_profile(avatar=avatar)
			else:
				await self.bot.edit_profile(password=pingbot.Config("./user/config/bot.json").load_json()["password"], avatar=avatar)
		except discord.errors.InvalidArgument:
			await text("Unsupported image type.", emoji=pingbot.get_emoji("failure"))
			return

		await text("Successfully changed avatar.", emoji=pingbot.get_emoji("member_update_avatar"))

	@commands.command(name="uptime")
	async def uptime_get(self):
		await text(self.bot_uptime())

	def bot_uptime(self):
		now = datetime.datetime.utcnow()
		delta = now - self.bot.uptime
		hours, remainder = divmod(int(delta.total_seconds()), 3600)
		minutes, seconds = divmod(remainder, 60)
		days, hours = divmod(hours, 24)
		if days:
			fmt = '{d} days, {h} hours, {m} minutes, and {s} seconds'
		else:
			fmt = '{h} hours, {m} minutes, and {s} seconds'

		return fmt.format(d=days, h=hours, m=minutes, s=seconds)


def setup(bot):
	bot.add_cog(System(bot))
