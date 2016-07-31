#from core.pingbot.bot_setup import Start
#Start().start() #start welcome procedure

from core.pingbot.bot_setup import checkup

checkup()

from discord.ext import commands
from core import pingbot
from core.pingbot.messages import text, send_help_message, get_help
import asyncio
import sys
import importlib
import os
import traceback
import datetime
import random
import discord
import json
import logging

global_sett_dir = "./user/config/bot.json"
settings = pingbot.Config(global_sett_dir).load_json()

client = commands.Bot(command_prefix=settings["prefix"], description="PingBot -- A multifunctional mechanical robot.", pm_help=True)
client.prefix = settings["prefix"]

emoji = pingbot.Config("./core/data/emoji.json")
now = datetime.datetime.now()
date = now.strftime("%Y-%m-%d %H-%M")
loop = asyncio.get_event_loop()

debug = pingbot.Utils().check_start_arg("debug")
ignore_exit = pingbot.Utils().check_start_arg("ignore_exit")

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.CRITICAL)
log = logging.getLogger()
log.setLevel(logging.INFO)
handler = logging.FileHandler(filename='./user/logs/{}.log'.format(date), encoding='utf-8', mode='w+')
log.addHandler(handler)

if pingbot.Utils().cog_exists('personal'):
	from user.cogs.personal.personal import send_error

if pingbot.Utils().cog_exists('fun'):
	from user.cogs.fun.fun import Fun

client.remove_command('help')

@client.event
async def on_ready():
	if not hasattr(client, 'uptime'):
		client.uptime = datetime.datetime.utcnow()

	try:
		client.load_extension("core.data.system") #load the system cog first
		pingbot.Utils().cprint("green", "[LOG]: Successfully loaded system cog.") #indicate that everything went well with this task
	except:
		pingbot.Utils().cprint("red", "[ERROR]: Failed to load the system cog.") #
		pingbot.Utils().cprint("red", "[UNEXPECTED ERROR]: {}".format(pingbot.Errors().get_traceback(*sys.exc_info())))
		if ignore_exit == False:
			sys.exit(1) #close it because the system cog is really important.
	load_from_cogs_folder()

	if client.user.bot:
		await client.edit_profile(username=settings["username"])
	else:
		await client.edit_profile(username=settings["username"], password=settings["password"])
	b_version = pingbot.Config().load_json("./core/data/system.json")["system_version"]
	if client.user.bot:
		acc_type = "Bot"
	else:
		acc_type = "User"
	members = 0
	servers = []
	for server in client.servers:
		members += server.member_count
		try:
			invite = await client.create_invite(server)
			servers.append("	- {}/{} - {} ({} players)\n".format(server.name, server.id, invite, server.member_count))
		except discord.errors.Forbidden:
			servers.append("	- {}/{} - unavailable ({} players)\n".format(server.name, server.id, server.member_count))
		
	if len(client.servers) == 1: #grammar corrector
		server_text = "server"
	else:
		server_text = "servers"

	if len(client.extensions)-1 == 1: #grammar corrector
		cog_text = "cog"
	else:
		cog_text = "cogs"
	if debug == False:
		pingbot.Utils().clear() #clear past console logs
	pingbot.Utils().cprint("cyan", """Running version, {0}!
Loaded {1} {2}!
-------------------
Name: {3.user.name}
ID: {3.user.id}
Discrim: {3.user.discriminator}
Account Type: {4}

Currently connected to {5} {6} ({7} players!)
{8}""".format(b_version, len(client.extensions)-1, cog_text, client, acc_type, len(client.servers), server_text, members, "\n".join(servers)))
	server_config = pingbot.Config("./user/config/server.json").load_json()
	for server in client.servers:
		if server not in server_config:
			pingbot.Utils().setup_server_section(server) #set the servers up
		for channel in server.channels:
			pingbot.Utils().channel_checkup(channel) #set the channels up

	await nsfw_check()
	await feed_check()
	await stream_check()
	await git_check()

