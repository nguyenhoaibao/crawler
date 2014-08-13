import requests
import threading
import Queue
import proxy_list

PROXY_DICT = {}
TIMEOUT = 24

def get_proxy():
	global PROXY_DICT
	PROXY_DICT = {
		'http' : "http://" + proxy_list.proxies.pop()
	}
	return PROXY_DICT

def request_to_url(url, useproxy):
	try:
		if useproxy:
			global PROXY_DICT
			if not PROXY_DICT:
				PROXY_DICT = get_proxy()
			print "Use proxy: " + str(PROXY_DICT)
			
			r = requests.get(url, proxies=PROXY_DICT, timeout=TIMEOUT)
		else:
			r = requests.get(url)
	except requests.exceptions.Timeout:
		raise Exception("Timeout")
	except requests.exceptions.RequestException as e:
		raise Exception("Error", e.args)
	else:
		return r.text


def get_html_from_url(url, useproxy):
	html = ''
	if url:
		while not html:
			try:
				html = request_to_url(url, useproxy)
			except Exception as e:	
				print str(e.args)
				#set PROXY_DICT empty
				global PROXY_DICT
				PROXY_DICT = {}
	else:
		print "No url specified!!!"
	return html
