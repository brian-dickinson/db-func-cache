# Database Function Cache

This project creates a simple wrapper allowing an argument to return value 
mapping to be saved for a function and used to speed up subsequent identical 
calls to that function. It is used much like cache or lru_cache from the 
functools module except that it is backed by a database. This allows the cache 
to persist between runs or between multiple users.

Each function decorated with db_cache will have its results saved in a separate 
table whose name is determined by the name of the decorated function. This helps 
to avoid random collisions in the case of identical arguments to different 
functions.

Because the system depends upon dill for serialization and deserialization, 
only arguments and return values that can be pickled by dill are supported.
Similarly, since different Python and package versions of objects might not 
always serialize in the same way, it is not guaranteed that the cache will always 
hit even when the exact same arguments are used.

## Basic Usage

```python
from db_func_cache import db_cache, connect

connect("sqlite://") # use any SQLAlchemy DB URL

@db_cache()
def fibonacci(x: int) -> int:
    if x < 0: raise ValueError("fibonacci not defined for negative values")
    elif x == 0: return 0
    elif x == 1: return 1
    else: return fibonacci(x-1) + fibonacci(x-2)
```

It is recommended to call `connect` in order to determine the database where 
cached results will be saved. This should be done before any functions are 
tagged with `@db_cache`. If `connect` is called more than once, it will change 
the database for all functions, not just those tagged later. If `connect` is 
never called, then an in-memory SQLite database is used.