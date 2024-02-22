from django.apps import AppConfig as BaseAppConfig
from django.db import connection

from .tagging import sql_query_tagger


class AppConfig(BaseAppConfig):
    name = 'django_sql_tagger'

    def ready(self):
        # Store the wrapper forever as Django app doesn't support unloading
        connection.execute_wrappers.append(sql_query_tagger)
