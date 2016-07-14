"""
Basic file-write logging module.
"""

import datetime
import os
now = datetime.datetime.now()

class Log:
	def log(self, string, **kwargs):
		spec_time = kwargs.get("spec_time", now.strftime("%Y-%m-%d %H-%M"))
		spec_fname = kwargs.get("spec_fname", "{}.log".format(now.strftime("%Y-%m-%d %H-%M")))
		direc = kwargs.get("dir", "./log/{}".format(spec_fname))
		status = kwargs.get("type", None)

		if status != None:
			types = {
			"log": "[LOG]",
			"warn": "[WARNING]",
			"warning": "[WARNING]",
			"error": "[ERROR]"
			}

			try:
				t = types[status]
			except IndexError:
				t = "[UNKNOWN]"
			
			fmt = "\n{}{}".format(t, string)
		else:
			fmt = "\n{}".format(string)

		if not os.path.exists("./log"):
			os.makedirs("./log")

		with open(direc, 'ab') as f:
			output = fmt.encode('utf-8')
			f.write(output)