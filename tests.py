#! /usr/bin/env python
# -*- coding: utf-8 -*-

from grequests import get, map, imap

########### Constants ############
urls = [
        'http://github.com',
        'http://www.google.com',
        'http://www.psf.org'
        ]
############# tests ##############
def test_get():
    global urls
    to_fetch = (get(url) for url in urls)
    map(to_fetch)
    for fetched in to_fetch:
        assert fetched.ok

def test_imap_with_size():
    global urls
    to_fetch = (get(url) for url in urls)
    imap(to_fetch, size = len(urls) - 1)
    for fetching in to_fetch:
        assert fetching.send()

import os
import time
import unittest

import requests
from requests.exceptions import Timeout
import grequests

HTTPBIN_URL = os.environ.get('HTTPBIN_URL', 'http://httpbin.org/')

def httpbin(*suffix):
    """Returns url for HTTPBIN resource."""
    return HTTPBIN_URL + '/'.join(suffix)


N = 5
URLS = [httpbin('get?p=%s' % i) for i in range(N)]


class GrequestsCase(unittest.TestCase):

    def test_map(self):
        reqs = [grequests.get(url) for url in URLS]
        resp = grequests.map(reqs, size=N)
        self.assertEqual([r.url for r in resp], URLS)

    def test_imap(self):
        reqs = (grequests.get(url) for url in URLS)
        i = 0
        for i, r in enumerate(grequests.imap(reqs, size=N)):
            self.assertTrue(r.url in URLS)
        self.assertEqual(i, N - 1)

    def test_hooks(self):
        result = {}

        def hook(r, **kwargs):
            result[r.url] = True
            return r

        reqs = [grequests.get(url, hooks={'response': [hook]}) for url in URLS]
        grequests.map(reqs, size=N)
        self.assertEqual(sorted(result.keys()), sorted(URLS))

    def test_callback_kwarg(self):
        result = {'ok': False}

        def callback(r, **kwargs):
            result['ok'] = True
            return r

        self.get(URLS[0], callback=callback)
        self.assertTrue(result['ok'])

    def test_session_and_cookies(self):
        c1 = {'k1': 'v1'}
        r = self.get(httpbin('cookies/set'), params=c1).json()
        self.assertEqual(r['cookies'], c1)
        s = requests.Session()
        r = self.get(httpbin('cookies/set'), session=s, params=c1).json()
        self.assertEqual(dict(s.cookies), c1)

        # ensure all cookies saved
        c2 = {'k2': 'v2'}
        c1.update(c2)
        r = self.get(httpbin('cookies/set'), session=s, params=c2).json()
        self.assertEqual(dict(s.cookies), c1)

        # ensure new session is created
        r = self.get(httpbin('cookies')).json()
        self.assertEqual(r['cookies'], {})

        # cookies as param
        c3 = {'p1': '42'}
        r = self.get(httpbin('cookies'), cookies=c3).json()
        self.assertEqual(r['cookies'], c3)

    def test_calling_request(self):
        reqs = [grequests.request('POST', httpbin('post'), data={'p': i})
                for i in range(N)]
        resp = grequests.map(reqs, size=N)
        self.assertEqual([int(r.json()['form']['p']) for r in resp], list(range(N)))

    def test_stream_enabled(self):
        r = grequests.map([grequests.get(httpbin('stream/10'))],
                          size=2, stream=True)[0]
        self.assertFalse(r._content_consumed)

    def test_concurrency_with_delayed_url(self):
        t = time.time()
        n = 10
        reqs = [grequests.get(httpbin('delay/1')) for _ in range(n)]
        grequests.map(reqs, size=n)
        self.assertLess((time.time() - t), n)

    def test_map_timeout_no_exception_handler(self):
        """
        compliance with existing 0.2.0 behaviour
        """
        reqs = [grequests.get(httpbin('delay/1'), timeout=0.001), grequests.get(httpbin('/'))]
        responses = grequests.map(reqs)
        self.assertIsNone(responses[0])
        self.assertTrue(responses[1].ok)
        self.assertEqual(len(responses), 2)

    def test_map_timeout_exception_handler_no_return(self):
        """
        ensure default behaviour for a handler that returns None
        """
        def exception_handler(request, exception):
            pass
        reqs = [grequests.get(httpbin('delay/1'), timeout=0.001), grequests.get(httpbin('/'))]
        responses = grequests.map(reqs, exception_handler=exception_handler)
        self.assertIsNone(responses[0])
        self.assertTrue(responses[1].ok)
        self.assertEqual(len(responses), 2)

    def test_map_timeout_exception_handler_returns_exception(self):
        """
        ensure returned value from exception handler is stuffed in the map result
        """
        def exception_handler(request, exception):
            return exception
        reqs = [grequests.get(httpbin('delay/1'), timeout=0.001), grequests.get(httpbin('/'))]
        responses = grequests.map(reqs, exception_handler=exception_handler)
        self.assertIsInstance(responses[0], Timeout)
        self.assertTrue(responses[1].ok)
        self.assertEqual(len(responses), 2)

    def test_imap_timeout_no_exception_handler(self):
        """
        compliance with existing 0.2.0 behaviour
        """
        reqs = [grequests.get(httpbin('delay/1'), timeout=0.001)]
        out = []
        try:
            for r in grequests.imap(reqs):
                out.append(r)
        except Timeout:
            pass
        self.assertEqual(out, [])

    def test_imap_timeout_exception_handler_no_return(self):
        """
        ensure imap-default behaviour for a handler that returns None
        """
        def exception_handler(request, exception):
            pass
        reqs = [grequests.get(httpbin('delay/1'), timeout=0.001)]
        out = []
        for r in grequests.imap(reqs, exception_handler=exception_handler):
            out.append(r)
        self.assertEqual(out, [])


    def test_imap_timeout_exception_handler_returns_value(self):
        """
        ensure behaviour for a handler that returns a value
        """
        def exception_handler(request, exception):
            return 'a value'
        reqs = [grequests.get(httpbin('delay/1'), timeout=0.001)]
        out = []
        for r in grequests.imap(reqs, exception_handler=exception_handler):
            out.append(r)
        self.assertEqual(out, ['a value'])

    def test_map_timeout_exception(self):
        class ExceptionHandler:
            def __init__(self):
                self.counter = 0

            def callback(self, request, exception):
                 self.counter += 1
        eh = ExceptionHandler()
        reqs = [grequests.get(httpbin('delay/1'), timeout=0.001)]
        list(grequests.map(reqs, exception_handler=eh.callback))
        self.assertEqual(eh.counter, 1)

    def test_imap_timeout_exception(self):
        class ExceptionHandler:
            def __init__(self):
                self.counter = 0

            def callback(self, request, exception):
                 self.counter += 1
        eh = ExceptionHandler()
        reqs = [grequests.get(httpbin('delay/1'), timeout=0.001)]
        list(grequests.imap(reqs, exception_handler=eh.callback))
        self.assertEqual(eh.counter, 1)

    def get(self, url, **kwargs):
        return grequests.map([grequests.get(url, **kwargs)])[0]


if __name__ == '__main__':
    unittest.main()
