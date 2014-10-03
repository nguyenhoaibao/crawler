import multiprocessing, re
from bs4 import BeautifulSoup

import request_url
from crawl import Crawl

SITE_NAME = 'nguyenkim'
INIT_URL = 'http://www.nguyenkim.com'
SKIP_URL = '\#|\\|trung\-tam|\.php|\.jpg'

REDIS_CRAWLING_URLS = 'nguyenkim_urls'
REDIS_CRAWLED_URLS = 'nguyenkim_crawled_urls'
REDIS_PRODUCT_URLS = 'nguyenkim_product_urls'

PRODUCT_PATTERN = '.*\.html$'

PROCESS_NUM = 2

USE_TOR = False

class Nguyenkim(Crawl):
	"""docstring for nguyenkim"""
	def __init__(self):
		init_params = {
			'site_name' : SITE_NAME,
			'init_url'  : INIT_URL,
			'skip_url'  : SKIP_URL,
			'redis_crawling_urls' : REDIS_CRAWLING_URLS,
			'redis_crawled_urls' : REDIS_CRAWLED_URLS,
			'redis_product_urls' : REDIS_PRODUCT_URLS,
			'product_pattern' : PRODUCT_PATTERN,
			'process_num' : PROCESS_NUM,
			'use_tor' : USE_TOR
		}
		Crawl.__init__(self, **init_params)
		#select collection
		self.mongo_collection = self.mongo_conn['nguyenkim_product']

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

	def feedproducturl(self):
		for data in self.mongo_collection.find():
			url = data.get('url')
			self.redis_conn.sadd(self.redis_product_urls, url)