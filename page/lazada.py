import threading, Queue, db.factory, request_url, stacktracer
import re
from urllib2 import Request, urlopen
from set_queue import SetQueue
from bs4 import BeautifulSoup
from pymongo import MongoClient

SITEMAP_URL = 'http://lazada.vn/sitemap-products.xml'

def get_url_from_sitemap():
	try:
		html = request_url.get_html_from_url(SITEMAP_URL)
		lazada_urls = re.findall('<loc>(.*?)</loc>', html)

		print len(lazada_urls), " links found!!!"
		return lazada_urls
	except Exception as e:
		print e.args

def get_url_to_crawl(**kwargs):
	try:
		#get url from redis set
		redis_conn = db.factory.get_connection('redis')

		#init queue
		#duplicate element does not allow
		if 'queue' in kwargs:
			q = kwargs['queue']
		else:
			q = Queue.Queue()

		lazada_urls = redis_conn.smembers('lazada_urls')

		if not lazada_urls or kwargs.get('refresh_url'):  #get new url from sitemap
			lazada_urls = get_url_from_sitemap()
			if lazada_urls:
				print "Importing %d links to redis sets (sets_name: lazada_urls)" % len(lazada_urls)
				for url in lazada_urls:
					#if not redis_conn.sismember('lazada_urls', url):
					redis_conn.sadd('lazada_urls', url)
					#put url to queue
					q.put(url)
				print "Import success!!!"

			else:
				print "No urls found from sitemap"
		elif 'cont' in kwargs and kwargs['cont']:
			#get mongo connection
			mongo_conn = db.factory.get_connection('mongo')
			#select collection
			mongo_collection = mongo_conn['lazada_product']

			urls_crawled = mongo_collection.find({}, {'url' : 1, '_id' : 0})
			urls_crawled_set = set()
			for url in urls_crawled:
				urls_crawled_set.add(url['url'])

			print "%s were crawled!!!" % len(urls_crawled_set) 

			lazada_urls = list(lazada_urls - urls_crawled_set)

			print "Continue to crawl %s urls" % len(lazada_urls)
			for url in lazada_urls:
				q.put(url)
		else:
			for url in lazada_urls:
				q.put(url)

	except Exception as e:
		print "Cannot get url to crawl: %s" + str(e.args)

def parse_lazada_product_url(q, i, mongo_collection):
	try:
		while q.get():
			#get url from queue
			url = q.get()

			print "Worker %s parsing url %s" % (i, url)
			
			#get product id
			product_id = re.search(r'(\d+)\.html$', url).group(1)

			#parse html from url
			html = request_url.get_html_from_url(url)
			
			#print re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', html)
			#return
			
			print "Trying to parse html from url %s" % url
			
			try:
				parsed_html = BeautifulSoup(html)
				
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
					'url'   : url
				}
			
				#insert data to mongo
				mongo_collection.insert(product_data)
			except Exception as e:
				print "Parse html error: %s" % str(e.args)
				print "Pass url %s" % url
				
				#logging parse url fail to file
				#with open('lazada-failed.txt', 'a') as f:
					#f.write(url + "\n")
				pass
		else:
			print "Crawl all urls"
	except Exception as e:
		print "Parse error: ", str(e)
		

def crawl(**kwargs):
	#get mongo connection
	mongo_conn = db.factory.get_connection('mongo')
	#select collection
	mongo_collection = mongo_conn['lazada_product']

	#use SetQueue to avoice duplicate url in Queue
	q = SetQueue()

	if 'cont' in kwargs and kwargs['cont']:
		get_url_to_crawl(queue = q, cont = True)
	else:
		get_url_to_crawl(queue = q)
	
	stacktracer.trace_start("trace.html")

	#start 5 threads
	for i in range(10):
		t = threading.Thread(target=parse_lazada_product_url, args=(q,i, mongo_collection,))
		t.start()
		