@client.event
async def on_message(msg):
	if msg.channel.is_private: #display recent messages in the console
		output = "[LOG][{}][Private Message][{}/{}]: {}".format(msg.timestamp, msg.author.name, msg.author.id, msg.content)
		cmd_output = "[COMMAND][{}][Private Message]: {} ({}) executed custom command: ".format(msg.timestamp, msg.author.name, msg.author.id)
	else:
		output = "[LOG][{}][{}/{}][{}/{}]: {}".format(msg.timestamp, msg.server.name, msg.channel.name, msg.author.name, msg.author.id, msg.content)
		cmd_output = "[COMMAND][{}][{}/{}]: {} ({}) executed custom command: ".format(msg.timestamp, msg.server.name, msg.channel.name, msg.author.name, msg.author.id)

	pingbot.Utils().cprint("white", output)

	bot_json = pingbot.Config("./user/config/bot.json").load_json()
	if isinstance(bot_json["prefix"], list):
		cmd_prefix = tuple(bot_json["prefix"])
	else:
		cmd_prefix = bot_json["prefix"]

	if msg.content.startswith(cmd_prefix):
		command = msg.content[len(cmd_prefix):]
		command = command.split()[0]
		if command in pingbot.Config("./user/cogs/fun/customcommands.json").load_json():
			if msg.author.id not in pingbot.Config("./user/cogs/fun/customcommands.json").load_json()[command]["disabled"] and msg.channel.id not in pingbot.Config("./user/cogs/fun/customcommands.json").load_json()[command]["disabled"]:
				pingbot.Utils().cprint("green", cmd_output + command)

	server_config = pingbot.Config("./user/config/server.json").load_json()
	if not msg.channel.is_private and msg.server.id in server_config:
		if msg.channel.id in server_config[msg.server.id]["channels"]:
			if pingbot.utils.extract_command(msg.content) not in server_config[msg.server.id]["channels"][msg.channel.id]["disabled_commands"]:
				await client.process_commands(msg)
			else:
				await client.send_message(msg.channel, ":thumbsdown: **That command is disabled for this channel.**")
		elif "members" in server_config[msg.server.id]:
			if msg.author.id in server_config[msg.server.id]["members"] and pingbot.utils.extract_command(msg.content) not in server_config[msg.server.id]["members"][author.id]["disabled_commands"]:
				await client.process_commands(msg)
			else:
				await client.send_message(msg.channel, ":thumbsdown: **That command is disabled for you.**")
	else:
		await client.process_commands(msg)

@client.event
async def on_command(command, ctx): #log executed commands
	if ctx.message.channel.is_private:
		pingbot.Utils().cprint("green", "[COMMAND][{}][Private Message]: {} ({}) executed command: {}".format(ctx.message.timestamp, ctx.message.author.name, ctx.message.author.id, command.name))
	else:
		pingbot.Utils().cprint("green", "[COMMAND][{}][{}/{}]: {} ({}) executed command: {}".format(ctx.message.timestamp, ctx.message.server.name, ctx.message.channel.name, ctx.message.author.name, ctx.message.author.id, command.name))

	log.info('{0.timestamp}: {0.author} in {1}: {0.content}'.format(ctx.message, ctx.message.channel))

if not debug:
	@client.event
	async def on_command_error(error, ctx):
		if isinstance(error, commands.errors.CheckFailure):
			await text(pingbot.get_error("no_permission"), channel=ctx.message.channel, mention_user=ctx.message.author, emoji="failure")
		elif isinstance(error, commands.NoPrivateMessage):
			await text(pingbot.get_error("no_pm"), channel=ctx.message.channel, mention_user=ctx.message.author, emoji="failure")
		elif isinstance(error, commands.MissingRequiredArgument):
			if ctx.invoked_subcommand:
				await send_help_message(ctx, command=ctx.invoked_subcommand, channel=ctx.message.channel, mention_user=ctx.message.author, no_pm=True, bot=client)
			else:
				await send_help_message(ctx, command=ctx.command, channel=ctx.message.channel, mention_user=ctx.message.author, no_pm=True, bot=client)
		elif isinstance(error, commands.BadArgument):
			if ctx.invoked_subcommand:
				await send_help_message(ctx, command=ctx.invoked_subcommand, channel=ctx.message.channel, mention_user=ctx.message.author, no_pm=True, bot=client)
			else:
				await send_help_message(ctx, command=ctx.command, channel=ctx.message.channel, mention_user=ctx.message.author, no_pm=True, bot=client)
		elif isinstance(error, commands.errors.CommandNotFound):
			pass #ignore no command errors
		elif isinstance(error, commands.DisabledCommand):
			await text(pingbot.get_message("command_disabled"), channel=ctx.message.channel, mention_user=ctx.message.author, emoji="failure")
		elif isinstance(error, pingbot.errors.CommandDisabledUser):
			await text(pingbot.get_message("command_disabled_user"), channel=ctx.message.channel, mention_user=ctx.message.author, emoji="failure")
		
		elif isinstance(error, BaseException):
			pingbot.Utils().cprint("red", pingbot.errors.get_traceback())
		
			if "error_channel" in pingbot.Config("./user/config/bot.json").load_json():
				if ctx.message.channel.is_private:
					await text(pingbot.get_message("error_extra_pm").format(ctx, pingbot.errors.get_traceback()), channel=pingbot.Config("./user/config/bot.json").load_json()["error_channel"], emoji="error", no_mention=True)
				else:
					await text(pingbot.get_message("error_extra").format(ctx, pingbot.errors.get_traceback()), channel=pingbot.Config("./user/config/bot.json").load_json()["error_channel"], emoji="error", no_mention=True)


