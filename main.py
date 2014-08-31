import importlib, sys, os

os.chdir('/home/hoaibao/Development/python/crawler')

def main():
	argv = sys.argv[1:]

	if not argv:
		print "usage: [--site] <site_to_crawl> [--useproxy <true|false>]"
		sys.exit(1)

	if argv[0] == '--site':
		site_crawl = argv[1]
	
	useproxy = False
	if len(argv) >= 4:
		if argv[2] == '--useproxy' and argv[3] == 'true':
			useproxy = True

	data = importlib.import_module("page.%s" % site_crawl);
	data.crawl()


if __name__ == '__main__':
	main()