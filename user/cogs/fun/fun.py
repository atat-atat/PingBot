from core import pingbot
from core.pingbot.messages import text
from discord.ext import commands
import discord
import random
import wikipedia
from bs4 import BeautifulSoup
import asyncio
from imgurpython import ImgurClient

cb_is_installed = True
try:
	from cleverbot import Cleverbot
	cb1 = Cleverbot()
except ImportError:
	cb1 = None
	cb_is_installed = False

config = pingbot.Config().load_json("./user/config/bot.json")
imgur_clientid = config['imgur']['client_id']
imgur_clientsecret = config['imgur']['client_secret']
imgur_client = ImgurClient(imgur_clientid, imgur_clientsecret)

emoji = pingbot.Config().load_json("./core/data/emoji.json")
mal_username = pingbot.Config("./user/config/bot.json").load_json()["myanimelist"]["username"]
mal_password = pingbot.Config("./user/config/bot.json").load_json()["myanimelist"]["password"]
pingbot.myanimelist.authorize(mal_username, mal_password)
class Fun:
	def __init__(self, bot):
		self.bot = bot
		self.game_data = {}

	@commands.command(name="mentions", pass_context=True, no_pm=True)
	async def _check_mentions(self, ctx, amount : int=1000):
		"""
		🎭 Checks for any messages that may have mentioned you.

		--------------------
		  USAGE: mentions <optional: amount of messages>
		EXAMPLE: mentions
		--------------------
		"""
		if await self.is_disabled(ctx, 'mentions'):
			return
		found_messages = []
		_msg = await self.bot.say(":warning: Retrieving logs...")
		async for message in self.bot.logs_from(ctx.message.channel, limit=amount+1):
			if '<@{}>'.format(ctx.message.author.id) in message.content and message.author != ctx.message.author and message.author != self.bot.user:
				found_messages.append("**[{}][{}]: {}**".format(message.timestamp, message.author, message.content))
			elif '@here' in message.content and message.author != ctx.message.author and message.author != self.bot.user:
				found_messages.append("**[{}][{}]: {}**".format(message.timestamp, message.author, message.content))
			elif '@everyone' in message.content and message.author != ctx.message.author and message.author != self.bot.user:
				found_messages.append("**[{}][{}]: {}**".format(message.timestamp, message.author, message.content))
			elif len(ctx.message.author.roles) > 0 and message.author != ctx.message.author and message.author != self.bot.user:
				for role in ctx.message.author.roles:
					if '<@&{}>'.format(role.id) in message.content:
						role_message = message.content.replace('@deleted-role', '@{}'.format(role.name))
						found_messages.append("**[{}][{}]: {}**".format(message.timestamp, message.author, role_message))

		if len(found_messages) <= 0:
			await self.bot.delete_message(_msg)
			await text("You have not been mentioned from the past {} messages.".format(amount), emoji=emoji["failure"])
			return

		await self.bot.delete_message(_msg)
		for msg in found_messages:
			await text(msg, emoji=":exclamation:", channel=ctx.message.author, no_mention=True)

		if len(found_messages) == 1:
			amount_of_times = "once"
		else:
			amount_of_times = "{} times".format(len(found_messages))
		await text("You have been mentioned {} (the messages have been sent to you via private message.)".format(amount_of_times), emoji=emoji["success"])

	@commands.group(name="notes", aliases=["note"], pass_context=True)
	async def notes(self, ctx):
		"""
		🎭 Views a note.

		--------------------
		  USAGE: notes <note name>
		EXAMPLE: notes test2
		--------------------
		"""
		if ctx.invoked_subcommand is None:
			if ctx.subcommand_passed == None:
				await text("You must provide the name of the note.", emoji=pingbot.Utils().get_config_emoji("failure"))
				return

			note_name = ctx.subcommand_passed
			note = self.get_note(note_name)
			if note == None:
				notes = self.load_notes()
				found_notes = []
				for _note in notes:
					if note_name in _note:
						found_notes.append(_note)
				if len(found_notes) != 0:
					await text("I could not find that note.\nPerhaps you meant `{}`?".format(random.choice(found_notes)), emoji=pingbot.Utils().get_config_emoji("failure"))
				else:
					await text("I could not find that note.", emoji=pingbot.Utils().get_config_emoji("failure"))
				return

			if not self.member_is_in_uses(note_name, ctx.message.author.id) and not self.member_is_submitter(note_name, ctx.message.author.id):
				self.append_note_uses(note_name, ctx.message.author.id)
			await text("**{}:** {}".format(note_name, note.content), no_bold=True, no_mention=True
				)


	@notes.command(name="add", aliases=["create"], pass_context=True)
	async def notes_create(self, ctx, note_name : str, *, note_content : str):
		"""
		🎭 Creates a note.

		--------------------
		  USAGE: notes create <note name> <content>
		EXAMPLE: notes create test2 Hello World!
		--------------------
		"""
		notes = self.get_note(note_name)
		if notes != None:
			await pingbot.Utils(self.bot, ctx.message).text("That note already exists.", emoji=pingbot.Utils().get_config_emoji("failure"))
			return

		self.add_note(ctx, note_name, note_content)
		await pingbot.Utils(self.bot, ctx.message).text("Successfully created note.", emoji=pingbot.Utils().get_config_emoji("success"))

	@notes.command(name="del", aliases=["remove", "delete", "rem"], pass_context=True)
	async def notes_remove(self, ctx, note_name : str):
		"""
		🎭 Deletes a note.

		--------------------
		  USAGE: notes delete <note name>
		EXAMPLE: notes delete test2
		--------------------
		"""
		note = self.get_note(note_name)
		if note == None:
			await pingbot.Utils(self.bot, ctx.message).text("I was unable to remove that note as it does not exist.", emoji=pingbot.get_emoji("failure"))
			return
		member_name = self.bot.get_member(note.submitter).name
		if note.submitter != member_name and not pingbot.permissions.can_ms(ctx.message.author) and not pingbot.permissions.is_serv_owner(ctx.message.author, ctx) and not pingbot.permissions.is_bot_owner(ctx.message.author):
			await pingbot.Utils(self.bot, ctx.message).text("You do not have permission to remove this note.", emoji=pingbot.get_emoji("failure"))
			return

		self.remove_note(note_name)
		await pingbot.Utils(self.bot, ctx.message).text("Successfully removed note.", emoji=pingbot.get_emoji("success"))
		return

	@notes.command(name="info", pass_context=True)
	async def notes_info(self, ctx, note_name : str):
		"""
		🎭 Returns information about a note.

		--------------------
		  USAGE: notes info <note name>
		EXAMPLE: notes info test2
		--------------------
		"""
		note = self.get_note(note_name)
		if note == None:
			await pingbot.Utils(self.bot, ctx.message).text("I was unable to find that note.", emoji=pingbot.get_emoji("failure"))
			return

		if len(note.content) > 90:
			content = note.content[:90] + "..."
		else:
			content = note.content

		if ctx.message.server.get_member(note.submitter) == None:
			submitter = note.submitter
		else:
			submitter = ctx.message.server.get_member(note.submitter).name

		fmt = """**Information about {0}**
**Name:** {0}
**Submitter:** {1}
**Submitted:** {2.submission_date}
**Contents:** {3}

**This note has been used {2.uses_int} times!**""".format(note_name, submitter, note, content)
		await pingbot.Utils(self.bot, ctx.message).text(fmt, no_bold=True, emoji=":bulb:")

	@notes.command(name="list", pass_context=True)
	async def notes_list(self, ctx, member : discord.Member=None):
		"""
		🎭 Lists the notes created.

		--------------------
		  USAGE: notes list <optional: member name or mention>
		EXAMPLE: notes list Bot
		--------------------
		"""
		if member == None:
			member = ctx.message.author

		await self.bot.say("SC: {}".format(ctx.subcommand_passed))
		notes_file = self.load_notes()
		notes = self.notes_from_member(member.id)
		if len(notes) == 0:
			await text("That member has not submitted any notes.", emoji=pingbot.get_emoji("failure"))
			return
		f_notes = []
		f_notes_uses = 0
		for note in notes:
			f_notes.append("{} (used {} times)".format(note, len(notes_file[note]["uses"])))
			f_notes_uses += len(notes_file[note]["uses"])

		await text("**{} has submitted a total of {} notes ({} total uses):** {}".format(member.name, len(f_notes), f_notes_uses, ', '.join(f_notes)), no_bold=True, emoji=":bulb:")

	@notes.command(name="search", pass_context=True)
	async def notes_search(self, ctx, note_name : str):
		"""
		🎭 Searches for a note.

		--------------------
		  USAGE: notes search <note name>
		EXAMPLE: notes search test
		--------------------
		"""
		notes = self.find_notes(note_name)

		if len(notes) == 0:
			await pingbot.Utils(self.bot, ctx.message).text("I could not find a note with that word in it.", emoji=pingbot.get_emoji["failure"])
			return

		await pingbot.Utils(self.bot, ctx.message).text("**Found {} notes with that word in them:** {}".format(len(notes), ', '.join(notes)))

	@notes.command(name="edit", aliases=["modify"], pass_context=True)
	async def notes_edit(self, ctx, note_name : str, *, note_content : str):
		"""
		🎭 Edits a note.

		--------------------
		  USAGE: notes edit <note name> <content>
		EXAMPLE: notes edit test2 Hello World!
		--------------------
		"""
		note = self.get_note(note_name)
		if note == None:
			await pingbot.Utils(self.bot, ctx.message).text("I was unable to access that note as it does not exist.", emoji=pingbot.get_emoji("failure"))
			return

		member_name = ctx.message.server.get_member(note.submitter).name
		if note.submitter != member_name and not pingbot.permissions.can_ms(ctx.message.author) and not pingbot.permissions.is_serv_owner(ctx.message.author, ctx) and not pingbot.permissions.is_bot_owner(ctx.message.author):
			await pingbot.Utils(self.bot, ctx.message).text("You do not have permission to edit this note.", emoji=pingbot.get_emoji("failure"))
			return

		self.modify_note('content', note_name, note_content)
		await pingbot.Utils(self.bot, ctx.message).text("Successfully modified note!", emoji=pingbot.get_emoji("success"))

	@notes.command(name="rename", aliases=["name", "title"], pass_context=True)
	async def notes_rename(self, ctx, old_note_name : str, new_note_name : str):
		"""
		🎭 Renames a note.

		--------------------
		  USAGE: notes rename <old note name> <new note name>
		EXAMPLE: notes rename test2 test3
		--------------------
		"""
		note = self.get_note(old_note_name)
		new_note = self.get_note(new_note_name)
		if note == None:
			await pingbot.Utils(self.bot, ctx.message).text("I was unable to rename that note as it does not exist.", emoji=pingbot.get_emoji("failure"))
			return
		if new_note != None:
			await text("That note already exists.", emoji=pingbot.get_emoji("failure"))
			return
		member_name = ctx.message.server.get_member(note.submitter).name
		if note.submitter != member_name and not pingbot.permissions.can_ms(ctx.message.author) and not pingbot.permissions.is_serv_owner(ctx.message.author, ctx) and not pingbot.permissions.is_bot_owner(ctx.message.author):
			await pingbot.Utils(self.bot, ctx.message).text("You do not have permission to edit this note.", emoji=pingbot.get_emoji("failure"))
			return

		self.modify_note('name', old_note_name, new_note_name)
		await pingbot.Utils(self.bot, ctx.message).text("Successfully renamed {} to {}!".format(old_note_name, new_note_name), emoji=pingbot.get_emoji("success"))

	@notes.command(name="direct_edit", pass_context=True)
	async def notes_dedit(self, ctx, note_name : str, n_type : str, value : str):
		"""
		🎭 Edits a note (includes the note type.)

		--------------------
		  USAGE: notes direct_edit <note name> <type> <value>
		EXAMPLE: notes direct_edit test2 submitter Bot
		--------------------
		"""
		note = self.get_note(note_name)
		if note == None:
			await text("That note doesn't exist.", emoji=pingbot.get_emoji("failure"))
			return
		member_name = ctx.message.server.get_member(note.submitter).name
		if note.submitter != member_name and not pingbot.permissions.can_ms(ctx.message.author) and not pingbot.permissions.is_serv_owner(ctx.message.author, ctx) and not pingbot.permissions.is_bot_owner(ctx.message.author):
			await pingbot.Utils(self.bot, ctx.message).text("You do not have permission to edit this note.", emoji=pingbot.get_emoji("failure"))
			return

		self.modify_note(n_type, note_name, value)
		await text("Successfully modified note.", emoji=pingbot.get_emoji("success"))

	@commands.command(name="profile", pass_context=True)
	async def profile_view(self, ctx, member: discord.Member=None):
		"""
		🎭 Views a profile.

		--------------------
		  USAGE: profile <optional: member name or mention>
		EXAMPLE: profile
		--------------------
		"""

		if member == None:
			member = ctx.message.author

		profile = self.get_profile(ctx.message.server.id, member.id)
		if profile == None:
			await text("That profile does not exist.", emoji=pingbot.get_emoji("failure"))
			return

		if len(profile.games.keys()) == 0:
			games = "None"
		else:
			game = sorted(profile.games, key=profile.games.get, reverse=True)[0]
			games = "{} (launched {} times)".format(game, self.get_gameplay_count(ctx.message.server.id, ctx.message.author.id, game))

		stats_json = self.load_stats()
		if member.id in stats_json[ctx.message.server.id]["commands_used"]:
			most_used_command = sorted(stats_json[ctx.message.server.id]["commands_used"][member.id], key=stats_json[ctx.message.server.id]["commands_used"][member.id].get, reverse=True)[0]
		else:
			most_used_command = "None"

		fmt = """```xl
			 Name: {0}
		    Level: {1.level_count} (XP: {1.experience_points}/{1.experience_cap})
		    Karma: {1.karma_count}
		 Respects: {1.respects}
		 Messages: {1.message_count}
 Most played game: {2}
Most used command: {3}```""".format(member.name, profile, games, most_used_command)
		await text(fmt)

	@commands.command(name="respects", pass_context=True)
	async def respects_view(self, ctx, member: discord.Member=None):
		"""
		🎭 Views total respects.

		--------------------
		  USAGE: respects <optional: member name or mention>
		EXAMPLE: respects
		--------------------
		"""
		if member == None:
			member = ctx.message.author
		profile_json = self.load_profiles()
		total_respects = profile_json[ctx.message.server.id]["respects"]
		member_respects = profile_json[ctx.message.server.id][member.id]["respects"]

		await text("**{} has paid {} respects out of total {} server respects.**".format(member.name, member_respects, total_respects))

	@commands.command(name="top_games", aliases=["top-games"], pass_context=True)
	async def top_games_list(self, ctx):
		"""
		🎭 Returns a list of the most played games.

		--------------------
		  USAGE: top_games
		EXAMPLE: top_games
		--------------------
		"""
		self.setup_profile_server_ifno(ctx.message.server.id)
		profile_json = self.load_profiles()

		_games = {}
		for member in profile_json[ctx.message.server.id]:
			if member != "respects":
				for game in profile_json[ctx.message.server.id][member]["games"]:
					if game not in _games:
						_games[game] = profile_json[ctx.message.server.id][member]["games"][game]
					else:
						_games[game] += profile_json[ctx.message.server.id][member]["games"][game]

		games = sorted(_games, key=_games.get, reverse=True)
		if len(games) == 0:
			await text("No games have been logged on this server yet.", emoji=pingbot.get_emoji("failure"))
			return
		fmt = ""
		if len(games) > 30:
			for i in range(len(games)-(len(games)-30)):
				fmt += "{}. {} (launched {} times)\n".format(i+1, games[i], _games[games[i]])
		else:
			for i in range(len(games)):
				fmt += "{}. {} (launched {} times)\n".format(i+1, games[i], _games[games[i]])
		fmt = """```xl
🎮 The top most played games on this server...
{}```""".format(fmt)
		await text(fmt)

	@commands.command(name="top_members", aliases=["top-members", "top_users", "top-users", "top_talkers", "top-talkers"], pass_context=True)
	async def top_talkers_list(self, ctx):
		"""
		🎭 Returns a list of the most talkative users.

		--------------------
		  USAGE: top_members
		EXAMPLE: top_members
		--------------------
		"""
		self.setup_profile_server_ifno(ctx.message.server.id)
		profile_json = self.load_profiles()

		_messages = {}
		for member in profile_json[ctx.message.server.id]:
			if member != "respects":
				_messages[member] = profile_json[ctx.message.server.id][member]["message_count"]

		messages = sorted(_messages, key=_messages.get, reverse=True)
		if len(messages) == 0:
			await text("No messages have been logged on this server yet.", emoji=pingbot.get_emoji("failure"))
			return
		fmt = ""
		if len(messages) > 30:
			for i in range(len(messages)-(len(messages)-30)):
				fmt += ("{}. {} : {} messages sent.\n".format(i+1, ctx.message.server.get_member(messages[i]), _messages[messages[i]]))
		else:
			for i in range(len(messages)):
				fmt += ("{}. {} : {} messages sent.\n".format(i+1, ctx.message.server.get_member(messages[i]), _messages[messages[i]]))

		fmt = """```xl
📊 The top most talkative members on this server...
{}```""".format(fmt)
		await text(fmt)

	@commands.command(name="top-commands", aliases=["top_commands"], pass_context=True)
	async def top_commands_used(self, ctx):
		"""
		🎭 Returns a list of the most used commands.

		--------------------
		  USAGE: top_commands
		EXAMPLE: top_commands
		--------------------
		"""
		self.setup_profile_server_ifno(ctx.message.server.id)
		stats_json = self.load_stats()
		if ctx.message.server.id not in stats_json:
			await text("I have not logged any commands on this server yet.", emoji=pingbot.get_emoji("failure"))
			return
		
		stats = sorted(stats_json[ctx.message.server.id]["commands_used"]["overall"], key=stats_json[ctx.message.server.id]["commands_used"]["overall"].get, reverse=True)
		if len(stats) == 0:
			await text("No command usages have been logged on this server yet.", emoji=pingbot.get_emoji("failure"))
			return
		fmt = ""
		if len(stats) > 30:
			for i in range(len(stats)-(len(stats)-30)):
				fmt += ("{}. {} : {} uses.\n".format(i+1, stats[i], stats_json[ctx.message.server.id]["commands_used"]["overall"][stats[i]]))
		else:
			for i in range(len(stats)):
				fmt += ("{}. {} : {} uses.\n".format(i+1, stats[i], stats_json[ctx.message.server.id]["commands_used"]["overall"][stats[i]]))

		fmt = """```xl
📊 The top most used commands on this server...
{}```""".format(fmt)
		await text(fmt)

	@commands.command(name="top_notes", aliases=["top-notes"], pass_context=True)
	async def top_notes_used(self, ctx):
		"""
		🎭 Returns a list of the most used notes.

		--------------------
		  USAGE: top_commands
		EXAMPLE: top_commands
		--------------------
		"""
		self.setup_profile_server_ifno(ctx.message.server.id)
		notes_json = self.load_notes()
		_notes = {}
		for note in notes_json:
			if not len(notes_json[note]["uses"]) == 0:
				_notes[note] = len(notes_json[note]["uses"])

		notes = sorted(_notes, key=_notes.get, reverse=True)
		if len(notes) == 0:
			await text("No notes have been used on this server yet.", emoji=pingbot.get_emoji("failure"))
			return
		fmt = ""
		if len(notes) > 30:
			for i in range(len(notes)-(len(notes)-30)):
				fmt += ("{}. {} : {} uses.\n".format(i+1, notes[i], len(notes_json[notes[i]]["uses"])))
		else:
			for i in range(len(notes)):
				fmt += ("{}. {} : {} uses.\n".format(i+1, notes[i], len(notes_json[notes[i]]["uses"])))

		fmt = """```xl
📊 The top most used notes...
{}```""".format(fmt)
		await text(fmt)

	@commands.command(name="movie", aliases=["show", "tv_show", "tv-show", "film"])
	async def movie_info(self, *, title : str):
		"""
		🎭 Returns information about a movie or TV show.

		--------------------
		  USAGE: movie <title>
		EXAMPLE: movie ant man
		--------------------
		"""
		movie = await pingbot.omdb.get_movie(title)
		if movie == None:
			await text("I could not find information about that movie or TV show.", emoji=pingbot.get_emoji("failure"))
			return

		fmt = """ {0.poster}
**Title:** {0.title}
**Director:** {0.director}
**Metascore:** {0.metascore} (**IMDb Rating:** {0.imdb_rating})
**Awards:** {0.awards}
**Actors:** {0.actors}
**Plot:** {0.plot}""".format(movie)
		await text(fmt, no_bold=True, emoji=pingbot.get_emoji("movie"))

	@commands.command(name="wikipedia", aliases=["wiki"])
	async def wikipedia_search(self, *, query : str):
		"""
		🎭 Returns information from wikipedia based on a topic.

		--------------------
		  USAGE: wikipedia <keyword>
		EXAMPLE: wikipedia regular expression
		--------------------
		"""
		try:
			topic = wikipedia.summary(query, sentences=3)
			_topic = wikipedia.page(query)
		except wikipedia.exceptions.PageError:
			await text("No topics found.", emoji=pingbot.get_emoji("failure"))
			return
		await text("**{}:** {}\n{}".format(_topic.title, topic, _topic.url), no_bold=True, emoji=pingbot.get_emoji("wikipedia"))

	@commands.command(pass_context=True, name="youtube")
	async def _youtube(self, ctx, *, query : str):
		"""
		🎭 Searches for a video from YouTube based on a keyword.

		--------------------
		  USAGE: youtube <keyword>
		EXAMPLE: youtube dogs
		--------------------
		"""
		url = "https://www.youtube.com/results?search_query=" + query
		url = url.replace(" ", "%20")
		response = await pingbot.WT(url).async_url_content()
		soup = BeautifulSoup(response, "html.parser")
		vids = soup.findAll(attrs={'class':'yt-uix-tile-link'})
		vid = vids[0]
		video = 'https://www.youtube.com' + vid['href']
		await text(video)

	@commands.command(pass_context=True, name="urban")
	async def _urban(self, ctx, *, query : str):
		"""
		🎭 Gets the Urban Dictionary definition of a word.

		--------------------
		  USAGE: urban <keyword>
		EXAMPLE: urban crouch spiders
		--------------------
		"""
		url = 'http://www.urbandictionary.com/define.php?term='
		meaning = pingbot.WT(url).div_get('class', 'meaning', query)
		example = pingbot.WT(url).div_get('class', 'example', query)
		contributor = pingbot.WT(url).div_get('class', 'contributor', query)
		fmt = """```xl
[Definition of {}]
{}
Example: {}
Contributed  {}
```""".format(query, meaning, example, contributor)

		if len(fmt) >= 2000:
			fmt = pingbot.Utils().string_chunk(fmt, '1000')

		if isinstance(fmt, list):
			for i in fmt:
				await pingbot.Utils(self.bot, ctx.message).text(i)
		else:
			await text(fmt)

		#await pingbot.Utils(self.bot, ctx.message).text(fmt)

	@commands.command(pass_context=True, name="anime")
	async def _mal_anime(self, ctx, *, query : str):
		"""
		🎭 Searches for an anime from MyAnimeList.net based on a keyword.

		--------------------
		  USAGE: anime <keyword>
		EXAMPLE: anime kiznaiver
		--------------------
		"""
		print("Getting anime")
		anime = pingbot.myanimelist.get_anime(query)
		print("Found anime")
		if anime == None:
			anime_not_found = pingbot.Utils().get_config_message("anime_not_found")
			await text("Test1", emoji=pingbot.Utils().get_config_emoji("failure"))
			return

		#theres probably a better way of doing this but i cant be fucked to actually think right now
		synopsis = anime.synopsis
		synopsis = synopsis.replace("&quot;", '"')
		synopsis = synopsis.replace("&mdash;", " --")
		synopsis = synopsis.split('<br />')[0] #shorten the synopsis to the first paragraph

		if anime.english == anime.title:
			english_name = ""
		else:
			english_name = "(**English:** {0.english})".format(anime)

		if anime.status == "Currently Airing":
			dates = ""
		else:
			dates = "(**{0.start_date}**-**{0.end_date}**)".format(anime)

		if anime.synonyms == None:
			synonyms = ""
		else:
			if english_name == "":
				synonyms = "\n**Synonyms:** {0.synonyms}".format(anime)
			else:
				synonyms = "\n**Synonyms:** {0.synonyms}\n".format(anime)

		fmt = """{0.image}
**Title:** {0.title} {1}{2}
**Episodes:** {0.episodes}
**Status:** {0.status} {3}
**Score:** {0.score}/10
	{4}""".format(anime, english_name, synonyms, dates, synopsis)

		await pingbot.Utils(self.bot, ctx.message).text(fmt, emoji=pingbot.get_emoji("anime"), no_bold=True)

	@commands.command(name="osu", pass_context=True)
	async def _osu_user(self, ctx, username : str):
		"""
		🎭 Returns information about an osu! user.

		--------------------
		  USAGE: osu <username>
		EXAMPLE: osu Cookiezi
		--------------------
		"""
		osu_key = pingbot.Config("./user/config/bot.json").load_json()["osu_key"]
		osu_info = await pingbot.osu.get_user(osu_key, username)

		if osu_info == None:
			osu_user_not_found = pingbot.Utils().get_config_message("osu_user_not_found")
			await pingbot.Utils(self.bot, ctx.message).text(osu_user_not_found, emoji=pingbot.Utils().get_config_emoji("failure"))
			return

		flag = ":flag_" + osu_info.country.lower() + ":"
		fmt = """{0.avatar}
**Name:** {0.username}
**Level:** {0.level}
**Playcount:** {0.playcount}
**Accuracy:** {0.accuracy}
**Ranked Score:** {0.ranked_score} (**Total:** {0.total_score})
**PP:** {0.pp_rank}
**Country:** {1}
**`{0.count300}` 300s, `{0.count100}` 100s, `{0.count50}` 50s**
**`{0.count_rank_ss}` SS', `{0.count_rank_s}` S', `{0.count_rank_a}` A's**
{0.user_profile}
""".format(osu_info, flag)
		await pingbot.Utils(self.bot, ctx.message).text(fmt, emoji=":red_circle:", no_bold=True)

	@commands.command(name="gif", aliases=["giphy"])
	async def giphy_search(self, *, query: str):
		"""
		🎭 Returns a gif image from giphy based on a keyword.

		--------------------
		  USAGE: osu <username>
		EXAMPLE: osu Cookiezi
		--------------------
		"""
		gif = await pingbot.giphy.get_gif(query)
		if gif == None:
			await text("No results found.", emoji=pingbot.get_emoji("failure"))
			return
		await text(gif.direct_embed_url, emoji=pingbot.get_emoji("success"), no_bold=True)

	@commands.group(name="cc", aliases=["cmd"], pass_context=True)
	async def customcom(self, ctx):
		"""
		🎭 Custom command management commands.

		--------------------
		  USAGE: cc <subcommand>
		EXAMPLE: cc create
		--------------------
		"""
		if ctx.invoked_subcommand is None:
			await text("You must provide a subcommand.", emoji=pingbot.get_emoji("failure"))

	@customcom.command(name="create", pass_context=True)
	async def cc_create(self, ctx, name : str, content : str):
		"""
		🎭 Creates a custom command.

		--------------------
		  USAGE: cc create <name> <content>
		EXAMPLE: cc create test1 Hello World!
		--------------------
		"""
		cmd_json = self.load_commands()
		if name in self.bot.commands or name in cmd_json:
			await text("That command already exists.", emoji=pingbot.get_emoji("failure"))
			return

		cmd_json[name] = {}
		cmd_json[name]["creator"] = ctx.message.author.id
		cmd_json[name]["creation_date"] = ctx.message.timestamp.strftime("%Y-%m-%d")
		cmd_json[name]["content"] = content
		cmd_json[name]["uses"] = []
		self.write_command(cmd_json)

		await text("Successfully created command!", emoji=pingbot.get_emoji("success"))

	@customcom.command(name="delete", aliases=["remove", "del", "rem"], pass_context=True)
	async def cc_del(self, ctx, name : str):
		"""
		🎭 Deletes a custom command.

		--------------------
		  USAGE: cc delete <name>
		EXAMPLE: cc delete test1
		--------------------
		"""
		cmd_json = self.load_commands()
		if name not in cmd_json:
			await text("That command doesn't exist.", emoji=pingbot.get_emoji("failure"))
			return

		if not ctx.message.author.id == cmd_json[name]["creator"] and not pingbot.permissions.can_ms(ctx.message.author) and not pingbot.permissions.is_serv_owner(ctx.message.author, ctx) and not pingbot.permissions.is_bot_owner(ctx.message.author):
			await text(no_perm, emoji=pingbot.get_emoji("failure"))
			return

		cmd_json.pop(name)
		self.write_command(cmd_json)
		await text("Successfully deleted command.", emoji=pingbot.get_emoji("success"))

	@customcom.command(name="edit", aliases=["modify"], pass_context=True)
	async def cc_edit(self, ctx, name : str, content : str):
		"""
		🎭 Modifies a custom command.

		--------------------
		  USAGE: cc edit <name> <content>
		EXAMPLE: cc edit test1 Hello world!
		--------------------
		"""
		cmd_json = self.load_commands()
		if name not in cmd_json:
			await text("That command doesn't exist.", emoji=pingbot.get_emoji("failure"))
			return

		cmd_json[name]["content"] = content
		self.write_command(cmd_json)

		await text("Successfully modified command!", emoji=pingbot.get_emoji("success"))

	@customcom.command(name="rename", pass_context=True)
	async def cc_rename(self, ctx, old_name : str, new_name : str):
		"""
		🎭 Renames a custom command.

		--------------------
		  USAGE: cc rename <old name> <new name>
		EXAMPLE: cc rename test1 test2
		--------------------
		"""
		cmd_json = self.load_commands()
		if name not in cmd_json:
			await text("That command doesn't exist.", emoji=pingbot.get_emoji("failure"))
			return

		old_cmd = cmd_json[old_name]
		cmd_json.pop(old_name)

		cmd_json[new_name] = {}
		cmd_json[new_name]["creator"] = old_cmd["creator"]
		cmd_json[new_name]["creation_date"] = old_cmd["creation_date"]
		cmd_json[new_name]["content"] = old_cmd["content"]
		cmd_json[new_name]["uses"] = old_cmd["uses"]
		self.write_command(cmd_json)

		await text("Successfully renamed command from {} to {}!".format(old_name, new_name), emoji=pingbot.get_emoji("success"))

	@customcom.command(name="info", aliases=["show"], pass_context=True)
	async def cc_info(self, ctx, name : str):
		"""
		🎭 Shows information about a custom command.

		--------------------
		  USAGE: cc info <name>
		EXAMPLE: cc info test1
		--------------------
		"""
		cmd = self.get_command(name)
		if cmd == None:
			await text("That command doesn't exist.", emoji=pingbot.get_emoji("failure"))
			return

		if len(cmd.content) > 90:
			content = cmd.content[:90] + "..."
		else:
			content = cmd.content

		if ctx.message.server.get_member(cmd.creator) == None:
			creator = cmd.creator
		else:
			creator = ctx.message.server.get_member(cmd.creator).name

		fmt = """**Information about {0}**
**Name:** {0}
**Creator:** {1}
**Created:** {2.creation_date}
**Contents:** {3}

**This note has been used {2.uses_int} times!**""".format(name, creator, cmd, content)
		await text(fmt, emoji=":bulb:", no_bold=True)

	@customcom.command(name="list", pass_context=True)
	async def cc_list(self, ctx, member : discord.Member=None):
		"""
		🎭 Returns a list of custom commands that you, or another member created.

		--------------------
		  USAGE: cc list <optional: member name or mention>
		EXAMPLE: cc list
		--------------------
		"""
		if member == None:
			member = ctx.message.author

		cmd_json = self.load_commands()

		commands = []
		for command in cmd_json:
			if cmd_json[command]["creator"] == member.id:
				commands.append(command)

		if len(commands) == 0:
			await text("You have not made any commands yet.", emoji=pingbot.get_emoji("failure"))
			return

		await text("**{} has created {} commands:** {}".format(member.name, len(commands), ", ".join(commands)), emoji=pingbot.get_emoji("success"), no_bold=True)

	@customcom.command(name="search", aliases=["find"], pass_context=True)
	async def cc_search(self, ctx, keyword : str):
		"""
		🎭 Returns a custom command based on a keyword.

		--------------------
		  USAGE: cc search <query>
		EXAMPLE: cc search test2
		--------------------
		"""
		cmd_json = self.load_commands()

		commands = []
		for command in cmd_json:
			if keyword in command:
				commands.append(command)

		if len(commands) == 0:
			await text("Your search yielded no results.", emoji=pingbot.get_emoji("failure"))
			return

		await text("**{} commands found:** {}".format(len(commands), ", ".join(commands)), no_bold=True, emoji=pingbot.get_emoji("success"))

	@commands.group(name="imgur", pass_context=True)
	async def imgur(self, ctx, *, keyword : str):
		"""
		🎭 Returns a result from imgur based on a keyword.

		--------------------
		  USAGE: imgur <query>
		EXAMPLE: imgur cat
		--------------------
		"""
		if ctx.invoked_subcommand is None:
			results = imgur_client.gallery_search(ctx.subcommand_passed)
			try:
				result = random.choice(results).link
			except IndexError:
				await text("That query yielded no results.", emoji=pingbot.get_emoji("failure"))
				return
			await text(result, emoji=pingbot.get_emoji("park"), no_bold=True)

	@imgur.command(name="sub")
	async def imgur_sub(self, subreddit : str):
		"""
		🎭 Returns images from Imgur based on a subreddit.

		--------------------
		  USAGE: imgur sub subreddit
		EXAMPLE: imgur sub cat
		--------------------
		"""
		results = imgur_client.subreddit_gallery(subreddit)
		try:
			result1 = random.choice(results).link
			result2 = random.choice(results).link
			result3 = random.choice(results).link
		except IndexError:
				await text("That query yielded no results.", emoji=pingbot.get_emoji("failure"))
				return
		await text("{}\n{}\n{}".format(result1, result2, result3), emoji=pingbot.get_emoji("park"), no_bold=True)

	@commands.command(name="cat")
	async def random_cat(self):
		"""
		🎭 Returns a random image of a cat.

		--------------------
		  USAGE: cat
		EXAMPLE: cat
		--------------------
		"""
		url = "http://random.cat/meow"
		resp = await pingbot.WT().async_json_content(url)
		cat_pic = resp["file"]
		await text(cat_pic, no_bold=True, emoji=pingbot.get_emoji("cat"))

	@commands.command(name="8ball")
	async def eight_ball(self, question : str=None):
		"""
		🎭 Returns an 8ball answer.

		--------------------
		  USAGE: 8ball <optional: question>
		EXAMPLE: 8ball
		--------------------
		"""
		eight_ball_answers = ["Signs point to yes.",
"Yes.",
"Reply hazy, try again.",
"Without a doubt.",
"My sources say no.",
"As I see it, yes.",
"You may rely on it.",
"Concentrate and ask again.",
"Outlook not so good.",
"It is decidedly so.",
"Better not tell you now.",
"Very doubtful.",
"Yes - definitely.",
"It is certain.",
"Cannot predict now.",
"Most likely.",
"Ask again later.",
"My reply is no.",
"Outlook good.",
"Don't count on it."]
		await text(random.choice(eight_ball_answers), emoji=pingbot.get_emoji("8ball"))

	@commands.command(name="flip", aliases=["flipcoin", "coinflip"], pass_context=True)
	async def coin_flip(self, ctx):
		"""
		🎭 Flips a coin.

		--------------------
		  USAGE: flip
		EXAMPLE: flip
		--------------------
		"""
		choices = ["Tails", "Heads"]
		msg = await self.bot.send_message(ctx.message.channel, "*I threw a coin and...*")
		asyncio.sleep(8)
		await self.bot.delete_message(msg)
		await text("**{}**".format(random.choice(choices)), emoji=pingbot.get_emoji("coin_flip"))

	@commands.command(name="roll", aliases=["dice"])
	async def roll_dice(self, dice : str=None):
		"""
		🎭 Rolls a dice.

		--------------------
		  USAGE: roll <NdN>
		EXAMPLE: roll 6d10
		--------------------
		"""
		if dice == None:
			rolls = 1
			limit = 6
		else:
			try:
				rolls, limit = map(int, dice.split('d'))
			except Exception:
				rolls = 1
				limit = 6

		result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
		await text(result, emoji=pingbot.get_emoji("dice"))

	@commands.command(description='For when you wanna settle the score some other way')
	async def choose(self, *choices : str):
		"""
		🎭 Selects a choice from a set of given choices.

		--------------------
		  USAGE: choose <choices>
		EXAMPLE: choose Something Something2 Something3
		--------------------
		"""
		await text(random.choice(choices))

