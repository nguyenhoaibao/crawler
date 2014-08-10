import os, ConfigParser, ast

#constant var
CRAWLER_ENV = os.environ.get('CRAWLER_ENV', 'dev')

def get_config(section, type):
	config = ConfigParser.RawConfigParser()
	config.read("config/%s.cfg" % CRAWLER_ENV)

	config = ast.literal_eval(config.get(section, CRAWLER_ENV))

	if config:
		return config[type]
	else:
		raise Exception("Config not found for section %s, type %s" % (section, type))

