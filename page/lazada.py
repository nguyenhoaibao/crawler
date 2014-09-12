import threading, re
from bs4 import BeautifulSoup

import db.factory, request_url
from crawl import Crawl
from set_queue import SetQueue

INIT_URL = 'http://www.lazada.vn'
SKIP_URL = '\#|\\|about|privacy|cart|customer|urlall|mobile|javascript|shipping|\.php|contact|huong\-dan|trung\-tam|faq'
THREAD_NUM = 10
REDIS_URLS = 'lazada_urls'
USE_TOR = False

class Lazada(Crawl):
	"""docstring for Lazada"""
	def __init__(self):
		Crawl.__init__(self, INIT_URL, SKIP_URL, USE_TOR)
		#select collection
		self.mongo_collection = self.mongo_conn['lazada_product']

	def parse_url(self, url):
		try:
			temp = url
			urls = self.find_all_link_from_url(url)
			for url in urls:
				self.redis_conn.sadd(REDIS_URLS, url)

				#put to queue
				self.queue.put(url)
	                
			m = re.match(".*(\d+)\.html$", temp)
	                
			if m:  #product url
	                        print "parse product url: %s ..." % temp
				html = request_url.get_html_from_url(temp, USE_TOR)

				parsed_html = BeautifulSoup(html)

				product_price_obj = parsed_html.body.find('span', {'class' : 'product-price'})

				if product_price_obj:

					#get product id
					product_id = re.search(r'(\d+)\.html$', temp).group(1)
						
					#parse product name
					product_name = parsed_html.body.findAll('span', {'class' : 'product-name'})[0].text.strip()

					#parse image
					product_image = parsed_html.body.find('img', {"data-placeholder": "placeholder.jpg"})['src']
				
					#parse price
					price = product_price_obj.text.strip()
					#use regular expression to replace VND and dot symbol
					price = re.sub('\s+VND|\.', '', price)
				
					product_data = {
						'product_id' : int(product_id),
						'name'  : product_name,
						'image' : product_image,
						'price' : price,
						'url'   : temp
					}
				
					#insert data to mongo
					self.mongo_collection.update({'product_id': int(product_id)}, product_data, upsert = True)
		except Exception, e:
			print url, str(e.args)
	
	def crawl(self):

		urls = self.redis_conn.smembers(REDIS_URLS)
		
		#first crawl
		if not urls:
			print "No url found from redis!!!"
			print "Find url from init url: %s" % INIT_URL
			#get list url from init url
			urls = self.find_all_link_from_url(INIT_URL)

	                print "Find %s urls ..." % len(urls)
			
			for url in urls:
				#insert all url to redis sets
				self.redis_conn.sadd(REDIS_URLS, url)
		
		#continue
		for url in urls:
			#put to queue
			self.queue.put(url)

	        print "Begin to crawl ..."

		#init threads
		for t in xrange(THREAD_NUM):
			print "Init thread %s ..." % t
			t = threading.Thread(target=self.start_crawl)
			#t.setDaemon(True)
			t.start()

	def start_crawl(self):
		while not self.queue.empty():
			url = self.queue.get()

			#remove url from redis sets
			self.redis_conn.srem(REDIS_URLS, url)

			try:
				print "Crawling url %s ..." % url
				self.parse_url(url)
			except Exception, e:
				print "Pass url: %s" % url
				pass