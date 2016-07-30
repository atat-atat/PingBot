from core import pingbot
from discord.ext import commands
import datetime
import os
import sys
import json
import importlib
import discord
import time
import random

now = datetime.datetime.now()

def is_disabled():
	def predicate(ctx): #this is currently broken atm, use permissions.has_permissions() instead since it has a built-in command checker thing
		if "members" not in pingbot.Config('./user/config/server.json').load_json()[ctx.message.server.id]:
			server_json = pingbot.Config('./user/config/server.json').load_json()
			server_json[ctx.message.server.id]["members"] = {}
			pingbot.Config('./user/config/server.json').write_json(server_json)

		if ctx.command.name in pingbot.Config('./user/config/server.json').load_json()[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"] or ctx.message.author.id in pingbot.Config('./user/config/server.json').load_json()[ctx.message.server.id]["members"] and ctx.command.name in pingbot.Config('./user/config/server.json').load_json()[ctx.message.server.id]["members"][ctx.message.author.id]["disabled_commands"]:
			raise commands.DisabledCommand("Command {} is disabled!".format(ctx.command))

	return commands.check(predicate)

def is_disabled_no_user():
	def predicate(ctx): #this is also currently broken
		if ctx.command in pingbot.Config('./user/config/server.json').load_json()[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"]:
			raise commands.DisabledCommand("Command {} is disabled!".format(ctx.command))

def is_disabled_user(*args):
	def predicate(ctx): #also broken
		print(ctx.command)
		if len(list(args)) == 0:
			if Utils().cmd_is_disabled_user_no_list(ctx, ctx.command):
				raise pingbot.errors.CommandDisabledUser("Command(s) {} is disabled for user!".format(', '.join(list(ctx.command))))
		else:
			if Utils().cmd_is_disabled_user(ctx, list(args)):
				raise pingbot.errors.CommandDisabledUser("Command(s) {} is disabled for user!".format(', '.join(list(args))))

	return commands.check(predicate)


def extract_command(string):
	if string.startswith(pingbot.Config("./user/config/bot.json").load_json()["prefix"]):
		cmd = string.split()[0]
		return cmd[len(pingbot.Config("./user/config/bot.json").load_json()["prefix"]):]

def get_role_by_name(name, server):
	for role in server.roles:
		if role.name.lower() == name.lower():
			return role

	return None

class Utils:
	def __init__(self, bot = None, msg = None):
		self.bot = bot
		self.msg = msg
		self.cogs = []

	def get_color(self, color):
		"""
		Gets a color value based on a keyword.
		"""
		colors = {"bold": "\033[1m","underline": "\033[4m","black": "\033[30m","red": "\033[31m","green": "\033[32m","yellow": "\033[33m","blue": "\033[34m","magenta": "\033[35m","cyan": "\033[36m","white": "\033[37m","bblack": "\033[40m","bred": "\033[41m","bgreen": "\033[42m","byellow": "\033[43m","bblue": "\033[44m","bmagenta": "\033[45m","bcyan": "\033[46m","bwhite": "\033[47m"}
		return colors[color.lower()]

	def cprint(self, color, string, auto_encode = True):
		"""
		Outputs text to the console as color.
		"""
		color = self.get_color(color)
		white = self.get_color("white")
		if auto_encode == False:
			print("{}{}{}".format(color, string, white))
		else:
			try:
				print("{}{}{}".format(color, string, white))
			except UnicodeEncodeError:
				string = string.encode('utf-8')
				print("{}{}{}".format(color, string, white))

	def convert_moduledir(self, module, no_start=False):
		"""
		"Cleans" the module string sent by removing unecessary stuff like the .py and if it begins with ./

		This function is pretty useless.
		"""
		if no_start == True:
			if module.startswith('.'):
				output = module[1:].strip()
			else:
				output = module
		else:
			output = module
		output = output.strip('.py')
		output = output.replace("/", ".")
		return output

	def add_cog(self, *cog):
		"""
		Adds a cog name to the list.
		"""
		for i in cog:
			self.cogs.append(cog)

		return

	def remove_cog(self, *cog):
		"""
		Removes a cog name from the list.
		"""
		for i in cog:
			self.cogs.remove(i)

		return

	@property
	def cog_list(self):
		return self.cogs

	def install_cog(self, *cog):
		"""
		"Optimized" version of bot.load_extension.
		"""
		for i in cog:
			self.bot.load_extension(i)
			self.cogs.append(i)

		return

	def uninstall_cog(self, *cog):
		for i in cog:
			self.bot.unload_extension(i)
			self.cogs.remove(i)

		return

	def get_clean_cog_list(self): #returns a list of extension's files excluding the directory so it returns something like ['test', 'system'] instead of ['cogs.test', 'cogs.system']
		_cogs = self.bot.extensions.keys()
		cogs = []
		for _c in _cogs:
			_c = _c.split('.')
			_c = _c[len(_c)-1]
			cogs.append(_c)
		return cogs

	def clear(self):
		"""
		Clears the console output.
		"""
		clear = lambda: os.system('cls')
		clear()

	def check_start_arg(self, arg):
		if arg in sys.argv:
			return True
		else:
			return False

	def string_chunk(self, s, block_size):
		w = []
		n = len(s)
		for i in range(0, n, block_size):
			w.append(s[i:i+block_size])
		return w

	async def text(self, string, **kwargs):
		"""
		"Optimized" version of send_message, includes stuff like auto type notifications, emoji indicators and more.
		"""
		dont_use_ctx = kwargs.get("no_ctx", False)
		if dont_use_ctx == True:
			channel = kwargs.get("channel")
		else:
			channel = kwargs.get("channel", self.msg.channel) #set the channel
		emoji = kwargs.get("emoji", None) #set the beginning emoji
		no_type = kwargs.get("no_type", False) #set whether the bot should not show that it is typing before it sends the message
		no_mention = kwargs.get("no_mention", False) #set whether the bot should not mention the author
		no_bold = kwargs.get("no_bold", False)
		if no_type == False:
			type_chan = kwargs.get("type_chan", channel) #if no_type is set to False (by default,) then have the ability to set the typing notification destination
		else:
			type_chan = channel

		if no_mention == False:
			mention_user = kwargs.get("mention_user", self.msg.author) #if no_mention is set to False (by default,) then have the ability to set the user to mention (defaults to message author) (if you are providing a member/user object, do not add the ``mention`` property, just include the object since it automatically gets the mention property.)
			if isinstance(mention_user, str):
				mention_format = "<@{}>".format(mention_user)
			else:
				mention_format = mention_user.mention

		if no_bold == False:
			if emoji != None:
				if no_mention == False:
					if string.endswith('```'):
						#if no_mention is set to False, then mention the member/user
						fmt = "{} **{}**{}".format(emoji, string, mention_format) #dont mind this
					else:
						fmt = "{} **{}** {}".format(emoji, string, mention_format)
				else:
					fmt = "{} **{}**".format(emoji, string) #do the opposite
			else:
				if no_mention == False:
					if string.endswith('```'):
						fmt = "**{}**{}".format(string, mention_format) #same thing here
					else:
						fmt = "**{}** {}".format(string, mention_format)
				else:
					fmt = "**{}**".format(string)
		else:
			if emoji != None:
				if no_mention == False:
					if string.endswith('```'):
						#if no_mention is set to False, then mention the member/user
						fmt = "{} {}{}".format(emoji, string, mention_format) #dont mind this
					else:
						fmt = "{} {} {}".format(emoji, string, mention_format)
				else:
					fmt = "{} {}".format(emoji, string) #do the opposite
			else:
				if no_mention == False:
					if string.endswith('```'):
						fmt = "{}{}".format(string, mention_format) #same thing here
					else:
						fmt = "{} {}".format(string, mention_format)
				else:
					fmt = "{}".format(string)

		await self.bot.send_message(channel, fmt) #finally send the message

	async def text_mod_chan(self, string, channel, **kwargs):
		ignore_mod_chan_check = kwargs.get('ignore_check', False)
		no_bold = kwargs.get('no_bold', False)
		emoji = kwargs.get('emoji', ':warning:')

		server_config = pingbot.Config("./user/config/server.json").load_json()

		if isinstance(channel, str):
			mod_channel = discord.Object(channel)
		else:
			if "mod_channel" not in server_config[channel.server.id]:
				return
			mod_channel = server_config[channel.server.id]["mod_channel"]
			if ignore_mod_chan_check == False:
				if mod_channel == None:
					return
			mod_channel = self.bot.get_channel(server_config[channel.server.id]["mod_channel"])
			if mod_channel == None: #make sure mod channel actually exists
				raise pingbot.errors.NoModChannel("No Moderator status channel found!")
		
		await self.text("[{}]: {}".format(channel.created_at, string), no_ctx=True, no_bold=no_bold, emoji=emoji, channel=mod_channel, no_type=True, no_mention=True)

	async def text_mod_member(self, string, member, **kwargs):
		ignore_mod_chan_check = kwargs.get('ignore_check', False)
		no_bold = kwargs.get('no_bold', False)
		emoji = kwargs.get('emoji', ':warning:')

		server_config = pingbot.Config("./user/config/server.json").load_json()
		mod_channel = server_config[member.server.id]["mod_channel"]
		if ignore_mod_chan_check == False:
			if mod_channel == None:
				return

		mod_channel = self.bot.get_channel(server_config[member.server.id]["mod_channel"])
		if mod_channel == None: #make sure mod channel actually exists
			raise pingbot.errors.NoModChannel("No Moderator status channel found!")

		await self.text("[{}]: {}".format(member.joined_at, string), no_ctx=True, no_bold=no_bold, emoji=emoji, channel=mod_channel, no_type=True, no_mention=True)

	async def text_mod(self, string, channel=None, **kwargs):
		ignore_mod_chan_check = kwargs.get('ignore_check', False)
		no_bold = kwargs.get('no_bold', False)
		emoji = kwargs.get('emoji', ':warning:')

		if channel != None:
			try: #I DONT KNOW WHY THE FUCK THIS SHIT ISNT WORKING
				server_config = pingbot.Config("./user/config/server.json").load_json()
				mod_channel = server_config[self.msg.server.id]["mod_channel"]
				if ignore_mod_chan_check == False:
					if mod_channel == None:
						return
				mod_channel = self.bot.get_channel(server_config[self.msg.server.id]["mod_channel"])
				if mod_channel == None: #make sure mod channel actually exists
					raise pingbot.errors.NoModChannel("No Moderator status channel found!")
			except AttributeError:
				if isinstance(channel, str):
					mod_channel = discord.Object(id=channel)
				else:
					mod_channel = channel
		else:
			if isinstance(channel, str):
				mod_channel = discord.Object(id=channel)
			else:
				mod_channel = channel

		if channel != None:
			await self.text("{}".format(string), no_ctx=True, no_bold=no_bold, emoji=emoji, channel=mod_channel, no_type=True, no_mention=True)
		else:
			try:
				await self.text("[{}]: {}".format(self.msg.timestamp, string), no_ctx=True, no_bold=no_bold, emoji=emoji, channel=mod_channel, no_type=True, no_mention=True)
			except AttributeError:
				await self.text("{}".format(string), no_ctx=True, no_bold=no_bold, emoji=emoji, channel=mod_channel, no_type=True, no_mention=True)

	async def text_direct_mod(self, string, channel, **kwargs):
		emoji = kwargs.get('emoji', ':warning:')
		no_bold = kwargs.get('no_bold', False)
		mod_channel = discord.Object(id=channel)
		await self.text(string, no_ctx=True, no_bold=no_bold, emoji=emoji, channel=mod_channel, no_type=True, no_mention=True)

	async def text_status(self, string, channel, **kwargs):
		ignore_status_chan_check = kwargs.get('ignore_check', False)
		no_bold = kwargs.get('no_bold', False)
		emoji = kwargs.get('emoji', ':warning:')

		server_config = pingbot.Config("./user/config/server.json").load_json()
		if isinstance(channel, str):
			status_channel = discord.Object(channel)
		else:
			try:
				status_channel = self.bot.get_channel(server_config[channel.server.id]["status_channel"])

				if status_channel == None: #make sure mod channel actually exists
					raise pingbot.errors.NoModChannel("No activity status channel found!")
			except AttributeError:
				status_channel = server_config[channel.server.id]["status_channel"]

		if ignore_status_chan_check == False:
			if status_channel == None:
				return
		try:
			await self.text("[{}]: {}".format(self.msg.timestamp, string), no_ctx=True, no_bold=no_bold, emoji=emoji, channel=status_channel, no_type=True, no_mention=True)
		except AttributeError:
			await self.text("{}".format(string), no_ctx=True, no_bold=no_bold, emoji=emoji, channel=status_channel, no_type=True, no_mention=True)

	def string_type(self, string):
		"""
		Returns whether the string is a URL or if it is a regular string.
		"""
		if string.startswith('http://') or string.startswith('https://'):
			return "LINK"
		else:
			return "STRING"

	def setup_server_section(self, server, ignore_server_check=False):
		"""
		Creates the server settings in the server.json file.
		"""
		server_config = pingbot.Config("./user/config/server.json").load_json()
		if ignore_server_check == False:
			if server.id in server_config:
				return
		server_config[server.id] = {}
		server_config[server.id]["tableflip"] = True
		server_config[server.id]["respects"] = {}
		server_config[server.id]["respects"]["enabled"] = False
		server_config[server.id]["respects"]["stats"] = {}
		server_config[server.id]["channels"] = {}
		server_config[server.id]["mod_channel"] = None
		server_config[server.id]["status_channel"] = None
		for channel in server.channels:
			server_config[server.id]["channels"][channel.id] = {}
			server_config[server.id]["channels"][channel.id]["disabled_commands"] = []
		with open('./user/config/server.json', 'w') as f:
			json.dump(server_config, f)
		return

	def server_checkup(self, server):
		server_config = pingbot.Config("./user/config/server.json").load_json()
		if server.id not in server_config:
			server_config[server.id] = {}

		if "tableflip" not in server_config[server.id]:
			server_config[server.id]["tableflip"] = True

		if "respects" not in server_config[server.id]:
			server_config[server.id]["respects"] = {}
			server_config[server.id]["respects"]["enabled"] = False
			server_config[server.id]["respects"]["stats"] = {}

		if "channels" not in server_config[server.id]:
			server_config[server.id]["channels"] = {}

		if "mod_channel" not in server_config[server.id]:
			server_config[server.id]["mod_channel"] = None

		if "status_channel" not in server_config[server.id]:
			server_config[server.id]["status_channel"] = None
		for channel in server.channels:
			if channel.id not in server_config[server.id]["channels"]:
				server_config[server.id]["channels"][channel.id] = {}
				server_config[server.id]["channels"][channel.id]["disabled_commands"] = []

		pingbot.Config("./user/config/server.json").write_json(server_config)
		return

	def server_section_flush(self, server):
		"""
		Removes the server section from the config file.
		"""
		server_config = pingbot.Config("./user/config/server.json").load_json()
		if server.id not in server_config:
			return
		server_config.pop(server.id)
		with open('./user/config/server.json', 'w') as f:
			json.dump(server_config, f)
		return

	def channel_checkup(self, channel, check_if_channel_exists=False):
		"""
		Adds a channel to the server config.
		"""
		server_config = pingbot.Config("./user/config/server.json").load_json()
		if channel.id in server_config[channel.server.id]["channels"]:
			return
		server_config[channel.server.id]["channels"][channel.id] = {}
		server_config[channel.server.id]["channels"][channel.id]["disabled_commands"] = []
		with open('./user/config/server.json', 'w') as f:
			json.dump(server_config, f)
		return

	def channel_flush(self, channel):
		"""
		Removes a channel from the server config.
		"""
		server_config = pingbot.Config("./user/config/server.json").load_json()
		if channel.id not in server_config[channel.server.id]["channels"]:
			return
		server_config[channel.server.id]["channels"].pop(channel.id)
		if "nsfw_channels" in server_config[channel.server.id]:
			if channel.id in server_config[channel.server.id]["nsfw_channels"]:
				server_config[channel.server.id]["nsfw_channels"].remove(channel.id)
		if server_config[channel.server.id]["mod_channel"] == channel.id:
			server_config[channel.server.id]["mod_channel"] = None
		with open('./user/config/server.json', 'w') as f:
			json.dump(server_config, f)
		return

	def disable_command(self, ctx, commands):
		"""
		Disables a command.
		"""
		server_config = pingbot.Config('./user/config/server.json').load_json()
		no_disable_cmds = pingbot.Config('./core/data/system.json').load_json()["no_disable"]
		if isinstance(commands, list): #if the parameter is a list
			for cmd in commands:
				if cmd not in server_config[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"]: #check if command is already in the disabled commands list
					if cmd not in no_disable_cmds: #make sure the command isnt in the no_disable list
						server_config[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"].append(cmd)
					else:
						return "NO_DISABLE"
				else:
					return "ALREADY_DISABLE"
		else:
			if commands not in server_config[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"]:
				if commands not in no_disable_cmds:
					server_config[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"].append(commands)
				else:
					return "NO_DISABLE"
			else:
				return "ALREADY_DISABLE"

		pingbot.Config("./user/config/server.json").write_json(server_config)

	def enable_command(self, ctx, commands):
		"""
		Enables a command.
		"""
		server_config = pingbot.Config('./user/config/server.json').load_json()
		no_disable_cmds = pingbot.Config('./core/data/system.json').load_json()["no_disable"]
		if isinstance(commands, list): #if the parameter is a list
			for cmd in commands:
				if cmd in server_config[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"]: #check if command is already in the disabled commands list
					server_config[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"].remove(cmd)
				else:
					return "ALREADY_ENABLE"
		else:
			if commands in server_config[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"]:
				server_config[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"].remove(commands)
			else:
				return "ALREADY_ENABLE"

		pingbot.Config("./user/config/server.json").write_json(server_config)

	def cmd_is_disabled(self, ctx, command):
		"""
		Checks if a command is disabled.
		"""
		disabled_commands = pingbot.Config('./user/config/server.json').load_json()[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"]
		if command in disabled_commands:
			return True
		else:
			return False

	def cmd_is_disabled_list_form(self, ctx, commands):
		"""
		Same thing as cmd_is_disabled but instead it takes lists instead of tuples.
		"""
		disabled_commands = pingbot.Config('./user/config/server.json').load_json()[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"]
		return any(True for x in disabled_commands if x in commands)

	def cmd_is_disabled_user(self, ctx, commands):
		if ctx.message.author.id not in pingbot.Config('./user/config/server.json').load_json()[ctx.message.server.id]["members"]:
			return False
		disabled_commands = pingbot.Config('./user/config/server.json').load_json()[ctx.message.server.id]["members"][ctx.message.author.id]["disabled_commands"]
		return any(True for x in disabled_commands if x in commands)

	def cmd_is_disabled_user_no_list(self, ctx, command):
		if ctx.message.author.id not in pingbot.Config('./user/config/server.json').load_json()[ctx.message.server.id]["members"]:
			return False
		disabled_commands = pingbot.Config('./user/config/server.json').load_json()[ctx.message.server.id]["members"][ctx.message.author.id]["disabled_commands"]
		if command in disabled_commands:
			return True
		else:
			return False

	def return_member_info(self, member):
		"""
		Returns the member information.
		"""
		roles = ', '.join([x.name for x in member.roles])
		roles = roles.replace('@', '(@)')
		fmt = """{0.avatar_url}
```xl
  Name: {0.name} (#{0.discriminator})
    ID: {0.id}
  Nick: {0.nick}
 Roles: {1}
Joined: {0.joined_at}
  Game: {0.game}
   Bot: {0.bot}
```""".format(member, roles)
		return fmt

	def return_channel_info(self, channel):
		"""
		Returns the channel information.
		"""
		fmt = """```xl
   Name: {0.name}
	 ID: {0.id}
Default: {0.is_default}
Created: {0.created_at}
  Topic: {0.topic}
```""".format(channel)
		return fmt

	def return_server_info(self, server):
		fmt = """{0.icon_url}
```xl
		   Name: {0.name}
			 ID: {0.id}
		  Roles: {1}
		Members: {0.member_count}
	   Channels: {2}
		 Region: {0.region}
		  Owner: {0.owner}
		Created: {0.created_at}
Default Channel: {0.default_channel}
```""".format(server, len(server.roles), len(server.channels))
		return fmt

	def reload_ping_modules(self):
		modules = ['core.pingbot.config', 'core.pingbot.errors', 'core.pingbot.log', 'core.pingbot.permissions', 'core.pingbot.utils', 'core.pingbot.webtools']
		for module in modules:
			importlib.reload(__import__(module))
			print("Reloaded {}".format(module))

	def return_what_updated_channel(self, before, after):
		"""
		Returns a list of items that the channel was updated.
		"""
		changed_items = []
		if before.name != after.name:
			changed_items.append("name")
		elif before.topic != after.topic:
			changed_items.append("topic")
		#if before.position != after.position:
		#	changed_items.append("totem pole position")
		return changed_items

	def return_what_updated_server(self, before, after):
		"""
		Returns a list of items that the server updated.
		"""
		changed_items = []
		if before.name != after.name:
			changed_items.append("name")
		if before.region != after.region:
			changed_items.append("region")
		if before.afk_timeout != after.afk_timeout:
			changed_items.append("afk timeout")
		if before.afk_channel != after.afk_channel:
			changed_items.append("afk channel")
		if before.icon != after.icon:
			changed_items.append("icon")
		if before.owner != after.owner:
			changed_items.append("owner")
		return changed_items

	def timer_format(self, sec=None, minu=None, hr=None):
		start = datetime.utcnow()
		if sec == None:
			sec = (datetime.utcnow() - start).seconds

		if minu == None:
			mini = 0

		if hr == None:
			hr = 0

		if seconds >= 60:
			minu += 1

		if minu >= 60:
			hr += 1

		fmt = "{}:{}:{}".format(hr, minu, sec)
		return fmt

	def get_config_message(self, message, **kwargs):
		directory = kwargs.get('direc', './core/data/messages.json')
		messages = pingbot.Config(directory).load_json()

		if message not in messages:
			raise KeyError("Could not find the message, {}.".format(message))

		if isinstance(messages[message], list): #if its a list of strings, then cycle through them and return a random result
			return random.choice(messages[message])

		return messages[message]

	def get_config_event_message(self, message, **kwargs):
		directory = kwargs.get('direc', './core/data/messages.json')
		messages = pingbot.Config(directory).load_json()

		if message not in messages["events"]:
			raise KeyError("Could not find the message, {}.".format(message))

		if isinstance(messages["events"][message], list): #if its a list of strings, then cycle through them and return a random result
			return random.choice(messages["events"][message])

		return messages["events"][message]

	def get_config_emoji(self, emoji):
		emojis = pingbot.Config('./core/data/emoji.json').load_json()

		if emoji not in emojis:
			raise KeyError("Could not find the emoji, {}.".format(emoji))

		if isinstance(emojis[emoji], list):
			return random.choice(emojis[emoji])

		return emojis[emoji]

	def cog_exists(self, cog):
		if os.path.isfile('./user/cogs/{0}/{0}.py'.format(cog)):
			return True
		else:
			return False

	def find_role(self, server, keyword):
		for role in server.roles:
			if role.name.startswith(keyword):
				return role
			elif keyword in role.name:
				return role
			elif keyword == role.id:
				return role

		return None