#---------------- Events ----------------#

	async def fun_message_listener(self, msg):
		"""
		on_message listener
		"""
		if not msg.channel.is_private:
			self.setup_profile_server_ifno(msg.server.id)
			self.setup_profile_member_ifno(msg.server.id, msg.author.id)
			self.increase_message_count(msg.server.id, msg.author.id)
		emoji = pingbot.Config().load_json("./core/data/emoji.json")
		if msg.content.lower() == "f":
			self.increase_respects(msg.server.id, msg.author.id)
			await self.bot.send_message(msg.channel, "**{} has paid respects!**".format(msg.author.name))

		bot_json = pingbot.Config("./user/config/bot.json").load_json()
		if isinstance(bot_json["prefix"], list):
			cmd_prefix = tuple(bot_json["prefix"])
		else:
			cmd_prefix = bot_json["prefix"]

		if msg.content.startswith(cmd_prefix):
			cmd_json = self.load_commands()
			command = msg.content[len(cmd_prefix):]
			command = command.split()[0]
			if command not in self.bot.commands and command in cmd_json:
				if msg.author.id not in cmd_json[command]["uses"] and msg.author.id != cmd_json[command]["creator"]:
					cmd_json[command]["uses"].append(msg.author.id)

				if '|' in cmd_json[command]["content"]:
					cmd_content = random.choice(cmd_json[command]["content"].split('|'))
				else:
					cmd_content = cmd_json[command]["content"]
				await self.bot.send_message(msg.channel, cmd_content)
		
		if msg.content.startswith("<@{}>".format(self.bot.user.id)):
			content = msg.content[len("<@{}>".format(self.bot.user.id)):]
			if content == "":
				mention_messages = random.choice(pingbot.Config("./user/config/bot.json").load_json()["mention_messages"])
				await self.bot.send_message(msg.channel, mention_messages)
				return
			if cb_is_installed == True:
				try:
					response = cb1.ask(content)
					await self.bot.send_message(msg.channel, ":loud_sound: {}".format(response))
				except IndexError:
					await self.bot.send_message(msg.channel, ":thumbsdown: Unable to access cleverbot.")

	async def fun_member_update(self, before, after):
		"""
		on_member_update listener.
		"""
		if before.game != after.game and after.game != None and not after.bot:
			self.setup_profile_server_ifno(after.server.id)
			self.setup_profile_member_ifno(after.server.id, after.id)
			self.append_game_ifno(after.server.id, after.id, after.game.name)
			self.increase_game(after.server.id, after.id, after.game.name)

			status_channel = pingbot.Config("./user/config/server.json").load_json()[after.server.id]["status_channel"]
			if before.nick != None:
				start_fmt = pingbot.get_event_message("start_fmt_with_nick").format(before, before.nick)
			else:
				start_fmt = pingbot.get_event_message("start_fmt_no_nick").format(before)

			if status_channel != None:
				await text(start_fmt + pingbot.get_event_message("member_game_update").format(after.game.name, self.get_gameplay_count(after.server.id, after.id, after.game.name)), channel=status_channel, emoji="member_update_game", no_mention=True)
				#await pingbot.Utils(self.bot).text_status(start_fmt + " is now playing *{}* (launched `{}` times!)".format(before.name, after.game.name, self.get_gameplay_count(after.server.id, after.id, after.game.name)), status_channel, emoji=emoji["member_update_game"])

	async def fun_server_join(self, server):
		"""
		on_server_join listener.
		"""
		self.setup_profile_server_ifno(server.id)

	async def fun_server_leave(self, server):
		"""
		on_server_remove listener.
		"""
		self.remove_profile_server_ifno(server.id)
		stats_json = self.load_stats()
		if server.id in stats_json:
			stats_json.pop(server.id)
			self.write_stats(stats_json)

		profile_json = self.load_profiles()
		if server.id in profile_json:
			profile_json.pop(server.id)
			self.write_profile(server.id)

	async def fun_channel_remove(self, channel):
		"""
		on_channel_delete listener.
		"""
		server_json = pingbot.Config("./user/config/server.json").load_json()
		if channel.server.id in server_json:
			if server_json[channel.server.id]["status_channel"] != None:
				server_json[channel.server.id]["status_channel"] = None
				pingbot.Config("./user/config/server.json").write_json(server_json)

	async def fun_command_listener(self, command, ctx):
		"""
		on_command listener.
		"""
		stats_json = self.load_stats()
		if ctx.message.channel.is_private:
			return
		if ctx.message.server.id not in stats_json:
			stats_json[ctx.message.server.id] = {}
			stats_json[ctx.message.server.id]["commands_used"] = {}
			stats_json[ctx.message.server.id]["commands_used"]["overall"] = {}
			stats_json[ctx.message.server.id]["commands_used"][ctx.message.author.id] = {}

		if "commands_used" not in stats_json[ctx.message.server.id]:
			stats_json[ctx.message.server.id]["commands_used"] = {}
			stats_json[ctx.message.server.id]["commands_used"]["overall"] = {}
			stats_json[ctx.message.server.id]["commands_used"][ctx.message.author.id] = {}

		if ctx.message.author.id not in stats_json[ctx.message.server.id]["commands_used"]:
			stats_json[ctx.message.server.id]["commands_used"][ctx.message.author.id] = {}

		if command.name not in stats_json[ctx.message.server.id]["commands_used"]["overall"]:
			stats_json[ctx.message.server.id]["commands_used"]["overall"][command.name] = 0

		if command.name not in stats_json[ctx.message.server.id]["commands_used"][ctx.message.author.id]:
			stats_json[ctx.message.server.id]["commands_used"][ctx.message.author.id][command.name] = 0

		stats_json[ctx.message.server.id]["commands_used"]["overall"][command.name] += 1
		stats_json[ctx.message.server.id]["commands_used"][ctx.message.author.id][command.name] += 1
		self.write_stats(stats_json)

