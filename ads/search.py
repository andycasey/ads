
import logging
import collections
import requests
from math import ceil
from ads import base, config, logger
import asyncio
import warnings

async def api_call(session, url, params):
    try:
        logger.info(f"Querying {url} with {params}")
        async with session.get(url, params=params) as response:
            logger.info(f"\tawaiting response on {params}")
            data = await response.json()
            logger.info(f"Retrieved response from {url} with {params}")
        return data

    except asyncio.CancelledError:
        logger.info(f"Cancelled request to {url} with {params}")
        raise

class SearchQuery(base.BaseQuery):

    _row_warning_level = 100_000

    def __init__(
        self,
        q=None,
        filter_query=None,
        filter_limit=None,
        sort=None,
        start=0,
        rows=50,
        query_dict=None,
        **kwargs
    ) -> None:
        """
        Search ADS.
        """
        super().__init__(**kwargs)

        self.buffer = collections.deque()
        self.num_docs = None
        self.retrieved_docs = 0

        self._started = False 
        self.queue = asyncio.Queue()
        
        if query_dict is not None:
            self._query = query_dict.copy()
            for k, v in dict(rows=50, sort="score desc,id desc").items():
                self._query.setdefault(k, v)

        else:

            if filter_limit is None:
                # TODO: Get defaults from a deque
                filter_limit = ["author", "first_author", "bibcode", "id", "year", "title"]

            """
            if sort is None and start is None:
                sort = "score desc, id desc"
            elif sort is None and start is not None:
                sort = "score desc"
            
            else:
                sort = sort.replace("+", " ")
                if not sort.endswith((" desc", " asc")):
                    sort = f"{sort} desc"
            """

            # Build the query,
            self._query = dict(
                q=q or "",
                fq=filter_query,
                fl=filter_limit,
                sort=sort,
                start=start,
                rows=rows,
            )
            self._query = dict((k, v) for k, v in self._query.items() if v is not None)

        if self.query["rows"] > self._row_warning_level:
            warnings.warn(
                f"You are planning to request many rows (more than {self._row_warning_level:,}). "
                f"This query may significantly expend your daily API limits."
            )
        
        return None


    @property
    def query(self):
        return self._query
    

    # Synchronous iterator protocol.

    def __iter__(self):
        return self


    def __next__(self):
        """
        iterator method, for backwards compatibility with the list() workflow
        """

        while True:
            try:
                document = self.buffer.popleft()
            except IndexError:
                if self.num_docs is None or self.retrieved_docs < self.num_docs:
                    self.fetch_page()
                else:
                    raise StopIteration
            else:
                return document


    def fetch_page(self):
        logger.info(f"Querying with {self.query}")
        response = self.session.get(config.SEARCH_URL, params=self.query)
        data = response.json()

        # If this is the first page, we will store the number of records to expect from this query.
        start, rows = (self.query["start"], self.query["rows"])
        self.num_docs = self.num_docs or min(data["response"]["numFound"] - start, rows)
        
        for doc in data["response"]["docs"]:
            self.buffer.append(doc)

        N = len(data["response"]["docs"])
        self.retrieved_docs += N

        logger.info(f"So far have {self.retrieved_docs} of {self.num_docs}")

        # This is the way we used to do it, but i don't like the idea of changing the original query.
        # TODO: Requires a thinko
        self.query.update(
            start=start + N,
            rows=min(N, self.num_docs - self.retrieved_docs)
        )


    # Asynchronous iterator protocol.

    def __aiter__(self):
        return self


    async def fetch_data(self):

        logger.info(f"in old_fetch_data")

        async with self.async_session as session:
            # We are going to have to await on the first result we send so we can see how many
            # results there are. Otherwise we could waste thousands of requests for data that
            # does not exist.

            data = await api_call(session, config.SEARCH_URL, self.query)

            # Send the first page of results to the queue.
            for doc in data["response"]["docs"]:
                self.queue.put_nowait(doc)
        
            # We cannot trust the number of rows that we supply to ADS, because it will be 
            # superceded by the maximum number of rows that it will return per request.
            received_rows = len(data["response"]["docs"])

            # This is the number of rows we expect from this query (from all requests).
            expected_rows = min(data["response"]["numFound"] - self.query["start"], self.query["rows"])

            if expected_rows > received_rows:
                # Start the other queries asynchronously.

                # Assume the number of rows per request is what we received on the first request.
                expected_pages = ceil((expected_rows - received_rows) / received_rows)

                requests = []
                for page in range(1, 1 + expected_pages):
                    pp = page * received_rows
                    start = self.query["start"] + pp
                    rows = min(received_rows, expected_rows - pp)

                    logger.info(f"Requesting page {page} with start {start} {rows}")

                    requests.append(
                        asyncio.ensure_future(
                            api_call(
                                session,
                                config.SEARCH_URL,
                                {**self.query, **dict(start=start, rows=rows)}
                            )
                        )
                    )
            
                for request in asyncio.as_completed(requests):
                    logger.info(f"Got another response: {type(request)} {request}")
                    data = await request
                    for doc in data["response"]["docs"]:
                        # Should we `await self.queue.put()` or `self.queue.put_nowait()`?
                        self.queue.put_nowait(doc)

        # Signal that we are done.
        await self.queue.put(None)
        
        return None


    async def __fetch_data(self):

        logger.info(f"in fetch_data")

        async with self.async_session as session:
            
            # Make all queries asynchronously.
            rows_per_page = 2_000
            expected_pages = ceil(self.query["rows"] / rows_per_page)
            logger.info(f"Expecting {expected_pages} pages")

            requests = []
            for page in range(expected_pages):
                pp = page * rows_per_page
                start = self.query["start"] + pp
                rows = min(rows_per_page, self.query["rows"] - pp)
                logger.info(f"on page {page} with {start} {rows}")
                requests.append(
                    asyncio.ensure_future(
                        api_call(
                            session,
                            config.SEARCH_URL,
                            {**self.query, **dict(start=start, rows=rows)}
                        )
                    )
                )
            
            logger.info(f"{len(requests)} requests queued")

            # Create a mutable requests list.
            mutable_requests = [] + requests
            iterable = asyncio.as_completed(mutable_requests)

            # Get the first available request, which we will use to see if there are coroutines
            # that we should cancel.
            data = await next(iterable)

            num_found = data["response"]["numFound"]
            if num_found < self.query["rows"]:
                
                # We should cancel some coroutines.
                n_keep = ceil(num_found / rows_per_page)
                n_cancel = expected_pages - n_keep

                logger.info(f"Cancelling {n_cancel} and keeping {n_keep}")

                for coroutine in requests[::-1][:n_cancel]:
                    logger.info(f"Cancelling request {coroutine.get_name()} {coroutine.done()} {coroutine}")
                    coroutine.cancel()
                    logger.info(f"Is cancelled? {coroutine.cancelled()} {coroutine.done()}")
                
                # Create a new iterable with just the remaining requests.
                iterable = asyncio.as_completed(requests[:n_keep])
            
            else:
                # Not deleting anything, so we should post the results to the queue.
                for doc in data["response"]["docs"]:
                    await self.queue.put_nowait(doc)

            for response in iterable:
                logger.info(f"Iterating with {response}")
                data = await response
                for doc in data["response"]["docs"]:
                    await self.queue.put_nowait(doc)
            
        # Signal that we are done.
        await self.queue.put(None)
        
        return None

        
    async def __anext__(self):
        
        if not self._started:
            # Execute the query.
            self._started = True
            asyncio.create_task(self.fetch_data())
            
        doc = await self.queue.get()
        if doc is None:
            raise StopAsyncIteration
        return doc




