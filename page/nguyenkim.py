import threading, re
from bs4 import BeautifulSoup

import request_url
from crawl import Crawl
from background import tasks

INIT_URL = 'http://www.nguyenkim.com'
SKIP_URL = '\#|\\|trung\-tam|\.php|\.jpg'
THREAD_NUM = 10
REDIS_CRAWLING_URLS = 'nguyenkim_urls'
REDIS_CRAWLED_URLS = 'nguyenkim_crawled_urls'
REDIS_PRODUCT_URLS = 'nguyenkim_product_urls'
USE_TOR = False

class Nguyenkim(Crawl):
	"""docstring for nguyenkim"""
	def __init__(self):
		Crawl.__init__(self, INIT_URL, SKIP_URL, USE_TOR)
		#select collection
		self.mongo_collection = self.mongo_conn['nguyenkim_product']

	def process_crawling_queue(self, url):
		try:
			temp = url
			urls = self.find_all_link_from_url(url)
			if urls:
				for url in urls:
					if self.redis_conn.sismember(REDIS_CRAWLED_URLS, url) or self.redis_conn.sismember(REDIS_PRODUCT_URLS, url):
						continue

					#put to crawling queue
					self.redis_conn.sadd(REDIS_CRAWLING_URLS, url)

					#put to queue
					self.queue.put(url)
	                
			if re.search(".*\.html$", temp):  #product url
				if not self.redis_conn.sismember(REDIS_PRODUCT_URLS, temp):
					#save product url to redis
					#use to set cron to update these product urls
					self.redis_conn.sadd(REDIS_PRODUCT_URLS, temp)
					#push to background job to parse
					tasks.parse_product_html.delay('nguyenkim', temp)
			else:
				self.redis_conn.srem(REDIS_CRAWLING_URLS, temp)
				self.redis_conn.sadd(REDIS_CRAWLED_URLS, temp)
		except Exception, e:
			pass

	def process_crawled_queue(self, url):
		try:
			urls = self.find_all_link_from_url(url)
			if urls:
				for url in urls:
					if re.search(".*\.html$", url) and not self.redis_conn.sismember(REDIS_PRODUCT_URLS, url):
						#save product url to redis
						#use to set cron to update these product urls
						self.redis_conn.sadd(REDIS_PRODUCT_URLS, url)
						#push to background job to parse
						tasks.parse_product_html.delay('nguyenkim', url)
					elif not self.redis_conn.sismember(REDIS_CRAWLED_URLS, url):
						self.redis_conn.sadd(REDIS_CRAWLING_URLS, url)
		except Exception, e:
			pass
	
	def crawl(self):
		#get crawling urls
		crawling_urls = self.redis_conn.smembers(REDIS_CRAWLING_URLS)
		#get crawled urls
		crawled_urls = self.redis_conn.smembers(REDIS_CRAWLED_URLS)

		if not crawling_urls and not crawled_urls:
			urls = self.find_all_link_from_url(INIT_URL)
			if urls:
				for url in urls:
					self.redis_conn.sadd(REDIS_CRAWLING_URLS, url)

		#init threads
		for t in xrange(THREAD_NUM):
			#print "Init thread %s ..." % t
			t = threading.Thread(target=self.start_crawl)
			#t.setDaemon(True)
			t.start()

	def start_crawl(self):
		while True:
			#get crawling urls
			crawling_urls = self.redis_conn.smembers(REDIS_CRAWLING_URLS)
			
			if crawling_urls:
				for url in crawling_urls:
					self.queue.put(url)
				while not self.queue.empty():
					url = self.queue.get()
					if self.redis_conn.sismember(REDIS_CRAWLED_URLS, url) or self.redis_conn.sismember(REDIS_PRODUCT_URLS, url):
						continue
					self.process_crawling_queue(url)
			
			#get crawled urls
			crawled_urls = self.redis_conn.smembers(REDIS_CRAWLED_URLS)
			
			if crawled_urls:
				for url in crawled_urls:
					self.queue.put(url)
				while not self.queue.empty():
					url = self.queue.get()
					self.process_crawled_queue(url)

	def parse_product_data(self, url):
		try:
			#print "parse product url: %s ..." % temp
			html = request_url.get_html_from_url(url, USE_TOR)

			if html:
				parsed_html = BeautifulSoup(html.encode('utf-8'))

				#parse product name
				product_obj = parsed_html.body.find('h1', {'class' : 'block_product-title'})

				if product_obj:

					#product name
					product_name = product_obj.text.strip()

					#get product id
					product_id = parsed_html.body.find('span', attrs={'id': re.compile(r"product_code.*")}).text.strip()
					
					#parse image
					product_image = parsed_html.body.find('img', {"class": "pict"})['src']
				
					#parse price
					price = parsed_html.body.findAll('span', {'class' : 'price-num'})[0].text.strip()
					#use regular expression to replace VND and dot symbol
					price = re.sub('\s+VND|\.', '', price)

				
					product_data = {
						'product_id' : product_id,
						'name'  : product_name,
						'image' : product_image,
						'price' : price,
						'url'   : url
					}
				
					#insert data to mongo
					self.mongo_collection.update({'product_id': product_id}, product_data, upsert = True)
		except Exception as e:
			#log info here
			#@TODO: send mail notify
			with open('fail.txt', 'a') as file_:
				file_.write('Cannot parse data from nguyenkim. Error: ' + str(e.args))
			pass