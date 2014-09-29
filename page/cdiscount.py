import threading, re
from bs4 import BeautifulSoup

import request_url
from crawl import Crawl
from background import tasks

INIT_URL = 'http://www.cdiscount.vn'
SKIP_URL = '\#|\\|huong\-dan\-mua\-hang|checkout|customer'
THREAD_NUM = 2
REDIS_CRAWLING_URLS = 'cdiscount_urls'
REDIS_CRAWLED_URLS = 'cdiscount_crawled_urls'
REDIS_PRODUCT_URLS = 'cdiscount_product_urls'
USE_TOR = False

class Cdiscount(Crawl):
	"""docstring for cdiscount"""
	def __init__(self):
		Crawl.__init__(self, INIT_URL, SKIP_URL, USE_TOR)
		#select collection
		self.mongo_collection = self.mongo_conn['cdiscount_product']

	def process_crawling_queue(self, url, t):
		try:
			temp = url
			print "Thread %s is crawling url %s" % (str(t), url)
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
					tasks.parse_product_html.delay('cdiscount', temp)
			else:
				self.redis_conn.srem(REDIS_CRAWLING_URLS, temp)
				self.redis_conn.sadd(REDIS_CRAWLED_URLS, temp)
			print 'Thread %s done....' % str(t)
		except Exception, e:
			print str(e.args)

	def process_crawled_queue(self, url, t):
		try:
			print "Thread %s is crawling url %s" % (str(t), url)
			urls = self.find_all_link_from_url(url)
			if urls:
				for url in urls:					
					if re.search(".*\.html$", url) and not self.redis_conn.sismember(REDIS_PRODUCT_URLS, url):
						#print url
						#save product url to redis
						#use to set cron to update these product urls
						self.redis_conn.sadd(REDIS_PRODUCT_URLS, url)
						#push to background job to parse
						tasks.parse_product_html.delay('cdiscount', url)
					elif not self.redis_conn.sismember(REDIS_CRAWLED_URLS, url):
						self.redis_conn.sadd(REDIS_CRAWLING_URLS, url)
			print 'Thread %s done....' % str(t)
		except Exception, e:
			print str(e.args)
	
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
			t = threading.Thread(target=self.start_crawl, args=(t,))
			#t.setDaemon(True)
			t.start()

	def start_crawl(self, t):
		while True:
			#get crawling urls
			crawling_urls = self.redis_conn.smembers(REDIS_CRAWLING_URLS)
			
			if crawling_urls:
				for url in crawling_urls:
					#print url
					self.queue.put(url)
				while not self.queue.empty():
					url = self.queue.get()
					if self.redis_conn.sismember(REDIS_CRAWLED_URLS, url) or self.redis_conn.sismember(REDIS_PRODUCT_URLS, url):
						continue
					self.process_crawling_queue(url, t)
			
			#get crawled urls
			crawled_urls = self.redis_conn.smembers(REDIS_CRAWLED_URLS)
			if crawled_urls:
				for url in crawled_urls:
					self.queue.put(url)
				while not self.queue.empty():
					url = self.queue.get()
					self.process_crawled_queue(url, t)

	def parse_product_data(self, url):
		try:
			#print "parse product url: %s ..." % temp
			html = request_url.get_html_from_url(url, USE_TOR)

			if html:

				parsed_html = BeautifulSoup(html.encode('utf-8'))

				#parse product name
				product_obj = parsed_html.body.find('h1', attrs={'itemprop': 'name'})

				if product_obj:

					#product name
					product_name = product_obj.text.strip()
					
					#get product id
					product_id = parsed_html.body.find('select', {'id': 'estimated-time-select'})['data-pid']
					
					#parse image
					product_image = parsed_html.body.find('a', {'id': 'zoom1'}).find('img')['src']
				
					#parse price
					price = parsed_html.body.findAll('span', attrs={'class': 'price', 'id': re.compile(r".*")})
					if len(price) == 2:
						price = u'%s' % price[1].text.strip()
					else:
						price = u'%s' % price[0].text.strip()
					
					price = price.encode("ascii", "ignore")

					#use regular expression to replace VND and dot symbol
					price = re.sub('\.', '', price)
				
					product_data = {
						'product_id' : int(product_id),
						'name'  : product_name,
						'image' : product_image,
						'price' : price,
						'url'   : url
					}
				
					#insert data to mongo
					self.mongo_collection.update({'product_id': int(product_id)}, product_data, upsert = True)
		except Exception as e:
			#log info here
			#@TODO: send mail notify
			with open('fail.txt', 'a') as file_:
				file_.write('Cannot parse data from cdiscount. Error: ' + str(e.args))
			pass