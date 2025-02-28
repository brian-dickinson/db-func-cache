from __future__ import annotations
import os
import sys
import time
import unittest
from timeit import timeit
from typing import TypeVar
from itertools import chain, product, permutations
from datetime import datetime, timedelta, UTC

# ensure the project directory is in the path
testdir = os.path.dirname(os.path.abspath(__file__))
projectdir = os.path.join(testdir, os.pardir)
sys.path.insert(0, projectdir)

# import items from the project
from db_func_cache import db_cache

T = TypeVar('T')

# define a simple function that takes a while for no reason for testing purposes
@db_cache()
def delayed_echo(x: T, delay_ms: int) -> T:
    # determine the exact time the echo should return
    return_time: datetime = datetime.now(UTC) + timedelta(milliseconds=delay_ms)
    # determine the number of seconds left to wait
    remaining_wait_seconds: float = (return_time - datetime.now(UTC)).total_seconds()
    # while there is still a over 10 ms to wait, wait for half the time
    while remaining_wait_seconds > 0.1:
        time.sleep(remaining_wait_seconds/2)
        remaining_wait_seconds = (return_time - datetime.now(UTC)).total_seconds()
    # after that, busy wait until it is time to return
    while datetime.now(UTC) < return_time: pass
    return x

# define a second simple function to make sure separate functions are in separate tables
@db_cache()
def fibonacci(x: int) -> int:
    if x < 0: raise ValueError("fibonacci not defined for negative values")
    elif x == 0: return 0
    elif x == 1: return 1
    else: return fibonacci(x-1) + fibonacci(x-2)

class TestDatabaseFuncCache(unittest.TestCase):
    # create some simple arguments to see if caching is working
    _ints:   tuple[int,...] = tuple(range(10))
    _floats: tuple[float,...] = tuple(x/100 for x in range(0,100,11))
    _strs:   tuple[str,...] = ('hello', 'world', 'foo', 'bar')

    def test_cache_hit(self):
        # take every individual item from int and float
        for x in chain(self._ints, self._floats):
            # make sure the delay is enforced the first time
            first: float = timeit(f"delayed_echo({x}, 100)",
                                  globals=globals(), number=1)*1000
            self.assertAlmostEqual(first, 100.0, delta=20.0)
            # make sure it is not the second time
            second: float = timeit(f"delayed_echo({x}, 100)",
                                  globals=globals(), number=1)*1000
            self.assertAlmostEqual(second, 0.0, delta=20.0)

    def test_simple_correct_answers(self):
        # take every individual item from int, float, and str
        for x in chain(self._ints, self._floats, self._strs):
            # do each of them twice to hit the cache the second time
            for _ in range(2):
                self.assertEqual(x, delayed_echo(x, 0))
    
    def test_combo_correct_answers(self):
        # take every combination of int, float, and str from the declared sets
        for items in product(self._ints, self._floats, self._strs):
            # take every possible order of this combination
            for order in permutations(items, 3):
                # do each of them twice to hit the cache the second time
                for _ in range(2):
                    self.assertEqual(order, delayed_echo(order, 0))

if __name__=='__main__':
    # define the ordering of any tests that are order sensitive
    first_tests: tuple[str,...] = (
        'test_cache_hit', # make sure we test if we hit the cache before filling the cache
    )
    last_tests: tuple[str,...] = ()
    # define a function that identifies when a test should run
    test_table: dict[str,int] = {test:i for i,test in enumerate(first_tests)}
    test_table.update({test:i+len(first_tests)+1 for i,test in enumerate(last_tests)})
    def get_test_order(test_name: str) -> int:
        return test_table.get(test_name, len(first_tests))
    def test_compare(_, test_a: str, test_b: str) -> int:
        a: int = get_test_order(test_a)
        b: int = get_test_order(test_b)
        if a > b: return 1
        elif a < b: return -1
        else: return 0
    # tell unittest to sort test methods using this order
    unittest.TestLoader.sortTestMethodsUsing = test_compare # type: ignore
    unittest.main()