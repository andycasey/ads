
import os
import unittest

class TestSetup(unittest.TestCase):
    def test_setup(self):
        from ads.utils import setup_database
        setup_database()

class TestSetupCLI(unittest.TestCase):
    def test_setup_cli(self):
        exit_status = os.system("ads-setup")
        self.assertEqual(0, exit_status)