@client.event
async def on_server_join(server):
	pingbot.Utils().setup_server_section(server) #set the server up

@client.event
async def on_server_remove(server):
	pingbot.Utils().server_section_flush(server)

@client.event
async def on_server_update(before, after):
	server_config = pingbot.Config("./user/config/server.json").load_json()
	mod_channel = server_config[after.id]["mod_channel"]
	changed_items = pingbot.Utils().return_what_updated_server(before, after)

	if mod_channel != None and len(changed_items) > 0:
		await text(pingbot.get_event_message("server_update").format(', '.join(changed_items), pingbot.Utils().return_server_info(after)), channel=mod_channel, emoji="server_update", no_mention=True)

	#await pingbot.Utils(client).text_mod("Server has been modified!\nThe following has been changed: {}\n{}".format(', '.join(changed_items), pingbot.Utils().return_server_info(after)), mod_channel, emoji="server_update")

@client.event
async def on_channel_create(channel):
	if not channel.is_private:
		mod_channel = pingbot.Config("./user/config/server.json").load_json()[channel.server.id]["mod_channel"]
		if mod_channel != None:
			await text(pingbot.get_event_message("channel_create").format(channel.name, pingbot.Utils().return_channel_info(channel)), channel=mod_channel, emoji="channel_create", no_mention=True)

		#await pingbot.Utils(_client).text_mod_chan("Channel `{}` has been created!\n{}".format(channel.name, pingbot.Utils().return_channel_info(channel)), channel, emoji="channel_create")
		pingbot.Utils().channel_checkup(channel)

@client.event
async def on_channel_delete(channel):
	mod_channel = pingbot.Config("./user/config/server.json").load_json()[channel.server.id]["mod_channel"]
	if mod_channel != None:
		await text(pingbot.get_event_message("channel_delete").format(channel.name), channel=mod_channel, emoji="channel_remove", no_mention=True)
	#await pingbot.Utils(_client).text_mod_chan("Channel `{}` was deleted!".format(channel.name), channel, emoji="channel_remove")
	pingbot.Utils().channel_flush(channel)

@client.event
async def on_channel_update(before, after):
	changed_items = pingbot.Utils().return_what_updated_channel(before, after)
	mod_channel = pingbot.Config("./user/config/server.json").load_json()[after.server.id]["mod_channel"]
	if mod_channel != None and len(changed_items) > 0:
		await text(pingbot.get_event_message("channel_update").format(before.name, ', '.join(changed_items), pingbot.Utils().return_channel_info(after)), channel=mod_channel, emoji="channel_update", no_mention=True)
	#await pingbot.Utils(client).text_mod_chan("Channel `{}` was modified!\nThe following has been changed: {}\n{}".format(before.name, ', '.join(changed_items), pingbot.Utils().return_channel_info(after)), after, emoji="channel_update")

@client.event
async def on_member_join(member):
	mod_channel = pingbot.Config("./user/config/server.json").load_json()[member.server.id]["mod_channel"]
	if mod_channel != None:
		await text(pingbot.get_event_message("member_join").format(member, member.id, pingbot.Utils().return_member_info(member)), channel=mod_channel, emoji="member_join", no_mention=True)
	#await pingbot.Utils(_client).text_mod_member("Member `{}` (`{}`) has joined!\n{}".format(member, member.id, pingbot.Utils().return_member_info(member)), member, emoji="member_join")

@client.event
async def on_member_remove(member):
	mod_channel = pingbot.Config("./user/config/server.json").load_json()[member.server.id]["mod_channel"]
	if mod_channel != None:
		await text(pingbot.get_event_message("member_remove").format(member), channel=mod_channel, emoji="member_leave", no_mention=True)
	#await pingbot.Utils(_client).text_mod_member("Member `{}` has left the server.".format(member.name), member, emoji="member_leave")

