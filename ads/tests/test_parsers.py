# coding: utf-8

""" Test query parsers """

__author__ = "Andy Casey <andy@astrowizici.st>"

import unittest
import ads.parser as parse

def test_acknowledgement_parser():
    assert parse.acknowledgements("nasa")   == " ack:(nasa)"
    assert parse.acknowledgements()         == None


class TestDatabaseParser(unittest.TestCase):

    def test_database_parser(self):
        assert parse.database() == None
        assert parse.database("general") == "database:general"
        assert parse.database("astronomy") == "database:astronomy"
        assert parse.database("physics") == "database:physics"
        assert parse.database("astronomy OR physics") == "database:astronomy OR database:physics"

        self.assertRaises(TypeError, parse.properties, 3.14)
        self.assertRaises(ValueError, parse.properties, "some database that doesn't exist")


class TestPropertiesParser(unittest.TestCase):

    def test_properties_parser(self):
        assert parse.properties("BOoK") == " property:(BOoK)"
        assert parse.properties("article") == " property:(article)"
        assert parse.properties(("article", "REFEREED")) == " property:(article,REFEREED)"
        assert parse.properties() == None

        self.assertRaises(TypeError, parse.properties, 3)
        self.assertRaises(ValueError, parse.properties, "")
        self.assertRaises(ValueError, parse.properties, ("ARTICLE", "WHAT!@#"))


class TestAffiliationParser(unittest.TestCase):

    def test_affiliation_parser(self):
        assert parse.affiliation("mit")             == " aff:(mit)"
        assert parse.affiliation("mit", 1)          == " pos(aff:(mit), 1)"
        assert parse.affiliation("stromlo", [3, 5]) == " pos(aff:(stromlo), 3, 5)"
        assert parse.affiliation("stromlo", ['1', '4']) == " pos(aff:(stromlo), 1, 4)"

    def test_invalid_pos(self):
        self.assertRaises(TypeError, parse.affiliation, "mit", "hullo")
        self.assertRaises(TypeError, parse.affiliation, "mit", ["hullo", "there"])
        self.assertRaises(TypeError, parse.affiliation, "mit", [1, "hullo"])
        self.assertRaises(ValueError, parse.affiliation, "mit", [2, 1])
        self.assertRaises(TypeError, parse.affiliation, "mit", [1, 2, 0])
        self.assertRaises(TypeError, parse.affiliation, "mit", [None])
        self.assertRaises(TypeError, parse.affiliation, "mit", [None, None])
        
    
def test_date_parser():
    assert parse.dates(None)                == None
    assert parse.dates(2002)                == " pubdate:[2002-01 TO 2002-12]"
    assert parse.dates(2002.)               == " pubdate:[2002-01 TO 2002-12]"
    assert parse.dates("2002")              == " pubdate:[2002-01 TO 2002-12]"
    assert parse.dates("2002-07")           == " pubdate:[2002-07 TO 2002-07]"
    assert parse.dates("2002-07-15")        == " pubdate:[2002-07 TO 2002-07]"
    assert parse.dates("2002/07")           == " pubdate:[2002-07 TO 2002-07]"
    assert parse.dates("2002..2005")        == " pubdate:[2002-01 TO 2005-12]"
    assert parse.dates("2002..05")          == " pubdate:[2002-01 TO 2005-12]"
    assert parse.dates("2002-01..2006/07")  == " pubdate:[2002-01 TO 2006-07]"
    assert parse.dates((2002, 2005))        == " pubdate:[2002-01 TO 2005-12]"
    assert parse.dates((2002, 2005))        == " pubdate:[2002-01 TO 2005-12]"
    assert parse.dates((2002, ))            == " pubdate:[2002-01 TO *]"
    assert parse.dates((None, 2002))        == " pubdate:[* TO 2002-12]"
    assert parse.dates(2002.02)             == " pubdate:[2002-02 TO 2002-02]"
    assert parse.dates("2002/05..08")       == " pubdate:[2002-05 TO 2008-12]"
    assert parse.dates("2002-")             == " pubdate:[2002-01 TO *]"
    assert parse.dates("2002..")            == " pubdate:[2002-01 TO *]"
    assert parse.dates("..2002")            == " pubdate:[* TO 2002-12]"
    assert parse.dates("-2002")             == " pubdate:[* TO 2002-12]"


class TestRowParser(unittest.TestCase):

    max_rows = 200

    def test_standard(self):
        assert parse.rows(0, 400, max_rows=self.max_rows)       == (0, self.max_rows)
        assert parse.rows(0, "all", max_rows=self.max_rows)     == (0, self.max_rows)
        assert parse.rows('0', '400', max_rows=self.max_rows)   == (0, self.max_rows)
        assert parse.rows('0', '20', max_rows=self.max_rows)    == (0, 20)
        assert parse.rows('0', 40.0, max_rows=self.max_rows)    == (0, 40)
        assert parse.rows(0.1, 34.3, max_rows=self.max_rows)    == (0, 34)
    
    def test_invalid_values(self):
        self.assertRaises(ValueError, parse.rows, 0, 0)
        self.assertRaises(ValueError, parse.rows, -1, self.max_rows)

    def test_invalid_types(self):
        self.assertRaises(TypeError, parse.rows, "hi", 1)
        self.assertRaises(TypeError, parse.rows, 1, "hello")


class TestOrderingParser(unittest.TestCase):

    def test_standard_inputs(self):
        order_options = ("asc", "desc", )
        sort_options = {
            "cited": "cited",
            "citations": "cited",
            "date": "date",
            "time": "date",
            "popular": "popularity",
            "popularity": "popularity",
            "relevance": "relevance"
        }
        for sort_input, sort_option in sort_options.iteritems():
            for order_option in order_options:        
                assert (sort_option.lower(), order_option.lower()) == parse.ordering(sort_input, order_option)
                assert (sort_option.lower(), order_option.lower()) == parse.ordering(sort_input, order_option.upper())
                assert (sort_option.lower(), order_option.lower()) == parse.ordering(sort_input.upper(), order_option)


    def test_invalid_values(self):        
        self.assertRaises(ValueError, parse.ordering, 0, 0)
        self.assertRaises(ValueError, parse.ordering, "date", "hullo")
        self.assertRaises(ValueError, parse.ordering, [], {})
