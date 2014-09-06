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
    /usr/bin/python $document_root/$worker --site "$1" &
}

# Stop all process
stop() {
	echo "Stopping $prog"
	ps -ef | grep "$1" | grep -v grep | awk '{print$2}' | xargs kill -9
}
# Detect process
detect() {
	current_num_prog=`ps -ef | grep -v grep | grep -c $1`
	if [ "$current_num_prog" -lt "$num_prog" ]; then
		let new_prog=$num_prog-$current_num_prog
		i=1
		while [ $i -le $new_prog ]; do
			start "$1"
			let i++
		done
	else
		echo "$1 is running..."
	fi
}
case "$1" in
	"start" )
        start "$2"
           ;;
	"stop" )
	    stop "$2"
           ;;
	"restart" )
	    stop "$2"
	    detect "$2"
           ;;
	"detect" )
        detect "$2"
           ;;
     	* )
           echo "Usage: $prog {start|stop|restart|detect} {sitename}"
           exit 1
esac

ps -ef | grep -v grep | grep "$2"
exit 0