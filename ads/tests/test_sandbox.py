"""
Tests for the search interface
"""
import json
import unittest

from ads.sandbox import SearchQuery, MetricsQuery, ExportQuery

from .stubdata.metrics import example_metrics_response
from .stubdata.solr import example_solr_response
from .stubdata.export import example_export_response


class TestSandbox(unittest.TestCase):
    """
    Test the sandbox environment
    """

    def test_search_query(self):
        """
        Test you should receive stub Solr data when using SearchQuery
        """
        sq = SearchQuery(q="star", rows=28)

        b1 = [a.bibcode for a in sq]

        resp = json.loads(example_solr_response)
        b2 = [i['bibcode'] for i in resp['response']['docs']]

        self.assertSequenceEqual(b1, b2)

    def test_article_get_field(self):
        """
        Test you should receive stub data when accessing cached properties
        """
        sq = SearchQuery(q='fake bibcode', fl=['bibcode', 'id'])
        b = [a for a in sq]

        citation_count = b[0].citation_count
        author = b[0].author
        volume = int(b[0].volume)

        self.assertEqual(citation_count, 0)
        self.assertEqual(author[0], u'Sudilovsky, Oscar')
        self.assertEqual(volume, 174)

        metrics = b[0].metrics
        self.assertEqual(metrics, json.loads(example_metrics_response))

        export = b[0].bibtex
        self.assertEqual(export, json.loads(example_export_response)['export'])

    def test_metrics_query(self):
        """
        Test you should receive stub metrics data when using MetricsQuery
        """
        mq = MetricsQuery(['bibcode'])
        metrics = mq.execute()

        self.assertEqual(metrics, json.loads(example_metrics_response))

    def test_export_query(self):
        """
        Test you should receive stub export data when using ExportQuery
        """
        eq = ExportQuery(bibcodes=['bibcode'], format='bibtex')
        export = eq.execute()

        self.assertEqual(export, json.loads(example_export_response)['export'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
