from Queue import Queue

class SetQueue(Queue):

	def _init(self, maxsize):
		Queue._init(self, maxsize) 
		self.all_items = set()

	def _put(self, item):
		if item not in self.all_items:
			Queue._put(self, item) 
			self.all_items.add(item)