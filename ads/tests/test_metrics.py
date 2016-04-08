"""
Tests for MetricsQuery
"""
import unittest
import six

from .mocks import MockMetricsResponse

from ads.metrics import MetricsQuery, MetricsResponse
from ads.config import METRICS_URL


class TestMetricsQuery(unittest.TestCase):
    """
    test the MetricsQuery object
    """
    def setUp(self):
        """
        Clear rate limits
        """
        MockMetricsResponse.current_ratelimit = 400

    def test_init(self):
        """
        an initialized MetricsQuery object should have a bibcode attributes
        that is a list
        """
        self.assertEqual(MetricsQuery('bibcode').bibcodes, ['bibcode'])
        self.assertEqual(MetricsQuery(['b1', 'b2']).bibcodes, ['b1', 'b2'])

    def test_execute(self):
        """
        MetricsQuery.execute() should return a MetricsResponse object, and
        that object should be set as the .response attribute
        """
        mq = MetricsQuery('bibcode')
        with MockMetricsResponse(METRICS_URL):
            retval = mq.execute()
        self.assertIsInstance(mq.response, MetricsResponse)
        self.assertEqual(retval, mq.response.metrics)

    def test_ratelimit_on_cached_property_access(self):
        """
        When a cached property is accessed, the parent query object should
        update the rate limit appropriately.
        """
        metrics_query = MetricsQuery('bibcode')
        with MockMetricsResponse(METRICS_URL):
            metrics_query.execute()

        self.assertEqual(metrics_query.get_ratelimits(), {'reset': '1436313600', 'limit': '400', 'remaining': '399'})

        self.assertEqual(MetricsQuery.get_ratelimits(), {'reset': '1436313600', 'limit': '400', 'remaining': '399'})


class TestMetricsResponse(unittest.TestCase):
    """
    test MetricsResponse object
    """

    def test_init(self):
        """
        an initialized MetricsResponse should have an attribute metrics
        that is a dictionary, and an attribute _raw that is a string
        """
        mr = MetricsResponse('{"valid":"json"}')
        self.assertIsInstance(mr.metrics, dict)
        self.assertIsInstance(mr._raw, six.string_types)

if __name__ == '__main__':
    unittest.main(verbosity=2)