"""
osu! Information Retriever.
(py3 stuff uses async)
"""

class OsuError(Exception):
	pass

import sys
import json
from core import pingbot

async def get_user(key, user, mode='0', stype='string', event_days=1):
	"""
	Returns the osu! User object.
	"""
	url = 'https://osu.ppy.sh/api/get_user?u={}&m={}&type={}&event_days={}&k={}'.format(user, mode, stype, event_days, key)
	osu_info = await pingbot.WT().async_json_content(url)
	if len(osu_info) <= 0:
		return None
	return User(osu_info[0]["user_id"], osu_info[0]["username"], osu_info[0]["count300"], osu_info[0]["count100"], osu_info[0]["count50"], osu_info[0]["playcount"], osu_info[0]["ranked_score"], osu_info[0]["total_score"], osu_info[0]["pp_rank"], osu_info[0]["level"], osu_info[0]["pp_raw"], osu_info[0]["accuracy"], osu_info[0]["count_rank_ss"], osu_info[0]["count_rank_s"], osu_info[0]["count_rank_a"], osu_info[0]["country"], osu_info[0]["pp_country_rank"], osu_info[0]["events"])

class User:
	"""
	osu! User/Player object.

	Parameters -

	key : the osu! api access key (https://osu.ppy.sh/p/api)
	user : the ID or username of the user.
	mode : the osu! mode.
	stype : the query type (string, id.)
	event_days : amount of event days from now.
	"""
	def __init__(self, user_id, username, count300, count100, count50, playcount, ranked_score, total_score, pp_rank, level, pp_raw, accuracy, count_rank_ss, count_rank_s, count_rank_a, country, pp_country_rank, events):
		self.user_id = user_id
		self.username = username
		self.avatar = "http://a.ppy.sh/{}".format(self.user_id)
		self.count300 = count300
		self.count100 = count100
		self.count50 = count50
		self.playcount = playcount
		self.ranked_score = ranked_score
		self.total_score = total_score
		self.pp_rank = pp_rank
		self.level = level
		self.pp_raw = pp_raw
		self.accuracy = accuracy
		self.count_rank_ss = count_rank_ss
		self.count_rank_s = count_rank_s
		self.count_rank_a = count_rank_a
		self.country = country
		self.pp_country_rank = pp_country_rank
		self.events = events
		self.user_profile = "https://osu.ppy.sh/u/{}".format(user_id)

	#@property
	#def user_id(self):
	#	return self.user_id
	