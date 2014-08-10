import config
from pymongo import MongoClient

def get_connection(type):
	try:
		cf = config.get_config('mongo', type)
		if cf:
			mongo_client = MongoClient(cf['host'], cf['port'])
			db = mongo_client[cf['db']]
			return db
		else:
			raise Exception("Config not found for section %s, type %s" % ('mongo', type))
	except Exception as e:
		print str(e)