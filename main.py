import importlib, sys, os

os.chdir('/home/hoaibao/Development/python/crawler')

def main():
	argv = sys.argv[1:]

	if not argv:
		print "usage: [--site] <site_to_crawl> [--func <crawl|update|feedproducturl>] [--useproxy <true|false>]"
		sys.exit(1)

	if argv[0] == '--site':
		site_crawl = argv[1]

	func = 'crawl'
	if len(argv) >= 4:
		if argv[2] == '--func':
			func = argv[3]
	
	#useproxy = False
	#if len(argv) >= 4:
		#if argv[2] == '--useproxy' and argv[3] == 'true'::
			#useproxy = True

	data = importlib.import_module("page.%s" % site_crawl)

	klass = getattr(data, site_crawl.title())()
	f = getattr(klass, func)
	f()
	#p.crawl()


if __name__ == '__main__':
	main()