from __future__ import absolute_import

from celery import Celery
import os

#custom module
import config

#change env variable
#@TODO: find how to change efficient way
os.environ["CRAWLER_ENV"] = "dev"

#get redis master server
cf = config.get_config('redis', 'write', 'background')
#broker string
broker = 'redis://%s:%s/%s' % (cf['host'], cf['port'], cf['db'])

app = Celery('background',
             broker=broker,
             include=['background.tasks'])

# Optional configuration, see the application user guide.
app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

if __name__ == '__main__':
    app.start()