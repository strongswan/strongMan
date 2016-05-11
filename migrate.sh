#!/usr/bin/env bash

# File name
readonly PROGNAME=$(basename $0)
# File name, without the extension
readonly PROGBASENAME=${PROGNAME%.*}
# File directory
readonly PROGDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# Arguments
readonly ARGS="$@"
# Arguments number
readonly ARGNUM="$#"

usage() {
	echo "Run's all migrations for strongMan in one script."
	echo
	echo "Usage: $PROGNAME [-dm <y/n>]"
	echo
	echo "Options:"
	echo
	echo "  -h, --help"
	echo "      This help text."
	echo
	echo "  -dm <y/n>, --deletemigrations <y/n>"
	echo "      Flags if the current migrations and the database are going to be deleted or not."
	echo
}
while [ "$#" -gt 0 ]
do
	case "$1" in
	-h|--help)
		usage
		exit 0
		;;
	-dm|--deletemigrations)
		delete_migrations="$2"
		;;
	--)
		break
		;;
	-*)
		echo "Invalid option '$1'. Use --help to see the valid options" >&2
		exit 1
		;;
	# an option argument, continue
	*)	;;
	esac
	shift
done
if [ -z $delete_migrations ]
	then
		read -r -p "${1:-Do you want to delete the database and all migrations? [y/N]} " delete_migrations
fi

# Start the main programm
# Delete the migrations if wanted
case $delete_migrations in
[yY][eE][sS]|[yY]) 
    	rm -rf $(find ./strongMan -name "migrations")
	rm -f "strongMan/db.sqlite3"
	echo Migrations deleted!
    ;;
*)
    echo "Let the migrations in silence."
    ;;
esac

#Migrate
./env/bin/python manage.py makemigrations certificates --settings=strongMan.settings.local
./env/bin/python manage.py makemigrations connections --settings=strongMan.settings.local
./env/bin/python manage.py migrate --settings=strongMan.settings.local
#Load initial data
./env/bin/python manage.py loaddata initial_data.json --settings=strongMan.settings.local
echo
echo Migratione done!





