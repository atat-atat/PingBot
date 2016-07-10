from discord.ext import commands
from core import pingbot
import aiohttp
import random
from urllib.parse import quote as urlquote
import urllib
import xml.etree.ElementTree as ET
from imgurpython import ImgurClient
import imgurpython
import os
import json
import asyncio
import discord
import sys
import datetime

now = datetime.datetime.now()
date = now.strftime("%Y-%m-%d %H-%M")

nsfw_config_dir = './user/cogs/nsfw/nsfw_info.json'

config = pingbot.Config().load_json("./user/config/bot.json")
nsfw_file = pingbot.Config(nsfw_config_dir).load_json()
emoji = pingbot.Config().load_json("./core/data/emoji.json")
sysmsg = pingbot.Config().load_json("./core/data/messages.json")
cmd_disabled = sysmsg['disabled_cmd']
no_results = sysmsg['no_results']
kw_require = sysmsg['keyword_requirement']
no_perm = sysmsg['no_permission']
no_pm = sysmsg['no_pm']
nsfwmsg = nsfw_file["messages"]
no_nsfw_chan = nsfwmsg["no_nsfw_in_chan"]
subtext = nsfwmsg["subtexts"]
imgur_clientid = config['imgur']['client_id']
imgur_clientsecret = config['imgur']['client_secret']
imgur_client = ImgurClient(imgur_clientid, imgur_clientsecret)

no_auto_nsfw_channel_start = pingbot.Utils().check_start_arg("no_auto_nsfw")

if "save_files" not in nsfw_file:
    save_nsfw = False
    nsfw_save_dir = ""
else:
    save_nsfw = nsfw_file["save_files"] #if you wanna start a collection ;)
    nsfw_save_dir = nsfw_file["nsfw_directory"]

