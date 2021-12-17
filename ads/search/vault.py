
from ads.search import SearchQuery

# TODO: Ask ADS team if VaultQuery service contributes to BigQuery rate limits, or something else?

# TODO: Suggest that the /query2svg/ end point actually renders as an image-type so it can appear on
#       websites, etc, and that the UI accepts query identifier as an end-point. That way people can
#       share "searches" rather than a library.

class VaultQuery(SearchQuery):

    def __init__(
        self,
        qid,
        q=None,
        fl=None,
        start=None,
        rows=None,
        sort=None,
        **kwargs
    ) -> None:
        """
        Search using a stored query on ADS.
        
        :param qid:
            The identifier string of the query, previously given by `ads.SearchQuery.save()`.
        """

        # Set the end-point for this query.
        self.qid = qid
        self._api_end_point = f"/vault/execute_query/{qid}"

        assert set([q, fl, start, rows, sort]).issubset({None}), "Need a thinko to decide what to do first."

        return None
    

    def get_information(self):
        """
        Retrieve information about this stored query.
        
        :returns:
            A two-length tuple containing the serialized JSON input search parameters, and the number of documents
            found by this query the last time it was execute. The number of documents found is up to date only
            when the query is stored. But if the number is higher than 0 then you can be sure that the query was
            executed.
        """
        d = self._api_request(f"/vault/query/{self.qid}", method="get").json
        # TODO: Ask ADS team if `numfound` should be `numFound` here to be consistent with other end points.
        return (d["query"], d["numfound"])
    




