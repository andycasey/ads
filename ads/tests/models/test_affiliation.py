import unittest
from ads.tests import strict
from ads.models import (Affiliation, Document)
from ads.models.affiliation import _safe_get_affiliation
from ads.services.search import SolrQuery



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
            str(SolrQuery(Document.affiliation == Affiliation.get(abbreviation="MIT"))),
            "(aff_id:A00331)"
        )

        self.assertEqual(
            str(SolrQuery(Document.affiliation.abbreviation == "Monash U")),
            "(aff_id:(A00409))"
        )

        self.assertEqual(
            str(SolrQuery(Document.affiliation.canonical_name == "Monash University, Australia")),
            "(aff_id:(A00409))" 
        )

        if strict:
            affs = Affiliation.select().where(Affiliation.canonical_name.contains("physics"))
            self.assertEqual(
                str(SolrQuery(Document.affiliation.canonical_name.contains("physics"))),
                f"(aff_id:({' OR '.join(aff.id for aff in affs)}))"
            )

        abbreviation = "Monash U"
        monash = Affiliation.get(abbreviation=abbreviation)
        # Supply abbreviation directly to Affiliation.
        s1 = str(SolrQuery(Document.affiliation == monash))
        s2 = str(SolrQuery(Document.affiliation == abbreviation))
        self.assertEqual(s1, s2)
        self.assertEqual(s1, "(aff_id:A00409)")
        

    def test_no_affiliation(self):
        for each in ("-", " - ", " -", "- "):
            self.assertIsNone(_safe_get_affiliation(each))

    def test_document_select(self):
        abbreviation = "Flatiron Inst"
        flatiron = Affiliation.get(abbreviation=abbreviation)

        doc = Document.get(Document.pos(Document.affiliation == flatiron, 1, 1))
        self.assertIn(flatiron, doc.affiliation[0])


    def test_repr_affiliation(self):
        flatiron = Affiliation.get(abbreviation="Flatiron Inst")
        self.assertEqual(
            flatiron.__repr__(),
            '<Affiliation A05812: Flatiron Institute, New York>'
        )

    def test_parent_children(self, affiliation=None):
        if affiliation is not None:
            self.assertIsNotNone(affiliation.parent)
            self.assertIsNotNone(affiliation.parents)
            for parent in affiliation.parents:
                children = list(parent.children)
                self.assertGreater(len(children), 0)
                self.assertIn(affiliation, children)
    
    def test_siblings(self, affiliation=None):
        if affiliation is not None:
            for sibling in affiliation.siblings:
                self.assertEqual(sibling.parent, affiliation.parent)
            parents = list(affiliation.parents)
            for sibling in affiliation.extended_siblings:
                self.assertIn(sibling.parent, parents)

    def test_family_caastro(self):
        caastro = Affiliation.get(abbreviation="CAASTRO")
        self.test_parent_children(caastro)
        self.test_siblings(caastro)
        
    def test_100_random_families(self):
        from peewee import fn
        # Test a random set of families
        q = Affiliation.select()\
                       .where(Affiliation.parent != None)\
                       .order_by(fn.Random())\
                       .limit(100)
        for affiliation in q:
            self.test_parent_children(affiliation)
            self.test_siblings(affiliation)

