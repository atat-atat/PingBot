from discord.ext import commands
from core import pingbot
from core.pingbot.messages import text
import aiohttp
import random
from urllib.parse import quote as urlquote
from urllib.parse import quote_plus
import urllib
import xml.etree.ElementTree as ET
from imgurpython import ImgurClient
from bs4 import BeautifulSoup, Tag
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
    - PornHub
    - And more...
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="set-nsfw", aliases=["set_nsfw"], pass_context=True, no_pm=True)
    @pingbot.permissions.has_permissions(manage_server=True, manage_channel=True)
    async def set_nsfw_channel(self, ctx):
        """
        🍆 Sets the NSFW channel.

        --------------------
          USAGE: set-nsfw
        EXAMPLE: set-nsfw
        --------------------
        """
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

    @commands.command(name="set-auto-nsfw", aliases=["set_auto_nsfw"], pass_context=True, no_pm=True)
    @pingbot.permissions.has_permissions(manage_server=True, manage_channel=True)
    async def _set_auto_nsfw_channel(self, ctx, nsfw_type : str='default'):
        """
        🍆 Sets the automatic NSFW-material-provider channel.

        --------------------
          USAGE: set-auto-nsfw <optional: nsfw type>
        EXAMPLE: set-auto-nsfw
        --------------------
        """
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

    @commands.command(aliases=["set-auto-nsfw-type", "auto-nsfw-type", "auto_nsfw_type"], pass_context=True, no_pm=True)
    @pingbot.permissions.has_permissions(manage_server=True, manage_channel=True)
    async def set_auto_nsfw_type(self, ctx, nsfw_type : str):
        """
        🍆 Sets the auto-NSFW channel type.

        --------------------
          USAGE: auto-nsfw-type
        EXAMPLE: auto-nsfw-type
        --------------------
        """
        self.install_auto_nsfw_ifno(ctx)
        nsfw_config = pingbot.Config(nsfw_config_dir).load_json()

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

    @commands.command(name="nsfw-types", aliases=["nsfw_types"], pass_context=True)
    @pingbot.permissions.has_permissions()
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

    @commands.command(name="nsfw-cleanup", aliases=["nsfw_cleanup"], pass_context=True)
    @pingbot.permissions.has_permissions()
    async def clean_nsfw_content(self, ctx, amount : int=500):
        """
        🍆 Clears the past 500 messages that may have contained NSFW content.

        --------------------
          USAGE: nsfw-cleanup <optional: amount of messages>
        EXAMPLE: nsfw-cleanup
        --------------------
        """

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
                elif 'http://www.pornhub.com' in m.content:
                    return True
                elif 'http://www.nuvid.com' in m.content:
                    return True
                elif 'http://www.gotporn.com' in m.content:
                    return True
                elif 'http://www.xvideos.com' in m.content:
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
            await text(no_bot_perm, emoji=emoji["failure"])

    @commands.command(aliases=["tits", "melons"], pass_context=True)
    async def boobs(self, ctx):
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

    @commands.command(aliases=["butts", "ass"], pass_context=True)
    async def butt(self, ctx):
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
        url = "http://api.redtube.com/?data=redtube.Videos.searchVideos&output=json&search={}&thumbsize=medium".format(kw)
        results = await pingbot.WT().async_json_content(url)
        if "videos" not in results:
            await text(no_results.format(query), emoji=emoji["failure"])
            return
        try:
            video_select = random.randint(0, len(results["videos"]))
            video_url = results["videos"][video_select]["video"]["url"]
            video_thumb_int = random.randint(0, len(results["videos"][video_select]["video"]["thumbs"]))
            video_thumb = results["videos"][video_select]["video"]["thumbs"][video_thumb_int]["src"]
        except IndexError:
            video_select = 0
            video_url = results["videos"][video_select]["video"]["url"]
            video_thumb_int = random.randint(0, len(results["videos"][video_select]["video"]["thumbs"]))
            video_thumb = results["videos"][video_select]["video"]["thumbs"][video_thumb_int]["src"]
        try:
            await text("{}\n**Thumbnail:** {}".format(video_url, video_thumb), no_bold=True)
        except discord.errors.HTTPException:
            await text("HTTP Exception error occurred.", emoji=emoji["error"])

    @commands.command(pass_context=True)
    async def nuvid(self, ctx, *, keyword : str):
        """
        🍆 Searches for an item from NuVid

        --------------------
          USAGE: nuvid <keyword>
        EXAMPLE: nuvid blowjob
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'nuvid'): #check if the command is disabled, or if the server has a NSFW channel and check if the messaged channel is a NSFW channel
            return
        query = keyword.replace(" ", "-").lower()
        url = "http://www.nuvid.com/search/videos/{}".format(query)
        resp = await pingbot.WT().async_url_content(url)
        soup = BeautifulSoup(resp, "html.parser")
        results = []
        for a in soup.find_all('a', href=True):
            if a['href'].startswith('/video/'):
                results.append("http://www.nuvid.com{}".format(a['href']))

        if len(results) == 0:
            await text("Yielded no results.")
            return

        result = random.choice(results)
        title = result.split('/')
        title = ' '.join(title[5:])
        title = title.split('-')
        title = ' '.join(title)

        await text("**{}**: {}".format(title, result), no_bold=True)

    @commands.command(pass_context=True)
    async def pornhub(self, ctx, *, keyword : str):
        """
        🍆 Searches for an item from PornHub.com

        --------------------
          USAGE: pornhub <keyword>
        EXAMPLE: pornhub blowjob
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'pornhub'): #check if the command is disabled, or if the server has a NSFW channel and check if the messaged channel is a NSFW channel
            return
        query = quote_plus(keyword)
        url = "http://www.pornhub.com/video/search?search={}".format(query)
        resp = await pingbot.WT().async_url_content(url)
        soup = BeautifulSoup(resp, "html.parser")
        results = []
        for a in soup.find_all('a', href=True):
            if a['href'].startswith('/view_video.php?viewkey='):
                results.append('http://www.pornhub.com{}'.format(a['href']))

        if len(results) == 0:
            await text("Yielded no results.")
            return

        result = random.choice(results)
        await text(result, no_bold=True)

    @commands.group(pass_context=True, aliases=["hh"])
    async def hentaihaven(self, ctx):
        """
        🍆 Searches for an item from HentaiHaven

        --------------------
          USAGE: hentaihaven <keyword>
        EXAMPLE: hentaihaven bible black
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'hentaihaven', 'hh'): #check if the command is disabled, or if the server has a NSFW channel and check if the messaged channel is a NSFW channel
            return
        if ctx.invoked_subcommand is None:
            keyword = ' '.join(ctx.message.content.split()[1:])
            if ctx.subcommand_passed:
                keyword = ' '.join(ctx.message.content.split()[1:])
                query = quote_plus(keyword)
                url = "http://hentaihaven.org/search/{}".format(query)
                resp = await pingbot.WT().async_url_content(url)
                soup = BeautifulSoup(resp, "html.parser")
                results = []
                for a in soup.find_all('a', href=True):
                    if not a['href'].startswith('http://hentaihaven.org/tag/') and not a['href'].startswith('http://hentaihaven.org/series/') and not a['href'].startswith('http://hentaihaven.org/contact-us/') and a['href'].startswith('http://hentaihaven.org/') and a['href'] != "http://hentaihaven.org/pick-your-series/" and a['href'] != "http://hentaihaven.org/pick-your-poison/" and a['href'] != "http://hentaihaven.org/join-us/":
                        results.append(a['href'])

                if len(results) == 0:
                    await text("Yielded no results.")
                    return

                result1 = random.choice(results)
                results.remove(result1) #make sure we dont get the same results
                result2 = random.choice(results)
                results.remove(result2)
                result3 = random.choice(results)

                r_results = [result1, result2, result3]
                result = "**Found {} results out of {}**\n{}".format(len(r_results), len(results), "\n".join(r_results))
                await text(result, emoji="success", no_bold=True)
                return
            else: #if no query was provided, then choose from a random tag
                tags = ["1080p", "ahegao", "alien", "anal", "bdsm", "big-boobs", "blow-job", "bondage", "boob-job", "comedy", "cosplay", "creampie", "demon", "double-penetration", "dubbed", "exclusive", "facial", "femdom", "filmed", "foot-job", "futanari", "gangbang", "gender-bender", "piss", "hand-job", "harem", "horror", "incest", "inflation", "kemonomimi", "lactation", "licking", "loli", "maid", "marathon", "masturbation", "milf", "mind-break", "mindcontrol", "monster", "netorare", "netori", "nurse", "orgy", "plot", "pov", "pregnant", "public-sex", "rape", "raw", "reverse-rape", "rimjob", "scat", "school-girl", "shota", "softcore", "swimsuit", "teacher", "tentacle", "threesome", "toys", "tsundere", "uncensored", "vanilla", "virgin", "x-ray", "yaoi", "yuri"]

                tag = random.choice(tags)

                url = "http://hentaihaven.org/tag/{}/".format(tag)
                resp = await pingbot.WT().async_url_content(url)
                soup = BeautifulSoup(resp, "html.parser")
                results = []
                for a in soup.find_all('a', href=True):
                    if '/tag/' not in a['href'] and '/series/' not in a['href'] and a['href'].startswith('http://hentaihaven.org/') and a['href'] != "http://hentaihaven.org/pick-your-series/" and a['href'] != "http://hentaihaven.org" and a['href'] != "http://hentaihaven.org/pick-your-poison/" and a['href'] != "http://hentaihaven.org/contact-us/" and a['href'] != "http://animehaven.org" and a['href'] != "http://hentaihaven.org/join-us/" and 'facebook.com' not in a['href'] and 'google.com' not in a['href'] and 'twitter.com' not in a['href']:
                        results.append(a['href'])

                if 'http://bit.ly/29TQzA8' in results: #make sure it isnt getting its results from the cloudflare cache
                    await text("Yielded no results.", emoji="failure")
                    return

                result = random.choice(results)
                await text("**{}**: {}".format(tag[0].upper() + tag[1:], result), no_bold=True, emoji="success")

    @hentaihaven.command(pass_context=True, name="random")
    async def hh_random(self, ctx, tag : str=None):
        """
        🍆 Returns a random result from a HentaiHaven tag.

        --------------------
          USAGE: hentaihaven random <keyword>
        EXAMPLE: hentaihaven random loli
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'hentaihaven', 'hh'): #check if the command is disabled, or if the server has a NSFW channel and check if the messaged channel is a NSFW channel
            return
        if tag == None:
            tag_ = random.choice(["1080p", "ahegao", "alien", "anal", "bdsm", "big-boobs", "blow-job", "bondage", "boob-job", "comedy", "cosplay", "creampie", "demon", "double-penetration", "dubbed", "exclusive", "facial", "femdom", "filmed", "foot-job", "futanari", "gangbang", "gender-bender", "piss", "hand-job", "harem", "horror", "incest", "inflation", "kemonomimi", "lactation", "licking", "loli", "maid", "marathon", "masturbation", "milf", "mind-break", "mindcontrol", "monster", "netorare", "netori", "nurse", "orgy", "plot", "pov", "pregnant", "public-sex", "rape", "raw", "reverse-rape", "rimjob", "scat", "school-girl", "shota", "softcore", "swimsuit", "teacher", "tentacle", "threesome", "toys", "tsundere", "uncensored", "vanilla", "virgin", "x-ray", "yaoi", "yuri"])
        else:
            tag_ = tag
        url = "http://hentaihaven.org/tag/{}/".format(tag_)
        resp = await pingbot.WT().async_url_content(url)
        soup = BeautifulSoup(resp, "html.parser")
        results = []
        for a in soup.find_all('a', href=True):
            if '/tag/' not in a['href'] and '/series/' not in a['href'] and a['href'].startswith('http://hentaihaven.org/') and a['href'] != "http://hentaihaven.org/pick-your-series/" and a['href'] != "http://hentaihaven.org" and a['href'] != "http://hentaihaven.org/pick-your-poison/" and a['href'] != "http://hentaihaven.org/contact-us/" and a['href'] != "http://animehaven.org" and a['href'] != "http://hentaihaven.org/join-us/" and 'facebook.com' not in a['href'] and 'google.com' not in a['href'] and 'twitter.com' not in a['href']:
                results.append(a['href'])

        if 'http://bit.ly/29TQzA8' in results: #make sure it isnt getting its results from the cloudflare cache
            await text("Yielded no results.", emoji="failure")
            return

        result = random.choice(results)
        if tag == None:
            result = "**{}**: {}".format(tag_[0].upper() + tag_[1:], result)

        await text(result, emoji="success")

    @commands.command(pass_context=True, aliases=["hardsextube"])
    async def gotporn(self, ctx, *, keyword : str):
        """
        🍆 Searches for an item from GotPorn/HardSexTube.

        --------------------
          USAGE: gotporn <keyword>
        EXAMPLE: gotporn blowjob
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'gotporn', 'hardsextube'): #check if the command is disabled, or if the server has a NSFW channel and check if the messaged channel is a NSFW channel
            return
        query = urlquote(keyword)
        url = "http://www.gotporn.com/results?search_query={}&src=ipt:b".format(query)
        resp = await pingbot.WT().async_url_content(url)
        soup = BeautifulSoup(resp, "html.parser")
        results = []
        for a in soup.find_all('a', href=True):
            if 'video-' in a['href'] and a['href'].startswith('http://www.gotporn.com/'):
                results.append(a['href'])

        if len(results) == 0:
            await text("Yielded no results.")
            return

        result = random.choice(results)
        await text(result)

    @commands.command(pass_context=True)
    async def drtuber(self, ctx, *, keyword : str):
        """
        🍆 Searches for an item from DrTuber

        --------------------
          USAGE: drtuber <keyword>
        EXAMPLE: drtuber blowjob
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'drtuber'): #check if the command is disabled, or if the server has a NSFW channel and check if the messaged channel is a NSFW channel
            return
        query = urlquote(keyword)
        url = "http://www.drtuber.com/search/videos/{}".format(query)
        resp = await pingbot.WT().async_url_content(url)
        soup = BeautifulSoup(resp, "html.parser")
        results = []
        for a in soup.find_all('a', href=True):
            if a['href'].startswith('/video/'):
                results.append("http://www.drtuber.com{}".format(a['href']))

        if len(results) == 0:
            await text("Yielded no results.")
            return
        
        result = random.choice(results)
        await text(result)

    @commands.command(pass_context=True)
    async def xhamster(self, ctx, *, keyword : str):
        """
        🍆 Searches for an item from xhamster.

        --------------------
          USAGE: xhamster <keyword>
        EXAMPLE: xhamster blowjob
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'xhamster'): #check if the command is disabled, or if the server has a NSFW channel and check if the messaged channel is a NSFW channel
            return
        query = quote_plus(keyword)
        url = "http://xhamster.com/search.php?from=&new=&q={}&qcat=video".format(query)
        resp = await pingbot.WT().async_url_content(url)
        soup = BeautifulSoup(resp, "html.parser")
        results = []
        for a in soup.find_all('a', href=True):
            if a['href'].startswith('http://xhamster.com/movies/'):
                results.append(a['href'])

        if len(results) == 0:
            await text("Yielded no results.")
            return

        result = random.choice(results)
        await text(result)

    @commands.command(pass_context=True)
    async def xvideos(self, ctx, *, keyword : str):
        """
        🍆 Searches for an item from xvideos.

        --------------------
          USAGE: xvideos <keyword>
        EXAMPLE: xvideos blowjob
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'xvideos'): #check if the command is disabled, or if the server has a NSFW channel and check if the messaged channel is a NSFW channel
            return
        query = quote_plus(keyword)
        url = "http://www.xvideos.com/?k={}".format(query)
        resp = await pingbot.WT().async_url_content(url)
        soup = BeautifulSoup(resp, "html.parser")
        results = []
        for a in soup.find_all('a', href=True):
            if a['href'].startswith('/video'):
                results.append("http://www.xvideos.com{}".format(a['href']))

        if len(results) == 0:
            await text("Yielded no results.")
            return

        result = random.choice(results)
        await text(result)

    @commands.command(pass_context=True)
    async def porn(self, ctx, *, keyword : str):
        """
        🍆 Searches for porn from a variety of sources based on a keyword.

        --------------------
          USAGE: porn <keyword>
        EXAMPLE: porn blowjob
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'porn'): #check if the command is disabled, or if the server has a NSFW channel and check if the messaged channel is a NSFW channel
            return
        source = "http://xhamster.com/search.php?from=&new=&q={}&qcat=video"

        if source == "http://xhamster.com/search.php?from=&new=&q={}&qcat=video":
            query = quote_plus(keyword)
            url = "http://xhamster.com/search.php?from=&new=&q={}&qcat=video".format(query)

            resp = await pingbot.WT().async_url_content(url)
            soup = BeautifulSoup(resp, "html.parser")
            results = []
            for a in soup.find_all('a', href=True):
                if a['href'].startswith('http://xhamster.com/movies/'):
                    results.append(a['href'])

            if len(results) > 0:
                result = random.choice(results)
                await text(result)
                return

        source = "http://www.drtuber.com/search/videos/{}"

        if source == "http://www.drtuber.com/search/videos/{}":
            query = urlquote(keyword)
            url = "http://xhamster.com/search.php?from=&new=&q={}&qcat=video".format(query)

            resp = await pingbot.WT().async_url_content(url)
            soup = BeautifulSoup(resp, "html.parser")
            results = []
            for a in soup.find_all('a', href=True):
                if a['href'].startswith('/video/'):
                    results.append("http://www.drtuber.com{}".format(a['href']))

            if len(results) > 0:
                result = random.choice(results)
                await text(result)
                return

        source = "http://www.gotporn.com/results?search_query={}&src=ipt:b"

        if source == "http://www.gotporn.com/results?search_query={}&src=ipt:b":
            query = urlquote(keyword)
            url = "http://www.gotporn.com/results?search_query={}&src=ipt:b".format(query)
            resp = await pingbot.WT().async_url_content(url)
            soup = BeautifulSoup(resp, "html.parser")
            results = []
            for a in soup.find_all('a', href=True):
                if 'video-' in a['href'] and a['href'].startswith('http://www.gotporn.com/'):
                    results.append(a['href'])

            if len(results) > 0:
                result = random.choice(results)
                await text(result)
                return

        source = "http://hentaihaven.org/search/{}"

        if source == "http://hentaihaven.org/search/{}":
            query = quote_plus(keyword)
            url = "http://hentaihaven.org/search/{}".format(query)
            resp = await pingbot.WT().async_url_content(url)
            soup = BeautifulSoup(resp, "html.parser")
            results = []
            for a in soup.find_all('a', href=True):
                if not a['href'].startswith('http://hentaihaven.org/tag/') and not a['href'].startswith('http://hentaihaven.org/series/') and not a['href'].startswith('http://hentaihaven.org/contact-us/') and a['href'].startswith('http://hentaihaven.org/'):
                    print(a['href'])
                    results.append(a['href'])

            if len(results) > 0:
                result = random.choice(results)
                await text(result)
                return

        source = "http://www.pornhub.com/video/search?search={}"

        if source == "http://www.pornhub.com/video/search?search={}":
            query = quote_plus(keyword)
            url = "http://www.pornhub.com/video/search?search={}".format(query)
            resp = await pingbot.WT().async_url_content(url)
            soup = BeautifulSoup(resp, "html.parser")
            results = []
            for a in soup.find_all('a', href=True):
                if a['href'].startswith('/view_video.php?viewkey='):
                    results.append('http://www.pornhub.com{}'.format(a['href']))

            if len(results) > 0:
                result = random.choice(results)
                await text(result)
                return

        source = "http://www.nuvid.com/search/videos/{}"

        if source == "http://www.nuvid.com/search/videos/{}":
            query = keyword.replace(" ", "-").lower()
            url = "http://www.nuvid.com/search/videos/{}".format(query)
            resp = await pingbot.WT().async_url_content(url)
            soup = BeautifulSoup(resp, "html.parser")
            results = []
            for a in soup.find_all('a', href=True):
                if a['href'].startswith('/video/'):
                    results.append("http://www.nuvid.com{}".format(a['href']))

            if len(results) > 0:
                result = random.choice(results)
                await text(result)
                return

        source = "http://api.redtube.com/?data=redtube.Videos.searchVideos&output=json&search={}&thumbsize=medium"

        if source == "http://api.redtube.com/?data=redtube.Videos.searchVideos&output=json&search={}&thumbsize=medium":
            kw = urlquote(query)
            url = "http://api.redtube.com/?data=redtube.Videos.searchVideos&output=json&search={}&thumbsize=medium".format(kw)
            results = await pingbot.WT().async_json_content(url)
            if 'message' not in results:
                video_select = random.randint(0, len(results["videos"]))
                video_url = results["videos"][video_select]["video"]["url"]
                await text(video_url)
                return

        source = "http://www.xvideos.com/?k={}"

        if source == "http://www.xvideos.com/?k={}":
            query = quote_plus(keyword)
            url = "http://www.xvideos.com/?k={}".format(query)
            resp = await pingbot.WT().async_url_content(url)
            soup = BeautifulSoup(resp, "html.parser")
            results = []
            for a in soup.find_all('a', href=True):
                if a['href'].startswith('/video'):
                    results.append("http://www.xvideos.com{}".format(a['href']))

            if len(results) > 0:
                result = random.choice(results)
                await text(result)
                return
            else:
                await text("Yielded no results.")
                return

    @porn.error
    async def porn_error(self, error, ctx):
        if isinstance(error, commands.MissingRequiredArgument):
            if await self.is_disabled_or_no_nsfw(ctx, 'porn'): #check if the command is disabled, or if the server has a NSFW channel and check if the messaged channel is a NSFW channel
                return
            choice = random.choice(['PetiteGoneWild', 'gonewild', 'porn_gifs', 'ClopClop', 'nsfw_gif', 'nsfw', 'hentai', 'hentaibondage', 'HENTAI_GIF', 'HQHentai', 'HentaiSource', 'Paizuri', 'Futanari', 'Touhou_NSFW', 'MonsterGirl', 'AnimeBooty', 'RealGirls', 'ginger', 'asstastic', 'LipsThatGrip', 'AsiansGoneWild', 'Unashamed', 'nsfw_html5', 'ladybonersgw', 'mangonewild', 'ChristianGirls', 'girlswithglasses', 'DarkAngels', 'gonewildcolor', 'japaneseporn', 'jilling', 'tentai', 'gamersgonewild', 'gayporn', 'LGBTGoneWild', 'publicboys', 'girlsdoingnerdythings', 'rule34'])
            result = self.return_subreddit_result(choice)
            await text("{}, {}".format(random.choice(subtext), result.link), emoji="success")
            await self.save_imgur_file(result, command=choice)

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
        if await self.is_disabled_or_no_nsfw(ctx, 'e621'): #check if the command is disabled, or if the server has a NSFW channel and check if the messaged channel is a NSFW channel
            return
        tag = urlquote(keyword)
        url = "https://e621.net/post/index.json?tags={}&limit=10".format(tag)
        resp = await pingbot.WT().async_json_content(url)
        if len(resp) == 0:
            await text(pingbot.get_message("e621_returned_none", direc=nsfw_config_dir), emoji="failure")
            return
        result = random.choice(resp)
        await text(result["file_url"], emoji=":dog:", no_bold=True)

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

    @commands.command(pass_context=True)
    async def hentai(self, ctx, include_sub : bool=False):
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

    @commands.command(pass_context=True)
    async def tsumino(self, ctx):
        """
        🍆 Returns a random book from Tsumino

        --------------------
          USAGE: tsumino
        EXAMPLE: tsumino
        --------------------
        """
        if await self.is_disabled_or_no_nsfw(ctx, 'tsumino'): #check if the command is disabled, or if the server has a NSFW channel and check if the messaged channel is a NSFW channel
            return
        url = "http://www.tsumino.com/Browse/Random"

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11"})

        url = urllib.request.urlopen(req).geturl()

        await text(url)

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
            try:
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
            except Exception as e:
                pingbot.Utils().cprint("red", "LOOP_ERROR@auto_nsfw! {}".format(pingbot.errors.get_traceback()))

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