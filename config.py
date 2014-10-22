import os, ConfigParser, ast


def get_config(section, type, *task):
	CRAWLER_ENV = os.environ.get('CRAWLER_ENV', 'dev')

	config = ConfigParser.RawConfigParser()
	config.read("config/%s.cfg" % CRAWLER_ENV)

	var = 'default'
	if task:
		var = task[0]
	config = ast.literal_eval(config.get(section, var))

	if config:
		return config[type]
	else:
		raise Exception("Config not found for section %s, type %s" % (section, type))

