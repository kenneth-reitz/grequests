GRequests: Asynchronous Requests
===============================

GRequests allows you to use Requests with Gevent to make asynchronous HTTP
Requests easily.

|version| |pyversions|



Installation
------------

Installation is easy with pip::

    $ pip install grequests
    ✨🍰✨


Usage
-----

Usage is simple:

.. code-block:: python

    import grequests

    urls = [
        'http://www.heroku.com',
        'http://python-tablib.org',
        'http://httpbin.org',
        'http://python-requests.org',
        'http://fakedomain/',
        'http://kennethreitz.com'
    ]

Create a set of unsent Requests:

.. code-block:: python

    >>> rs = (grequests.get(u) for u in urls)

Send them all at the same time using ``map``:

.. code-block:: python

    >>> grequests.map(rs)
    [<Response [200]>, <Response [200]>, <Response [200]>, <Response [200]>, None, <Response [200]>]


The HTTP verb methods in ``grequests`` (e.g., ``grequests.get``, ``grequests.post``, etc.) accept all the same keyword arguments as in the ``requests`` library.

Error Handling
^^^^^^^^^^^^^^

To handle timeouts or any other exception during the connection of
the request, you can add an optional exception handler that will be called with the request and
exception inside the main thread. The value returned by your exception handler will be used in the result list returned by ``map``.


.. code-block:: python

    >>> def exception_handler(request, exception):
    ...    print("Request failed")

    >>> reqs = [
    ...    grequests.get('http://httpbin.org/delay/1', timeout=0.001),
    ...    grequests.get('http://fakedomain/'),
    ...    grequests.get('http://httpbin.org/status/500')]
    >>> grequests.map(reqs, exception_handler=exception_handler)
    Request failed
    Request failed
    [None, None, <Response [500]>]


imap
^^^^

For some speed/performance gains, you may also want to use ``imap`` instead of ``map``. ``imap`` returns a generator of responses. Order of these responses does not map to the order of the requests you send out. The API for ``imap`` is equivalent to the API for ``map``. You can also adjust the ``size`` argument to ``map`` or ``imap`` to increase the gevent pool size.


.. code-block:: python

    for resp in grequests.imap(reqs, size=10):
        print(resp)


There is also an enumerated version of ``imap``, ``imap_enumerated`` which yields the index of the request from the original request list and its associated response. However, unlike ``imap``, failed requests and exception handler results that return ``None`` will also be yielded (whereas in ``imap`` they are ignored). Aditionally, the ``requests`` parameter for ``imap_enumerated`` must be a sequence. Like in ``imap``, the order in which requests are sent and received should still be considered arbitrary.

.. code-block:: python

    >>> rs = [grequests.get(f'https://httpbin.org/status/{code}') for code in range(200, 206)]
    >>> for index, response in grequests.imap_enumerated(rs, size=5):
    ...     print(index, response)
    1 <Response [201]>
    0 <Response [200]>
    4 <Response [204]>
    2 <Response [202]>
    5 <Response [205]>
    3 <Response [203]>

gevent - when things go wrong
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Because ``grequests`` leverages ``gevent`` (which in turn uses monkeypatching for enabling concurrency), you will often need to make sure ``grequests`` is imported before other libraries, especially ``requests``, to avoid problems. See `grequests gevent issues <https://github.com/spyoungtech/grequests/issues?q=is%3Aissue+label%3A%22%3Ahear_no_evil%3A%3Asee_no_evil%3A%3Aspeak_no_evil%3A++gevent%22+>`_ for additional information.


.. code-block:: python

    # GOOD
    import grequests
    import requests
    
    # BAD
    import requests
    import grequests



grequests - "Too many open files" error
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Be aware, that the Request and Response objects contain a reference to the underlying HTTP[S]Connection, which will be kept alive by default. That means every Request and Response object will hold a reference to an open TCP socket, that will consume memory and consume a file descriptor to the TCP socket. If you create more than ``ulimit -u`` requests, you will run out of open file descriptors per process and will see  ``Too many open files`` error. For example:

.. code-block:: python

    import os
    import grequests
    from subprocess import check_output

    def get_tcp_conn_count():
        cmd = f"lsof -i -n | grep {os.getpid()} | grep https | wc -l"
        out = check_output(['bash', '-c', cmd]).decode().strip()
        return out

    reqs = [grequests.get("https://www.google.com") for i in range(10)]
    resps = grequests.map(reqs)
    print("File descriptors created:", [resp.raw._pool.pool.queue[-1].sock.fileno() for resp in resps]) 
    print("Active TCP connections:", get_tcp_conn_count())

>>> File descriptors created: [89, 93, 84, 91, 85, 86, 87, 88, 92, 90]
>>> Active TCP connections: 10

These sockets are closed when:
    - both Request and Response object are garbage collected, or
    - when the underling HTTPSConnection is closed manually.

Be very careful about keeping open Request/Response when crawling large amount of URLs and sending hundreds/thousands of requests. Make sure to either close the underlying connection pool after processing Response object: ``resp.raw._pool.close()``, so that you don't have more than ``ulimut -u`` active TCP connections at any point of program's lifetime.

.. code-block:: python

    for resp in grequests.imap(reqs):
        # do something with resp.content
        resp.raw._pool.close() # close the TCP connection and release file descriptor


or alternatively, you can send Requests in batches that are less than ``ulimit -u`` and let the Garbage Collector cleanup all the resources after each batch run.

.. code-block:: python

    import os
    import grequests
    from subprocess import check_output

    urls = ["https://www.google.com/"] * 100
    BATCH_SIZE = 10

    def get_tcp_conn_count():
        cmd = f"lsof -i -n | grep {os.getpid()} | grep https | wc -l"
        out = check_output(['bash', '-c', cmd]).decode().strip()
        return out

    def send_batch(batch_urls: list):
        """ batch_size urls are converted into requests, sent to grequests, responses processed and 
            TCP sockets are promptly garbage collected after return """
    
        batch_reqs = [grequests.get(url) for url in batch_urls]
        print("Active TCP connections before:", get_tcp_conn_count())
        for resp in grequests.imap(batch_reqs, size=BATCH_SIZE):
            pass # do something with resp.content
        print("Active TCP connections after:", get_tcp_conn_count())

    for i in range(0, len(urls), BATCH_SIZE):
        print(f"sending batch [{i}:{i+BATCH_SIZE}]")
        send_batch(urls[i:i+BATCH_SIZE]) 

>>> sending batch [0:10]
>>> Active TCP connections before: 0
>>> Active TCP connections after: 10
>>> sending batch [10:20]
>>> Active TCP connections before: 0
>>> Active TCP connections after: 10
>>> sending batch [20:30]
>>> Active TCP connections before: 0
>>> Active TCP connections after: 10
>>> ...
>>> sending batch [90:100]
>>> Active TCP connections before: 0
>>> Active TCP connections after: 10

As you can see, ``BATCH_SIZE`` connections are created and promptly closed after each batch run, and the risk of hitting too many open sockets is mitigated.



.. |version| image:: https://img.shields.io/pypi/v/grequests.svg?colorB=blue
    :target: https://pypi.org/project/grequests/

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/grequests.svg?
    :target: https://pypi.org/project/grequests/
    
    
