import importlib, sys

def main():
	site_crawl = 'lazada'

	data = importlib.import_module("page.%s" % site_crawl);
	data.crawl()


if __name__ == '__main__':
	main()