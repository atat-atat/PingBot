import json
import configparser
import os
from core import pingbot

class Config:
	def __init__(self, directory=None):
		self._dir = directory

	def load_json(self, directory = None, read_mode = None):
		if directory == None:
			if self._dir == None:
				raise pingbot.errors.ConfigError("Failed to load JSON. A directory was not supplied with the function, or class.")
			else:
				directory = self._dir

		if read_mode == None:
			read_mode = 'r'
		else:
			read_mode = read_mode

		with open(directory, read_mode) as f:
			return json.load(f)

	def write_json(self, file, directory = None, write_mode='w+'):
		if directory == None:
			if self._dir == None:
				raise pingbot.errors.ConfigError("Failed to write to JSON. A directory was not supplied with the function, or class.")
			else:
				directory = self._dir

		with open(directory, write_mode) as f:
			json.dump(file, f)

	def load_ini(self, section, key, directory = None):
		if directory == None:
			if self._dir == None:
				raise pingbot.errors.ConfigError("Failed to load INI. A directory was not supplied with the function, or class.")
			else:
				directory = self._dir

		config = configparser.ConfigParser()
		config.read(directory)
		return config[section][key]

	def write_ini(self, section, key, value, directory = None, write_mode='w'):
		if directory == None:
			if self._dir == None:
				raise pingbot.errors.ConfigError("Failed to write to INI. A directory was not supplied with the function, or class.")
			else:
				directory = self._dir

		config = configparser.ConfigParser()
		config.read(directory)
		if not config.has_section(section):
			config.add_section(section)
		config[section][key] = value
		with open(directory, write_mode) as f:
			config.write(f)

	def write_ini_template(self, section, dictionary, directory=None):
		"""
		Writes to an INI file using a dictionary template.
		"""
		directory = self.dir_parse(directory)

		for key in dictionary:
			self.write_ini(section, key, dictionary[key])
		return

	def dir_parse(self, directory):
		if directory == None:
			if self._dir == None:
				raise pingbot.errors.ConfigError("Failed to write to INI. A directory was not supplied with the function, or class.")
			else:
				return self._dir
		else:
			return directory

	def file_exists(self, file=None):
		file = self.dir_parse(file)

		if os.path.isfile(file):
			return True
		else:
			return False

	def dir_exists(self, directory=None):
		directory = self.dir_parse(directory)

		if os.path.exists(directory):
			return True
		else:
			return False

	def make_dir(self, directory=None):
		directory = self.dir_parse(directory)

		os.makedirs(directory)