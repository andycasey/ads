
import os
import unittest
import requests
import warnings
from tempfile import NamedTemporaryFile

from ads.utils import parse_bibcode

class TestSetup(unittest.TestCase):
    def test_setup(self):
        exit_status = os.system("ads-setup")
        self.assertEqual(0, exit_status)

class TestUtilities(unittest.TestCase):
        
    def test_parse_arxiv_bibcode(self):
        parts = parse_bibcode("2022arXiv220105796S")
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
        parts = parse_bibcode("2018A&A...616A...1G")
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
        parts = parse_bibcode("2018JOURN151512345G")
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
            parse_bibcode("A018JOURN151512345G")