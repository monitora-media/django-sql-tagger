import inspect
import io
import logging
import re
import threading
from functools import wraps
from types import FrameType, CodeType

from django.conf import settings
from django.db.models import QuerySet, Model, Manager

transaction_tag = threading.local()
logger = logging.getLogger(__name__)
code_root = str(settings.SQL_TAGGER_CODE_ROOT)


def is_code_ours(f_code: CodeType) -> bool:
    return f_code.co_filename.startswith(code_root)


def filepath(f_code: CodeType) -> str:
    path = f_code.co_filename
    if path.startswith(code_root):
        path = f_code.co_filename[len(code_root) + 1:]
    for regex, replacement in settings.SQL_TAGGER_PATH_REPLACEMENTS:
        path = re.sub(regex, replacement, path)

    path = re.sub(r'/management/commands/', '/m/c/', path)
    return path


transaction_mgmt_re = re.compile(r'^(BEGIN|COMMIT|SAVEPOINT|RELEASE\s+SAVEPOINT|ROLLBACK|ROLLBACK\s+TO\s+SAVEPOINT)\b', flags=re.IGNORECASE)

ignore_below_stack = threading.local()


def ignore_below(func):
    """
    When determining the calling frame for SQL tagging, ignore anything that's in the annotated function
    or called from it.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        set_up = False
        if not hasattr(ignore_below_stack, 'frame'):
            ignore_below_stack.frame = inspect.currentframe().f_back
            set_up = True
        try:
            return func(*args, **kwargs)
        finally:
            if set_up:
                del ignore_below_stack.frame

    return wrapper


def sql_query_tagger(execute, sql, params, many, context):
    if not transaction_mgmt_re.match(sql):
        transactions_and_savepoints = getattr(transaction_tag, 'stack', None)
        comment = io.StringIO()
        comment.write('/* ')

        if transactions_and_savepoints:
            transactions_and_savepoints.render(comment)

        if hasattr(ignore_below_stack, 'frame'):
            calling_frame = ignore_below_stack.frame
        else:
            calling_frame = inspect.currentframe().f_back

        while calling_frame.f_back:
            _cls = calling_frame.f_locals.get('cls')
            if (
                (not is_code_ours(calling_frame.f_code))
                or (isinstance(calling_frame.f_locals.get('self'), (QuerySet, Model, Manager)))
                or (_cls and inspect.isclass(_cls) and issubclass(_cls, (QuerySet, Model, Manager)))
            ):
                calling_frame = calling_frame.f_back
            else:
                break

        comment.write(f'{filepath(calling_frame.f_code)}:{calling_frame.f_lineno}')

        comment.write(' */')
        logger.debug(comment.getvalue())
        sql = comment.getvalue() + ' ' + sql
    return execute(sql, params, many, context)
