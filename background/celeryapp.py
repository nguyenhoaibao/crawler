from __future__ import absolute_import

from celery import Celery

#custom module
import config

#get redis master server
cf = config.get_config('redis', 'write')
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