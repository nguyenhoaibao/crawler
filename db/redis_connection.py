import config, redis

def get_connection(type):
	try:
		cf = config.get_config('redis', type)
		if cf:
			#convert dict to kwargs
			#Refer: http://stackoverflow.com/questions/1559638/how-to-send-a-dictionary-to-a-function-that-accepts-kwargs
			pool = redis.ConnectionPool(**cf)
			r = redis.Redis(connection_pool=pool)
			return r
	except Exception as e:
		print e.args
  