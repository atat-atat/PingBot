"""
PingBot Utilities Module.
"""

from .utils import Utils
from .config import Config
from .errors import *
from .log import Log
from .webtools import WT
from .permissions import *
from .osu import *
from .myanimelist import *
from .messages import *
from .omdb import *
from .giphy import *

def get_emoji(emoji):
	"""
	Short version of Utils().get_config_emoji
	"""
	return Utils().get_config_emoji(emoji)

def get_error(error):
	"""
	Short version of Utils().get_config_message
	"""
	return Utils().get_config_message(error)

def get_message(message, event=False, **kwargs):
	"""
	Short version of Utils().get_config_message
	"""
	if event == True:
	 	return Utils().get_config_event_message(message, **kwargs)
	else:
	 	return Utils().get_config_message(message, **kwargs)

def get_event_message(message, **kwargs):
	"""
	Short version of Utils().get_config_event_message
	"""
	return Utils().get_config_event_message(message, **kwargs)

def get_event_msg(message, **kwargs):
	"""
	Short version of Utils().get_config_event_message
	"""
	return Utils().get_config_event_message(message, **kwargs)