class NSFW:
    """
    A cog full of NSFW commands, like...

    - RedTube API access
    - Yande.re search commands
    - Gelbooru
    - And more...

    (Excuse some of the ridiculous command names.)
    (Actually this entire script is ridiculous, why did I even make this...)
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="set-nsfw", aliases=["set_nsfw"], pass_context=True, no_pm=True)
    async def set_nsfw_channel(self, ctx):
        """
        🍆 Sets the NSFW channel.

        --------------------
          USAGE: set-nsfw
        EXAMPLE: set-nsfw
        --------------------
        """
        if not pingbot.permissions.can_ms(ctx.message.author) and not pingbot.permissions.is_serv_owner(ctx.message.author, ctx) and not pingbot.permissions.is_bot_owner(ctx.message.author):
            await pingbot.Utils(self.bot, ctx.message).text(no_perm, emoji=emoji["failure"])
            return
        nsfw_config = pingbot.Config(nsfw_config_dir).load_json()
        if ctx.message.server.id not in nsfw_config["servers"]: #if the server has not been added to the servers list.
            nsfw_config["servers"][ctx.message.server.id] = {}
            nsfw_config["servers"][ctx.message.server.id]["auto_nsfw_channels"] = {}
            nsfw_config["servers"][ctx.message.server.id]["nsfw_channels"] = []
            pingbot.Config(nsfw_config_dir).write_json(nsfw_config)
            nsfw_config = pingbot.Config(nsfw_config_dir).load_json()

        if ctx.message.channel.id in nsfw_config["servers"][ctx.message.server.id]["nsfw_channels"]:
            nsfw_config["servers"][ctx.message.server.id]["nsfw_channels"].remove(ctx.message.channel.id)
            pingbot.Config(nsfw_config_dir).write_json(nsfw_config)
            await pingbot.Utils(self.bot, ctx.message).text("This channel is no longer a NSFW channel.", emoji=emoji["success"])
            return
        else:
            nsfw_config["servers"][ctx.message.server.id]["nsfw_channels"].append(ctx.message.channel.id)
            pingbot.Config(nsfw_config_dir).write_json(nsfw_config)
            await pingbot.Utils(self.bot, ctx.message).text("This channel is now a NSFW channel.", emoji=emoji["success"])
            return

    @commands.command(name="set-auto-nsfw", pass_context=True, no_pm=True)
    async def _set_auto_nsfw_channel(self, ctx, nsfw_type : str='default'):
        """
        🍆 Sets the automatic NSFW-material-provider channel.

        --------------------
          USAGE: set-auto-nsfw <optional: nsfw type>
        EXAMPLE: set-auto-nsfw
        --------------------
        """
        if not pingbot.permissions.can_ms(ctx.message.author) and not pingbot.permissions.is_serv_owner(ctx.message.author, ctx) and not pingbot.permissions.is_bot_owner(ctx.message.author):
            await pingbot.Utils(self.bot, ctx.message).text(no_perm, emoji=emoji["failure"])
            return

        nsfw_config = pingbot.Config(nsfw_config_dir).load_json()
        if ctx.message.server.id not in nsfw_config["servers"]: #if the server has not been added to the servers list.
            nsfw_config["servers"][ctx.message.server.id] = {}
            nsfw_config["servers"][ctx.message.server.id]["auto_nsfw_channels"] = {}
            nsfw_config["servers"][ctx.message.server.id]["nsfw_channels"] = []
            pingbot.Config(nsfw_config_dir).write_json(nsfw_config)
            nsfw_config = pingbot.Config(nsfw_config_dir).load_json()

        if not self.nsfw_check_chan(ctx) == True:
            if self.is_auto_nsfw_chan(ctx): #if the current channel is already an auto-nsfw channel, then set auto_nsfw_channel to None
                nsfw_config["servers"][ctx.message.server.id]["auto_nsfw_channels"].pop(ctx.message.channel.id)
                pingbot.Config(nsfw_config_dir).write_json(nsfw_config)
                await pingbot.Utils(self.bot, ctx.message).text("This channel is no longer an auto-NSFW channel.", emoji=emoji["success"])
                return
            elif not self.is_auto_nsfw_chan(ctx): #if the current channel is not an auto-nsfw channel, then set auto_nsfw_channel to the current channel id
                nsfw_config = pingbot.Config(nsfw_config_dir).load_json()
                nsfw_config["servers"][ctx.message.server.id]["auto_nsfw_channels"][ctx.message.channel.id] = nsfw_type
                pingbot.Config(nsfw_config_dir).write_json(nsfw_config)
                await pingbot.Utils(self.bot, ctx.message).text("This channel will now output a random NSFW image from time to time.", emoji=emoji["success"])
                return
        else:
            await pingbot.Utils(self.bot, ctx.message).text("This channel must be a NSFW channel.", emoji=emoji["failure"])
            return

    @commands.command(name="auto-nsfw-type", aliases=['set-auto-nsfw-type'], pass_context=True, no_pm=True)
    async def _set_auto_nsfw_type(self, ctx, nsfw_type : str):
        """
        🍆 Sets the auto-NSFW channel type.

        --------------------
          USAGE: auto-nsfw-type
        EXAMPLE: auto-nsfw-type
        --------------------
        """
        self.install_auto_nsfw_ifno(ctx)
        nsfw_config = pingbot.Config(nsfw_config_dir).load_json()
        if not pingbot.permissions.can_ms(ctx.message.author) and not pingbot.permissions.is_serv_owner(ctx.message.author, ctx) and not pingbot.permissions.is_bot_owner(ctx.message.author):
            await pingbot.Utils(self.bot, ctx.message).text(no_perm, emoji=emoji["failure"])
            return

        if self.is_auto_nsfw_chan(ctx):
            if nsfw_type not in nsfw_config["nsfw_types"]:
                await pingbot.Utils(self.bot, ctx.message).text(nsfw_config["messages"]["unknown_type"], emoji=emoji["failure"])
            
            nsfw_config["servers"][ctx.message.server.id]["auto_nsfw_channels"][ctx.message.channel.id] = nsfw_type
            pingbot.Config(nsfw_config_dir).write_json(nsfw_config)
            await pingbot.Utils(self.bot, ctx.message).text("This channel will now output images relating to {}".format(nsfw_type), emoji=emoji["success"])
            return
        else:
            await pingbot.Utils(self.bot, ctx.message).text("This channel must be an auto-NSFW channel.", emoji=emoji["failure"])
            return

    @commands.command(name="nsfw-types", pass_context=True)
    async def _return_nsfw_types(self, ctx):
        """
        🍆 Gives a list of NSFW types.

        --------------------
          USAGE: nsfw-types
        EXAMPLE: nsfw-types
        --------------------
        """
        nsfw_types = pingbot.Config(nsfw_config_dir).load_json()["nsfw_types"]
        await pingbot.Utils(self.bot, ctx.message).text("There are {} auto-NSFW types: {}".format(len(nsfw_types.keys()), ', '.join(nsfw_types.keys())))

    @commands.command(name="nsfw-cleanup", pass_context=True)
    async def clean_nsfw_content(self, ctx, amount : int=500):
        """
        🍆 Clears the past 500 messages that may have contained NSFW content.

        --------------------
          USAGE: nsfw-cleanup <optional: amount of messages>
        EXAMPLE: nsfw-cleanup
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'nsfw-cleanup'):
            return

        def is_msg(m):
            if m.author == self.bot.user:
                if 'http://media.oboobs.ru' in m.content:
                    return True
                elif 'http://media.obutts.ru' in m.content:
                    return True
                elif 'http://www.redtube.com' in m.content:
                    return True
                elif 'http://simg4.gelbooru.com' in m.content:
                    return True
                elif 'http://img.rule34.xxx' in m.content:
                    return True
                elif 'http://files.yande.re' in m.content:
                    return True
                elif 'http://i.imgur.com' in m.content:
                    return True
                elif 'Have fun, ' in m.content:
                    return True
                elif "You're welcome, " in m.content:
                    return True
                elif 'Here you go, ' in m.content:
                    return True
        try:
            await self.bot.purge_from(ctx.message.channel, limit=amount+1, check=is_msg)
        except discord.errors.Forbidden:
            await pingbot.Utils(self.bot, ctx.message).text(no_bot_perm, emoji=emoji["failure"])

    @commands.command(name="boobs", aliases=["tits", "melons"], pass_context=True)
    async def _boobs(self, ctx):
        """
        🍆 Returns a random image of some boobs.

        --------------------
          USAGE: boobs
        EXAMPLE: boobs
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'boobs', 'tits', 'melons'): #check if the command is disabled, or if the server has a NSFW channel and check if the messaged channel is a NSFW channel
            return

        random_int = random.randint(0, 176)
        url = "http://api.oboobs.ru/boobs/{}/1/rank/".format(random_int)
        result = await pingbot.WT().async_json_content(url)
        image = result[0]["preview"]
        await pingbot.Utils(self.bot, ctx.message).text("{}, http://media.oboobs.ru/{}".format(random.choice(subtext), image), emoji=pingbot.get_emoji("success"), no_bold=True)
        await self.save_nsfw_file('http://media.oboobs.ru/{}'.format(image), file_name="boobs_" + image)

    @commands.command(name="butt", aliases=["butts", "ass"], pass_context=True)
    async def _butt(self, ctx):
        """
        🍆 Returns a random image of a butt.

        --------------------
          USAGE: butt
        EXAMPLE: butt
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'butt', 'butts', 'ass'):
            return

        random_int = random.randint(0, 176)
        url = "http://api.obutts.ru/butts/{}/1/rank/".format(random_int)
        result = await pingbot.WT().async_json_content(url)
        image = result[0]["preview"]
        await pingbot.Utils(self.bot, ctx.message).text("{}, http://media.obutts.ru/{}".format(random.choice(subtext), image, emoji=pingbot.get_emoji("success"), no_bold=True))
        await self.save_nsfw_file('http://media.oboobs.ru/{}'.format(image), file_name="butts_" + image)

    @commands.command(name="redtube", pass_context=True)
    async def _redtube(self, ctx, *, query : str):
        """
        🍆 Searches for a video from the RedTube API via a query.

        --------------------
          USAGE: redtube <keyword>
        EXAMPLE: redtube blowjob
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'redtube'):
            return

        kw = urlquote(query)
        url = "http://api.redtube.com/?data=redtube.Videos.searchVideos&output=json&tags[]={}&thumbsize=medium".format(kw)
        results = await pingbot.WT().async_json_content(url)
        if "videos" not in results:
            await pingbot.Utils(self.bot, ctx.message).text(no_results.format(query), emoji=emoji["failure"])
            return
        try:
            video_select = random.randint(0, len(results["videos"]))
            video_title = results["videos"][video_select]["video"]["title"]
            video_views = results["videos"][video_select]["video"]["views"]
            video_rating = results["videos"][video_select]["video"]["rating"]
            video_published = results["videos"][video_select]["video"]["publish_date"]
            video_duration = results["videos"][video_select]["video"]["duration"]
            video_tags_len = len(results["videos"][video_select]["video"]["tags"])
            video_tags = []
            for i in results["videos"][video_select]["video"]["tags"]:
                video_tags.append(i["tag_name"])
            video_url = results["videos"][video_select]["video"]["url"]
            video_thumb_int = random.randint(0, len(results["videos"][video_select]["video"]["thumbs"]))
            video_thumb = results["videos"][video_select]["video"]["thumbs"][video_thumb_int]["src"]
        except IndexError:
            video_select = 0
            video_title = results["videos"][video_select]["video"]["title"]
            video_views = results["videos"][video_select]["video"]["views"]
            video_rating = results["videos"][video_select]["video"]["rating"]
            video_published = results["videos"][video_select]["video"]["publish_date"]
            video_duration = results["videos"][video_select]["video"]["duration"]
            video_tags_len = len(results["videos"][video_select]["video"]["tags"])
            video_tags = []
            for i in results["videos"][video_select]["video"]["tags"]:
                video_tags.append(i["tag_name"])
            video_url = results["videos"][video_select]["video"]["url"]
            video_thumb_int = random.randint(0, len(results["videos"][video_select]["video"]["thumbs"]))
            video_thumb = results["videos"][video_select]["video"]["thumbs"][video_thumb_int]["src"]
        try:
            await pingbot.Utils(self.bot, ctx.message).text("**Title:** {}\n**Views:**{}\n**Rating:** {}\n**Published:** {}\n**Duration:** {}\n**Tags:** {}\n**URL:** {}\n**Thumbnail(out of {}):** {}".format(video_title, video_views, video_rating, video_published, video_duration, ", ".join(video_tags), video_url, len(results["videos"][video_select]["video"]["thumbs"]), video_thumb), no_bold=True)
        except discord.errors.HTTPException:
            await pingbot.Utils(self.bot, ctx.message).text("HTTP Exception error occurred.", emoji=emoji["error"])

    @commands.command(name="gelbooru", pass_context=True)
    async def _gelbooru(self, ctx, *, query : str):
        """
        🍆 Searches for an item from gelbooru.com

        --------------------
          USAGE: gelbooru <keyword>
        EXAMPLE: gelbooru kawaii
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'gelbooru'):
            return
        kw = urlquote(query)
        url = "http://gelbooru.com/index.php?page=dapi&s=post&tags={}&q=index&json=1&limit=1&pid=1".format(kw)
        result = await pingbot.WT().async_json_content(url)
        try:
            image_url = result[0]["file_url"]
        except (IndexError, TypeError):
            await pingbot.Utils(self.bot, ctx.message).text(no_results.format(query), emoji=emoji['failure'])
            return
        await pingbot.Utils(self.bot, ctx.message).text("{}, {}".format(random.choice(subtext), image_url), emoji=emoji['success'], no_bold=True)
        await self.save_nsfw_file(image_url, file_name=result[0]["image"], command="gelbooru")

    @commands.command(name="rule34", pass_context=True)
    async def _rule34(self, ctx, *, query : str):
        """
        🍆 Searches for an item from rule34.xxx based on a keyword.

        --------------------
          USAGE: rule34 <keyword>
        EXAMPLE: rule34 pokemon
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'rule34'):
            return
        kw = urlquote(query)
        req = pingbot.WT().web_get('http://rule34.xxx/index.php?page=dapi&s=post&q=index&tags={}'.format(kw))
        results = ET.fromstring(req)

        if len(results) <= 0: #if no results were found
            await pingbot.Utils(self.bot, ctx.message).text(no_results.format(query), emoji=emoji["failure"])
            return

        selection = random.choice(results)
        link = "http:{}".format(selection.attrib['file_url'])
        await pingbot.Utils(self.bot, ctx.message).text("{}, {}".format(random.choice(subtext), link), emoji=emoji["success"], no_bold=True)
        await self.save_nsfw_file(link, file_name=selection.attrib['md5'], command="rule34")

    @_rule34.error
    async def _rule34_error(self, error, ctx):
        if isinstance(error, commands.MissingRequiredArgument):
            if await self.is_disabled_or_no_nsfw(ctx, 'rule34'):
                return
            result = self.return_subreddit_result('rule34')
            await pingbot.Utils(self.bot, ctx.message).text("{}, {}".format(random.choice(subtext), result.link), emoji=emoji['success'], no_bold=True)
            await self.save_imgur_file(result, command="rule34")

    @commands.command(name="yandere", pass_context=True)
    async def _yandere(self, ctx, *, query : str):
        """
        🍆 Searches for an item from yande.re

        --------------------
          USAGE: yandere <keyword>
        EXAMPLE: yandere loli
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'yandere'):
            return
        kw = urlquote(query)
        url = "https://yande.re/post.json?limit=1&page=0&tags={}".format(kw)
        result = await pingbot.WT().async_json_content(url)
        try:
            image_url = result[0]["file_url"]
        except (IndexError, TypeError):
            await pingbot.Utils(self.bot, ctx.message).text(no_results.format(query), emoji=emoji['failure'])
            return
        await pingbot.Utils(self.bot, ctx.message).text("{}, {}".format(random.choice(subtext), image_url), emoji=emoji['success'], no_bold=True)
        await self.save_nsfw_file(image_url, file_name='{}.jpg'.format(result[0]["id"]), direct_save=True, command="yandere") #this has a chance of not working

    @commands.command(name="e621", pass_context=True)
    async def _e621_retrieve(self, ctx, keyword : str):
        """
        🍆 Searches for an item from e621.net

        --------------------
          USAGE: e621 <keyword>
        EXAMPLE: e621 dragon
        --------------------
        """
        url = "https://e621.net/post/index.json?limit=1"
        await text("This feature is still being worked on.", emoji="failure")
        #https://e621.net/help/show/api

        #TODO: actually work on command

    @commands.command(name="gonewild", pass_context=True)
    async def _gonewild(self, ctx):
        """
        🍆 Returns a random image from the r/gonewild subreddit.

        --------------------
          USAGE: gonewild
        EXAMPLE: gonewild
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'gonewild'):
            return
        result = self.return_subreddit_result('gonewild')
        await pingbot.Utils(self.bot, ctx.message).text("{}, {}".format(random.choice(subtext), result.link), emoji=emoji['success'], no_bold=True)
        await self.save_imgur_file(result, command="gonewild")

    @commands.command(name="porn_gif", aliases=["porn_gifs"], pass_context=True)
    async def _porn_gif(self, ctx):
        """
        🍆 Returns a random image from the r/porn_gifs subreddit.

        --------------------
          USAGE: porn_gif
        EXAMPLE: porn_gif
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'porn_gif', 'porn_gifs'):
            return
        result = self.return_subreddit_result('porn_gifs', True)
        await pingbot.Utils(self.bot, ctx.message).text("{}, {}".format(random.choice(subtext), result.link), emoji=emoji['success'])
        await self.save_imgur_file(result, command="porn_gif")

    @commands.command(name="hentai", pass_context=True)
    async def _hentai(self, ctx, include_sub : bool=False):
        """
        🍆 Returns a random image from a variety of hentai subreddits.

        --------------------
          USAGE: hentai
        EXAMPLE: hentai
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'hentai'):
            return
        choice = random.choice(['hentai', 'hentaibondage', 'HENTAI_GIF', 'HQHentai', 'HentaiSource', 'Paizuri', 'Futanari', 'Touhou_NSFW', 'MonsterGirl', 'AnimeBooty', 'tentai'])
        result = self.return_subreddit_result(choice)
        if include_sub == True:
            await pingbot.Utils(self.bot, ctx.message).text("({}): {}, {}".format(choice, random.choice(subtext), result.link), emoji=emoji['success'], no_bold=True)
        else:
            await pingbot.Utils(self.bot, ctx.message).text("{}, {}".format(random.choice(subtext), result.link), emoji=emoji['success'], no_bold=True)
        await self.save_imgur_file(result, command=choice)

    @commands.command(name="hentai_gif", pass_context=True)
    async def _hentai_gif(self, ctx):
        """
        🍆 Returns a random image from the r/HENTAI_GIF subreddit.

        --------------------
          USAGE: hentai_gif
        EXAMPLE: hentai_gif
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'hentai_gif'):
            return
        result = self.return_subreddit_result('HENTAI_GIF')
        await pingbot.Utils(self.bot, ctx.message).text("{}, {}".format(random.choice(subtext), result.link), emoji=emoji['success'], no_bold=True)
        await self.save_imgur_file(result, command="hentai_gif")

    @commands.command(name="nsfw_gif", pass_context=True)
    async def _nsfw_gif(self, ctx):
        """
        🍆 Returns a random image from the r/NSFW_GIF subreddit.

        --------------------
          USAGE: nsfw_gif
        EXAMPLE: nsfw_gif
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'nsfw_gif'):
            return
        result = self.return_subreddit_result('NSFW_GIF')
        await pingbot.Utils(self.bot, ctx.message).text("{}, {}".format(random.choice(subtext), result.link), emoji=emoji['success'], no_bold=True)
        await self.save_imgur_file(result, command="nsfw_gif")

    @commands.command(name="clop", pass_context=True)
    async def _clop(self, ctx):
        """
        🍆 If you're into horses.

        --------------------
          USAGE: clop
        EXAMPLE: clop
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'clop'):
            return
        result = self.return_subreddit_result('Horses')
        await pingbot.Utils(self.bot, ctx.message).text("{}, {}".format(random.choice(subtext), result.link), emoji=emoji['success'], no_bold=True)
        await self.save_imgur_file(result, command="clop")

    @commands.command(name="clopping", pass_context=True)
    async def _clopping(self, ctx):
        """
        🍆 (This one is for real.)

        --------------------
          USAGE: clopping
        EXAMPLE: clopping
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'clopping'):
            return
        result = self.return_subreddit_result('ClopClop')
        await pingbot.Utils(self.bot, ctx.message).text("{}, {}".format(random.choice(subtext), result.link), emoji=emoji['success'], no_bold=True)
        await self.save_imgur_file(result, command="clopping")

    @commands.command(name="porn", pass_context=True)
    async def _all_porn(self, ctx, include_sub : bool=False):
        """
        🍆 Returns a random pornographic image.

        --------------------
          USAGE: porn
        EXAMPLE: porn
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'porn'):
            return
        choice = random.choice(['PetiteGoneWild', 'gonewild', 'porn_gifs', 'ClopClop', 'nsfw_gif', 'nsfw', 'hentai', 'hentaibondage', 'HENTAI_GIF', 'HQHentai', 'HentaiSource', 'Paizuri', 'Futanari', 'Touhou_NSFW', 'MonsterGirl', 'AnimeBooty', 'RealGirls', 'ginger', 'asstastic', 'LipsThatGrip', 'AsiansGoneWild', 'Unashamed', 'nsfw_html5', 'ladybonersgw', 'mangonewild', 'ChristianGirls', 'girlswithglasses', 'DarkAngels', 'gonewildcolor', 'japaneseporn', 'jilling', 'tentai', 'gamersgonewild', 'gayporn', 'LGBTGoneWild', 'publicboys', 'girlsdoingnerdythings', 'rule34'])
        result = self.return_subreddit_result(choice)
        if include_sub == True:
            await pingbot.Utils(self.bot, ctx.message).text("({}): {}, {}".format(choice, random.choice(subtext), result.link), emoji=emoji['success'], no_bold=True)
        else:
            await pingbot.Utils(self.bot, ctx.message).text("{}, {}".format(random.choice(subtext), result.link), emoji=emoji['success'], no_bold=True)
        await self.save_imgur_file(result, command=choice)

    @commands.command(name='r34_games', pass_context=True)
    async def _r34_games(self, ctx, include_sub : bool=False):
        """
        🍆 Returns a random rule34 image of a video game character.

        --------------------
          USAGE: r34_games
        EXAMPLE: r34_games
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'r34_games'):
            return
        choice = random.choice(['portalporn', 'pixelartnsfw', 'Overwatch_Porn', 'mariorule34', 'smashbros34', 'TheLostWoods', 'metroid34', 'pokeporn', 'fire_emblem_r34', 'animalcrossingr34', 'sonic34', 'slutoon', 'FalloutRule34', 'undertail'])
        result = self.return_subreddit_result(choice)
        if include_sub == True:
            await pingbot.Utils(self.bot, ctx.message).text("({}): {}, {}".format(choice, random.choice(subtext), result.link), emoji=emoji['success'], no_bold=True)
        else:
            await pingbot.Utils(self.bot, ctx.message).text("{}, {}".format(random.choice(subtext), result.link), emoji=emoji['success'], no_bold=True)
        await self.save_imgur_file(result, command=choice)

    @commands.command(name="gay", pass_context=True)
    async def _gay_porn(self, ctx):
        """
        🍆 Returns a random pornographic image that targets the LGBT community demographic (basically gay porn.)

        --------------------
          USAGE: gay
        EXAMPLE: gay
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'gay'):
            return
        result = self.return_subreddit_result(random.choice(['gayporn', 'publicboys', 'LGBTGoneWild']))
        await pingbot.Utils(self.bot, ctx.message).text("{}, {}".format(random.choice(subtext), result.link), emoji=emoji['success'], no_bold=True)
        await self.save_imgur_file(result, command="gay")

    @commands.command(name="subreddit_get", pass_context=True, hidden=True)
    async def _get_subreddit(self, ctx, subreddit : str):
        """
        🍆 Subreddit test.

        --------------------
          USAGE: subreddit_get <subreddit>
        EXAMPLE: subreddit_get <subreddit>
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'subreddit_get'):
            return
        result = self.return_subreddit_result(subreddit)
        await pingbot.Utils(self.bot, ctx.message).text("{}, {}".format(random.choice(subtext), result.link), emoji=emoji['success'], no_bold=True)

    async def auto_nsfw(self):
        """
        The auto-NSFW loop.

        This will output a random NSFW image to the auto-nsfw channel.
        """
        if no_auto_nsfw_channel_start:
            pingbot.errors.debug_print("Auto NSFW channels are disabled.")
            return
        print("Task started!")
        await self.bot.wait_until_ready()
        while not self.bot.is_closed:
            #print("Task: " + channel)
            
            nsfw_config = pingbot.Config('./user/cogs/nsfw/nsfw_info.json').load_json()
            for server in nsfw_config["servers"]:
                self.install_auto_nsfw_ifno(server_id=server)
                nsfw_config = pingbot.Config('./user/cogs/nsfw/nsfw_info.json').load_json()
                for channel in nsfw_config["servers"][server]["auto_nsfw_channels"]:
                    nsfw_types = pingbot.Config(nsfw_config_dir).load_json()["nsfw_types"]
                    nsfw_type = nsfw_config["servers"][server]["auto_nsfw_channels"][channel]
                    channel = discord.Object(id=channel)
                    try:
                        if nsfw_type in nsfw_types:
                            nsfw_type = pingbot.Config(nsfw_config_dir).load_json()["nsfw_types"][nsfw_type]
                            link1 = self.return_subreddit_result(random.choice(nsfw_type))
                            link2 = self.return_subreddit_result(random.choice(nsfw_type))
                            link3 = self.return_subreddit_result(random.choice(nsfw_type))
                        else:
                            link1 = self.return_subreddit_result(random.choice(nsfw_type))
                            link2 = self.return_subreddit_result(random.choice(nsfw_type))
                            link3 = self.return_subreddit_result(random.choice(nsfw_type))

                        if link1 == None:
                            link1 = self.return_subreddit_result(nsfw_type)
                        if link2 == None:
                            link2 = self.return_subreddit_result(nsfw_type)
                        if link3 == None:
                            link3 = self.return_subreddit_result(nsfw_type)

                        try:
                            link1_l = link1.link
                        except AttributeError:
                            link1_l = "Unknown link"

                        try:
                            link2_l = link2.link
                        except AttributeError:
                            link2_l = "Unknown link"

                        try:
                            link3_l = link3.link
                        except AttributeError:
                            link3_l = "Unknown link"

                        await self.bot.send_message(channel, '\n'.join([link1_l, link2_l, link3_l]))
                    except imgurpython.helpers.error.ImgurClientError as e:
                        await self.bot.send_message(channel, "Imgur client error occurred. \n{}".format(e.__str__))

            await asyncio.sleep(200)

#---------------- Utilities ----------------#
    def return_subreddit_result(self, subreddit, sort=None):
        """
        Returns a random item from a subreddit.
        """
        if sort != None:
            try:
                result = random.choice(imgur_client.subreddit_gallery(subreddit, sort=sort))
                return result
            except IndexError:
                return None
        else:
            try:
                result = random.choice(imgur_client.subreddit_gallery(subreddit))
                return result
            except IndexError:
                return None

    async def save_nsfw_file(self, url, **kwargs):
        """
        Saves the NSFW file to the collection folder.
        """
        #So yeah, this is pretty messy...
        if save_nsfw == True:
            file_name = kwargs.get('file_name', url)
            no_convert_name = kwargs.get('no_convert', False)
            no_convert_file = kwargs.get('no_convert_file', False)
            direct_save = kwargs.get('direct_save', False)
            executed_command = kwargs.get('command', None)
            if not os.path.exists(nsfw_save_dir):
                os.makedirs(nsfw_save_dir)
            if direct_save == True:
                await pingbot.WT(url).async_save_image(nsfw_save_dir + '/{}'.format(file_name))
                return
            if no_convert_name == False:
                file_name = file_name.replace('/', '-')
            else:
                file_name = file_name
            if no_convert_file == False:
                if url.endswith('.jpeg') or url.endswith('.jpg'):
                    file_ext = '.jpg'
                elif url.endswith('.png'):
                    file_ext = '.png'
                elif url.endswith('.gif'):
                    file_ext = '.gif'
                else:
                    file_ext = ""
            if executed_command == None:
                command = ""
            else:
                command = "_{}".format(executed_command)
            if not file_name.endswith(tuple(['.jpeg', '.jpg', '.png', '.gif'])):
                if os.path.isfile(nsfw_save_dir + '/{}{}.{}'.format(url, command, file_ext)):
                    return
                await pingbot.WT(url).async_save_image(nsfw_save_dir + '/{}{}.{}'.format(file_name, command, file_ext))
            else:
                if os.path.isfile(nsfw_save_dir + '/{}{}'.format(url, command)):
                    return
                await pingbot.WT(url).async_save_image(nsfw_save_dir + '/{}{}'.format(file_name, command))
            return
        else:
            print("NSFW Saving isnt enabled.")

    async def save_imgur_file(self, imgur_object, **kwargs):
        """
        Saves the imgur NSFW file to the collection folder.
        """
        executed_command = kwargs.get('command', None)
        if save_nsfw == True:
            if imgur_object.type == 'image/jpeg':
                file_type = 'jpg'
            elif imgur_object.type == 'image/gif':
                file_type = 'gif'
            elif imgur_object.type =='image/png':
                file_type = 'png'
            else:
                print("[]: could not find the file type")
                return #if the file type is unknown, then just quit

            if not os.path.exists(nsfw_save_dir):
                os.makedirs(nsfw_save_dir)

            if executed_command == None:
                command = ""
            else:
                command = "_{}".format(executed_command)

            if os.path.isfile('./user/cogs/nsfw/collection/{}{}.{}'.format(imgur_object.id, command, file_type)): #if the file already exists, then dont bother
                print("[]: file already exists, quitting...")
                return
            await pingbot.WT(imgur_object.link).async_save_image(nsfw_save_dir + '/{}{}.{}'.format(imgur_object.id, command, file_type))
        else:
            print("[]: save nsfw files is set to false")
            return

    def nsfw_check_chan(self, ctx):
        """
        Checks if the channel is NSFW or not.
        """
        try:
            nsfw_channels = pingbot.Config('./user/cogs/nsfw/nsfw_info.json').load_json()["servers"][ctx.message.server.id]["nsfw_channels"]
        except KeyError:
            nsfw_channels = pingbot.Config('./user/cogs/nsfw/nsfw_info.json').load_json()
            if ctx.message.server.id not in nsfw_channels["servers"]:
                nsfw_channels["servers"][ctx.message.server.id] = {}
            nsfw_channels["servers"][ctx.message.server.id]["nsfw_channels"] = []
            pingbot.Config('./user/cogs/nsfw/nsfw_info.json').write_json(nsfw_channels)
            nsfw_channels = pingbot.Config('./user/cogs/nsfw/nsfw_info.json').load_json()["servers"][ctx.message.server.id]["nsfw_channels"]

        if ctx.message.channel.id not in nsfw_channels:
            return True
        else:
            return False

    def is_auto_nsfw_chan(self, ctx):
        """
        Checks if the channel is auto-NSFW or not.
        """
        try:
            auto_nsfw_channel = pingbot.Config('./user/cogs/nsfw/nsfw_info.json').load_json()["servers"][ctx.message.server.id]["auto_nsfw_channels"]
        except KeyError:
            auto_nsfw_channel = pingbot.Config('./user/cogs/nsfw/nsfw_info.json').load_json()
            auto_nsfw_channel["servers"][ctx.message.server.id]["auto_nsfw_channels"] = {}
            pingbot.Config('./user/cogs/nsfw/nsfw_info.json').write_json(auto_nsfw_channel)

            auto_nsfw_channel = pingbot.Config('./user/cogs/nsfw/nsfw_info.json').load_json()["servers"][ctx.message.server.id]["auto_nsfw_channels"]

        if ctx.message.channel.id not in auto_nsfw_channel.keys():
            return False
        else:
            return True

    def install_auto_nsfw_ifno(self, ctx=None, server_id=None):
        """
        Adds the auto_nsfw_channel configuration if it doesn't exist.
        """
        nsfw_config = pingbot.Config('./user/cogs/nsfw/nsfw_info.json').load_json()
        if server_id == None:
            server = ctx.message.server.id
        else:
            server = server_id

        if "auto_nsfw_channels" not in nsfw_config["servers"][server]:
            nsfw_config["servers"][server]["auto_nsfw_channels"] = {}

            pingbot.Config('./user/cogs/nsfw/nsfw_info.json').write_json(nsfw_config)

            #auto_nsfw_channel = pingbot.Config('./user/config/server.json').load_json()[server]["auto_nsfw_channel"]

    async def is_disabled_or_no_nsfw(self, ctx, *args):
        """
        Checks if the command is disabled or if the command has been executed in a non-NSFW channel.
        """
        if ctx.message.channel.is_private:
            return False
        if pingbot.Utils().cmd_is_disabled_list_form(ctx, list(args)):
            await pingbot.Utils(self.bot, ctx.message).text(cmd_disabled, emoji=emoji["failure"])
            return True
        if self.nsfw_check_chan(ctx):
            await pingbot.Utils(self.bot, ctx.message).text(no_nsfw_chan + "(to set the current channel as a NSFW channel, use `set-nsfw`)", emoji=emoji["failure"])
            return True
#-------------------------------------------#

#---------------- Events ----------------#
    async def nsfw_server_join(self, server):
        """
        on_server_join listener.
        """
        nsfw_config = pingbot.Config(nsfw_config_dir).load_json()

        if server.id not in nsfw_config["servers"]:
            nsfw_config["servers"][server.id] = {}

        if "nsfw_channels" not in nsfw_config["servers"][server.id]:
            nsfw_config["servers"][server.id]["nsfw_channels"] = []

        if "auto_nsfw_channels" not in nsfw_config["servers"][server.id]:
            nsfw_config["servers"][server.id]["auto_nsfw_channels"] = {}

        pingbot.Config(nsfw_config_dir).write_json(nsfw_config)

    async def nsfw_server_remove(self, server):
        """
        on_server_remove listener.
        """
        nsfw_config = pingbot.Config(nsfw_config_dir).load_json()

        if server.id in nsfw_config["servers"]:
            nsfw_config["servers"].pop(server.id)

        pingbot.Config(nsfw_config_dir).write_json(nsfw_config)

    async def nsfw_channel_delete(self, channel):
        """
        on_channel_create listener.
        """
        nsfw_config = pingbot.Config(nsfw_config_dir).load_json()

        if channel.id in nsfw_config["servers"][channel.server.id]["nsfw_channels"]:
            nsfw_config["servers"][channel.server.id]["nsfw_channels"].remove(channel.id)

        if channel.id in nsfw_config["servers"][channel.server.id]["auto_nsfw_channels"]:
            nsfw_config["servers"][channel.server.id]["auto_nsfw_channels"].pop(channel.id)

        pingbot.Config(nsfw_config_dir).write_json(nsfw_config)
#----------------------------------------#

def setup(bot):
    bot.add_listener(NSFW(bot).nsfw_server_join, "on_server_join")
    bot.add_listener(NSFW(bot).nsfw_server_remove, "on_server_remove")
    bot.add_listener(NSFW(bot).nsfw_channel_delete, "on_channel_delete")
    bot.add_cog(NSFW(bot))