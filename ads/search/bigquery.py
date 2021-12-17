# No rate limit information given back by ADS for BigQuery, but documentation
# says it is limited to ~100 per day.
# TODO: Raise this with the ADS team.

from ads.search import SearchQuery

class BigQuery(SearchQuery):
    
    _api_endpoint = "/search/bigquery"
    _api_method = "post"

    def __init__(
        self,
        bibcodes,
        **kwargs
    ) -> None:
        """
        Search ADS using a list of many bibcodes.

        This endpoint accepts standard search query parameters and returns standard search results, 
        but it also accepts as input a very large query (i.e. a query that can be expressed only as 
        a list of search criteria, typically bibcodes). There is currently no limit to the size of 
        the submitted data (besides buffer/time limits imposed by our API frontend); however, there 
        are severe limits on how often you can call this endpoint. 
        Typically, only 100 requests per day per user are allowed.

        The bigquery is always executed as a filter after the main query (to filter out unwanted 
        results and keep only the results specified by the bigquery). 
        
        You may want to use `q=*:*` to filter contents of the whole database, however it is advisable 
        to make the q as specific as possible. Broad queries have higher qTime (execution time) and 
        that will be counted towards your rate-limit (in the future).

        The bigquery filter is applied only after the main search (i.e. it limits results of the main search).

        :param bibcodes:
            A list of strings of bibliographic codes.
        """

        super(BigQuery, self).__init__(**kwargs)
        print(self.query)
        self._bibcodes = list(bibcodes)
        
        q = self._query.get("q", "")
        self._query.update(
            dict(
                q=q or "*:*",
                wt="json",
                fq="{!bitset}",
                # TODO: Is this what we want to be doing with start and rows?
                start=0,
                rows=len(bibcodes),
            )
        )
        self.initial_query = self._query.copy()
        return None

    # TODO: Before we can remove these monkey patches, we need to better store the payload params + data, as they
    # are different.
    def api_request(self, end_point, params, method=None, **kwargs):
        return self._api_request(
            "/search/bigquery", 
            method="post", 
            params=params,
            data="\n".join(["bibcode"] + self._bibcodes)
        )

    async def async_api_request(self, async_session, params):
        return self._async_api_request(
            async_session, 
            "/search/bigquery", 
            method="post", 
            params=params,
            data="\n".join(["bibcode"] + self._bibcodes)
        )

    
    @property
    def request_headers(self):
        """ The HTTP headers to send with this request. """
        # BigQuery searches break if you give application/json, because they
        # require "big-query/csv" as their Content-Type, or for the content-type
        # not to be set at all.
        # But BigQuery is the anomaly: other end-points (e.g., vault/store) require 
        # application/json to be set as the content-type, otherwise they die.
        return {
            **super(BigQuery, self).request_headers,
            **{"Content-Type": "big-query/csv"}
        }
