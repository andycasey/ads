
import os
import unittest
import requests
import warnings
from tempfile import NamedTemporaryFile

import ads.utils

class TestUtilities(unittest.TestCase):
        
    def test_flatten(self):
        structs = [
            ((1, 2, 3), [1, 2, 3]),
            ([1, [2, 3]], [1, 2, 3]),
            (["A", "B", ["C", ["D"], ["E"]]], ["A", "B", "C", "D", "E"]),
            (1, [1]),   
        ]
        for struct, expected in structs:
            self.assertEqual(ads.utils.flatten(struct), expected)


    def test_parse_arxiv_bibcode(self):
        parts = ads.utils.parse_bibcode("2022arXiv220105796S")
        expected = {
            'year': '2022',
            'journal_abbreviation': 'arXiv',
            'volume': '2201',
            'qualifier': '',
            'page_number': '05796',
            'first_letter_of_last_name': 'S'
        }
        for key, value in expected.items():
            self.assertEqual(parts[key], value)

    def test_parse_bibcode(self):
        parts = ads.utils.parse_bibcode("2018A&A...616A...1G")
        expected = {
            'year': '2018',
            'journal_abbreviation': 'A&A',
            'volume': '616',
            'qualifier': 'A',
            'page_number': '1',
            'first_letter_of_last_name': 'G'
        }
        for key, value in expected.items():
            self.assertEqual(parts[key], value)

    def test_parse_bibcode_with_long_page_number(self):
        parts = ads.utils.parse_bibcode("2018JOURN151512345G")
        expected = {
            'year': '2018',
            'journal_abbreviation': 'JOURN',
            'volume': '1515',
            'qualifier': '',
            'page_number': '12345',
            'first_letter_of_last_name': 'G'
        }        
        for key, value in expected.items():
            self.assertEqual(parts[key], value)

    
    def test_parse_bibcode_fail(self):
        with self.assertRaises(ValueError):
            ads.utils.parse_bibcode("A018JOURN151512345G")