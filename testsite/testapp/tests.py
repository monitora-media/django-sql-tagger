from inspect import currentframe
import logging

import pytest
from django.test import TestCase

from django_sql_tagger import transaction
from django_sql_tagger.tagging import logger as tagging_logger
from testapp.models import Website


class CapturingHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record.msg)


def get_linenumber():
    cf = currentframe()
    return cf.f_back.f_lineno


@pytest.fixture(scope='session', autouse=True)
def _enable_logger():
    if tagging_logger.getEffectiveLevel() > logging.DEBUG:
        tagging_logger.setLevel(logging.DEBUG)


@pytest.fixture(scope='function')
def tags():
    handler = CapturingHandler()
    tagging_logger.addHandler(handler)
    yield handler.records
    tagging_logger.removeHandler(handler)


@pytest.mark.django_db
def test_plain(tags):
    assert tags == []
    Website.objects.first()
    assert [f'/* ta/tests.py:{get_linenumber() - 1} */'] == tags


@pytest.mark.django_db
def test_transaction(tags):
    assert tags == []
    with transaction.atomic():
        Website.objects.first()
    assert [f'/* ta/tests.py:{get_linenumber() - 2} |> ta/tests.py:{get_linenumber() - 1} */'] == tags


@pytest.mark.django_db
def test_transaction_nested(tags):
    assert tags == []
    with transaction.atomic():
        with transaction.atomic():
            Website.objects.first()
    assert [f'/* ta/tests.py:{get_linenumber() - 3} |> ta/tests.py:{get_linenumber() - 2} |> ta/tests.py:{get_linenumber() - 1} */'] == tags


@pytest.mark.django_db
def test_tag(tags):
    assert tags == []
    with transaction.atomic(tag='xxx'):
        Website.objects.first()
    assert [f'/* T=xxx ta/tests.py:{get_linenumber() - 2} |> ta/tests.py:{get_linenumber() - 1} */'] == tags
