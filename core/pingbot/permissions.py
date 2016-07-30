"""
PingBot Permissions Checking Module
------------
The functions checks if any of the member's roles has the permission.

(Some of the functions will be modified later as they somewhat dont work.)
"""

from core import pingbot
from discord.ext import commands
import discord

class BasePermError(Exception):
	pass

class NotBotOwner(BasePermError):
	"""
	Called when is_bot_owner returns false
	"""
	pass

class NotServerOwner(BasePermError):
	"""
	Called when is_serv_owner returns false
	"""
	pass

class NotAdmin(BasePermError):
	"""
	Called when is_administrator returns false
	"""
	pass

def is_bot_owner(**kwargs):
	def predicate(ctx):
		member = kwargs.get("member", ctx.message.author)
		return _is_bot_owner(member)
	return commands.check(predicate)

def is_serv_owner(**kwargs):
	def predicate(ctx):
		member = kwargs.get("member", ctx.message.author)
		return _is_serv_owner(member, ctx)
	return commands.check(predicate)

def is_administrator(**kwargs):
	def predicate(ctx):
		member = kwargs.get("member", ctx.message.author)
		return _is_administrator(member)
	return commands.check(predicate)

def _is_bot_owner(member):
	"""
	Checks if the member is a bot owner.
	"""
	if isinstance(member, str):
		member_id = member
	else:
		member_id = member.id
	bot_owners = pingbot.Config("./user/config/bot.json").load_json()["bot_owners"]
	if member_id not in bot_owners:
		return False
	else:
		return True

def _is_serv_owner(member, ctx):
	"""
	Checks if the member is the server owner.
	"""
	if not ctx.message.channel.is_private:
		if member == ctx.message.server.owner:
			return True
		else:
			return False
	else:
		return True

def _is_administrator(member):
	"""
	Checks if the member is an administrator.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.administrator:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def has_permissions(**perms):
	def predicate(ctx):
		member = perms.get("member", ctx.message.author)
		no_cmd_check = perms.get("no_d_cmd_check", True)
		if _is_bot_owner(member):
			return True
		if _is_serv_owner(member, ctx):
			return True
		if _is_administrator(member):
			return True

		if no_cmd_check == True:
			server_json = pingbot.Config('./user/config/server.json').load_json()
			if ctx.message.server.id not in server_json:
				pass
			elif ctx.message.channel.id not in server_json[ctx.message.server.id]["channels"]:
				pass
			elif "members" in server_json[ctx.message.server.id] and member.id not in server_json[ctx.message.server.id]["members"]:
				pass
			elif ctx.command.name in server_json[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"] or "members" in server_json[ctx.message.server.id] and ctx.command.name in server_json[ctx.message.server.id]["members"][member.id]["disabled_commands"]:
				raise commands.DisabledCommand("Command '{}' is disabled!".format(ctx.command))
			
		channel = ctx.message.channel
		resolved = channel.permissions_for(member)
		return all(getattr(resolved, name, None) == value for name, value in perms.items())

	return commands.check(predicate)

def _has_permissions(ctx, **perms):
	"""
	Normal function of has_permissions wrapper.
	"""
	member = perms.get("member", ctx.message.author)
	if _is_bot_owner(member):
		return True
	if _is_serv_owner(member, ctx):
		return True
	if _is_administrator(member):
		return True

	if no_cmd_check == True:
		server_json = pingbot.Config('./user/config/server.json').load_json()
		if ctx.message.server.id not in server_json:
			pass
		elif ctx.message.channel.id not in server_json[ctx.message.server.id]["channels"]:
			pass
		elif member.id not in server_json[ctx.message.server.id]["members"]:
			pass
		elif ctx.command.name in server_json[ctx.message.server.id]["channels"][ctx.message.channel.id]["disabled_commands"] or ctx.command.name in server_json[ctx.message.server.id]["members"][member.id]["disabled_commands"]:
			raise commands.DisabledCommand("Command '{}' is disabled!".format(ctx.command))
			
	channel = ctx.message.channel
	resolved = channel.permissions_for(member)
	return all(getattr(resolved, name, None) == value for name, value in perms.items())

def can_create_invite(member):
	"""
	Checks if the member can create an instant invite.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.create_instant_invite:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_kick(member):
	"""
	Checks if the member can kick members.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.kick_members:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_ban(member):
	"""
	Checks if the member can ban members.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.ban_members:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_mc(member):
	"""
	Checks if the member can manage channels.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.manage_channels:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_ms(member):
	"""
	Checks if the member can manage the server.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.manage_server:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_read(member):
	"""
	Checks if the member can read messages.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.read_messages:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_send(member):
	"""
	Checks if the member can send messages.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.send_messages:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_send_tts(member):
	"""
	Checks if the member can send TTS messages.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.send_tts_messages:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_mm(member):
	"""
	Checks if the member can manage messages.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.manage_messages:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_embed(member):
	"""
	Checks if the member can embed links.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.embed_links:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_attach(member):
	"""
	Checks if the member can attach files to their messages.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.attach_files:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_read_history(member):
	"""
	Checks if the member can read the chat history.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.read_message_history:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_mention_everyone(member):
	"""
	Checks if the member can mention everyone.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.mention_everyone:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_connect(member):
	"""
	Checks if the member can connect to a voice channel.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.connect:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_speak(member):
	"""
	Checks if the member can speak in a voice channel.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.speak:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_mute(member):
	"""
	Checks if the member can mute members.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.mute_members:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_deafen(member):
	"""
	Checks if the member can deafen members.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.deafen_members:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_move_members(member):
	"""
	Checks if the member can move members.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.move_members:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_use_voice(member):
	"""
	Checks if the member can use voice activation in a voice channel.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.use_voice_activation:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_change_nick(member):
	"""
	Checks if the member can change their nickname on the server.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.change_nicknames:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_manage_nicks(member):
	"""
	Checks if the member can manage other member's nicknames on the server.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.manage_nicknames:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True

def can_manage_roles(member):
	"""
	Checks if the member can manage roles.
	"""
	can = []
	try:
		for role in member.roles:
			if role.permissions.manage_roles:
				can.append("True")
	except AttributeError:
		return True

	if len(can) == 0:
		return False
	else:
		return True