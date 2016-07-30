"""
Initial PingBot Setup Procedure(s)
"""

import sys
import json
import re
import os

if os.name != 'posix': #if the code is being ran on an Android, then don't import pip as we have a different method to pip for Android machines.
	import pip

def check_dir(directory):
	if not os.path.exists(directory):
		if directory.startswith('.'):
			warn_directory = directory.replace('.', os.getcwd().replace('\\', '/'), 1)
		cprint("red", "WARNING: The directory, {} did not exist, so I have created the directory for you.".format(warn_directory))
		os.makedirs(directory)
		return False
	else:
		return True

def check_file(file, data, ftype):
	if not os.path.isfile(file):
		if file.startswith('.'):
			warn_file = file.replace('.', os.getcwd().replace('\\', '/'), 1)
		cprint("red", "WARNING: The file, {} did not exist, so I have created the file for you.".format(warn_file))
		if ftype.lower() == "json":
			with open(file, "w+") as f:
				json.dump(data, f)
		elif ftype.lower() == "standard":
			with open(file, "w+") as f:
				f.write(data)

def checkup():
	"""
	Checks whether all files/directories exist, and no index errors or key errors exist
	"""

	#File/Directory checkup
	check_dir('./core/data')
	check_dir('./core/data/cache')
	check_dir('./core/data/cache/images')

	check_dir('./user')
	check_dir('./user/cogs')
	check_dir('./user/config')
	check_dir('./user/logs')

	check_file('./core/data/cache/cache.json', {}, 'json')
	check_file('./core/data/cache/stats.json', {}, 'json')
	check_file('./user/config/server.json', {}, 'json')

def bot_system():
	with open('./core/data/system.json', 'r') as f:
		return json.load(f)

def bot_system_write(file):
	with open('./core/data/system.json', 'w') as f:
		json.dump(file, f)

def bot_config():
	with open('./user/config/bot.json', 'r') as f:
		return json.load(f)

def bot_config_write(file):
	with open('./user/config/bot.json', 'w') as f:
		json.dump(file, f)

def clear():
	os.system('cls' if os.name=='nt' else 'clear')

def cprint(color, string):
	colors = {"bold": "\033[1m","underline": "\033[4m","black": "\033[30m","red": "\033[31m","green": "\033[32m","yellow": "\033[33m","blue": "\033[34m","magenta": "\033[35m","cyan": "\033[36m","white": "\033[37m","bblack": "\033[40m","bred": "\033[41m","bgreen": "\033[42m","byellow": "\033[43m","bblue": "\033[44m","bmagenta": "\033[45m","bcyan": "\033[46m","bwhite": "\033[47m"}
	color = colors[color]
	white = colors["white"]
	print("{}{}{}".format(color, string, white))

def pip_install(*modules):
	"""
	Pip install for Windows/Unix machines
	"""
	for module in modules:
		pip.main(['install', module])

def qpy_pip_install(*modules):
	"""
	Support for QPython/Android
	"""
	if not (os.path.exists(sys.prefix + "/bin/pip")):
		raise StartError("PIP must be installed.")
	for module in modules:
		os.system(sys.executable + " " + sys.prefix + "/bin/" + module)

def get_input(string=None):
	if string == None:
		input()
		clear()
	else:
		return input(string)
		clear()

