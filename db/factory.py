import importlib

def get_connection(db, *type):
	if not type:
		type = 'read'
	if db:
		module = importlib.import_module("db.%s_connection" % db)
		conn = module.get_connection(type)
		return conn

def get_read_connection(db):
	return get_connection(db, 'read')

def get_write_connection(db):
	return get_connection(db, 'write')