import threading, Queue, db.factory, request_url
import re
from set_queue import SetQueue
from bs4 import BeautifulSoup
from crawl import Crawl

INIT_URL = 'http://www.nguyenkim.com'
SKIP_URL = '\#|\\|trung\-tam|gioi\-thieu|tieu\-chi|doi\-tac|dich\-vu|chinh\-sach|khu\-vuc|huong\-dan|doi\-tra|lien\-he|hop\-tac|giai\-thuong|bao\-mat|tuyen\-dung|dang\-ky|gio\-hang|\.php|khach\-hang|tai\-khoan|don\-hang|san\-pham|tra\-hang|lua\-dao|sinh\-nhat\-online'
THREAD_NUM = 10

class Nguyenkim(Crawl):
	"""docstring for NguyenkimCrawl"""
	def __init__(self):
		Crawl.__init__(self, INIT_URL, SKIP_URL)
		#select collection
		self.mongo_collection = self.mongo_conn['nguyenkim_product']

	def parse_url(self, url):
		try:
			temp = url
			urls = self.find_all_link_from_url(url)
			for url in urls:
				self.redis_conn.sadd('nguyenkim_urls', url)

				#put to queue
				self.queue.put(url)
	                
			m = re.match(".*\.html$", temp)
	                
			if m:  #product url
	                        print "parse product url: %s ..." % temp
				html = request_url.get_html_from_url(temp)

				parsed_html = BeautifulSoup(html)

				
				with open('Failed.py', 'w') as file_:
				    file_.write(html.encode('utf-8'))

				#print "here"
				#print parsed_html.body.find('div', {'class' : 'block_product-title'})
				return

				#get product id
				product_id = re.search(r'(\d+)\.html$', temp).group(1)
					
				#parse product name
				product_name = parsed_html.body.findAll('span', {'class' : 'product-name'})[0].text.strip()

				#parse image
				product_image = parsed_html.body.find('img', {"data-placeholder": "placeholder.jpg"})['src']
			
				#parse price
				price = parsed_html.body.find('span', {'class' : 'product-price'}).text.strip()
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

		urls = self.redis_conn.smembers('nguyenkim_urls')
		
		#first crawl
		if not urls:
			print "No url found from redis!!!"
			print "Find url from init url: %s" % INIT_URL
			#get list url from init url
			urls = self.find_all_link_from_url(INIT_URL)

	                print "Find %s urls ..." % len(urls)
			
			for url in urls:
				#insert all url to redis sets
				self.redis_conn.sadd('nguyenkim_urls', url)
		
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
			self.redis_conn.srem('nguyenkim_urls', url)

			try:
				print "Crawling url %s ..." % url
				self.parse_url(url)
			except Exception, e:
				print "Pass url: %s" % url
				pass