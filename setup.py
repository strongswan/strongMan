#!/usr/bin/env python
# coding: utf8
import argparse
import subprocess
from argparse import RawTextHelpFormatter
from string import Template

import os
import shutil


authors = '''
Samuel Kurath <samuel.kurath@gmail.com>
Severin Bühler <sevi_buehler@hotmail.com>
'''





class InstallerException(Exception):
    pass


class BaseInstaller(object):
    PRODUCTION_SETTINGS = "strongMan.settings.production"
    LOCAL_SETTINGS = "strongMan.settings.local"
    mute = True

    def _tab(self, msg, times=2):
        ret = ""
        for line in msg.split('\n'):
            ret += '\t' * times + line + '\n'
        return ret[:-1]

    def _run_bash(self, cmd, force_mute=False):
        output = subprocess.check_output(cmd.split())
        output = output.decode('utf-8')
        if output != '':
            if not self.mute:
                if not force_mute:
                    print(self._tab(output))
        return output

    @property
    def virtualenv_installed(self):
        try:
            self._run_bash('virtualenv --version', force_mute=True)
            return True
        except Exception as e:
            print(e)
            return False

    @property
    def django_dir(self):
        return os.path.dirname(os.path.realpath(__file__))

    @property
    def is_installed(self):
        return os.path.exists(self.env)

    @property
    def env(self):
        return self.django_dir + "/env"


class Migrator(BaseInstaller):
    def delete_migrations(self):
        for entries in os.walk(self.django_dir + "/strongMan"):
            dir = list(entries)[0]
            if str(dir).__contains__('migrations'):
                if os.path.exists(dir):
                    if not self.mute:
                        print(self._tab("Delete " + dir))
                    shutil.rmtree(dir)

    def delete_db(self):
        print(self._tab("Delete " + "strongMan/db.sqlite3"))
        os.remove(self.django_dir + "/strongMan/db.sqlite3")

    def migrate(self):
        self._run_bash(
            self.env + "/bin/python " + self.django_dir + "/manage.py makemigrations certificates --settings=strongMan.settings.local")
        self._run_bash(
            self.env + "/bin/python " + self.django_dir + "/manage.py makemigrations connections --settings=strongMan.settings.local")
        self._run_bash(
            self.env + "/bin/python " + self.django_dir + "/manage.py makemigrations eap_secrets --settings=strongMan.settings.local")
        self._run_bash(
            self.env + "/bin/python " + self.django_dir + "/manage.py makemigrations pools --settings=strongMan.settings.local")
        self._run_bash(
            self.env + "/bin/python " + self.django_dir + "/manage.py makemigrations server_connections --settings=strongMan.settings.local")
        self._run_bash(
            self.env + "/bin/python " + self.django_dir + "/manage.py migrate --settings=strongMan.settings.local")

    def load_fixtures(self):
        self._run_bash(
            self.env + "/bin/python " + self.django_dir + "/manage.py loaddata initial_data.json --settings=strongMan.settings.local")


class Installer(BaseInstaller):
    def install_virtualenv(self, python_interpreter):
        self._run_bash("virtualenv -p " + python_interpreter + " " + self.env)

    def install_requirements(self):
        self._run_bash(self.env + "/bin/pip install -r requirements.txt")

    def migrate_db(self):
        migrator = Migrator()
        migrator.mute = self.mute
        try:
            migrator.delete_migrations()
        except Exception as e:
            print(e)
        try:
            migrator.delete_db()
        except Exception as e:
            print(e)
        migrator.migrate()
        migrator.load_fixtures()

    def collect_staticfiles(self):
        self._run_bash("env/bin/python manage.py collectstatic --settings=" + self.PRODUCTION_SETTINGS + " --noinput")

    def check_preconditions(self):
        if self.is_installed:
            raise InstallerException("strongMan is already installed.")

        if not self.virtualenv_installed:
            raise InstallerException("Virtualenv is required and not installed.")


class Uninstaller(BaseInstaller):
    def remove_virtualenv(self):
        shutil.rmtree(self.env)

    def remove_staticfiles(self):
        shutil.rmtree(self.django_dir + "/strongMan/staticfiles")


