
import unittest

import ads.services.misc
from ads import Document

class TestMiscellaneousServices(unittest.TestCase):

    def test_citation_helper(self):
        
        bibcodes = list(map(str.strip, """
            2020A&A...642C...1G 2020A&A...637C...3G 2019MNRAS.488.2892P 2019A&A...625A..97R 
            2019MNRAS.485.2642G 2019A&A...623A.110G 2019A&A...622A.205K 2019A&A...622A..60C 
            2019A&A...621A.144M 2018A&A...620A.127M 2018A&A...620A.197R 2018A&A...618A..30H 
            2018A&A...618A..58M 2018A&A...616A...2L 2018A&A...616A..14G 2018A&A...616E...1F 
            2018A&A...616A..17A 2018A&A...616A...1G 2018A&A...616A...7S 2018A&A...616A...4E 
            2018A&A...616A...5C 2018A&A...616A...8A 2018A&A...616A..16L 2018A&A...616A...9L 
            2018A&A...616A..11G 2018A&A...616A..13G 2018A&A...616A..12G 2018A&A...616A...3R 
            2018A&A...616A...6S 2018A&A...616A..10G 2018A&A...616A..15H 2017A&A...607A.105M 
            2017A&A...605A..79G 2017A&A...605A..52M 2017A&A...601A..19G 2017A&A...601C...1C 
            2017A&A...600A..51E 2017A&A...599A..32V 2017A&A...599A..50A 2017arXiv170203295E 
            2016A&A...595A...2G 2016A&A...595A...7C 2016A&A...595A.133C 2016A&A...595A...3F 
            2016A&A...595A...5M 2016A&A...595A...6C 2016A&A...595A...4L
            """.split()))

        suggested = ads.services.misc.citation_helper(bibcodes)
        self.assertIsNotNone(suggested)
        self.assertEqual(len(suggested), 10) # We expect 10 suggestions because the input bibcodes are related.
        for item in suggested:
            self.assertIsInstance(item, Document)

        suggested_bibcodes = ads.services.misc.citation_helper(bibcodes, as_documents=False)
        self.assertIsInstance(suggested_bibcodes, list)
        expected_keys = ("bibcode", "score", "title", "author")

        for item in suggested_bibcodes:
            self.assertIsInstance(item, dict)
            self.assertEqual(len(item), len(expected_keys))

            for key in expected_keys:
                self.assertIn(key, item)
            
            self.assertIsInstance(item["bibcode"], str)
            self.assertIsInstance(item["score"], int)
            self.assertIsInstance(item["title"], str) # Different format to what we get from Solr
            self.assertIsInstance(item["author"], str) # Different format to what we get from Solr
            # Email the ADS team about this.