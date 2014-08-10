import threading, Queue, db.factory, request_url
from re import findall
from urllib2 import Request, urlopen
from set_queue import SetQueue
from bs4 import BeautifulSoup
from pymongo import MongoClient

SITEMAP_URL = 'http://lazada.vn/sitemap-products.xml'

def get_url_from_sitemap():
	try:
		html = request_url.get_html_from_url(SITEMAP_URL)
		lazada_urls = findall('<loc>(.*?)</loc>', html)

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
		print "Worker %s" % i
		#get url from queue
		url = q.get()

		#parse html from url
		html = request_url.get_html_from_url(url)
		parsed_html = BeautifulSoup(html)

		#get mongo connection
		mongo_connect = db.factory.get_connection('mongo')

		parsed_html = BeautifulSoup(html)

		price = parsed_html.body.find('span', {'class' : 'product-price'}).text.strip()
		print price
		return


		product_data = {
			'name'  : product_name,
			'price' : price,
			'url'   : url
		}

		print product_data
		

	except Exception as e:
		print str(e)


def crawl(**kwargs):
	#use SetQueue to avoice duplicate url in Queue
	q = SetQueue()

	#get url to crawl
	#urls is put in q
	get_url_to_crawl(queue = q)

	#start 5 threads
	for i in range(1):
		t = threading.Thread(target=parse_lazada_product_url, args=(q,i,))
		t.start()
		