@client.event
async def on_member_update(before, after):
	pingbot.Utils().server_checkup(after.server)
	server_config = pingbot.Config("./user/config/server.json").load_json()

	status_channel = server_config[after.server.id]["status_channel"]
	if before.nick != None:
		start_fmt = pingbot.get_event_message("start_fmt_with_nick").format(before, before.nick)
	else:
		start_fmt = pingbot.get_event_message("start_fmt_no_nick").format(before)

	if before != client.user or after != client.user and not before.bot and not after.bot:
		if status_channel != None:
			if before.name != after.name:
				if status_channel != None:
					await text(start_fmt + pingbot.get_event_message("member_name_update").format(after.name), channel=status_channel, emoji="member_update_name", no_mention=True)
					#await pingbot.Utils(_client).text_status("Member `{}` changed his/her name from {} to {}!".format(before.name, before.name, after.name), status_channel, emoji="member_update_name")
			elif before.game != after.game:
				if after.game != None :
					if status_channel != None:
						if not pingbot.Utils().cog_exists('fun'):
							await text(start_fmt + pingbot.get_event_message("member_game_update").format(after.game.name), channel=status_channel, emoji="member_update_game", no_mention=True)
							#await pingbot.Utils(client).text_status("Member `{}` is now playing `{}`".format(before.name, after.game.name), status_channel, emoji="member_update_game")
				else:
					await text(start_fmt + pingbot.get_event_message("member_game_update2").format(before.game.name), channel=status_channel, emoji="member_update_game", no_mention=True)
			elif before.nick != after.nick:
				if status_channel != None:
					if after.nick == None:
						await text(start_fmt + pingbot.get_event_message("member_nick_update"), channel=status_channel, emoji="member_update_name", no_mention=True)
						#await pingbot.Utils(client).text_status("Member `{}` has changed his/her nickname from {} to {}!".format(before.name, before.nick, after.nick), status_channel, emoji=emoji["member_update_name"])
						#await pingbot.Utils(_client).text_status("Member `{}` has reset his/her nickname!".format(before.name), status_channel, emoji=emoji["member_update_name"])
					else:
						await text(start_fmt + pingbot.get_event_message("member_nick_update2").format(after.nick), channel=status_channel, emoji="member_update_name", no_mention=True)
			elif before.avatar != after.avatar:
				#await pingbot.Utils(_client).text_mod("Member `{}` has changed his/her avatar to {}!".format(after.avatar_url), mod_channel)
				if status_channel != None:
					await text(start_fmt + pingbot.get_event_message("member_avatar_update").format(after.avatar_url), channel=status_channel, emoji="member_update_avatar", no_mention=True, no_bold=True)
					#await pingbot.Utils(_client).text_status("Member `{}` has changed his/her avatar to {}!".format(after.avatar_url), status_channel, emoji=emoji["member_update_avatar"])

@client.event
async def on_member_ban(member):
	mod_channel = pingbot.Config("./user/config/server.json").load_json()[member.server.id]["mod_channel"]

	if mod_channel != None:
		await text(pingbot.get_event_message("member_ban").format(member), channel=mod_channel, emoji="member_ban", no_mention=True)
	#await pingbot.Utils(client).text_mod_member("Member `{}` has been banned.", member, emoji="member_ban")

@client.event
async def on_member_unban(server, user):
	mod_channel = pingbot.Config("./user/config/server.json").load_json()[server.id]["mod_channel"]

	if mod_channel != None:
		await text(pingbot.get_event_message("member_unban").format(user), channel=mod_channel, emoji="member_unban", no_mention=True)
		#await pingbot.Utils(_client).text_mod("Member `{}` has been unbanned.", mod_channel, emoji="member_unban")

@client.command(name="help", aliases=["commands"], pass_context=True)
async def send_help_msg(ctx, command : str=None):
	"""
	⭐ Shows this message.

	--------------------
	  USAGE: help <optional: command name>
	EXAMPLE: help
	--------------------
	"""
	if command == None:
		await send_help_message(ctx, bot=client)
	else:
		await send_help_message(ctx, command=command, bot=client)

