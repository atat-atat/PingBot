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

	@commands.command(pass_context=True, name="set-log", aliases=["set_log"])
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

	@commands.command(pass_context=True, name="set-status", aliases=["set_status"])
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
		  USAGE: toggle-command <command> <optional: member name or mention>
		EXAMPLE: toggle-command rule34
		--------------------
		"""
		server_config = pingbot.Config("./user/config/server.json").load_json()
		if command not in self.bot.commands: #if the command doesn't exist.
			await text(pingbot.get_message("toggle_command_not_found"), emoji="failure")
			return

		if command in pingbot.Config("./core/data/system.json").load_json()["no_disable"]: #make sure the user doesnt try disabling something like the help command or this command.
			await text(pingbot.get_message("toggle_command_cannot_be_toggled"), emoji="failure")
			return

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
	@pingbot.permissions.has_permissions()
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
				await text(pingbot.get_message("iam_role_botowner_error"), emoji="failure")
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

def setup(bot):
	bot.add_cog(Admin(bot))