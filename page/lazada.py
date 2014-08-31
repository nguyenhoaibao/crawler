import threading, Queue, db.factory, request_url
import re
from set_queue import SetQueue
from bs4 import BeautifulSoup

INIT_URL = 'http://lazada.vn'
SKIP_URL = '\#|\\|about|privacy|cart|customer|urlall|mobile|javascript|shipping|google|tumblr|facebook|twitter|apple\.com|\.php|wildwingsphotography|aquoid|jerrywhitephotography|itunes|blog\.lazada|co\.|com\.|\.sg|\.vn|\.aspx|windowsphone|API|contact|huong\-dan|trung\-tam|faq|techinasia|linkedin|US|weibo'
#SKIP_URL = [
#	'/',
#	'#'
#	'/about/',
#	'/privacy-policy/',
#	'/cart',
#	'/customer/account/login',
#	'/urlall-products/',
#	'/cart?setDevice=desktop',
#	'/mobile-promotions/?child',
#	'javascript:void(0)'
#]

redis_conn = ''
mongo_conn = ''
mongo_collection  = ''
queue = ''

def init():
	global redis_conn
	global queue
	global mongo_conn
	global mongo_collection
	if not redis_conn:
		redis_conn = db.factory.get_connection('redis')

	if not mongo_conn:
		mongo_conn = db.factory.get_connection('mongo')
		mongo_collection = mongo_conn['lazada_product']

	if not queue:
		queue = SetQueue()


def find_all_link_from_url(url):
	try:
		html = request_url.get_html_from_url(url)

		list_urls = []

		if html:
			#get all link
			soup = BeautifulSoup(html)
			urls = soup.findAll('a')

			
			for url in urls:
				href = url.get('href')
				if href and href != INIT_URL and href != '/' and href not in list_urls and not re.search(SKIP_URL, href):
					list_urls.append(href)
		return list_urls
	except Exception, e:
		print url, str(e.args)

def parse_url(url):
	try:
		temp = url
		urls = find_all_link_from_url(url)
		for url in urls:
			redis_conn.sadd('lazada_urls', url)

			#put to queue
			queue.put(url)
                
		m = re.match(".*(\d+)\.html$", temp)
                
		if m:  #product url
                        print "parse product url: %s ..." % temp
			html = request_url.get_html_from_url(temp)

			parsed_html = BeautifulSoup(html)

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
			mongo_collection.update({'product_id': int(product_id)}, product_data, upsert = True)
	except Exception, e:
		print url, str(e.args)
	
def crawl():

	init()

	urls = redis_conn.smembers('lazada_urls')
	
	#first crawl
	if not urls:
		print "No url found from redis!!!"
		print "Find url from init url: %s" % INIT_URL
		#get list url from init url
		urls = find_all_link_from_url(INIT_URL)

                print "Find %s urls ..." % len(urls)
		
		for url in urls:
			#insert all url to redis sets
			redis_conn.sadd('lazada_urls', url)
	
	#continue
	for url in urls:
		#put to queue
		queue.put(url)

        print "Begin to crawl ..."

	#init threads
	for t in xrange(10):
		print "Init thread %s ..." % t
		t = threading.Thread(target=start_crawl)
		t.start()

def start_crawl():
	while not queue.empty():
		url = queue.get()

		#remove url from redis sets
		redis_conn.srem('lazada_urls', url)

		if url.startswith('/') and not url.startswith('\\'):
			url = 'http://www.lazada.vn' + url

		try:
			print "Crawling url %s ..." % url
			parse_url(url)
		except Exception, e:
			print "Pass url: %s" % url
			pass