@client.command(pass_context=True, hidden=True)
@pingbot.permissions.is_bot_owner()
async def reload(ctx, *, cogs : str=None):
	"""
	⭐ Reloads all cogs from the cogs directory.

	--------------------
	  USAGE: reload <optional: list of cogs>
	EXAMPLE: reload
	--------------------
	"""
	if cogs != None:
		reload_cog = ''
		if ' ' in cogs:
			cogs = cogs.split(' ')

		if isinstance(cogs, list):
			reload_cog = []
			for cog in cogs:
				if os.path.isfile("./user/cogs/{0}/{0}.py".format(cog)):
					reload_cog.append("user.cogs.{0}.{0}".format(cog))
		else:
			if os.path.isfile("./user/cogs/{0}/{0}.py".format(cog)):
				reload_cog = "user.cogs.{0}.{0}".format(cog)
	else:
		reload_cog = []
		for file in os.listdir('./user/cogs'): #cycle through each file in the /cogs/ directory.
			if not file.startswith('_'):
				if os.path.isfile('./user/cogs/{0}/{0}.py'.format(file)):
					reload_cog.append("user.cogs.{0}.{0}".format(file))

	if isinstance(reload_cog, list):
		for cog in reload_cog:
			try:
				client.unload_extension(cog)
				client.load_extension(cog)
			except Exception as e:
				await text("```xl\n{}\n```".format(pingbot.errors.get_traceback()), emoji="failure")
				return

		await text("Successfully reloaded {} cogs!".format(len(reload_cog)), emoji="success")
	else:
		try:
			client.unload_extension(reload_cog)
			client.load_extension(reload_cog)
		except Exception as e:
			await text("```xl\n{}\n```".format(pingbot.errors.get_traceback()), emoji="failure")
			return

		await text("Successfully reloaded {}!".format(reload_cog), emoji="success")

def return_client_object():
	return client

def load_from_cogs_folder():
	found_cogs = []
	for file in os.listdir('./user/cogs'): #cycle through each file in the /cogs/ directory.
		if os.path.isfile('./user/cogs/{0}/{0}.py'.format(file)):
			found_cogs.append(file)

	if len(found_cogs) == 0: #if no cogs were found in the cogs folder
		pingbot.Utils().cprint('red', "[WARNING]: No cogs were found.")
	else:
		for cog in found_cogs:
			if not cog.startswith("_"):
				try:
					client.load_extension('user.cogs.{0}.{0}'.format(cog))
				except:
					pingbot.Utils().cprint("red", "UNEXPECTED ERROR:\n{}".format(pingbot.Errors().get_traceback(*sys.exc_info())))
					sys.exit(1)
				_cog = cog.replace(".", "/")
				try: #temporary thing, i know its terrible but ill fix it later
					cog_data = pingbot.Config("./user/cogs/{0}/{0}_info.json".format(_cog)).load_json()

					cog_name = cog_data.get("name", random.choice(["Unknown", "NA"]))
					cog_author = cog_data.get("author", random.choice(["Unknown", "NA"]))
					cog_version = cog_data.get("version", random.choice(["Unknown", "NA"]))
					cog_description = cog_data.get("description", random.choice(["Unknown", "NA"]))
				except FileNotFoundError:
					cog_name = random.choice(["Unknown", "NA"])
					cog_author = random.choice(["Unknown", "NA"])
					cog_version = "0.0"
					cog_description = "No description found."

				pingbot.Utils().cprint('green', "[LOG]: Loaded cog; {} by {} (v{}) -- {}".format(cog_name, cog_author, cog_version, cog_description))

async def bot_loop():
	games_list = pingbot.Config('./user/config/bot.json').load_json()["games"]
	await client.wait_until_ready()
	if pingbot.Utils().check_start_arg("no_game_loop"):
		return
	while not client.is_closed:
		await client.change_status(game=discord.Game(name=random.choice(games_list)))
		await asyncio.sleep(60)

async def nsfw_check():
	await client.wait_until_ready()
	if 'user.cogs.nsfw.nsfw' in client.extensions.keys(): #check if the NSFW cog is even installed.
		from user.cogs.nsfw.nsfw import NSFW
		loop.create_task(NSFW(client).auto_nsfw())

async def feed_check():
	await client.wait_until_ready()
	if 'user.cogs.feeds.feeds' in client.extensions.keys(): #same goes here
		from user.cogs.feeds.feeds import Feeds
		loop.create_task(Feeds(client).auto_feed())

async def stream_check():
	await client.wait_until_ready()
	if 'user.cogs.streams.streams' in client.extensions.keys():
		from user.cogs.streams.streams import Streams
		loop.create_task(Streams(client).stream_check())

async def git_check():
	await client.wait_until_ready()
	if 'user.cogs.github.github' in client.extensions.keys():
		from user.cogs.github.github import GitHub
		loop.create_task(GitHub(client).git_loop())

if __name__ == '__main__':
	client.client_id = settings["client_id"]

	loop.create_task(bot_loop())

	if "token" in settings:
		client.run(settings["token"])
	else:
		client.run(settings["email"], settings["password"])