from __future__ import absolute_import
import importlib

from background.celeryapp import app

@app.task
def parse_product_html(page, url):
   	data = importlib.import_module("page.%s" % page)

   	p = getattr(data, page.title())()
	p.parse_product_data(url)