"""

    async def fetch_data(self):
        # Work out how many pages we need to query.
        start = self.query["start"]
        rows = self.query["rows"]

        max_possible_pages = int(ceil((rows - start) / max_rows_per_page))
        
        # We will need to query at least one page, possibly more.
        async with self.async_session:
            async with base.semaphore:
                # TODO: handle the rate limiting through an APIResponse
                request = await self.async_session.get(
                    SEARCH_URL,
                    params=self.query
                )
                contents = await request.json()
        
        return self
        max_rows_per_page = 200

        # Work out how many pages we need to query.
        start = self.query["start"]
        rows = self.query["rows"]

        max_possible_pages = int(ceil((rows - start) / max_rows_per_page))
        
        # We will need to query at least one page, possibly more.
        async with self.async_session:
            async with base.semaphore:
                # TODO: handle the rate limiting through an APIResponse
                request = await self.async_session.get(
                    SEARCH_URL,
                    params=self.query
                )
                contents = await request.json()

        # Here is where we continue to iterate over the pages.
        num_found = contents["response"]["numFound"]
        max_pages = int(ceil(num_found / max_rows_per_page))
        num_pages = min(max_pages, max_possible_pages)

        coroutines = []
        for page in range(1, num_pages + 1):
            kwds = dict(start=start + page * max_rows_per_page, rows=max_rows_per_page)
            async with self.async_session:
                async with base.semaphore:
                    coroutines.append(
                        self.async_session.get(
                            SEARCH_URL, 
                            params={**self.query, **kwds}
                        )
                    )



        raise a

            # NOTE: If the 'sort' field isn't given, then we don't have to await these synchronously
        if "sort" not in self.query:
            async for coroutine in asyncio.as_completed(coroutines):
                result = await coroutine
                foo = await result.json()
                for doc in foo["response"]["docs"]:
                    self.documents.append(doc)

        else:
                
            for task in coroutines:
                foo = await task

                raise a



    def __next__(self):
        if self.__iter_counter == 0:
            self.execute()
        
        try:
            yield from self.documents
        except StopIteration:
            raise a




            recieved_rows = 0
            async with self.async_session as session:
                while True:
                    params = query.copy()
                    params.update(start=start, rows=requested_rows)

                    logger.info(f"Querying with {params}")
                    async with base.semaphore:
                        async with session.get(config.SEARCH_URL, params=params) as response:
                            data = await response.json()

                    await self.queue.put(data)

                    rows = len(data["response"]["docs"])
                    
                    # Update cursor pointer
                    recieved_rows += rows
                    start += rows

                    logger.info(f"Total received {recieved_rows} ({rows} here) and start {start} of {requested_rows}")

                    if not has_next_page(data) or recieved_rows >= requested_rows:
                        # Signal the peer to quit.
                        await self.queue.put(None)
                        break


        asyncio.ensure_future(fetch_all_pages())

        while True:
            data = await self.queue.get()
            if not data:
                break
            
            for doc in get_docs(data):
                self.documents.append(doc)

"""

def has_next_page(data):
    num_found = data["response"]["numFound"]
    start = data["response"]["start"]
    rows_recieved = len(data["response"]["docs"])
    return num_found > start + rows_recieved