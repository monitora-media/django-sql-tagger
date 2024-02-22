from django.core.management import BaseCommand
from django.db import connection

from django_sql_tagger import transaction
from testapp.models import Website


class Command(BaseCommand):
    def handle(self, *args, **options):
        Website.objects.first()

        with transaction.atomic():
            Website.objects.first()

        with transaction.atomic():
            with transaction.atomic():
                Website.objects.first()

        with transaction.atomic(tag='xxx'):
            Website.objects.first()

        print(connection.queries_log)
