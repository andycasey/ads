
import unittest

from ads.models.document import Document


def expression_as_string(expression):
    return Document.select().where(expression).__str__()


class TestExpressions(unittest.TestCase):

    # TODO: This seems syntactically correct, but will not work on ADS!
    #(Document.year != 2005, "-=year:2005"),
    # TODO: Same with this:
    #(~(Document.year <= 2020), "-year:-2020")

    def test_year_eq(self):
        self.assertEqual(expression_as_string(Document.year == 2005), "year:2005")

    def test_year_gt(self):
        self.assertEqual(expression_as_string(Document.year > 2005), "year:2006-")
    
    def test_year_lt(self):
        self.assertEqual(expression_as_string(Document.year < 2020), "year:-2019")
    
    def test_year_gte(self):
        self.assertEqual(expression_as_string(Document.year >= 2020), "year:2020-")
    
    def test_year_lte(self):
        self.assertEqual(expression_as_string(Document.year <= 2020), "year:-2020")
    
    def test_year_between(self):
        self.assertEqual(expression_as_string(Document.year.between(2005, 2020)), "year:[2005 TO 2020]")

    def test_year_like(self):
        self.assertEqual(expression_as_string(Document.year.like("201?")), "year:201?")

    '''

    # TODO: Auto-generate tests for all the IntegerFields?

    #def test_title_like(self):
    #    self.assertEqual((Document.title.like("globular *")), "title:\"globular *\"")

    # Test virtual operators.


    def test_pos_without_end_position(self):
        self.assertEqual(expression_as_string(Document.pos(Document.author == "Ness, M", 2)), 'pos(=author:"Ness, M", 2)')

    def test_pos_with_end_position(self):
        self.assertEqual(expression_as_string(Document.pos(Document.author == "Ness, M", 2, 3)), 'pos(=author:"Ness, M", 2, 3)')
    
    def test_pos_missing_argument(self):
        self.assertRaises(TypeError, lambda *_: Document.pos(Document.author == "Ness, M"))

    def test_pos_too_many_arguments(self):
        self.assertRaises(TypeError, lambda *_: Document.pos(Document.author == "Ness, M", 2, 3, 4))
    
    # TODO: type hinting and tests for invalid types.
    def test_and_or(self):
        # We don't expect = exact operator for the year field.
        self.assertEqual(
            expression_as_string((Document.year == 2005) | (Document.year == 2020)), 
            "year:2005 OR year:2020"
        )

        self.assertEqual(
            expression_as_string((Document.title.like("JWST *") | Document.ack.like("JWST")) & Document.year.between(2005, 2020)),
            '((title:"JWST *") OR (ack:"JWST")) AND (year:[2005 TO 2020])'
        )


    #def test_self_eq(self):
    #    doc = Document(bibcode="BIB..1234")
    #    self.assertEqual((Document == doc), "bibcode:BIB..1234")
    
    def test_negation(self):
        q = ~(Document.title == "SDSS") & Document.title.like("Sloan Digital Sky Survey")
        self.assertEqual(
            expression_as_string(q),
            '(-=title:"SDSS") AND (title:"Sloan Digital Sky Survey")'
        )


    def test_citations(self):
        self.assertEqual(
            expression_as_string(Document.citations("2015ApJ...808...16")),
            "citations(2015ApJ...808...16)"
        )
    
    def test_references(self):
        self.assertEqual(
            expression_as_string(Document.references("2015ApJ...808...16")),
            "references(2015ApJ...808...16)"
        )
    
    def test_top_n(self):
        self.assertEqual(
            expression_as_string(Document.top_n(10, Document.author.like("Casey, A"))),
            "topn(10, (author:\"Casey, A\"))"
        )
        self.assertEqual(
            expression_as_string(Document.top_n(3, Document.title.like("JWST *"), "citation_count desc")),
            'topn(3, (title:"JWST *"), citation_count desc)'
        )

    '''
