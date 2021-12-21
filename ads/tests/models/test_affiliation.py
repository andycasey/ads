import unittest
from ads.tests import strict
from ads.models import (Affiliation, Document)

def expression_as_string(expression):
    return Document.select().where(expression).__str__()


class TestAffiliation(unittest.TestCase):

    def test_affiliation_ingest_count(self):
        count = Affiliation.select().count()
        self.assertGreaterEqual(count, 7_236)

    def test_affiliation_get(self):

        def _check_affiliation(a):
            self.assertIsNotNone(a)
            self.assertIsNotNone(a.id)
            self.assertIsNotNone(a.abbreviation)
            self.assertIsNotNone(a.canonical_name)

        # Check any random affiliation
        _check_affiliation(Affiliation.get())

        # Get by exact name.
        a = Affiliation.get(abbreviation="MIT")
        _check_affiliation(a)
        self.assertEqual(a.canonical_name, "Massachusetts Institute of Technology")

        # Get by canonical name.
        a = Affiliation.get(canonical_name="Massachusetts Institute of Technology")
        _check_affiliation(a)
        self.assertEqual(a.abbreviation, "MIT")

        # Get by expression
        a1 = Affiliation.get(abbreviation="CERN")
        a2 = Affiliation.get(Affiliation.canonical_name == "European Organization for Nuclear Research, Switzerland")
        self.assertEqual(a1, a2)

        # Get non-existant affiliation
        non_existant_affiliation = "FARM"
        with self.assertRaises(Affiliation.DoesNotExist):
            Affiliation.get(abbreviation=non_existant_affiliation)
        self.assertIsNone(Affiliation.get_or_none(abbreviation=non_existant_affiliation))

    
    def test_affiliation_select(self):
        self.assertGreaterEqual(
            Affiliation.select().where(Affiliation.canonical_name.contains("physics")).count(),
            843
        )
        a1 = next(iter(Affiliation.select().where(Affiliation.id == "A00409")))
        a2 = Affiliation.get(abbreviation="Monash U")
        self.assertEqual(a1, a2)


    def test_affiliation_order_by(self):
        A = Affiliation.select().order_by(Affiliation.id.asc())
        B = Affiliation.select().order_by(Affiliation.id.desc())
        for a, b in zip(A[::-1], B):
            self.assertEqual(a, b)

        A = Affiliation.select().order_by(Affiliation.canonical_name.asc())
        canonical_names = [j.canonical_name for j in A]
        self.assertEqual(canonical_names, sorted(canonical_names))

        
    def test_affiliation_limit(self):
        count = Affiliation.select().count()
        for limit in (1, 67, 132, 938):
            self.assertGreater(count, limit)
            self.assertEqual(limit, Affiliation.select().limit(limit).count())
            self.assertEqual(limit, len(Affiliation.select().limit(limit)))
    

    def test_affiliation_expression_resolution(self):

        self.assertEqual(
            expression_as_string(Document.affiliation == Affiliation.get(abbreviation="MIT")),
            "aff_id:A00331"
        )

        self.assertEqual(
            expression_as_string(Document.affiliation.abbreviation == "Monash U"),
            "aff_id:(A00409)" # TODO: 
        )

        self.assertEqual(
            expression_as_string(Document.affiliation.canonical_name == "Monash University, Australia"),
            "aff_id:(A00409)" # TODO: 
        )

        if strict:
            affs = Affiliation.select().where(Affiliation.canonical_name.contains("physics"))
            self.assertEqual(
                expression_as_string(Document.affiliation.canonical_name.contains("physics")),
                f"aff_id:({' OR '.join(aff.id for aff in affs)})"
            )

        abbreviation = "Monash U"
        monash = Affiliation.get(abbreviation=abbreviation)
        # Supply abbreviation directly to Affiliation.
        s1 = expression_as_string(Document.affiliation == monash)
        s2 = expression_as_string(Document.affiliation == abbreviation)
        self.assertEqual(s1, s2)
        self.assertEqual(s1, "aff_id:A00409")
        

    def test_document_select(self):
        abbreviation = "Flatiron Inst"
        flatiron = Affiliation.get(abbreviation=abbreviation)

        doc = Document.get(Document.pos(Document.affiliation == flatiron, 1, 1))
        self.assertIn(flatiron, doc.affiliation[0])