class Icon(BaseInstaller):
    def __init__(self):
        self.DESTINATION = "/usr/share/applications/strongMan.desktop"
        self.ORIGIN = self.django_dir + "/setup/strongMan.desktop"

    def exists(self):
        return os.path.exists(self.DESTINATION)

    @property
    def content(self):
        with open(self.ORIGIN, "r") as f:
            content = f.read()

        template = Template(content)
        values = {"workingDir": self.django_dir}
        return template.substitute(values)

    def create(self):
        content = self.content
        with open(self.DESTINATION, 'w') as f:
            f.write(content)
        return True

    def remove(self):
        os.remove(self.DESTINATION)




class GunicornService(BaseInstaller):
    SERVICE_PATH = "/etc/systemd/system/strongMan.service"


    @property
    def exists(self):
        return os.path.exists(self.SERVICE_PATH)

    @property
    def content(self):
        with open(self.django_dir + "/setup/strongMan.service", "r") as f:
            content = f.read()

        template = Template(content)
        values = {"workingDir": self.django_dir}
        return template.substitute(values)

    def create(self):
        content = self.content
        with open(self.SERVICE_PATH, 'w') as f:
            f.write(content)
        self._run_bash("systemctl daemon-reload")
        Icon().create()
        return True

    def enable(self):
        self._run_bash("systemctl enable strongMan")

    def start(self):
        self._run_bash("systemctl start strongMan")

    def disable(self):
        self._run_bash("systemctl disable strongMan")

    def stop(self):
        self._run_bash("systemctl stop strongMan")

    def remove(self):
        os.remove(self.SERVICE_PATH)
        self._run_bash("systemctl daemon-reload")
        Icon().remove()

    @property
    def socket_exists(self):
        socket = self.django_dir + "/gunicorn.sock"
        return os.path.exists(socket)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument("command", choices=['install',
                                            'uninstall',
                                            'runserver',
                                            'migrate',
                                            'add-service',
                                            'remove-service'],
                        help="""
                        Command what to do:
                        install \t-> Installs strongMan
                        uninstall \t-> Uninstall strongMan

                        Migrate \t-> Migrates the database (Mainyl developer use)
                        add-service \t-> Adds a systemd service for strongMan
                        remove-service \t-> Removes the systemd service""")
    parser.add_argument("-p", "--python", help="choice your python interpreter.")
    parser.add_argument("-dm", "--delete-migrations", action="store_true",
                        help="indicates if the migrations are going to be deleted.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="sets output verbose.")
    args = parser.parse_args()

    if args.command == "install":
        interpreter = args.python
        if interpreter is None:
            interpreter = "python3"

        install = Installer()
        if args.verbose:
            install.mute = False

        try:
            install.check_preconditions()

            print("Start strongMan installation")
            print("\t- Virtualenv")
            install.install_virtualenv(interpreter)
            print("\t- Requirements")
            install.install_requirements()
            print("\t- Database migration")
            install.migrate_db()
            print("\t- Static files")
            install.collect_staticfiles()
        except Exception as e:
            print(e)

    if args.command == "uninstall":
        print("Uninstall strongMan")
        uninstaller = Uninstaller()
        if args.verbose:
            uninstaller.mute = False
        try:
            print("\t- Remove virtualenv")
            uninstaller.remove_virtualenv()
        except Exception as e:
            print(e)
        try:
            print("\t- Remove staticfiles")
            uninstaller.remove_staticfiles()
        except Exception as e:
            print(e)
        try:
            service = GunicornService()
            if service.exists:
                print("\t- Remove systemd gunicorn service")
                service.remove()
        except Exception as e:
            print(e)

        exit(0)

    if args.command == "migrate":
        migrator = Migrator()
        if not migrator.is_installed:
            raise InstallerException("strongMan is not installed.")
        if args.verbose:
            migrator.mute = False

        print("Migrate strongMan")
        if args.delete_migrations:
            migrator.delete_migrations()
            migrator.delete_db()
        migrator.migrate()
        migrator.load_fixtures()
        print("Migrations completed")

    if args.command == "add-service":
        try:
            g = GunicornService()
            g.create()
            g.enable()
            g.start()
        except Exception as e:
            print(e)
        exit(0)

    if args.command == "remove-service":
        try:
            g = GunicornService()
            g.stop()
            g.disable()
            g.remove()
        except Exception as e:
            print(e)
