import requests, requesocks, re
from TorCtl import TorCtl

session = ''

TIMEOUT = 48

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
    conn = TorCtl.connect(controlAddr="127.0.0.1", controlPort=9051, passphrase="Camicyoab")
    conn.send_signal("NEWNYM")
    conn.close()

def request_to_url(url, use_tor):
	try:
		if use_tor:
			init_tor_session()
		else:
			init()
		resp = session.get(url, timeout=TIMEOUT)

		#if useproxy:
			#global PROXY_DICT
			#if not PROXY_DICT:
				#PROXY_DICT = get_proxy()
			#print "Use proxy: " + str(PROXY_DICT)
			
			#r = requests.get(url, proxies=PROXY_DICT, timeout=TIMEOUT)
		#else:
			#r = requests.get(url)
	except requesocks.exceptions.Timeout:
		raise Exception("Timeout")
		#renew_connection()
	except requests.exceptions.RequestException as e:
		raise Exception("Error", e.args)
		#pass
	except:
		print "Exception"
	else:
		return resp.text


def get_html_from_url(url, use_tor):
	html = ''
	if url:
		while not html:
			try:
				html = request_to_url(url, use_tor)
			except Exception as e:
				#print str(e.args)
				if use_tor:
					renew_connection()
                pass
	else:
		print "No url specified!!!"
	return html