#---------------- Utilities ----------------#
	async def is_disabled(self, ctx, *args):
		if pingbot.Utils().cmd_is_disabled_list_form(ctx, list(args)):
			await pingbot.Utils(self.bot, ctx.message).text(cmd_disabled, emoji=emoji["failure"])
			return True

	def edit_server_settings(self, server, key, value):
		config_data = self.load_server_settings(server)
		config_data[key] = value
		self.write_server_settings(config_data)

	def get_server_value(self, server, key, value=None):
		config_data = self.load_server_settings(server)
		if key not in config_data:
			config_data[key] = value
			self.write_server_settings(config_data)
			config_data = self.load_server_settings(server)
		return config_data[key]

	def get_note_from_file(self, note):
		"""
		Returns the note from the file instead of an object.
		"""
		if note in self.load_notes():
			return self.load_notes()[note]
		else:
			return None

	def get_note(self, note):
		"""
		Returns the note object.
		"""
		if note in self.load_notes():
			note_info = self.load_notes()[note]
			return Note(note_info["submitter"], note_info["submission_date"], note_info["content"], note_info["uses"])
		else:
			return None

	def find_notes(self, name):
		"""
		Finds a note based on a keyword.
		"""
		notes = self.load_notes()
		f_notes = []
		for note in notes:
			if name in note:
				f_notes.append(note)

		return f_notes

	def notes_from_member(self, member):
		"""
		Returns a list of notes that a member has submitted.
		"""
		notes = self.load_notes()
		submitted_notes = []
		for note in notes:
			if notes[note]["submitter"] == member:
				submitted_notes.append(note)

		return submitted_notes

	def load_notes(self):
		return pingbot.Config("./user/cogs/fun/notes.json").load_json()

	def write_notes(self, config_data):
		pingbot.Config('./user/cogs/fun/notes.json').write_json(config_data)
		return

	def add_note(self, ctx, note, content, submitter=None, submission_date=None):
		"""
		Adds a note.
		"""
		notes = self.load_notes()

		if submitter == None:
			submitter = ctx.message.author.id

		if submission_date == None:
			submission_date = ctx.message.timestamp.strftime("%Y-%m-%d")

		notes[note] = {}
		notes[note]["submitter"] = submitter
		notes[note]["submission_date"] = submission_date
		notes[note]["content"] = content
		notes[note]["uses"] = []
		pingbot.Config('./user/cogs/fun/notes.json').write_json(notes)
		return

	def remove_note(self, note):
		"""
		Removes a note.
		"""
		notes = self.load_notes()

		notes.pop(note)
		pingbot.Config('./user/cogs/fun/notes.json').write_json(notes)
		return

	def append_note_uses(self, note, item):
		"""
		Appends a member ID to the list of note uses.
		"""
		notes = self.load_notes()

		notes[note]["uses"].append(item)
		self.write_notes(notes)
		return

	def member_is_in_uses(self, note, item):
		"""
		Checks if an ID has already been added to the note's uses.
		"""
		notes = self.load_notes()

		return item in notes[note]["uses"]

	def member_is_submitter(self, note, member):
		"""
		Checks if the member ID is the note submitter.
		"""
		note = self.get_note(note)
		if note == None:
			return None

		if member == note.submitter:
			return True
		else:
			return False

	def modify_note(self, edit_type, note_name, value, **kwargs):
		"""
		Modifies a note.
		"""
		if edit_type == 'content':
			notes = self.load_notes()
			notes[note_name]["content"] = value
			pingbot.Config('./user/cogs/fun/notes.json').write_json(notes)
			return
		elif edit_type == 'name':
			notes = self.load_notes()
			original_note = notes[note_name]

			notes.pop(note_name)
			notes[value] = original_note
			pingbot.Config('./user/cogs/fun/notes.json').write_json(notes)
			return
		elif edit_type == 'uses':
			notes = self.load_notes()
			if isinstance(value, str):
				raise PingBotError("Value must be a list, not string!")
			notes[note_name]["uses"] = value
			pingbot.Config('./user/cogs/fun/notes.json').write_json(notes)
			return
		elif edit_type == 'submitter':
			notes = self.load_notes()
			notes[note_name]["submitter"] = value
			pingbot.Config('./user/cogs/fun/notes.json').write_json(notes)
			return
		elif edit_type == 'submission_date':
			notes = self.load_notes()
			notes[note_name]["submission_date"] = value
			pingbot.Config('./user/cogs/fun/notes.json').write_json(notes)
			return
		else:
			raise PingBotError("Unknown note edit type!")

	def load_server_settings(self, server):
		return pingbot.Config('./user/cogs/fun/stats.json').load_json()[server]
		return

	def load_stats(self):
		return pingbot.Config('./user/cogs/fun/stats.json').load_json()

	def write_stats(self, config_data):
		pingbot.Config('./user/cogs/fun/stats.json').write_json(config_data)
		return

	def load_profiles(self):
		return pingbot.Config('./user/cogs/fun/profiles.json').load_json()

	def write_profile(self, config_data):
		pingbot.Config('./user/cogs/fun/profiles.json').write_json(config_data)
		return

	def setup_profile_server_ifno(self, server_id):
		profile_json = self.load_profiles()
		if server_id not in profile_json:
			profile_json[server_id] = {}
			profile_json[server_id]["respects"] = 0
			self.write_profile(profile_json)

	def remove_profile_server_ifno(self, server_id):
		profile_json = self.load_profiles()
		if server_id in profile_json:
			profile_json.pop(server_id)
			self.write_profile(profile_json)

	def setup_profile_member_ifno(self, server_id, member_id):
		profile_json = self.load_profiles()
		if member_id not in profile_json[server_id]:
			profile_json[server_id][member_id] = {}
			profile_json[server_id][member_id]["exp"] = 0
			profile_json[server_id][member_id]["exp_cap"] = 10
			profile_json[server_id][member_id]["level"] = 0
			profile_json[server_id][member_id]["karma"] = 0
			profile_json[server_id][member_id]["karma_messages"] = []
			profile_json[server_id][member_id]["message_count"] = 0
			profile_json[server_id][member_id]["respects"] = 0
			profile_json[server_id][member_id]["games"] = {}
			self.write_profile(profile_json)

	def increase_exp(self, server_id, member_id):
		profile_json = self.load_profiles()
		profile_json[server_id][member_id]["exp"] += 1
		self.write_profile(profile_json)

	def increase_level(self, server_id, member_id):
		profile_json = self.load_profiles()
		profile_json[server_id][member_id]["level"] += 1
		self.write_profile(profile_json)

	def increase_karma(self, server_id, member_id, message_id):
		profile_json = self.load_profiles()
		profile_json[server_id][member_id]["karma"] += 1
		profile_json[server_id][member_id]["karma_messages"].append(message_id)
		self.write_profile(profile_json)

	def increase_message_count(self, server_id, member_id):
		profile_json = self.load_profiles()
		profile_json[server_id][member_id]["message_count"] += 1
		self.write_profile(profile_json)

	def append_game(self, server_id, member_id, game_name, value=0):
		profile_json = self.load_profiles()
		profile_json[server_id][member_id]["games"][game_name] = value
		self.write_profile(profile_json)

	def append_game_ifno(self, server_id, member_id, game_name, value=0):
		profile_json = self.load_profiles()
		if game_name not in profile_json[server_id][member_id]["games"]:
			profile_json[server_id][member_id]["games"][game_name] = value
			self.write_profile(profile_json)

	def increase_game(self, server_id, member_id, game_name):
		profile_json = self.load_profiles()
		profile_json[server_id][member_id]["games"][game_name] += 1
		self.write_profile(profile_json)

	def get_gameplay_count(self, server_id, member_id, game_name):
		return self.get_profile(server_id, member_id).games[game_name]

	def get_gameplay_count_broad(self, server_id, game_name):
		profile_json = self.load_profiles()

		for i in profile_json[server_id]:
			if i != "respects":
				try:
					game = profile_json[server_id][i]["games"][game_name]
					pingbot.errors.debug_print(game)
					return game
				except KeyError:
					game = None
					pingbot.errors.debug_print(game)
					return game

	def get_profile(self, server_id, member_id):
		profiles_json = self.load_profiles()
		if server_id not in profiles_json:
			return None
		elif member_id not in profiles_json[server_id]:
			return None
		return Profile(profiles_json[server_id][member_id]["exp"], profiles_json[server_id][member_id]["exp_cap"], profiles_json[server_id][member_id]["level"], profiles_json[server_id][member_id]["karma"], profiles_json[server_id][member_id]["karma_messages"], profiles_json[server_id][member_id]["message_count"], profiles_json[server_id][member_id]["respects"], profiles_json[server_id][member_id]["games"])

	def increase_respects(self, server_id, member_id):
		profiles_json = self.load_profiles()
		profiles_json[server_id][member_id]["respects"] += 1
		profiles_json[server_id]["respects"] += 1
		self.write_profile(profiles_json)
		return

	def load_commands(self):
		return pingbot.Config("./user/cogs/fun/customcommands.json").load_json()

	def write_command(self, config_data):
		pingbot.Config("./user/cogs/fun/customcommands.json").write_json(config_data)
		return

	def get_command(self, cmd_name):
		cmd_json = self.load_commands()
		if cmd_name not in cmd_json:
			return None
		return CustomCommand(cmd_json[cmd_name]["creator"], cmd_json[cmd_name]["creation_date"], cmd_json[cmd_name]["content"], cmd_json[cmd_name]["uses"])

class Note:
	def __init__(self, submitter, submission_date, content, uses):
		self.submitter = submitter
		self.submission_date = submission_date
		self.content = content
		self.uses = uses
		self.uses_int = len(uses)

class Profile:
	def __init__(self, experience_points, experience_cap, level_count, karma_count, karma_messages, message_count, respects, games):
		self.experience_points = experience_points
		self.experience_cap = experience_cap
		self.level_count = level_count
		self.karma_count = karma_count
		self.karma_messages = karma_messages
		self.message_count = message_count
		self.respects = respects
		self.games = games

class CustomCommand:
	def __init__(self, creator, creation_date, content, uses):
		self.creator = creator
		self.creation_date = creation_date
		self.content = content
		self.uses = uses
		self.uses_int = len(uses)

def setup(bot):
	bot.add_listener(Fun(bot).fun_message_listener, "on_message")
	bot.add_listener(Fun(bot).fun_command_listener, "on_command")
	bot.add_listener(Fun(bot).fun_member_update, "on_member_update")
	bot.add_listener(Fun(bot).fun_server_join, "on_server_join")
	bot.add_cog(Fun(bot))