class Start:
	def __init__(self):
		self.x = ""

	def start(self):
		"""
		Work in progress bot setup
		"""
		if bot_system()["startup"] == True:

			if sys.version_info[0] == 2:
				raise StartError("PingBot is not compatible with Python 2.\nPlease switch to Python 3 or make an environment.")

			cprint("cyan", "Welcome to the PingBot Setup Procedure.")
			cprint("cyan", "We will go through the necessary steps to configurate your bot, if you wish to skip any of the questions, simply enter 'skip' as an answer.")
			input()
			clear()
			config = bot_config()
			missing_modules = []
			cprint("yellow", "Checking if the required modules are installed...")
			try:
				import discord
			except ImportError:
				missing_modules.append('discord.py')

			try:
				import asyncio
			except ImportError:
				missing_modules.append('asyncio')

			try:
				import aiohttp
			except ImportError:
				missing_modules.append("aiohttp")

			try:
				import imgurpython
			except ImportError:
				missing_modules.append("imgurpython")

			try:
				import bs4
			except ImportError:
				missing_modules.append("bs4")

			if len(missing_modules) > 0:
				cprint("red", "It seems that you are missing some required modules:")
				cprint("yellow", "{}: {}".format(len(missing_modules), ', '.join(missing_modules)))
				cprint("cyan", "\nWould you like me to download and install those modules?")
				choice = input("Yes, or No.")
				
				if choice.lower() == "yes":
					pip_install(tuple(missing_modules))
					#for module in missing_modules:
					#	pip.main(['install', module])
				elif choice.lower() == "no" or choice.lower() == "skip":
					clear()

			client_id = get_input("Enter your bot's client ID (if you haven't created a bot application yet, follow the instructions from this link: ")

			client_id = input("Enter your bot's client ID (if you haven't created a bot application yet, please do so via https://discordapp.com/developers/applications/me): ")

			if client_id.lower() == "skip":
				clear()
			else:
				config["client_id"] = client_id

			bot_token = int(input("Enter your bot's token (found in your application page): "))

			if bot_token.lower() == "skip":
				clear()
			else:
				config["token"] = bot_token

			bot_owner = input("Enter your discord user ID (you can get your ID by either right clicking your profile and clicking 'Copy ID' or by entering \@<YourName> in a chat): ")

			if bot_owner.lower() == "skip":
				clear()
			else:
				config["bot_owners"] = []
				config["bot_owners"].append(bot_owner)

			cprint("cyan", "Now to set the bot's 'personality.'")
			bot_name = input("What do you want your bot's name to be? ")

			if bot_name.lower() != "skip":
				config["username"] = bot_name
			clear()

			bot_prefix = input("What do you want your bot's command prefix to be? ")

			if bot_prefix.lower() != "skip":
				config["prefix"] = bot_prefix
			clear()

			games = input("Would you like your bot to change its currently playing game to a random list of games? If so, enter the list of games you want your bot to use (use commas as a delimiter): ")

			if games.lower() != "skip":
				config["games"] = []
				if ',' in games:
					games = re.split(', |,', games)
					for game in games:
						config["games"].append(game)
				else:
					games = games
					config["games"].append(games)
			clear()

			mention_messages = input("Would you like your bot to output a random message in the chat when it gets mentioned? If so, enter the list of messages you want chosen (use commas as a delimiter): ")

			if mention_messages.lower() != "skip":
				config["mention_messages"] = []
				if ',' in mention_messages:
					mention_messages = re.split(', |,', mention_messages)
					for message in mention_messages:
						config["mention_messages"].append(message)
				else:
					mention_messages = mention_messages
					config["mention_messages"].append(mention_messages)

			clear()

			cprint("cyan", "Now to set the APIs up!\nWe'll start with osu!")

			osu_key = input("What is your osu! API key? (You can get one by going to https://osu.ppy.sh/p/api): ")

			if osu_key.lower() != "skip":
				config["osu_key"] = osu_key
			clear()

			cprint("cyan", "Now for MyAnimeList...")

			mal_username = input("What is your myanimelist username? ")
			if mal_username.lower() != "skip":
				config["myanimelist"] = {}
				config["myanimelist"]["username"] = mal_username

			mal_password = input("What is your myanimelist password? ")
			if mal_password.lower() != "skip":
				if "myanimelist" not in config:
					config["myanimelist"] = {}
					config["myanimelist"]["username"] = ""
				#config["myanimelist"]["password"] = mal_password

			
		else:
			return

class StartError(Exception):
	pass

