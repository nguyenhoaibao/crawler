import threading, Queue, db.factory, request_url
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
		else:
			for url in lazada_urls:
				q.put(url)

	except Exception as e:
		print "Cannot get url to crawl: %s" + str(e.args)

def parse_lazada_product_url(q, i):
	try:
		#get mongo connection
		mongo_connect = db.factory.get_connection('mongo')
		#select collection
		mongo_collection = mongo_connect['lazada_product']
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
			
				#parse price
				price = parsed_html.body.find('span', {'class' : 'product-price'}).text.strip()
				#use regular expression to replace VND and dot symbol
				price = re.sub('\s+VND|\.', '', price)
			
				product_data = {
					'product_id' : int(product_id),
					'name'  : product_name,
					'price' : price,
					'url'   : url
				}
			
				#insert data to mongo
				mongo_collection.insert(product_data)
			except:
				print "Parse html error"
				print "Pass url %s" % url
				
				#logging parse url fail to file
				#with open('lazada-failed.txt', 'a') as f:
					#f.write(url + "\n")
				pass
	except Exception as e:
		print "Parse error: ", str(e)
		


def crawl(**kwargs):
	#use SetQueue to avoice duplicate url in Queue
	q = SetQueue()

	#get url to crawl
	#urls is put in q
	get_url_to_crawl(queue = q)

	#start 5 threads
	for i in range(10):
		t = threading.Thread(target=parse_lazada_product_url, args=(q,i,))
		t.start()
		
