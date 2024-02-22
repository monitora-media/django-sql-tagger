import dataclasses
import inspect
from io import StringIO

from django.db import DEFAULT_DB_ALIAS
from django.db.transaction import Atomic

from django_sql_tagger.tagging import is_frame_in_our_code, transaction_tag, filepath


@dataclasses.dataclass(frozen=True)
class TransactionInfo:
    filename: str
    line: int
    tag: str | None


class TransactionStack:
    def __init__(self):
        self.stack = []

    def enter(self, info: TransactionInfo):
        self.stack.append(info)

    def exit(self):
        self.stack.pop()

    def render(self, buffer: StringIO):
        for i, info in enumerate(self.stack):
            if info.tag:
                buffer.write(f'T={info.tag} ')
            buffer.write(f'{info.filename}:{info.line}')
            buffer.write(' |> ')


class TaggingAtomic(Atomic):
    def __init__(self, *args, tag=None, **kwargs):
        self.tag = tag
        super().__init__(*args, **kwargs)

    def __enter__(self):
        calling_frame = inspect.currentframe().f_back
        assert is_frame_in_our_code(calling_frame)
        if not hasattr(transaction_tag, 'stack'):
            transaction_tag.stack = TransactionStack()

        transaction_tag.stack.enter(TransactionInfo(filepath(calling_frame), calling_frame.f_lineno, self.tag))
        return super().__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        transaction_tag.stack.exit()
        return super().__exit__(exc_type, exc_value, traceback)


def atomic(using=None, savepoint=True, durable=False, tag=None):
    # Bare decorator: @atomic -- although the first argument is called
    # `using`, it's actually the function being decorated.
    if callable(using):
        return TaggingAtomic(DEFAULT_DB_ALIAS, savepoint, durable, tag=tag)(using)
    # Decorator: @atomic(...) or context manager: with atomic(...): ...
    else:
        return TaggingAtomic(using, savepoint, durable, tag=tag)
