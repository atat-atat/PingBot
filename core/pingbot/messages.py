"""
PingBot Message Utilities.
"""

from core import pingbot
import __main__
from discord.ext.commands import bot

async def send_help_message(ctx, command=None, **kwargs):
	"""
	Sends the help message.
	"""
	channel = kwargs.get("channel", bot._get_variable('_internal_channel'))
	no_pm = kwargs.get("no_pm", False)
	_bot = kwargs.get("bot", __main__.return_client_object())

	if command == None:
		pages = _bot.formatter.format_help_for(ctx, _bot)
		fmt = pingbot.get_message("help_msg_sent")
	else:
		if isinstance(command, str):
			if command in _bot.commands:
				pages = _bot.formatter.format_help_for(ctx, _bot.commands.get(command))
				fmt = pingbot.get_message("help_cmd_sent").format(command)
			else:
				await pingbot.messages.text(pingbot.get_message("help_cmd_not_found"), channel=channel, emoji="failure", **kwargs)
				return
		else:
			pages = _bot.formatter.format_help_for(ctx, command)
			fmt = pingbot.get_message("help_cmd_sent").format(command)

	if not ctx.message.channel.is_private and no_pm != True:
		await pingbot.messages.text(fmt, channel=channel, emoji="robot", **kwargs)

	if no_pm == True:
		for page in pages:
			await _bot.send_message(ctx.message.channel, page)
	else:
		for page in pages:
			await _bot.send_message(ctx.message.author, page)

async def get_help(ctx, command=None, **kwargs):
	"""
	Returns the help pages regarding all/a command(s).
	"""
	_bot = kwargs.get("bot", __main__.return_client_object()) #if no bot object is provided, then get the client object from bot.py

	if command == None:
		pages = _bot.formatter.format_help_for(ctx, _bot)

	else:
		if command in bot.commands:
			pages = _bot.formatter.format_help_for(ctx, _bot.commands.get(command))
		else:
			return None

	return pages

async def text(string, **kwargs):
	"""
	Short version of Utils().text
	"""
	client = __main__.return_client_object()

	extensions = ('delete_after',)
	params = {
		k: kwargs.pop(k, None) for k in extensions
	}

	channel = kwargs.get("channel", bot._get_variable('_internal_channel')) #set the channel
	emoji = kwargs.get("emoji", None) #set the beginning emoji
	no_mention = kwargs.get("no_mention", False) #set whether the bot should not mention the author
	no_bold = kwargs.get("no_bold", False)
	if 'http' in string or '*' in string:
		no_bold = True
	no_message_limiter = kwargs.get("no_message_limiter", False)

	no_auto_capitalizer = kwargs.get("no_auto_cap", False)
	if not no_auto_capitalizer and not no_mention:
		if not string[0].lower() == 'i':
			string = string[0].lower() + string[1:]

	if isinstance(emoji, str) and emoji != None and not emoji.startswith(":"):
		if emoji in pingbot.Config("./core/data/emoji.json").load_json():
			emoji = pingbot.Config("./core/data/emoji.json").load_json()[emoji]

	if isinstance(channel, str):
		o_channel = channel
		channel = client.get_channel(channel)
		if channel == None:
			raise pingbot.errors.PingBotError("Unable to find channel {} :(".format(o_channel))

	if no_mention == False:
		mention_user = kwargs.get("mention_user", bot._get_variable('_internal_author')) #if no_mention is set to False (by default,) then have the ability to set the user to mention (defaults to message author) (if you are providing a member/user object, do not add the ``mention`` property, just include the object since it automatically gets the mention property.)
		#if isinstance(mention_user, str):
		mention_format = "{},".format(mention_user)
		#else:
		#	try:
		#		mention_format = mention_user.mention
		#	except AttributeError:
		#		mention_format = mention_user

	if no_bold == False:
		if emoji != None:
			if no_mention == False:
				if string.endswith('```'):
					#if no_mention is set to False, then mention the member/user
					fmt = "{} **{} {}**".format(emoji, mention_format, string) #dont mind this
				else:
					fmt = "{} **{} {}**".format(emoji, mention_format, string)
			else:
				fmt = "{} **{}**".format(emoji, string) #do the opposite
		else:
			if no_mention == False:
				if string.endswith('```'):
					fmt = "**{}** {}".format(mention_format, string) #same thing here
				else:
					fmt = "**{} {}**".format(mention_format, string)
			else:
				fmt = "**{}**".format(string)
	else:
		if emoji != None:
			if no_mention == False:
				if string.endswith('```'):
					#if no_mention is set to False, then mention the member/user
					fmt = "{} {}".format(emoji, string) #dont mind this
				else:
					fmt = "{} **{}** {}".format(emoji, mention_format, string)
			else:
				fmt = "{} {}".format(emoji, string) #do the opposite
		else:
			if no_mention == False:
				if string.endswith('```'):
					fmt = "**{}**{}".format(mention_format, string) #same thing here
				else:
					fmt = "**{}** {}".format(mention_format, string)
			else:
				fmt = "{}".format(string)
	
	if no_message_limiter == False:
		if len(fmt) >= 2000:
			chunks = pingbot.Utils().string_chunk(fmt, 1000)
			for chunk in chunks:
				await client.send_message(channel, chunk)
		else:
			await client.send_message(channel, fmt)
	else:
		await client.send_message(channel, fmt)

async def whisper(string, **kwargs):
	"""
	Whispers to a member (or the message author.)
	"""
	bot = kwargs.get("bot", __main__.return_client_object())
	emoji = kwargs.get("emoji", '')
	no_bold = kwargs.get("no_bold", False)
	no_mention = kwargs.get("no_mention", False)
	mention_user = kwargs.get("mention_user", False)
	user = kwargs.get("user", bot._get_variable('_internal_author'))

	await text(string, emoji=emoji, no_bold=no_bold, no_mention=no_mention, mention_user=mention_user, user=user)