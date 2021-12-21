import unittest
from ads.models.document import Document

class TestExpressions(unittest.TestCase):

    def test_lazy_load(self):
        year = 2005

        fields = (Document.title, Document.author)
        query = Document.select(*fields)\
                        .where(Document.year == year)\
                        .limit(1)

        doc, = list(query)
        self.assertNotIn("year", doc.__data__)

        # It should have bibcode and id, even though we did
        # not ask for them, because these are necessary.
        self.assertIn("id", doc.__data__)
        self.assertIn("bibcode", doc.__data__)

        # Now let's try execute a lazy load.
        self.assertEqual(int(doc.year), year)
        self.assertIn("year", doc.__data__)
        self.assertEqual(int(doc.__data__["year"]), year)
        