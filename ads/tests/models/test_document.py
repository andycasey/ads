import unittest
from ads.tests import strict
from ads.models import Document
from ads.services.search import SolrQuery
from datetime import date, datetime

def expression_as_string(expression):
    return str(SolrQuery(expression))

class TestDocument(unittest.TestCase):

    #def setUp(self):
        #self.doc = Document.get(bibcode="2018A&A...616A...1G")


    #def test_representation(self):
    #    doc = self.doc
    #    self.assertEqual(str(doc), "<Document: bibcode=2018A&A...616A...1G>")
    #    self.assertEqual(doc.__repr__(), str(doc))


    #def test_date_formats(self):
    #    doc = self.doc
    #    self.assertIsInstance(doc.pubdate, date)
    #    self.assertIsInstance(doc.date, datetime)
    #    self.assertIsInstance(doc.entry_date, datetime)
    #    self.assertIsInstance(doc.indexstamp, datetime)


    def test_expression_id(self):
        _id = 15229396
        self.assertEqual("(id:A)", expression_as_string(Document.id == "A"))
        self.assertEqual("(id:(A OR B))", expression_as_string(Document.id.in_(["A", "B"])))
        self.assertEqual("(id:[A TO C])", expression_as_string(Document.id.between("A", "C")))
        self.assertEqual(f"(id:[{_id} TO ])", expression_as_string(Document.id >= _id))
        self.assertEqual(f"(id:[{_id + 1} TO ])", expression_as_string(Document.id > _id))
        self.assertEqual(f"(id:[0 TO {_id}])", expression_as_string(Document.id <= _id))
        self.assertEqual(f"(id:[0 TO {_id - 1}])", expression_as_string(Document.id < _id))
        self.assertEqual("(id:1522939*)", expression_as_string(Document.id.like("1522939")))

    # entry stamp and index stamp can be searched like indexstamp:["2022-01-20t00:00:00Z" TO "2023-01-01t00:00:00Z"] 
    def test_expression_abstract(self):
        self.assertEqual('(=abstract:"star")', expression_as_string(Document.abstract.exact("star")))
        self.assertEqual('(abstract:"star")', expression_as_string(Document.abstract == "star"))
        self.assertEqual(
            '((abstract:"star") OR (abstract:"death"))',
            expression_as_string((Document.abstract == "star") | (Document.abstract == "death"))
        )

    def test_aff(self):
        self.assertEqual('(aff:"flatiron")', expression_as_string(Document.aff == "flatiron"))
    
    def test_aff_id(self):
        self.assertEqual('(aff_id:A100)', expression_as_string(Document.aff_id == "A100"))
        self.assertEqual('(=aff_id:A100)', expression_as_string(Document.aff_id.exact("A100")))
        self.assertEqual('(aff_id:[A11118 TO A11130])', expression_as_string(Document.aff_id.between("A11118", "A11130")))
        self.assertEqual('(aff_id:(A11118 OR A11130))', expression_as_string(Document.aff_id.in_(["A11118", "A11130"])))

    def test_aff_id_slice(self):
        self.assertEqual('(pos((=aff_id:A100), 1, 1))', expression_as_string(Document.aff_id[0].exact("A100")))
        self.assertEqual('(pos((aff_id:A100), 2, 2))', expression_as_string(Document.aff_id[1] == "A100"))
        self.assertEqual('(pos((aff_id:A100), 4, 6))', expression_as_string(Document.aff_id[3:5] == "A100"))
        #self.assertEqual('(pos((aff_id:"A100"), 3))', expression_as_string(Document.aff_id[2:] == "A100"))
    
    def test_author_count(self):
        self.assertEqual("(author_count:1)", expression_as_string(Document.author_count == 1))
        self.assertEqual("(author_count:[2 TO 10])", expression_as_string(Document.author_count.between(2, 10)))
        self.assertEqual("(author_count:[6 TO *])", expression_as_string(Document.author_count > 5))
        self.assertEqual("(author_count:[0 TO 4])", expression_as_string(Document.author_count < 5))
        self.assertEqual("(author_count:[0 TO 5])", expression_as_string(Document.author_count <= 5))
        self.assertEqual("(author_count:[5 TO *])", expression_as_string(Document.author_count >= 5))
        
    def test_date(self):
        A, B = datetime(2013, 2, 1), datetime(2013, 3, 1)
        self.assertEqual(
            '(date:["2013-02-01T00:00:00Z" TO "2013-03-01T00:00:00Z"])',
            expression_as_string(Document.date.between(A, B))
        )

    def test_year_eq(self):
        self.assertEqual(expression_as_string(Document.year == 2005), "(year:2005)")

    def test_year_gt(self):
        self.assertEqual(expression_as_string(Document.year > 2005), "(year:[2006 TO ])")
    
    def test_year_lt(self):
        self.assertEqual(expression_as_string(Document.year < 2020), "(year:[0 TO 2019])")
    
    def test_year_gte(self):
        self.assertEqual(expression_as_string(Document.year >= 2020), "(year:[2020 TO ])")
    
    def test_year_lte(self):
        self.assertEqual(expression_as_string(Document.year <= 2020), "(year:[0 TO 2020])")
    
    def test_year_between(self):
        self.assertEqual(expression_as_string(Document.year.between(2005, 2020)), "(year:[2005 TO 2020])")

    def test_year_like(self):
        self.assertEqual(expression_as_string(Document.year == "201?"), "(year:201?)")

    def test_pos_without_end_position(self):
        self.assertEqual(expression_as_string(Document.pos(Document.author == "Ness, M", 2)), '(pos((author:"Ness, M"), 2, 2))')

    def test_pos_with_end_position(self):
        self.assertEqual(expression_as_string(Document.pos(Document.author == "Ness, M", 2, 3)), '(pos((author:"Ness, M"), 2, 3))')
    
    def test_pos_missing_argument(self):
        with self.assertRaises(TypeError):
            Document.pos(Document.author == "Ness, M")

    def test_pos_too_many_arguments(self):
        with self.assertRaises(TypeError):
            Document.pos(Document.author == "Ness, M", 2, 3, 4)

    

    def test_and_or(self):
        self.assertEqual(
            expression_as_string((Document.year == 2005) | (Document.year == 2020)), 
            "((year:2005) OR (year:2020))"
        )

        self.assertEqual(
            expression_as_string(((Document.title == "JWST") | (Document.ack == "JWST")) & Document.year.between(2005, 2020)),
            '(((title:"JWST") OR (ack:"JWST")) AND (year:[2005 TO 2020]))'
        )

    
    def test_negation(self):
        q = ~(Document.title.exact("SDSS")) & (Document.title == "Sloan Digital Sky Survey")
        self.assertEqual(
            expression_as_string(q),
            '(-(=title:"SDSS") AND (title:"Sloan Digital Sky Survey"))'
        )


    def test_citations(self):
        self.assertEqual(
            expression_as_string(Document.citations("2015ApJ...808...16")),
            "(citations(2015ApJ...808...16))"
        )
    
    def test_references(self):
        self.assertEqual(
            expression_as_string(Document.references("2015ApJ...808...16")),
            "(references(2015ApJ...808...16))"
        )
    
    def test_top_n(self):
        self.assertEqual(
            expression_as_string(Document.top_n(10, Document.author == "Casey, A")),
            "(topn(10, (author:\"Casey, A\")))"
        )
        self.assertEqual(
            expression_as_string(Document.top_n(3, Document.title.like("JWST"), "citation_count desc")),
            '(topn(3, (title:"JWST*"), citation_count desc))'
        )
