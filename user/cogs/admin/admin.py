from core import pingbot
from core.pingbot.messages import text
from discord.ext import commands
import discord
import random
import json

sysmsg = pingbot.Config().load_json("./core/data/messages.json")
config = pingbot.Config().load_json("./user/config/bot.json")
no_perm = sysmsg['no_permission']
no_bot_perm = sysmsg['no_bot_permission']
no_pm_msg = sysmsg['no_pm']
if isinstance(config['prefix'], list): #kind of useless but just a little thingy
	if len(config['prefix']) > 1:
		command_prefix = random.choice(config['prefix'])
	else:
		command_prefix = config['prefix'][0]
else:
	command_prefix = config['prefix']

class Admin:
	def __init__(self, bot):
		self.bot = bot

		self.cur_votekick = {
			"Server ID": { #the votekick server ID
				"instigator": "The member's ID", #the instigator's ID
				"voters": [], #the members who voted yes
				"devoters": [] #the members who voted no
			}
		}

	@commands.command(pass_context=True, name="set-log", aliases=["set_log"], no_pm=True)
	@pingbot.permissions.is_bot_owner()
	@pingbot.permissions.is_serv_owner()
	@pingbot.permissions.is_administrator()
	async def _admin_log(self, ctx):
		"""
		⚔ Sets the channel to become a Moderator log.

		--------------------
		  USAGE: set-log
		EXAMPLE: set-log
		--------------------
		"""

		server_config = pingbot.Config("./user/config/server.json").load_json()
		if "mod_channel" not in server_config[ctx.message.server.id]:
			server_config[ctx.message.server.id]["mod_channel"] = None
			server_config = pingbot.Config("./user/config/server.json").write_json(server_config)
			server_config = pingbot.Config("./user/config/server.json").load_json()

		if server_config[ctx.message.server.id]["mod_channel"] == None: #if the mod chan is set to nothing, then set it to the current channel
			server_config[ctx.message.server.id]["mod_channel"] = ctx.message.channel.id
			with open('./user/config/server.json', 'w') as f:
				json.dump(server_config, f)
			await text("Successfully set mod status log to the current channel!", emoji="success")
			return
		else: #or if the mod chan is set to something, then remove it
			server_config[ctx.message.server.id]["mod_channel"] = None
			with open('./user/config/server.json', 'w') as f:
				json.dump(server_config, f)
			await text("Successfully removed mod status log from the current channel!", emoji="success")
			return

	@commands.command(pass_context=True, name="set-status", aliases=["set_status"], no_pm=True)
	@pingbot.permissions.is_bot_owner()
	@pingbot.permissions.is_serv_owner()
	@pingbot.permissions.is_administrator()
	async def _status_log(self, ctx):
		"""
		⚔ Sets the channel to output member activity.

		--------------------
		  USAGE: set-status
		EXAMPLE: set-status
		--------------------
		"""

		server_config = pingbot.Config("./user/config/server.json").load_json()
		status_channel = server_config[ctx.message.server.id]["status_channel"]
		if status_channel == None:
			server_config[ctx.message.server.id]["status_channel"] = ctx.message.channel.id
			await text("Successfully set general member activity log to the current channel!", emoji="success")
		else:
			server_config[ctx.message.server.id]["status_channel"] = None
			await text("This channel is no longer a member activity logger.", emoji="success")
		pingbot.Config("./user/config/server.json").write_json(server_config)

	@commands.command(name="toggle-command", aliases=["toggle_command"], pass_context=True, no_pm=True)
	@pingbot.permissions.has_permissions(manage_server=True)
	async def _toggle_command(self, ctx, command : str, member : discord.Member=None):
		"""
		⚔ Disables or enables a command for a channel or member.

		--------------------
		  USAGE: toggle-command <command or "all"> <optional: member name or mention>
		EXAMPLE: toggle-command rule34
		--------------------
		"""
		server_config = pingbot.Config("./user/config/server.json").load_json()
		if command not in self.bot.commands and command not in pingbot.Config("./user/cogs/fun/customcommands.json").load_json() and command.lower() != "all": #if the command doesn't exist.
			await text(pingbot.get_message("toggle_command_not_found"), emoji="failure")
			return

		if command in pingbot.Config("./core/data/system.json").load_json()["no_disable"]: #make sure the user doesnt try disabling something like the help command or this command.
			await text(pingbot.get_message("toggle_command_cannot_be_toggled"), emoji="failure")
			return

		if command.lower() == "all":
			if member != None:
				disabling = False
				if member.id not in server_config[ctx.message.server.id]["members"]:
					server_config[ctx.message.server.id]["members"][member.id] = {}
					server_config[ctx.message.server.id]["members"][member.id]["disabled_commands"] = []

				for cmd in self.bot.commands: #disable all regular commands
					if cmd not in server_config[ctx.message.server.id]["members"][member.id]["disabled_commands"] and cmd not in pingbot.Config("./core/data/system.json").load_json()["no_disable"]:
						server_config[ctx.message.server.id]["members"][member.id]["disabled_commands"].append(cmd)
						disabling = True
					elif cmd in server_config[ctx.message.server.id]["members"][member.id]["disabled_commands"]:
						server_config[ctx.message.server.id]["members"][member.id]["disabled_commands"].remove(cmd)

				cc_json = pingbot.Config("./user/cogs/fun/customcommands.json").load_json()
				for cc in cc_json: #disable all custom commands
					if member.id not in cc_json[cc]["disabled"] and cc not in pingbot.Config("./core/data/system.json").load_json()["no_disable"]:
						cc_json[cc]["disabled"].append(member.id)
						disabling = True
					elif member.id in cc_json[cc]["disabled"]:
						cc_json[cc]["disabled"].remove(member.id)

				pingbot.Config("./user/config/server.json").write_json(server_config)
				pingbot.Config("./user/cogs/fun/customcommands.json").write_json(cc_json)

				if disabling == True:
					await text("Successfully disabled all commands, and custom commands for {}!".format(member), emoji="success")
				else:
					await text("Successfully enabled all commands, and custom commands for {}!".format(member), emoji="success")
				return
			else:
				disabling = False
				if ctx.message.channel.id not in server_config[ctx.message.server.id]["channels"]:
					server_config[ctx.message.server.id]["channels"][ctx.message.channel.id] = {}
					server_config[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"] = []

				for cmd in self.bot.commands:
					if cmd not in server_config[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"] and cmd not in pingbot.Config("./core/data/system.json").load_json()["no_disable"]:
						disabling = True
						server_config[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"].append(cmd)
					elif cmd in server_config[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"]:
						server_config[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"].remove(cmd)

				cc_json = pingbot.Config("./user/cogs/fun/customcommands.json").load_json()
				for cc in cc_json: #disable all custom commands
					if ctx.message.channel.id not in cc_json[cc]["disabled"] and cc not in pingbot.Config("./core/data/system.json").load_json()["no_disable"]:
						cc_json[cc]["disabled"].append(ctx.message.channel.id)
						disabling = True
					elif ctx.message.channel.id in cc_json[cc]["disabled"]:
						cc_json[cc]["disabled"].remove(ctx.message.channel.id)

				pingbot.Config("./user/config/server.json").write_json(server_config)
				pingbot.Config("./user/cogs/fun/customcommands.json").write_json(cc_json)

				if disabling == True:
					await text("Successfully disabled all commands, and custom commands for this channel!", emoji="success")
				else:
					await text("Successfully enabled all commands, and custom commands for this channel!", emoji="success")

				return

		if command in pingbot.Config("./user/cogs/fun/customcommands.json").load_json() and command not in self.bot.commands:
			if member != None:
				cc_json = pingbot.Config("./user/cogs/fun/customcommands.json").load_json()
				if member.id not in cc_json[command]["disabled"]:
					cc_json[command]["disabled"].append(member.id)
					pingbot.Config("./user/cogs/fun/customcommands.json").write_json(cc_json)
					await text("Successfully disabled custom command for {}".format(member), emoji="success")
					return
				else:
					cc_json[command]["disabled"].remove(member.id)
					pingbot.Config("./user/cogs/fun/customcommands.json").write_json(cc_json)
					await text("Successfully enabled custom command for {}".format(member), emoji="success")
					return
			else:
				cc_json = pingbot.Config("./user/cogs/fun/customcommands.json").load_json()

				if ctx.message.channel.id not in cc_json[command]["disabled"]:
					cc_json[command]["disabled"].append(ctx.message.channel.id)
					pingbot.Config("./user/cogs/fun/customcommands.json").write_json(cc_json)
					await text("Successfully disabled custom command for this channel.", emoji="success")
					return
				else:
					cc_json[command]["disabled"].remove(ctx.message.channel.id)
					pingbot.Config("./user/cogs/fun/customcommands.json").write_json(cc_json)
					await text("Successfully enabled custom command for this channel.", emoji="success")
					return
		else:
			if member != None:
				if member.id not in server_config[ctx.message.server.id]["members"]:
					server_config[ctx.message.server.id]["members"][member.id] = {}
					server_config[ctx.message.server.id]["members"][member.id]["disabled_commands"] = []

				if command not in server_config[ctx.message.server.id]["members"][member.id]["disabled_commands"]: #disable command
					server_config[ctx.message.server.id]["members"][member.id]["disabled_commands"].append(command)
					pingbot.Config("./user/config/server.json").write_json(server_config)
					await text(pingbot.get_message("disabled_command_success_member").format(member), emoji="success")
					return
				else: #enable command
					server_config[ctx.message.server.id]["members"][member.id]["disabled_commands"].remove(command)
					pingbot.Config("./user/config/server.json").write_json(server_config)
					await text(pingbot.get_message("enabled_command_success_member").format(member), emoji="success")
					return
				
			else:
				if ctx.message.channel.id not in server_config[ctx.message.server.id]["channels"]:
					server_config[ctx.message.server.id]["channels"][ctx.message.channel.id] = {}
					server_config[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"] = []

				if command not in server_config[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"]:
					server_config[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"].append(command) #disable command
					pingbot.Config("./user/config/server.json").write_json(server_config)
					await text(pingbot.get_message("disabled_command_success"), emoji="success")
					return
				else:
					server_config[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"].remove(command) #enable command
					pingbot.Config("./user/config/server.json").write_json(server_config)
					await text(pingbot.get_message("enabled_command_success"), emoji="success")
					return

	@commands.command(pass_context=True, no_pm=True)
	@pingbot.permissions.has_permissions(ban_members=True)
	async def ban(self, ctx, member : discord.Member, reason : str = "No reason provided."):
		"""
		⚔ Bans a member from the server.

		--------------------
		  USAGE: ban <member name or mention>
		EXAMPLE: ban Bot
		--------------------
		"""
		msg = ctx.message
		try:
			await self.bot.ban(member)
			fmt = """**[{}]: You have been banned from {} (#{}) by {} for the following reason(s)...**
`{}`""".format(msg.timestamp, msg.server, msg.channel, msg.author, reason)
			await text(fmt, channel=member, no_mention=True, no_bold=True)
			await text("Successfully banned {}!".format(member.name), emoji="success")
		except discord.errors.Forbidden:
			await text(pingbot.get_message("no_bot_perm"), emoji="failure")

	@commands.command(pass_context=True, no_pm=True, aliases=["softban"])
	@pingbot.permissions.has_permissions(kick_members=True)
	async def kban(self, ctx, member : discord.Member, reason : str = "No reason provided.", delete_days : int = 1):
		"""
		⚔ Kicks a member from the server and deletes a day worth of messages.

		--------------------
		  USAGE: kban <member name or mention>
		EXAMPLE: kban Bot
		--------------------
		"""
		msg = ctx.message

		try:
			fmt = """**[{}]: You have been kicked from {} (#{}) by {} for the following reason(s)...**
`{}`""".format(msg.timestamp, msg.server, msg.channel, msg.author.name, reason)
			await text(fmt, channel=member, no_mention=True, no_bold=True)
			await self.bot.ban(member, delete_days)
			await self.bot.unban(msg.server, member)
		except discord.errors.Forbidden:
			await text(no_bot_perm, emoji="failure")
			return
		await text("Successfully kick-banned {}!".format(member.name), emoji="success")

	@commands.command(pass_context=True, no_pm=True)
	@pingbot.permissions.has_permissions(kick_members=True)
	async def kick(self, ctx, member : discord.Member, reason : str = "No reason provided."):
		"""
		⚔ Kicks a member from the server.

		--------------------
		  USAGE: kick <member name or mention>
		EXAMPLE: kick Bot
		--------------------
		"""
		msg = ctx.message

		try:
			fmt = """**[{}]: You have been kicked from {} (#{}) by {} for the following reason(s)...**
`{}`""".format(msg.timestamp, msg.server, msg.channel, msg.author.name, reason)
			await text(fmt, channel=member, no_mention=True, no_bold=True)
			await self.bot.kick(member)
		except discord.errors.Forbidden:
			await text(pingbot.get_message("no_bot_perm"), emoji="failure")
			return
		await text("Successfully kicked {}!".format(member), emoji="success")

	@commands.group(pass_context=True, aliases=["clean", "purge"], no_pm=True)
	@pingbot.permissions.has_permissions(manage_messages=True)
	async def clear(self, ctx):
		"""
		⚔ Clears past messages.

		--------------------
		  USAGE: clear <number of messages>
		EXAMPLE: clear 16
		--------------------
		"""
		if ctx.invoked_subcommand is None:
			try:
				amount = int(ctx.subcommand_passed)
			except ValueError:
				await text("Invalid message amount.", emoji="failure")
				return

			try:
				await self.bot.purge_from(ctx.message.channel, limit=amount+1)
			except discord.errors.Forbidden:
				await text(pingbot.get_message("no_bot_perm"), emoji="failure")

	@clear.command(pass_context=True, name="member", no_pm=True)
	async def _clear_from_member(self, ctx, member : discord.Member, amount : int = 100):
		"""
		⚔ Clears past messages sent by a specific member.

		--------------------
		  USAGE: clear member <member name or mention> <optional: amount of messages>
		EXAMPLE: clear member Bot
		--------------------
		"""

		def is_mem(m):
			if m == ctx.message or m.author == member:
				return True
			else:
				return False

		try:
			await self.bot.purge_from(ctx.message.channel, limit=amount+1, check=is_mem)
		except discord.errors.Forbidden:
			await text(pingbot.get_message("no_bot_perm"), emoji="failure")

	@clear.command(pass_context=True, name="contains", no_pm=True)
	async def _clear_contains(self, ctx, keyword : str, amount : int = 100):
		"""
		⚔ Clears the past messages containing a keyword.

		--------------------
		  USAGE: clear contains <keyword> <optional: amount of messages>
		EXAMPLE: clear contains yolo
		--------------------
		"""

		def is_msg(m):
			return keyword in m.content

		try:
			await self.bot.purge_from(ctx.message.channel, limit=amount+1, check=is_msg)
		except discord.errors.Forbidden:
			await text(no_bot_perm, emoji="failure")

	@commands.command(pass_context=True, name="member", no_pm=True)
	@pingbot.permissions.has_permissions(send_messages=True)
	async def _get_member_info(self, ctx, member : discord.Member=None):
		"""
		⚔ Returns information about a member.

		--------------------
		  USAGE: member <optional: member name or mention>
		EXAMPLE: member
		--------------------
		"""
		if member == None:
			member = ctx.message.author

		await text(pingbot.Utils().return_member_info(member))

	@commands.command(pass_context=True, name="avatar", no_pm=True)
	@pingbot.permissions.has_permissions(send_messages=True)
	async def _get_member_avatar(self, ctx, member : discord.Member=None):
		"""
		⚔ Returns the avatar URL of a member.

		--------------------
		  USAGE: avatar <optional: member name or mention>
		EXAMPLE: avatar
		--------------------
		"""
		if member == None:
			member = ctx.message.author

		if member.avatar == None:
			avatar = "{} has no avatar.".format(member)
		else:
			avatar = "{}'s avatar is {}".format(member, member.avatar_url)

		await text(avatar, emoji="member_update_avatar", no_bold=True)

	@commands.command(pass_context=True, name="channel", no_pm=True)
	@pingbot.permissions.has_permissions(send_messages=True)
	async def _get_channel_info(self, ctx, channel : discord.Channel=None):
		"""
		⚔ Returns information about a channel.

		--------------------
		  USAGE: channel <optional: channel name>
		EXAMPLE: channel
		--------------------
		"""
		if channel == None:
			channel = ctx.message.channel
		elif channel != None:
			if channel.type.voice:
				await text("Unable to retrieve information on voice channels.", emoji="failure")
				return

		await text(pingbot.Utils().return_channel_info(channel))

	@commands.command(pass_context=True, name="server", no_pm=True)
	@pingbot.permissions.has_permissions(send_messages=True)
	async def _get_server_info(self, ctx):
		"""
		⚔ Returns information about the server.

		--------------------
		  USAGE: server
		EXAMPLE: server
		--------------------
		"""
		await text(pingbot.Utils().return_server_info(ctx.message.server))

	@commands.group(pass_context=True, name="iam")
	@pingbot.permissions.has_permissions(send_messages=True)
	async def _iam_role(self, ctx):
		"""
		⚔ Adds you to a role (or sets the bot owner to the author.)

		--------------------
		  USAGE: iam <role name>
		EXAMPLE: iam Admin
		--------------------
		"""
		if ctx.invoked_subcommand is None:
			author = ctx.message.author
			if ctx.subcommand_passed is None:
				await text(pingbot.get_message("iam_role_not_included"), emoji="failure")
				return

			role = discord.utils.find(lambda r: r.name == ctx.subcommand_passed, ctx.message.channel.server.roles)
			if role == None:
				await text(pingbot.get_message("iam_role_not_found"), emoji="failure")
				return
			#command permission requirements scale to how "powerful" the role is (if your a bot owner, server owner or administrator, then the power check wont do anything)

			power = 0

			if role.permissions.administrator:
				power += 100
			if role.permissions.manage_channels:
				power += 70

			if role.permissions.manage_server:
				power += 100

			if role.permissions.read_messages:
				power += 2

			if role.permissions.send_messages:
				power += 3

			if role.permissions.send_tts_messages:
				power += 3

			if role.permissions.embed_links:
				power += 1

			if role.permissions.attach_files:
				power += 1

			if role.permissions.read_message_history:
				power += 2

			if role.permissions.mention_everyone:
				power += 1

			if role.permissions.connect:
				power += 1

			if role.permissions.speak:
				power += 1

			if role.permissions.mute_members:
				power += 10

			if role.permissions.deafen_members:
				power += 10

			if role.permissions.move_members:
				power += 4

			if role.permissions.use_voice_activation:
				power += 1

			if role.permissions.change_nicknames:
				power += 2

			if role.permissions.manage_nicknames:
				power += 30

			if role.permissions.manage_roles:
				power += 100

			if not pingbot.permissions._is_bot_owner(author) and not pingbot.permissions._is_serv_owner(author, ctx) and not pingbot.permissions._is_administrator(author):
				if power >= 60:
					await text(pingbot.get_message("iam_role_insufficient_perm"), emoji="failure")
					return
				else:
					await self.bot.add_roles(ctx.message.author, role)
					await text(pingbot.get_message("iam_role_success").format(role.name), emoji="success")
					return
			else:
				await self.bot.add_roles(ctx.message.author, role)
				await text(pingbot.get_message("iam_role_success").format(role.name), emoji="success")

	@_iam_role.command(pass_context=True, name="owner", aliases=["bot_owner"])
	async def _iam_bot_owner(self, ctx, member : discord.Member=None):
		"""
		⚔ Adds you (or a member) to the list of bot owners (if none have been added.)

		--------------------
		  USAGE: iam owner <optional: member name or mention>
		EXAMPLE: iam bot_owner
		--------------------
		"""
		if member == None:
			user = ctx.message.author
		else:
			user = member

		bot_json = pingbot.Config("./user/config/bot.json").load_json()
		if member == None:
			author = ctx.message.author
			if "bot_owners" not in bot_json:
				bot_json["bot_owners"] = []
				bot_json["bot_owners"].append(author.id)
			elif len(bot_json["bot_owners"]) == 0:
				bot_json["bot_owners"].append(author.id)

			elif "bot_owners" in bot_json and len(bot_json["bot_owners"]) > 0 and author.id not in bot_json["bot_owners"]:
				await text(pingbot.get_message("iam_role_botowner_error_yourself"), emoji="failure")
				return
			elif author.id in bot_json["bot_owners"]:
				await text(pingbot.get_message("iam_role_botowner_already_added_yourself"), emoji="failure")
				return
		else:
			if ctx.message.author.id not in bot_json["bot_owners"]:
				await text(pingbot.get_message("iam_role_botowner_error_member"), emoji="failure")
				return

			if "bot_owners" not in bot_json:
				bot_json["bot_owners"] = []
				bot_json["bot_owners"].append(user.id)
			elif len(bot_json["bot_owners"]) == 0:
				bot_json["bot_owners"].append(user.id)
			elif user.id in bot_json["bot_owners"]:
				await text(pingbot.get_message("iam_role_botowner_already_added_member"), emoji="failure")
				return
			else:
				bot_json["bot_owners"].append(user.id)

		await text(pingbot.get_message("iam_role_botowner_verification"), emoji="question")
		#Verification process
		pingbot.Utils().cprint("green", "A user has attempted to set themselves as a bot owner.\n\nPlease confirm this via 'y' or 'n'")
		verification = input("-> ")
		if verification.lower() == "yes" or verification.lower() == "y":
			pingbot.Config("./user/config/bot.json").write_json(bot_json)
			pingbot.Utils().cprint("green", "Successfully added user as bot owner!")
			await text(pingbot.get_message("iam_role_botowner_success"), emoji="success")
		elif verification.lower() == "no" or verification.lower() == "n":
			pingbot.Utils().cprint("red", "Alright.")
			await text(pingbot.get_message("iam_role_botowner_verification_denied"), emoji="failure")
			return
		else:
			pingbot.Utils().cprint("red", "Unknown response.\nDefaulting to 'n'")
			await text(pingbot.get_message("iam_role_botowner_verification_denied"), emoji="failure")
			return

	@commands.group(pass_context=True, aliases=["auto_reply", "auto-reply", "autoreplies", "auto-replies", "auto_replies", "autoreplys", "auto-replys", "auto_replys"], no_pm=True)
	@pingbot.permissions.has_permissions(manage_messages=True)
	async def autoreply(self, ctx):
		"""
		⚔ Auto reply management command.

		--------------------
		  USAGE: autoreply <subcommand or auto reply keyword>
		EXAMPLE: autoreply add
		--------------------
		"""
		if ctx.invoked_subcommand is None:
			if ctx.subcommand_passed is None:
				await text("You must provide a subcommand or auto reply keyword.", emoji="failure")
				return

			auto_replies = pingbot.Config('./user/cogs/fun/fun_info.json').load_json()["auto_replies"]
			if ctx.message.server.id not in auto_replies:
				await text("No auto replies have been added to this server.", emoji="failure")
				return

			ar_keyword = ctx.subcommand_passed
			if ar_keyword not in auto_replies[ctx.message.server.id]:
				await text("That keyword doesn't exist!", emoji="failure")
				return

			await text("The value of `{}` is, `{}`.".format(ar_keyword, auto_replies[ctx.message.server.id][ar_keyword]))

	@autoreply.command(pass_context=True, no_pm=True)
	@pingbot.permissions.has_permissions(manage_messages=True)
	async def add(self, ctx, keyword : str, *, value : str):
		"""
		⚔ Adds an auto reply keyword.

		--------------------
		  USAGE: autoreply add <keyword> <value>
		EXAMPLE: autoreply add ayy lmao
		--------------------
		"""
		auto_replies = pingbot.Config('./user/cogs/fun/fun_info.json').load_json()
		if ctx.message.server.id not in auto_replies["auto_replies"]:
			auto_replies["auto_replies"][ctx.message.server.id] = {}
			auto_replies["auto_replies"][ctx.message.server.id][keyword] = value
			pingbot.Config('./user/cogs/fun/fun_info.json').write_json(auto_replies)
			await text("Successfully added auto reply keyword!", emoji="success")
			return

		elif keyword not in auto_replies["auto_replies"][ctx.message.server.id]:
			auto_replies["auto_replies"][ctx.message.server.id][keyword] = value
			pingbot.Config('./user/cogs/fun/fun_info.json').write_json(auto_replies)
			await text("Successfully added auto reply keyword!", emoji="success")
			return
		else:
			await text("That keyword has already been added.", emoji="failure")
			return

	@autoreply.command(pass_context=True, no_pm=True)
	@pingbot.permissions.has_permissions(manage_messages=True)
	async def rename(self, ctx, keyword : str, new_keyword : str):
		"""
		⚔ Renames an auto reply keyword.

		--------------------
		  USAGE: autoreply rename <keyword> <new_keyword>
		EXAMPLE: autoreply rename ayy ayy_lmao
		--------------------
		"""
		auto_replies = pingbot.Config('./user/cogs/fun/fun_info.json').load_json()
		if ctx.message.server.id not in auto_replies["auto_replies"]:
			await text("No keywords have been added on this server.", emoji="failure")
			return
		elif keyword not in auto_replies["auto_replies"][ctx.message.server.id]:
			await text("That keyword has not been added on this server.", emoji="failure")
		else:
			old_keyword_data = auto_replies["auto_replies"][ctx.message.server.id][keyword]
			auto_replies["auto_replies"][ctx.message.server.id].pop(keyword)
			auto_replies["auto_replies"][ctx.message.server.id][new_keyword] = old_keyword_data
			pingbot.Config('./user/cogs/fun/fun_info.json').write_json(auto_replies)
			await text("Successfully renamed keyword!", emoji="success")
			return

	@autoreply.command(pass_context=True, no_pm=True)
	@pingbot.permissions.has_permissions(manage_messages=True)
	async def edit(self, ctx, keyword : str, new_value : str):
		"""
		⚔ Modifies an auto reply keyword value.

		--------------------
		  USAGE: autoreply edit <keyword> <new value>
		EXAMPLE: autoreply edit ayy lmao1
		--------------------
		"""
		auto_replies = pingbot.Config('./user/cogs/fun/fun_info.json').load_json()
		if ctx.message.server.id not in auto_replies["auto_replies"]:
			await text("No keywords have been added on this server.", emoji="failure")
			return
		elif keyword not in auto_replies["auto_replies"][ctx.message.server.id]:
			await text("That keyword has not been added on this server.", emoji="failure")
		else:
			auto_replies["auto_replies"][ctx.message.server.id][keyword] = new_value
			pingbot.Config('./user/cogs/fun/fun_info.json').write_json(auto_replies)
			await text("Successfully modified keyword!", emoji="success")
			return

	@autoreply.command(pass_context=True, no_pm=True)
	@pingbot.permissions.has_permissions(manage_messages=True)
	async def remove(self, ctx, keyword : str):
		"""
		⚔ Removes an auto reply keyword.

		--------------------
		  USAGE: autoreply remove <keyword>
		EXAMPLE: autoreply remove ayy
		--------------------
		"""
		auto_replies = pingbot.Config('./user/cogs/fun/fun_info.json').load_json()
		if ctx.message.server.id not in auto_replies["auto_replies"]:
			await text("No keywords have been added on this server.", emoji="failure")
			return
		elif keyword not in auto_replies["auto_replies"][ctx.message.server.id]:
			await text("That keyword has not been added on this server.", emoji="failure")
		else:
			auto_replies["auto_replies"][ctx.message.server.id].pop(keyword)
			pingbot.Config('./user/cogs/fun/fun_info.json').write_json(auto_replies)
			await text("Successfully removed keyword!", emoji="success")
			return

	@commands.group(pass_context=True, aliases=["welcome_msg", "welcome-msg"], no_pm=True)
	@pingbot.permissions.has_permissions(manage_channels=True)
	async def welcomemsg(self, ctx):
		"""
		⚔ Welcome message management command.

		--------------------
		  USAGE: welcomemsg <subcommand>
		EXAMPLE: welcomemsg add
		--------------------
		"""
		if ctx.invoked_subcommand is None:
			await text("You must provide a subcommand.")

	@welcomemsg.command(name="add", pass_context=True, no_pm=True)
	async def welcomemsg_add(self, ctx, channel : discord.Channel, *, welcome_message : str):
		"""
		⚔ Adds a welcome message to a channel.

		--------------------
		  USAGE: welcomemsg add <channel> <welcome message>
		EXAMPLE: welcomemsg add #general Welcome to {0.server.name}!
		--------------------
		"""
		welcome_json = pingbot.Config('./user/cogs/admin/admin_info.json').load_json()
		if channel.id not in welcome_json["welcome_messages"]:
			welcome_json["welcome_messages"][channel.id] = []
			welcome_json["welcome_messages"][channel.id].append(welcome_message)
		elif welcome_message not in welcome_json["welcome_messages"][channel.id]:
			welcome_json["welcome_messages"][channel.id].append(welcome_message)
		else:
			await text("That message has already been added.", emoji="failure")
			return

		pingbot.Config('./user/cogs/admin/admin_info.json').write_json(welcome_json)

		await text("Successfully added welcome message.", emoji="success")

	@welcomemsg.command(name="remove", pass_context=True, no_pm=True)
	async def welcomemsg_remove(self, ctx, *, welcome_message : str):
		"""
		⚔ Remove a welcome message.

		--------------------
		  USAGE: welcomemsg remove <exact string or index>
		EXAMPLE: welcomemsg remove 0
		--------------------
		"""
		welcome_json = pingbot.Config('./user/cogs/admin/admin_info.json').load_json()
		if ctx.message.channel.id not in welcome_json["welcome_messages"]:
			await text("No welcome messages have been added to this channel.", emoji="failure")
			return
		elif welcome_message not in welcome_json["welcome_messages"][ctx.message.channel.id]:
			await text("That welcome message has not been added to this channel.", emoji="failure")
			return
		elif any(char in welcome_message for char in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '/', '\\', '`', '[', ';', '.', ',', ']', '-', '=', '_', '+', '~', '{', '}', ':', "'", '"', '<', '>', '?', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')']):
			try:
				welcome_index = int(welcome_message)
			except ValueError:
				await text("That welcome message has not been added to this channel.", emoji="failure")
				return

			try:
				welcome_message = welcome_json["welcome_messages"][ctx.message.channel.id][welcome_index]
			except IndexError:
				await text("Index is out of range.", emoji="failure")
				return

			welcome_json["welcome_messages"][ctx.message.channel.id].pop(welcome_index)
		pingbot.Config('./user/cogs/admin/admin_info.json').write_json(welcome_json)
		await text("Successfully removed message.", emoji="success")

	@welcomemsg.command(name="disable", pass_context=True, no_pm=True)
	async def welcomemsg_disable(self, ctx):
		"""
		⚔ Removes/disables all welcome messages.

		--------------------
		  USAGE: welcomemsg disable
		EXAMPLE: welcomemsg disable
		--------------------
		"""
		welcome_json = pingbot.Config('./user/cogs/admin/admin_info.json').load_json()
		if ctx.message.channel.id not in welcome_json["welcome_messages"]:
			await text("No welcome messages have been added to this channel.", emoji="failure")
			return
		welcome_json["welcome_messages"].pop(ctx.message.channel.id)
		pingbot.Config('./user/cogs/admin/admin_info.json').write_json(welcome_json)
		await text("Successfully removed all welcome messages from this channel.", emoji="success")

	@welcomemsg.command(name="all", aliases=["view"], pass_context=True, no_pm=True)
	async def welcomemsg_view_all(self, ctx):
		"""
		⚔ Views all welcome messages added to the current channel as well as their index.

		--------------------
		  USAGE: welcomemsg all
		EXAMPLE: welcomemsg all
		--------------------
		"""
		welcome_json = pingbot.Config('./user/cogs/admin/admin_info.json').load_json()
		if ctx.message.channel.id not in welcome_json["welcome_messages"]:
			await text("No welcome messages have been added to this server.", emoji="success")
			return

		msgs = []
		for msg in welcome_json["welcome_messages"][ctx.message.channel.id]:
			msgs.append("(`{}`) {}".format(welcome_json["welcome_messages"][ctx.message.channel.id].index(msg), msg))

		fmt = "There are {} welcome messages set in this channel: {}".format(len(msgs), ', '.join(msgs))
		if len(fmt) >= 2000:
			await text("There are {} welcome messages set in this channel. Since the length of the message(s) exceed the message word count (2000), I will not output the messages.".format(len(msgs)))
			return

		await text(fmt)

	@commands.group(pass_context=True, aliases=["leave_msg", "leave-msg"], no_pm=True)
	@pingbot.permissions.has_permissions(manage_channels=True)
	async def leavemsg(self, ctx):
		"""
		⚔ Leave message management command.

		--------------------
		  USAGE: leavemsg <subcommand>
		EXAMPLE: leavemsg add
		--------------------
		"""
		if ctx.invoked_subcommand is None:
			await text("You must provide a subcommand.", emoji="failure")

	@leavemsg.command(name="add", pass_context=True, no_pm=True)
	async def leavemsg_add(self, ctx, channel : discord.Channel, *, leave_message : str):
		"""
		⚔ Adds a leave message to a channel.

		--------------------
		  USAGE: leavemsg add <channel> <leave message>
		EXAMPLE: leavemsg add #general {0} has left the server!
		--------------------
		"""
		leave_json = pingbot.Config('./user/cogs/admin/admin_info.json').load_json()
		if channel.id not in leave_json["leave_messages"]:
			leave_json["leave_messages"][channel.id] = []
			leave_json["leave_messages"][channel.id].append(leave_message)
		elif leave_message not in leave_json["leave_messages"][channel.id]:
			leave_json["leave_messages"][channel.id].append(leave_message)
		else:
			await text("That message has already been added.", emoji="failure")
			return

		pingbot.Config('./user/cogs/admin/admin_info.json').write_json(leave_json)

		await text("Successfully added leave message.", emoji="success")

	@leavemsg.command(name="remove", pass_context=True, no_pm=True)
	async def leavemsg_remove(self, ctx, *, leave_message : str):
		"""
		⚔ Remove a leave message.

		--------------------
		  USAGE: leavemsg remove <exact string or index>
		EXAMPLE: leavemsg remove 0
		--------------------
		"""
		leave_json = pingbot.Config('./user/cogs/admin/admin_info.json').load_json()
		if ctx.message.channel.id not in leave_json["leave_messages"]:
			await text("No leave messages have been added to this channel.", emoji="failure")
			return
		elif leave_message not in leave_json["leave_messages"][ctx.message.channel.id]:
			await text("That leave message has not been added to this channel.", emoji="failure")
			return
		elif any(char in leave_message for char in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '/', '\\', '`', '[', ';', '.', ',', ']', '-', '=', '_', '+', '~', '{', '}', ':', "'", '"', '<', '>', '?', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')']):
			try:
				leave_index = int(leave_message)
			except ValueError:
				await text("That leave message has not been added to this channel.", emoji="failure")
				return

			try:
				leave_message = leave_json["leave_messages"][ctx.message.channel.id][leave_index]
			except IndexError:
				await text("Index is out of range.", emoji="failure")
				return

			leave_json["leave_messages"][ctx.message.channel.id].pop(leave_index)
		pingbot.Config('./user/cogs/admin/admin_info.json').write_json(leave_json)
		await text("Successfully removed message.", emoji="success")

	@leavemsg.command(name="disable", pass_context=True, no_pm=True)
	async def leavemsg_disable(self, ctx):
		"""
		⚔ Removes/disables all leave messages.

		--------------------
		  USAGE: leavemsg disable
		EXAMPLE: leavemsg disable
		--------------------
		"""
		leave_json = pingbot.Config('./user/cogs/admin/admin_info.json').load_json()
		if ctx.message.channel.id not in leave_json["leave_messages"]:
			await text("No welcome messages have been added to this channel.", emoji="failure")
			return
		leave_json["leave_messages"].pop(ctx.message.channel.id)
		pingbot.Config('./user/cogs/admin/admin_info.json').write_json(leave_json)
		await text("Successfully removed all leave messages from this channel.", emoji="success")

	@leavemsg.command(name="all", aliases=["view"], pass_context=True, no_pm=True)
	async def leavemsg_view_all(self, ctx):
		"""
		⚔ Views all leave messages added to the current channel as well as their index.

		--------------------
		  USAGE: leavemsg all
		EXAMPLE: leavemsg all
		--------------------
		"""
		leave_json = pingbot.Config('./user/cogs/admin/admin_info.json').load_json()
		if ctx.message.channel.id not in leave_json["leave_messages"]:
			await text("No leave messages have been added to this server.", emoji="success")
			return

		msgs = []
		for msg in leave_json["leave_messages"][ctx.message.channel.id]:
			msgs.append("(`{}`) {}".format(leave_json["leave_messages"][ctx.message.channel.id].index(msg), msg))

		fmt = "There are {} leave messages set in this channel: {}".format(len(msgs), ', '.join(msgs))
		if len(fmt) >= 2000:
			await text("There are {} leave messages set in this channel. Since the length of the message(s) exceed the message word count (2000), I will not output the messages.".format(len(msgs)))
			return

		await text(fmt)

	@commands.group(pass_context=True, no_pm=True)
	@pingbot.permissions.has_permissions(manage_roles=True)
	async def autorole(self, ctx):
		"""
		⚔ Automatic role assigner management command.

		--------------------
		  USAGE: autorole <subcommand>
		EXAMPLE: autorole add
		--------------------
		"""
		if ctx.invoked_subcommand is None:
			await text("You must provide a subcommand.")

	@autorole.command(name="add", pass_context=True, no_pm=True)
	async def autorole_add(self, ctx, *, role_name : str):
		"""
		⚔ Add a role to the list of auto-roles.

		--------------------
		  USAGE: autorole add <role name or ID>
		EXAMPLE: autorole add Member
		--------------------
		"""
		autorole_json = pingbot.Config('./user/cogs/admin/admin_info.json').load_json()
		if ctx.message.server.id not in autorole_json["auto_roles"]:
			autorole_json["auto_roles"][ctx.message.server.id] = []
			autorole_json["auto_roles"][ctx.message.server.id].append(role_name)
		elif role_name not in autorole_json["auto_roles"][ctx.message.server.id]:
			autorole_json["auto_roles"][ctx.message.server.id].append(role_name)

		else:
			await text("That role has already been added.", emoji="failure")
			return

		pingbot.Config('./user/cogs/admin/admin_info.json').write_json(autorole_json)
		await text("Successfully added role!", emoji="success")

	@autorole.command(name="remove", aliases=["rem", "rm"], pass_context=True, no_pm=True)
	async def autorole_remove(self, ctx, *, role_name : str):
		"""
		⚔ Add a role to the list of auto-roles.

		--------------------
		  USAGE: autorole add <role name or ID>
		EXAMPLE: autorole add Member
		--------------------
		"""
		autorole_json = pingbot.Config('./user/cogs/admin/admin_info.json').load_json()
		if ctx.message.server.id not in autorole_json["auto_roles"]:
			await text("No roles have been added on this server.", emoji="failure")
			return
		elif role_name not in autorole_json["auto_roles"][ctx.message.server.id]:
			await text("That role doesn't exist.", emoji="failure")
			return
		elif any(char in role_name for char in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '/', '\\', '`', '[', ';', '.', ',', ']', '-', '=', '_', '+', '~', '{', '}', ':', "'", '"', '<', '>', '?', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')']):
			try:
				role_index = int(role_name)
			except ValueError:
				await text("That role doesn't exist..", emoji="failure")
				return

			try:
				role = autorole_json["auto_roles"][ctx.message.server.id][role_index]
			except IndexError:
				await text("Index is out of range.", emoji="failure")
				return

			autorole_json["auto_roles"][ctx.message.server.id].pop(role_index)
		pingbot.Config('./user/cogs/admin/admin_info.json').write_json(autorole_json)
		await text("Successfully removed role.", emoji="success")

	@autorole.command(name="disable", pass_context=True, no_pm=True)
	async def autorole_disable(self, ctx):
		"""
		⚔ Removes/disables all automatic roles.

		--------------------
		  USAGE: autorole disable
		EXAMPLE: autorole disable
		--------------------
		"""
		autorole_json = pingbot.Config('./user/cogs/admin/admin_info.json').load_json()
		if ctx.message.server.id not in autorole_json["auto_roles"]:
			await text("No roles have been added to this server.", emoji="failure")
			return
		autorole_json["auto_roles"].pop(ctx.message.server.id)
		pingbot.Config('./user/cogs/admin/admin_info.json').write_json(autorole_json)
		await text("Successfully removed all roles from this server.", emoji="success")

	@autorole.command(name="all", aliases=["view"], pass_context=True, no_pm=True)
	async def autorole_view_all(self, ctx):
		"""
		⚔ Views all auto-roles that have been added.

		--------------------
		  USAGE: autorole all
		EXAMPLE: autorole all
		--------------------
		"""
		autorole_json = pingbot.Config('./user/cogs/admin/admin_info.json').load_json()
		if ctx.message.server.id not in autorole_json["auto_roles"]:
			await text("No roles have been added to this server.", emoji="failure")
			return

		msgs = []
		for msg in autorole_json["auto_roles"][ctx.message.server.id]:
			msgs.append("(`{}`) {}".format(autorole_json["auto_roles"][ctx.message.server.id].index(msg), msg))

		fmt = "There are {} added auto-roles: {}".format(len(msgs), ', '.join(msgs))

		await text(fmt)

	@commands.command(name="votekick", pass_context=True, no_pm=True)
	async def _votekick_start(self, ctx, member : discord.Member, reason : str=None):
		"""
		⚔ Starts a votekick against a member.

		--------------------
		  USAGE: votekick <member name or mention> <optional: reason>
		EXAMPLE: votekick Bot
		--------------------
		"""
		await text("This feature is still being worked on.", emoji="failure")
		
	async def admin_member_join(self, member):
		"""
		on_member_join listener.
		"""
		admin_json = pingbot.Config('./user/cogs/admin/admin_info.json').load_json()
		welcome_messages = admin_json["welcome_messages"]
		for channel in member.server.channels:
			if channel.id in welcome_messages:
				welcome_msg = random.choice(welcome_messages[channel.id])
				if '{' in welcome_msg and '}' in welcome_msg:
					fmt = welcome_msg.format(member)
				else:
					fmt = welcome_msg
				await text(fmt, no_bold=True, no_mention=True, channel=channel)
				break

		if len(admin_json["auto_roles"]) > 0 and member.server.id in admin_json["auto_roles"]:
			for _role in admin_json["auto_roles"][member.server.id]:
				role = pingbot.utils.get_role_by_name(_role, member.server)
				if role:
					await self.bot.add_roles(member, role)

	async def admin_member_remove(self, member):
		"""
		on_member_remove listener.
		"""
		leave_messages = pingbot.Config('./user/cogs/admin/admin_info.json').load_json()["leave_messages"]
		for channel in member.server.channels:
			if channel.id in leave_messages:
				leave_msg = random.choice(leave_messages[channel.id])
				if '{' in leave_msg and '}' in leave_msg:
					fmt = leave_msg.format(member)
				else:
					fmt = leave_msg
				await text(fmt, no_bold=True, no_mention=True, channel=channel)
				return

def setup(bot):
	bot.add_listener(Admin(bot).admin_member_join, 'on_member_join')
	bot.add_listener(Admin(bot).admin_member_remove, 'on_member_remove')
	bot.add_cog(Admin(bot))