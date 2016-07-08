#!/bin/bash

function FA2gephi {
	for f in gexfs/*.gexf
	do
		if [[ "$f" != *_.gexf* ]]
		then
			java -jar tinaviz-2.0-SNAPSHOT.jar "$f" 10 &
			break;
		fi
	done
}

function testing {
	for f in gexfs/*.gexf
	do
		if [[ "$f" != *_.gexf* ]]
		then
			variable=`cat $f | grep "<description>Carla__Taramasco"`
			if [[ "$variable" != "" ]]
			then
				echo $f
			fi
		fi
	done
}

# Usage:
# ./zearcher.sh "extension" "the query"
function test2 {
	extension=$1
	query=$2
	# echo "lala $extension , $query"
	iter=`find . -name "*.$extension" -print`
	
	counter=0
	for f in $iter
	do
		filename=`echo $f | sed s/"\.\/"//g`
		variable=`cat $filename | grep "$query"`
		if [[ "$variable" != "" ]]
		then
			echo $filename
			counter=$((counter + 1));
		fi
	done

	if [ $counter -eq 0 ]
	then
		echo "Nothing found. Die."
	fi		
}

test2 $1 $2
