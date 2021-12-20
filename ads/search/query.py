import asyncio
import collections
import json
import warnings
from math import ceil

from ads import config, logger
from ads.client import Client
from ads.models import Document


class SearchQuery(Client):

    _row_warning_level = 100_000
    _max_rows = 200

    # There are a few end points that can paginate search results, and those end points
    # have different locations and methods.
    # We will follow the 'explicit it better than implicit' approach and use sub-classes
    # for the appropriate end points (e.g., BigQuery, VaultQuery) and update the end-points
    # in those sub-classes.
    _api_end_point = "/search/query"
    _api_method = "get"

    def __init__(
        self,
        q=None,
        fields=None,
        filter_query=None,
        sort=None,
        start=0,
        rows=50,
        query_dict=None,
        **kwargs
    ) -> None:
        """
        Search ADS.
        """
        
        self.buffer = collections.deque()
        self.num_docs = None
        self.retrieved_docs = 0

        self._started = False 
        

        if query_dict is not None:
            self._query = query_dict.copy()
            for k, v in dict(rows=50, sort="score desc,id desc").items():
                self._query.setdefault(k, v)

        else:

            if fields is None:
                # TODO: Get defaults from a deque
                fields = ["author", "first_author", "bibcode", "id", "year", "title"]

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
                fl=fields,
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

        self.initial_query = self._query.copy()
        
        return None
        
    @property
    def query(self):
        return self._query

    @property
    def queue(self):
        """
        Asynchronous queue for communicating documents.
        
        We initialize this as a cached property instead of in `__init__` so that we don't get 
        asyncio warnings when exiting Python if we never used any asynchronous functionality.
        """
        while True:
            try:
                return self._queue
            except AttributeError:
                self._queue = asyncio.Queue()

    # Save a query.
    def save(self):
        """
        Save a query for later execution.

        :returns:
            A query identifier returned by ADS, and the number of documents found.
        """
        response = self._api_request(
            "/vault/query", 
            method="post",
            data=json.dumps(self.initial_query)
        )
        return (response.json["qid"], response.json["numFound"])
    

    @classmethod
    def load(cls, query_id):
        """
        Load a saved query from ADS.
        
        :param query_id:
            The query identifier that was previously returned by ADS.
        """

        with cls() as session:
            return session._api_request(f"/vault/execute_query/{query_id}", method="get", params=dict(start=0, rows=23))



    # Synchronous iterator protocol.

    def __iter__(self):
        return self

    def __next__(self):

        while True:
            try:
                document_kwds = self.buffer.popleft()
            except IndexError:
                if self.num_docs is None or self.retrieved_docs < self.num_docs:
                    self.fetch_page()
                else:
                    try:
                        # Close the session before we finish iterating.
                        self.session.close()
                    finally:
                        raise StopIteration
            else:
                obj = Document(**document_kwds)
                obj._dirty.clear()
                return obj

    
    def fetch_page(self):
        logger.debug(f"Querying with {self.query}")
        
        response = self.api_request(self._api_end_point, method=self._api_method, params=self.query)

        num_found = response.json["response"]["numFound"]
        documents = response.json["response"]["docs"]

        # If this is the first page, we will store the number of records to expect from this query.
        if self.num_docs is None:
            start, rows = (self.query["start"], self.query["rows"])
            self.num_docs = min(num_found - start, rows)
        
        N = 0
        for N, doc in enumerate(documents, start=1):
            self.buffer.append(doc)

        self.retrieved_docs += N

        logger.debug(f"So far have {self.retrieved_docs} of {self.num_docs}")
        
        # `initial_query` refers to the original query, `query` refers to a mutable query.
        self.query.update(
            start=start + N,
            rows=min(N, self.num_docs - self.retrieved_docs)
        )
        return None

    # Asynchronous iterator protocol.

    def __aiter__(self):
        return self

    async def async_fetch_pages(self):

        logger.debug(f"in async_fetch_pages")

        async with self.async_session as session:
            
            # Make all queries asynchronously.
            expected_pages = ceil(self.query["rows"] / self._max_rows)
            logger.debug(f"Expecting {expected_pages} pages")

            requests = []
            for page in range(expected_pages):
                pp = page * self._max_rows
                start = self.query["start"] + pp
                rows = min(self._max_rows, self.query["rows"] - pp)
                logger.debug(f"on page {page} with {start} {rows}")
                requests.append(
                    asyncio.ensure_future(
                        self.async_api_request(
                            session,
                            self._api_end_point,
                            method=self._api_end_point,
                            params={**self.query, **dict(start=start, rows=rows)}
                        )
                    )
                )
            
            logger.debug(f"{len(requests)} requests queued")

            # Create a mutable requests list.
            mutable_requests = [] + requests
            iterables = asyncio.as_completed(mutable_requests)

            # Get the first available request, which we will use to see if there are coroutines
            # that we should cancel.
            response = await next(iterables)

            num_found = response.json["response"]["numFound"]
            if num_found < self.query["rows"]:
                
                # We should cancel some coroutines.
                n_keep = ceil(num_found / self._max_rows)
                n_cancel = expected_pages - n_keep

                logger.debug(f"Cancelling {n_cancel} and keeping {n_keep}")

                for coroutine in requests[::-1][:n_cancel]:
                    logger.debug(f"Cancelling request {coroutine.get_name()} {coroutine.done()} {coroutine}")
                    coroutine.cancel()
                    logger.debug(f"Is cancelled? {coroutine.cancelled()} {coroutine.done()}")
                
                # Create a new iterable with just the remaining requests.
                iterables = asyncio.as_completed(requests[:n_keep])
            
            else:
                # Not deleting anything, so we should post the results to the queue.
                for doc in response.json["response"]["docs"]:
                    await self.queue.put(doc)

            for request in iterables:
                logger.debug(f"Iterating with {response}")
                response = await request
                for doc in response.json["response"]["docs"]:
                    await self.queue.put(doc)
            
        # Signal that we are done.
        await self.queue.put(None)

        return None

        
    async def __anext__(self):
        
        if not self._started:
            # Execute the query.
            self._started = True
            asyncio.create_task(self.async_fetch_pages())
            
        doc = await self.queue.get()
        if doc is None:
            raise StopAsyncIteration
        return doc
