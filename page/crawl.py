import re

#custom module
import db.factory, request_url
from set_queue import SetQueue
from bs4 import BeautifulSoup

class Crawl():
	"""class crawl"""
	def __init__(self, init_url, skip_url, use_tor):
		self.queue = SetQueue()

		#init redis connection
		self.redis_conn = db.factory.get_connection('redis')

		#init mongo connection
		self.mongo_conn = db.factory.get_connection('mongo')

		self.init_url = init_url
		self.skip_url = skip_url
		self.use_tor  = use_tor

	def find_all_link_from_url(self, url):
		try:
			urls = ''
			list_urls = []
			i = 0

			while not urls:	#try to request 3 times
				html = request_url.get_html_from_url(url, self.use_tor)

				if html:
					#get all link
					#trick for parse lazada page
					#TODO: test other page
					soup = BeautifulSoup(html)
					if self.init_url == 'http://www.lazada.vn':
						soup = BeautifulSoup(html, 'html5lib')
					
					urls = soup.findAll('a')

					if urls:
						for url in urls:
							href = url.get('href')

							if href and href != '/' and href not in list_urls and href != self.init_url:
								if href.startswith('/'):
									href = self.init_url + href

								if not href.startswith(self.init_url):
									continue

								if re.search(self.skip_url, href):
									continue
								
								href = re.sub(r'\?.*$', '', href)

								list_urls.append(href)
					if self.use_tor:
						request_url.renew_connection()
					else:
						return list_urls
		except Exception, e:
			print url, str(e.args)
