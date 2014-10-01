import requests, requesocks, re, threading, sys
from TorCtl import TorCtl

session = ''
TIMEOUT = 12

def init_tor_session():
	global session
	if not session:
		session = requesocks.session()
		session.proxies = {
    			'http': 'socks5://127.0.0.1:9050',
    			'https': 'socks5://127.0.0.1:9050'
		}
		session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36'

def init():
	global session
	if not session:
		session = requests.session()
		session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36'

def renew_connection():
	try:
		threading.Lock().acquire()
	 	conn = TorCtl.connect(controlAddr="127.0.0.1", controlPort=9051, passphrase="Camicyoab")
		conn.send_signal("NEWNYM")
		conn.close()
	except:
		sys.exit()
	else:
		threading.Lock().release()
    		

def request_to_url(url):
	try:
		resp = session.get(url, timeout=TIMEOUT)
	except Exception as e:
		raise Exception("Error", e.args)
	else:
		return resp.text


def get_html_from_url(url, use_tor):
	html = ''
	if url:
		if use_tor:
			init_tor_session()
			i = 0
			while i < 3:	#retry 3 times
				try:
					html = request_to_url(url)
					return html
				except:
					#try to change ip
					renew_connection()
					i += 1
		else:
			init()
			try:
				html = request_to_url(url)
			except Exception as e:
				pass
	
	return html
