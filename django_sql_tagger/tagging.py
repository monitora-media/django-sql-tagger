import inspect
import io
import logging
import re
import threading
from types import FrameType

from django.conf import settings
from django.db.models import QuerySet


transaction_tag = threading.local()
logger = logging.getLogger(__name__)


def is_frame_in_our_code(frame: FrameType) -> bool:
    return frame.f_code.co_filename.startswith(str(settings.SQL_TAGGER_CODE_ROOT))


def filepath(frame: FrameType) -> str:
    path = frame.f_code.co_filename[len(str(settings.SQL_TAGGER_CODE_ROOT)) + 1:]
    for regex, replacement in settings.SQL_TAGGER_PATH_REPLACEMENTS:
        path = re.sub(regex, replacement, path)

    path = re.sub(r'/management/commands/', '/m/c/', path)
    return path


transaction_mgmt_re = re.compile(r'^(BEGIN|COMMIT|SAVEPOINT|RELEASE\s+SAVEPOINT|ROLLBACK|ROLLBACK\s+TO\s+SAVEPOINT)\b', flags=re.IGNORECASE)


def sql_query_tagger(execute, sql, params, many, context):
    if not transaction_mgmt_re.match(sql):
        transactions_and_savepoints = getattr(transaction_tag, 'stack', None)
        comment = io.StringIO()
        comment.write('/* ')

        if transactions_and_savepoints:
            transactions_and_savepoints.render(comment)

        calling_frame = inspect.currentframe().f_back
        while calling_frame.f_back and (
                not is_frame_in_our_code(calling_frame)
                or isinstance(calling_frame.f_locals.get('self'), QuerySet)):
            calling_frame = calling_frame.f_back

        comment.write(f'{filepath(calling_frame)}:{calling_frame.f_lineno}')

        comment.write(' */')
        logger.debug(comment.getvalue())
        sql = comment.getvalue() + ' ' + sql
    return execute(sql, params, many, context)
