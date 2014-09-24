import threading, re
from bs4 import BeautifulSoup

import request_url
from crawl import Crawl
from background import tasks

INIT_URL = 'http://www.cdiscount.vn'
SKIP_URL = '\#|\\|huong\-dan\-mua\-hang|checkout|customer'
THREAD_NUM = 10
REDIS_URLS = 'cdiscount_urls'
USE_TOR = False

class Cdiscount(Crawl):
	"""docstring for Cdiscount"""
	def __init__(self):
		Crawl.__init__(self, INIT_URL, SKIP_URL, USE_TOR)
		#select collection
		self.mongo_collection = self.mongo_conn['cdiscount_product']

	def parse_url(self, url):
		try:
			temp = url
			urls = self.find_all_link_from_url(url)
			for url in urls:
				self.redis_conn.sadd(REDIS_URLS, url)

				#put to queue
				self.queue.put(url)
	                
			m = re.match(".*\.html$", temp)
			
			#with open('Failed.py', 'w') as file_:
				#file_.write(html.encode('utf-8'))
			#return
	                
			if m:  #product url
				tasks.parse_product_html.delay('cdiscount', temp)
		except Exception, e:
			print url, str(e.args)
			pass
	
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

	def parse_product_data(self, url):
		try:
			#print "parse product url: %s ..." % temp
			html = request_url.get_html_from_url(url, USE_TOR)

			if html:

				parsed_html = BeautifulSoup(html.encode('utf-8'))
				
				#with open('Failed.py', 'w') as file_:
				    #file_.write(html.encode('utf-8'))

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