import multiprocessing, re, time
from bs4 import BeautifulSoup

#custom module
import db.factory, request_url
from background import tasks

class Crawl():
	"""class crawl"""
	def __init__(self, **params):
		#init redis connection
		self.redis_conn = db.factory.get_connection('redis')

		#init mongo connection
		self.mongo_conn = db.factory.get_connection('mongo')

		self.site_name = params['site_name']
		self.init_url = params['init_url']
		self.skip_url = params['skip_url']
		self.redis_crawling_urls = params['redis_crawling_urls']
		self.redis_crawled_urls = params['redis_crawled_urls']
		self.redis_product_urls = params['redis_product_urls']
		self.product_pattern = params['product_pattern']
		self.process_num = params['process_num']
		self.use_tor  = params['use_tor']

	def crawl(self):
		#get crawling urls
		crawling_urls = self.redis_conn.smembers(self.redis_crawling_urls)
		#get crawled urls
		crawled_urls = self.redis_conn.smembers(self.redis_crawled_urls)

		if not crawling_urls and not crawled_urls:
			urls = self.find_all_link_from_url(self.init_url)
			if urls:
				for url in urls:
					self.redis_conn.sadd(self.redis_crawling_urls, url)
			self.redis_conn.sadd(self.redis_crawled_urls, self.init_url)

		#multiprocessing.log_to_stderr()
		#logger = multiprocessing.get_logger()
		#logger.setLevel(logging.INFO)

		#init threads
		for t in xrange(self.process_num):
			t = multiprocessing.Process(target=self.start_crawl)
			#t.daemon = True
			t.start()

	def start_crawl(self):
		while self.redis_conn.scard(self.redis_crawling_urls) or self.redis_conn.scard(self.redis_crawled_urls):
			while self.redis_conn.scard(self.redis_crawling_urls):
				url = self.redis_conn.spop(self.redis_crawling_urls)
				if self.redis_conn.sismember(self.redis_crawled_urls, url) or self.redis_conn.sismember(self.redis_product_urls, url):
					continue
				self.process_crawling_queue(url)

			while self.redis_conn.scard(self.redis_crawled_urls):
				url = self.redis_conn.spop(self.redis_crawled_urls)
				self.process_crawled_queue(url)

			time.sleep(120)

	def process_crawling_queue(self, url):
		try:
			#print "%s is crawling %s" % (multiprocessing.current_process().name, url)
			temp = url
			urls = self.find_all_link_from_url(url)
			if urls:
				for url in urls:
					if self.redis_conn.sismember(self.redis_crawled_urls, url) or self.redis_conn.sismember(self.redis_product_urls, url):
						continue

					#put to crawling queue
					self.redis_conn.sadd(self.redis_crawling_urls, url)
	                
			if re.search(self.product_pattern, temp):  #product url
				if not self.redis_conn.sismember(self.redis_product_urls, temp):
					#save product url to redis
					#use to set cron to update these product urls
					self.redis_conn.sadd(self.redis_product_urls, temp)
					#push to background job to parse
					tasks.parse_product_html.delay(self.site_name, temp)
			else:
				self.redis_conn.srem(self.redis_crawling_urls, temp)
				self.redis_conn.sadd(self.redis_crawled_urls, temp)
		except Exception, e:
			pass

	def process_crawled_queue(self, url):
		try:
			#print "%s is crawling %s" % (multiprocessing.current_process().name, url)
			urls = self.find_all_link_from_url(url)
			if urls:
				for url in urls:
					if re.search(self.product_pattern, url) and not self.redis_conn.sismember(self.redis_product_urls, url):
						#save product url to redis
						#use to set cron to update these product urls
						self.redis_conn.sadd(self.redis_product_urls, url)
						#push to background job to parse
						tasks.parse_product_html.delay(self.site_name, url)
					elif not self.redis_conn.sismember(self.redis_crawled_urls, url):
						self.redis_conn.sadd(self.redis_crawling_urls, url)
		except Exception, e:
			pass

	def find_all_link_from_url_with_tor(self, url):
		try:
			urls = ''
			list_urls = []
			i = 0

			while i < 3:
				#download html
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
								
								if self.site_name == 'tiki':
									href = re.sub(r'(.*)\?.*(p=\d+).*', r'\1?\2', href)
								elif self.site_name == 'lazada':
									href = re.sub(r'(.*)\?.*(page=\d+).*', r'\1?\2', href)
								else:
									href = re.sub(r'\?.*$', '', href)

								list_urls.append(href)

						return list_urls
					
					#try to change ip	
					request_url.renew_connection()

				i += 1
		except Exception, e:
			pass

	def find_all_link_from_url_without_tor(self, url):
		try:
			urls = ''
			list_urls = []
			i = 0

			#download html
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

							if self.site_name == 'tiki':
								href = re.sub(r'(.*)\?.*(p=\d+).*', r'\1?\2', href)
							elif self.site_name == 'lazada':
								href = re.sub(r'(.*)\?.*(page=\d+).*', r'\1?\2', href)
							else:
								href = re.sub(r'\?.*$', '', href)

							list_urls.append(href)
				
			return list_urls
		except Exception, e:
			pass

	def find_all_link_from_url(self, url):
		if self.use_tor:
			return self.find_all_link_from_url_with_tor(url)
		return self.find_all_link_from_url_without_tor(url)

	def update(self):
		while self.redis_conn.scard(self.redis_product_urls):
			url = self.redis_conn.spop(self.redis_product_urls)
			tasks.parse_product_html.delay(self.site_name, url)