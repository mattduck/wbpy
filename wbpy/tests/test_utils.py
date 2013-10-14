# -*- coding: utf-8 -*-
import sys
try:
    # py2.6
    import unittest2 as unittest
except ImportError:
    # py2.7+
    import unittest

import mock

from wbpy import utils


class TestFetchFn(unittest.TestCase):

    def setUp(self):
        self.url = "http://www.google.com"

    def test_caching_response(self):
        cache_fn = mock.patch("wbpy.utils._cache_response").start()
        utils.fetch(self.url, check_cache=False, cache_response=True)
        self.assertTrue(cache_fn.called)

    def test_fetching_from_cache(self):
        # Make call once so we know it's been cached
        utils.fetch(self.url, check_cache=False, cache_response=True)

        # Make sure reading from file, rather than calling url
        if sys.version_info > (3,):
            builtin_mod = "builtins"
        else:
            builtin_mod = "__builtin__"

        open_fn = mock.patch(builtin_mod + ".open").start()
        utils.fetch(self.url, check_cache=True)
        self.assertTrue(open_fn.called)
        open_fn.stop()
