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

# Settings files for django
readonly PRODUCTION_SETTINGS="strongMan.settings.production"
readonly LOCAL_SETTINGS="strongMan.settings.local"

usage() {
	echo "Management script for strongMan"
	echo
	echo "Usage: $PROGNAME [install] [runserver [-d]] [migrate [-dm <y/n>]] [uninstall]"
	echo
	echo "Options:"
	echo
	echo "  -h, --help"
	echo "      This help text."
	echo
	echo "  install"
	echo "      Installs the strongMan application within it's own virtualenv."
	echo
	echo "  uninstall"
	echo "      Uninstalls the strongMan application within it's virtualenv."
	echo
	echo "  runserver"
	echo "      Runs the server on localhost:8000"
	echo
	echo "      -d, --debug"
	echo "      Runs the server on localhost:8000 in debug mode (standalone mode without a proper webservice."
	echo
	echo "  migrate"
	echo "      Makes the django migrations. Developer use."
	echo
	echo "      -dm <y/n>, --deletemigration <y/n>"
	echo "          Flags if the current migrations and the database are going to be deleted or not."
	echo
}
while [ "$#" -gt 0 ]
do
	case "$1" in
	-h|--help)
		usage
		exit 0
		;;
	migrate)
		migrate=1
		;;
	-dm|--deletemigration)
		if [ -z $migrate ]
			then
				echo "-dm|--deletemigration needs the 'migrate' command"
				exit 1
		fi
		if [ -z $2 ]
			then
				echo "-dm|--deletemigration needs a y or n like ' -dm y'"
				exit 1
		fi
		delete_migrations="$2"
		;;
	install)
		install=1
		;;
	runserver)
		runserver=1
		;;
	-d | --debug)
		runDebug=1
		;;
	uninstall)
		uninstall=1
		;;
	start-gunicorn-socket)
		gunicornSocket=1
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

function deleteSecretKeys {
    rm -f secret_key.txt > /dev/null
	rm -f db_key.txt > /dev/null
}
readonly GUNICORN_SERVICE="gunicorn_strongMan"

function start_gunicorn_socket {
    NAME="strongMan"                                #Name of the application (*)
    DJANGODIR=$(pwd)                                # Django project directory (*)
    SOCKFILE=$DJANGODIR/gunicorn.sock               # we will communicate using this unix socket (*)
    USER=osboxes                                    # the user to run as (*)
    GROUP=osboxes                                   # the group to run as (*)
    NUM_WORKERS=4                                   # how many worker processes should Gunicorn spawn (*)
    DJANGO_SETTINGS_MODULE=strongMan.settings.production             # which settings file should Django use (*)
    DJANGO_WSGI_MODULE=strongMan.wsgi                                # WSGI module name (*)

    echo "Starting $NAME as `whoami`"

    # Activate the virtual environment
    cd $DJANGODIR
    export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
    export PYTHONPATH=$DJANGODIR:$PYTHONPATH

    # Create the run directory if it doesn't exist
    RUNDIR=$(dirname $SOCKFILE)
    test -d $RUNDIR || mkdir -p $RUNDIR

    # Start your Django Unicorn
    # Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
    exec $DJANGODIR/env/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
      --name $NAME \
      --workers $NUM_WORKERS \
      --user $USER \
      --bind=unix:$SOCKFILE

}

function create_gunicorn_service {
    service=$(echo "/lib/systemd/system/"$GUNICORN_SERVICE".service")
    echo $service
    echo "[Unit]" > ${service}
    echo "Description=strongMan gunicorn daemon" >> ${service}
    echo >> ${service}
    echo "[Service]" >> ${service}
    echo "Type=simple" >> ${service}
    echo "User=osboxes" >> ${service}
    echo "ExecStart=$(pwd)/strongMan.sh start-gunicorn-socket" >> ${service}
    echo >> ${service}
    echo "[Install]" >> ${service}
    echo "WantedBy=multi-user.target" >> ${service}
}


if [ $migrate ]
	then
		if [ $delete_migrations ] 
			then
			#Migrate with parameter
			./migrate.sh -dm $delete_migrations
		else
			#Migrate without parameter
			./migrate.sh
		fi
		exit 1
fi

if [ $install ]
	then
		if [ -d "env" ]; then
		  echo "strongMan already installed"
		  exit 1
		fi

		echo "Install strongMan"
		echo
		read -r -p "${1:-Enter your python interpreter (python3.4 or python3.5):} " pythonInterpreter
		virtualenv -p $pythonInterpreter --no-site-packages env
		env/bin/pip install -r requirements.txt
		./migrate.sh -dm y
		env/bin/python manage.py collectstatic --settings=$PRODUCTION_SETTINGS --noinput

		echo
		echo strongMan installed!
		exit 1
fi

if [ $uninstall ]
	then
		if [ -d "env" ]; then
		  rm -rf env/
		  rm -rf strongMan/staticfiles
		  echo "strongMan virtualenv deleted."
		else
			echo "No installation found."
		  	exit 1
		fi
		exit 1
fi

if [ $runserver ]
	then
		if [ -d "env" ]; then
		    if [ $runDebug ]; then
                echo "Run strongMan standalone debug"
                echo
                env/bin/python manage.py runserver --settings=$LOCAL_SETTINGS
            else
                echo "Run strongMan"
                echo
                create_gunicorn_service
            fi
            exit
		else
			echo "No installation found. Can't run server. "
			echo "Install strongMan with './strongman.sh install'"
		  	exit 1
		fi
		exit 1
fi

if [ $gunicornSocket ]; then
    start_gunicorn_socket
fi


