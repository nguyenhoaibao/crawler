import re

#custom module
import db.factory, request_url
from set_queue import SetQueue
from bs4 import BeautifulSoup

class Crawl():
	"""class crawl"""
	def __init__(self, init_url, skip_url):
		self.queue = SetQueue()

		#init redis connection
		self.redis_conn = db.factory.get_connection('redis')

		#init mongo connection
		self.mongo_conn = db.factory.get_connection('mongo')

		self.init_url = init_url

		self.skip_url = skip_url

	def find_all_link_from_url(self, url):
		try:
			html = request_url.get_html_from_url(url)

			list_urls = []

			if html:
				#get all link
				soup = BeautifulSoup(html)
				urls = soup.findAll('a')

				
				for url in urls:
					href = url.get('href')

					if href and href != '/' and href != self.init_url and not re.search(self.skip_url, href) and href not in list_urls:
						if not href.startswith('http://'):
							href = self.init_url + href
						if not href.startswith(self.init_url):
							continue

						list_urls.append(href)
			return list_urls
		except Exception, e:
			print url, str(e.args)