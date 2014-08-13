import importlib, sys

def main():
	argv = sys.argv[1:]

	if not argv:
		print "usage: [--site] <site_to_crawl> [--cont <true|false>] [--useproxy <true|false>]"
		sys.exit(1)

	if argv[0] == '--site':
		site_crawl = argv[1]

	cont = False
	if len(argv) >= 4:
		if argv[2] == '--cont' and argv[3] == 'true':
			cont = True
	
	useproxy = False
	if len(argv) >= 6:
		if argv[4] == '--useproxy' and argv[5] == 'true':
			useproxy = True

	data = importlib.import_module("page.%s" % site_crawl);
	data.crawl(cont = cont, useproxy = useproxy)


if __name__ == '__main__':
	main()