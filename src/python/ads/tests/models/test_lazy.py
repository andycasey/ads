import unittest
from ads.models.document import Document
from ads.models.lazy import LazyAttributesWarning
from ads.exceptions import APIResponseError

class TestExpressions(unittest.TestCase):

    def test_lazy_load(self):
        """ Test lazy-loading field attributes. """
        year = 2005
        fields = (Document.title, Document.author)
        query = Document.select(*fields)\
                        .where(Document.year == year)\
                        .limit(1)

        doc, = list(query)
        # The only things that should be in doc.__data__ are:
        # - title, author, bibcode, id
        self.assertNotIn("year", doc.__data__)
        self.assertIn("title", doc.__data__)
        self.assertIn("author", doc.__data__)    
        # It should have bibcode and id, even though we did
        # not ask for them, because these are necessary.
        self.assertIn("id", doc.__data__)
        self.assertIn("bibcode", doc.__data__)
        self.assertEqual(len(doc.__data__), 4)

        # Now let's try execute a lazy load.
        self.assertNotIn("year", doc.__data__)
        with self.assertWarns(LazyAttributesWarning):
            lazy_year = doc.year
        self.assertIn("year", doc.__data__)
        self.assertEqual(int(lazy_year), year)
        self.assertEqual(int(doc.__data__["year"]), year)
        
        # Let's remove the (id, bibcode) from the __data__
        # and try to make a lazy load. It should fail.
        del doc.__data__["id"]
        del doc.__data__["bibcode"]
        with self.assertRaises(APIResponseError):
            doc.citation_count