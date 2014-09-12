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

			while not urls:
				html = request_url.get_html_from_url(url, self.use_tor)

				if html:
					#get all link
					soup = BeautifulSoup(html)
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

								list_urls.append(href)
						return list_urls
					else:
						request_url.renew_connection()
		except Exception, e:
			print url, str(e.args)