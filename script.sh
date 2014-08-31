#!/bin/bash
env=development
document_root=/home/hoaibao/Development/python/crawler
worker=main.py
prog=script.sh
num_prog=1
date=`date +"%Y-%m-%d"`

#Start process
start() {
	echo "Starting $prog"
    /usr/bin/python $document_root/$worker --site lazada &
}

# Stop all process
stop() {
	echo "Stopping $prog"
	ps -ef | grep "$worker" | grep -v grep | awk '{print$2}' | xargs kill -9
}
# Detect process
detect() {
	current_num_prog=`ps -ef | grep -v grep | grep -c "$worker"`
	if [ "$current_num_prog" -lt "$num_prog" ]; then
		let new_prog=$num_prog-$current_num_prog
		i=1
		while [ $i -le $new_prog ]; do
			start
			let i++
		done
	else
		echo "$worker is running..."
	fi
}
case "$1" in
	"start" )
        start
           ;;
	"stop" )
	    stop
           ;;
	"restart" )
	    stop
	    detect
           ;;
	"detect" )
        detect
           ;;
     	* )
           echo "Usage: $prog {start|stop|restart|detect)"
           exit 1
esac

ps -ef | grep -v grep | grep "$worker"
exit 0