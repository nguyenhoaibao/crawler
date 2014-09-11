import requests, requesocks, re
from TorCtl import TorCtl

PROXY_DICT = {}
TIMEOUT = 24

session = ''

TIMEOUT = 48

def init():
	global session
	if not session:
		session = requesocks.session()
		session.proxies = {
    		'http': 'socks5://127.0.0.1:9050',
    		'https': 'socks5://127.0.0.1:9050'
		}
		session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.66 Safari/537.36'

def renew_connection():
    conn = TorCtl.connect(controlAddr="127.0.0.1", controlPort=9051, passphrase="Camicyoab")
    conn.send_signal("NEWNYM")
    conn.close()

def request_to_url(url):
	try:
		init()
		resp = session.get(url, timeout=TIMEOUT)

		print resp
		return

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


def get_html_from_url(url):
	html = ''
	if url:
		while not html:
			try:
				html = request_to_url(url)
			except Exception as e:
				#print str(e.args)
				renew_connection()
                pass
	else:
		print "No url specified!!!"
	return html
