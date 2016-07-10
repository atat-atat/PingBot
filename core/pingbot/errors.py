"""
Error handling module.
"""

import traceback
import sys
from core import pingbot

class PingBotError(Exception):
	pass

class ConfigError(PingBotError):
	pass

class NoModChannel(PingBotError):
	pass

class CommandDisabledUser(PingBotError):
	pass

def debug_print(string, color="yellow"):
	debug = pingbot.Utils().check_start_arg("debug")
	if debug == True:
		pingbot.Utils().cprint(color, string)

def get_traceback():
	return Errors().get_traceback(*sys.exc_info())

class Errors:
	def __init__(self):
		self.recent_error = ""

	def set_new_error(self, traceback):
		self.recent_error = traceback
	
	def get_traceback(self, etype, value, tb, limit=None, file=None, chain=True):
		"""
		Based off of traceback script.
		Returns the traceback.

		USAGE: get_traceback(exception_type, value, throwback, kwargs)
		"""
		if file is None:
			file = sys.stderr
		exceptions = []
		for line in traceback.TracebackException(
				type(value), value, tb, limit=limit).format(chain=chain):
			exceptions.append(line)
		return "\n".join(exceptions)
	
	@property
	def last_error(self):
		return self.recent_error
	