from __future__ import annotations
import sys
from dill import dumps, loads
from datetime import datetime, timedelta, UTC
from typing import NamedTuple, Type, Any, Callable
from sqlalchemy import create_engine, Engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

# create a global record of the database engine and a function to connect
class DBEngine(NamedTuple):
    url: str
    engine: Engine
_engine: DBEngine|None = None
def connect(url:str) -> Engine:
    global _engine
    # if there is no current engine or a different engine, make the engine and save it
    if _engine is None or _engine.url != url:
        engine: Engine = create_engine(url)
        _engine = DBEngine(url, engine)
    return _engine.engine
# define an exception to be raised if connections are attempted without an engine
class MissingDatabaseConnection(RuntimeError): pass

# create a base class from which all record classes will inherit
class Base(DeclarativeBase): pass

# create a global record of record classes based on their table names
_tables: dict[str,Type[Base]] = {}

# create a helper function that manufactures subclasses of Base for new tables
def make_record_class(table_name: str) -> Type[Base]:
    class RecordClass(Base):
        __tablename__ = table_name
        args:   Mapped[bytes] = mapped_column(primary_key=True)
        result: Mapped[bytes] = mapped_column()
    return RecordClass

# create a helper function that converts an args tuple and kwargs dict into bytes
def serialize_args(args: tuple[Any,...], kwargs: dict[str,Any]) -> bytes:
    return dumps((args,tuple(sorted(kwargs.items()))))

# create the wrapper function that creates a decorator for a particular function
# TODO: add a timeout option to always refresh the DB if it has been too long
def db_cache(table: str|None=None, engine:Engine|None = None) -> Callable:
    global _tables, _engine
    # prefer the locally defined engine, but back it up with default
    engine = engine if engine is not None else _engine.engine if _engine is not None else None
    # if there is no engine, then issue a runtime warning and make an in-memory SQLite3 database
    if engine is None:
        print(f"WARNING: No DB connected. Defaulting to SQLite3 database in memory", file=sys.stderr)
        connect('sqlite://')
        if _engine is None:
            raise MissingDatabaseConnection("No database connection found!")
        else:
            engine = _engine.engine
    # define the decorator that will replace the original function
    def decorator(func: Callable):
        # use either the given table_name or the function name as the table name
        table_name = table if table is not None else func.__name__
        # ensure the table exists in the global mapping and in the connected database
        if table_name not in _tables:
            _tables[table_name] = make_record_class(table_name)
            Base.metadata.create_all(engine, checkfirst=True)
        # remember this class for later use
        RecordClass: Type[Base] = _tables[table_name]
        # define the wrapper function the decorator applies to the function
        def wrapper(*func_args, **func_kwargs):
            # ensure there is still a database connection
            if _engine is None: raise MissingDatabaseConnection("Database not connected!")
            # compute the serialization of this set of arguments
            args_id: bytes = serialize_args(func_args, func_kwargs)
            # open a DB session to either find or add an entry for these arguments
            with Session(engine) as session:
                # first attempt to look up the record that goes with these arguments
                query = select(RecordClass).where(RecordClass.args == args_id) # type: ignore
                cached_record = session.scalars(query).first()
                # if a record is found . . .
                if cached_record is not None:
                    # deserialize the answer from this record
                    answer = loads(cached_record.result) # type: ignore
                    # return the answer
                    return answer
                # otherwise . . .
                else:
                    # call the function to get the correct answer
                    answer = func(*func_args, **func_kwargs)
                    # save this answer in a new record in the DB
                    result: bytes = dumps(answer)
                    session.add(RecordClass(args=args_id, result=result))
                    session.commit()
                    # return the answer
                    return answer
        return wrapper
    return decorator
