import multiprocessing, re, time, os
from bs4 import BeautifulSoup
from time import strftime

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

		self.re_rm_url = re.compile(r"\?.*$", re.MULTILINE|re.DOTALL)

	def crawl(self):
		#get crawling urls
		crawling_urls = self.redis_conn.smembers(self.redis_crawling_urls)
		#get crawled urls
		crawled_urls = self.redis_conn.smembers(self.redis_crawled_urls)

		if not crawling_urls and not crawled_urls:
			urls = self.push_url_to_crawling_queue(self.init_url)
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

			urls = self.redis_conn.smembers(self.redis_crawled_urls)
			if urls:
				for url in urls:
					self.process_crawled_queue(url)

			time.sleep(120)

	def process_crawling_queue(self, url):
		try:
			#print "%s is crawling %s" % (multiprocessing.current_process().name, url)
			temp = url
			self.push_url_to_crawling_queue(url)
	                
			if re.search(self.product_pattern, temp):  #product url
				if not self.redis_conn.sismember(self.redis_product_urls, temp):
					#save product url to redis
					#use to set cron to update these product urls
					self.redis_conn.sadd(self.redis_product_urls, temp)
					#push to background job to parse
					tasks.parse_product_html.delay(self.site_name, temp)
			else:
				self.redis_conn.sadd(self.redis_crawled_urls, temp)
		except Exception, e:
			if os.environ.get('CRAWLER_ENV', 'dev') == 'dev':
				print str(e.args)
			pass

	def process_crawled_queue(self, url):
		try:
			#print "%s is crawling %s" % (multiprocessing.current_process().name, url)
			product_urls = self.push_url_to_crawling_queue(url)
			if product_urls:
				for url in product_urls:
					#save product url to redis
					#use to set cron to update these product urls
					self.redis_conn.sadd(self.redis_product_urls, url)
					#push to background job to parse
					tasks.parse_product_html.delay(self.site_name, url)
		except Exception, e:
			if os.environ.get('CRAWLER_ENV', 'dev') == 'dev':
				print str(e.args)
			pass

	def before_find_link(self, soup):
		return soup

	def format_href(self, href):
		href = re.sub(self.re_rm_url, '', href)
		return href

	def get_soup_html(self, url):
		#download html
		html = request_url.get_html_from_url(url, self.use_tor)
		if html:
			#get all link
			#trick for parse lazada page
			#TODO: test other page
			if self.init_url == 'http://www.lazada.vn':
				soup = BeautifulSoup(html, 'html5lib')
			else:
				soup = BeautifulSoup(html)

			#format soup before find link from soup
			soup = self.before_find_link(soup)
			return soup
		else:
			return ''

	def push_url_to_crawling_queue(self, url):
		soup = self.get_soup_html(url)
		if soup:

			#find all link from soup
			urls = soup.findAll('a')
			if urls:
				product_urls = []

				for url in urls:
					#get href
					href = url.get('href')

					if href and href != '/' and href not in product_urls:
						if href.startswith('/'):
							href = self.init_url + href

						if not href.startswith(self.init_url):
							continue

						if re.search(self.skip_url, href):
							continue

						#format url again before save to redis
						href = self.format_href(href)

						if not self.redis_conn.sismember(self.redis_crawled_urls, href) and not self.redis_conn.sismember(self.redis_product_urls, href):
							self.redis_conn.sadd(self.redis_crawling_urls, href)

							if re.search(self.product_pattern, href):
								product_urls.append(href)
				return product_urls

	def update(self):
		urls = self.redis_conn.smembers(self.redis_product_urls)
		if urls:
			for url in urls:
				tasks.parse_product_html.delay(self.site_name, url)
			with open('cron.txt', 'a') as file_:
				file_.write("%s Update all product of site %s \n" % (str(strftime("%Y-%m-%d %H:%M:%S")), self.site_name))
			pass