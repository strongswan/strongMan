#!/bin/bash

helpmsg ()
{
	echo No python interpreter found.
	echo Run .\/migrate.sh [pythoninterpreter] [delete_migrations]
	echo Example\: \'migrate.sh python3.5\'
	echo Example \(delete migrations\)\: \'migrate.sh python3.5 y\'
}

if [ -z $1 ]
	then
		helpmsg
		exit
fi

if [ $1 == "--help" ]
	then
		helpmsg
		exit
fi

mypython=$1
echo Using \'$mypython\' as python interpreter

if [ -z $2 ]
	then
		echo Do you want to delete the database and all migrations \(y\/n\)?
		read delete_migrations
else
	delete_migrations=$2
fi

if [ $delete_migrations == "y" ]
	then
		rm -rf $(find . -name "migrations")
		rm -f "strongMan/db.sqlite3"
		echo Migrations deleted!
fi


#Migrate
$mypython manage.py makemigrations certificates --settings=strongMan.settings.local
$mypython manage.py makemigrations connections --settings=strongMan.settings.local
$mypython manage.py migrate --settings=strongMan.settings.local
#Load initial data
$mypython manage.py loaddata initial_data.json --settings=strongMan.settings.local
echo
echo migratione done!
