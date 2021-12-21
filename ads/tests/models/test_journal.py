
import os
import unittest
import json
from ads.tests import strict
from ads.models import Document, Journal
from ads.utils import setup_database, _get_data_path

def expression_as_string(expression):
    return Document.select().where(expression).__str__()

class TestJournal(unittest.TestCase):

    #def setUp(self):
    #    # Initialize the database, in case we haven't already.
    #    setup_database()


    def test_journal_ingest_count(self):
        with open(_get_data_path("journals.json"), "r") as fp:
            journals = json.load(fp)
        count = Journal.select().count()

        self.assertEqual(count, len(journals))
        self.assertGreater(count, 0)
        

    def test_journal_get(self):

        def _check_journal(j):
            self.assertIsNotNone(j)
            self.assertIsNotNone(j.title)
            self.assertIsNotNone(j.abbreviation)

        # Get any journal.
        _check_journal(Journal.get())

        # Get by exact keyword.
        j = Journal.get(abbreviation="ApJ")
        _check_journal(j)
        self.assertEqual(j.title, "The Astrophysical Journal")

        j = Journal.get(title="Raumfahrtforschung")
        _check_journal(j)
        self.assertEqual(j.abbreviation, "RF")

        # Get by expression.
        j1 = Journal.get(abbreviation="ApJ")
        j2 = Journal.get(Journal.title == "The Astrophysical Journal")
        self.assertEqual(j1, j2)

        # Get non existant journals.
        non_existant_journal = "MOOCOW"
        with self.assertRaises(Journal.DoesNotExist):
            Journal.get(abbreviation=non_existant_journal)
        self.assertIsNone(Journal.get_or_none(abbreviation=non_existant_journal))


    def test_journal_select(self):

        self.assertGreater(
            Journal.select().where(Journal.title.contains("monthly")).count(),
            0
        )
        j1 = next(iter(Journal.select().where(Journal.abbreviation == "ApJ")))
        j2 = Journal.get(abbreviation="ApJ")
        self.assertEqual(j1, j2)


    def test_journal_order_by(self):

        A = Journal.select().order_by(Journal.abbreviation.asc())
        B = Journal.select().order_by(Journal.abbreviation.desc())
        for a, b in zip(A[::-1], B):
            self.assertEqual(a, b)

        A = Journal.select().order_by(Journal.title.asc())
        titles = [j.title for j in A]
        self.assertEqual(titles, sorted(titles))

        
    def test_journal_limit(self):
        count = Journal.select().count()
        for limit in (1, 10, 100, 1000):
            self.assertGreater(count, limit)
            self.assertEqual(limit, Journal.select().limit(limit).count())
            self.assertEqual(limit, len(Journal.select().limit(limit)))
    

    def test_journal_expression_resolution(self):

        self.assertEqual(
            expression_as_string(Document.journal == Journal.get(abbreviation="MNRAS")),
            "bibstem:MNRAS"
        )

        self.assertEqual(
            expression_as_string(Document.journal.title == "The Astrophysical Journal"),
            "bibstem:ApJ"
        )

        self.assertEqual(
            expression_as_string(Document.journal.abbreviation == "ApJ"),
            "bibstem:ApJ"
        )

        if strict:
            js = Journal.select().where(Journal.title.contains("gravitation"))
            self.assertEqual(
                expression_as_string(Document.journal.title.contains("gravitation")),
                f"bibstem:({' OR '.join(j.abbreviation for j in js)})"
            )

        abbreviation = "PASA"
        pasa = Journal.get(abbreviation=abbreviation)
        # Supply abbreviation directly to Journal.
        s1 = expression_as_string(Document.journal == pasa)
        s2 = expression_as_string(Document.journal == abbreviation)
        self.assertEqual(s1, s2)

        self.assertEqual(s1, "bibstem:PASA")
        

    def test_document_select(self):
        abbreviation = "PASA"
        pasa = Journal.get(abbreviation=abbreviation)
        d1 = Document.get(journal=pasa)
        self.assertEqual(d1.journal, pasa)
        