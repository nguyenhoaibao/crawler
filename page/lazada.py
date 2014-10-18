import multiprocessing, re
from bs4 import BeautifulSoup

import request_url
from crawl import Crawl

SITE_NAME = 'lazada'
INIT_URL = 'http://www.lazada.vn'
SKIP_URL = 'urlall|mobile|shipping|\.php|contact|faq|chinh\-sach\-doi\-tra\-hang|about|huong\-dan|marketplace|privacy|terms\-of\-use|career|kiem\-tra\-don\-hang|link\-cac\-san\-pham|customer'

REDIS_CRAWLING_URLS = 'lazada_urls'
REDIS_CRAWLED_URLS = 'lazada_crawled_urls'
REDIS_PRODUCT_URLS = 'lazada_product_urls'

PRODUCT_PATTERN = '.*(\d+)\.html$'

PROCESS_NUM = 2

USE_TOR = False

class Lazada(Crawl):
	"""docstring for Lazada"""
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
		self.mongo_collection = self.mongo_conn['lazada_product']

		self.page_link_format = re.compile(r"(.*)\?.*(page=\d+).*", re.MULTILINE|re.DOTALL)

	def before_find_link(self, soup):
		for ul in soup.findAll('ul', { "class" : "fct-list" }):
			ul.extract()
		for div in soup.findAll('div', { "class" : "component-filters" }):
			div.extract()
		return soup

	def format_href(self, href):
		if re.search(self.page_link_format, href):
			href = re.sub(self.page_link_format, r'\1?\2', href)
		else:
			href = re.sub(self.re_rm_url, '', href)
		return href

	def parse_product_data(self, url):
		try:
			#print "parse product url: %s ..." % temp
			html = request_url.get_html_from_url(url, USE_TOR)

			if html:
				if html == '404':
					self.mongo_collection.update({"url" : url}, {"$set" : {"is_active" : 0}})
					return

				parsed_html = BeautifulSoup(html, 'html5lib')

				product_name_obj = parsed_html.body.find('h1', {'id' : 'prod_title'})

				if product_name_obj:

					#get product id
					product_id = re.search(r'(\d+)\.html$', url).group(1)
						
					#parse product name
					product_name = product_name_obj.text.strip()

					#parse image
					product_image = parsed_html.body.findAll('span', {"class": "productImage"})[0]['data-image']
				
					#parse price
					price = parsed_html.body.find('span', {'id': 'product_price'}).text.strip()
					
					#use regular expression to replace VND and dot symbol
					price = re.sub('\s+VND|\.\d+$', '', price)
				
					product_data = {
						'product_id' : int(product_id),
						'name'  : product_name,
						'image' : product_image,
						'price' : price,
						'url'   : url,
						'is_active': 1
					}
				
					#insert data to mongo
					self.mongo_collection.update({'product_id': int(product_id)}, product_data, upsert = True)
		except Exception as e:
			#log info here
			#@TODO: send mail notify
			with open('fail.txt', 'a') as file_:
				file_.write('Cannot parse data from lazada. Error: ' + str(e.args))
			pass

	def feedproducturl(self):
		for data in self.mongo_collection.find():
			url = data.get('url')
			url = re.sub(r'\?.*$', '', url)
			self.redis_conn.sadd(self.redis_product_urls, url)