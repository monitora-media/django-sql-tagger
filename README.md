# django-sql-tagger
Adds a comment to SQL queries pointing to their place of origin

## Usage

Install:

`pip install django-sql-tagger`

Configure and add to `INSTALLED_APPS` in your `settings.py` file:

```python
INSTALLED_APPS = [
    ...
    'django_sql_tagger',
    ...
]

SQL_TAGGER_CODE_ROOT = BASE_DIR
SQL_TAGGER_PATH_REPLACEMENTS = [
    (r'^myapp/', 'a/'),
]
```

### Settings

`SQL_TAGGER_CODE_ROOT` - The root of your codebase. This is used to find out which stack frames belong to your
                         application code.

`SQL_TAGGER_PATH_REPLACEMENTS` - A list of tuples of regular expressions and replacements. This is used to shorten
                                paths in the comments. For example, if you have a file at
                                `/myapp/views.py` and you want to replace `/myapp/` with `a/`, you would add
                                `(r'^myapp/', 'a/')` to the list.

## Example

See the `testsite/` directory for an example project using this package.

```python
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
```

The above command executes the following SQL queries:

```sql

/* ta/m/c/example.py:10 */ SELECT "testapp_website"."id", "testapp_website"."name", "testapp_website"."url" FROM "testapp_website"; args=(); alias=default
BEGIN;
/* ta/m/c/example.py:12 |> ta/m/c/example.py:13 */ SELECT "testapp_website"."id", "testapp_website"."name", "testapp_website"."url" FROM "testapp_website";
COMMIT;
BEGIN;
SAVEPOINT "s140328319196032_x1";
/* ta/m/c/example.py:15 |> ta/m/c/example.py:16 |> ta/m/c/example.py:17 */ SELECT "testapp_website"."id", "testapp_website"."name", "testapp_website"."url" FROM "testapp_website";
RELEASE SAVEPOINT "s140328319196032_x1";
COMMIT;
BEGIN;
/* T=xxx ta/m/c/example.py:19 |> ta/m/c/example.py:20 */ SELECT "testapp_website"."id", "testapp_website"."name", "testapp_website"."url" FROM "testapp_website";
COMMIT;
```

The comments make it easier to identify where the SQL queries are coming from, for example when you see the query
in the database log or a database monitoring tool.

## License

GPLv3 (see `LICENSE` file)
