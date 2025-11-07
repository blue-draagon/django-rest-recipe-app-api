"""
Django commande to wait for the database to be available
"""
import time

from psycopg2 import OperationalError as Psycopg2Error

from django.core.management.base import BaseCommand
from django.db.utils import OperationalError


class Command(BaseCommand):
    """ Django commande to wait for database """
    def handle(self, *args, **options):
        """Entrypoint for command."""
        self.stdout.write("Waiting for database ...")
        database_up = False
        while not database_up:
            try:
                self.check(databases=["default"])
                database_up = True
            except (Psycopg2Error, OperationalError):
                wait_time = 2
                error_message = "Database not available,"
                wait_messge = f" waiting {wait_time}s ..."
                self.stdout.write(error_message + wait_messge)
                time.sleep(wait_time)
        self.stdout.write(self.style.SUCCESS("Database available!"))
