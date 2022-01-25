import os
import unittest
import ads.services.export
from ads import Document

def export_data_path(basename):
    return os.path.join(os.path.dirname(__file__), "export_data", basename)



class TestExport(unittest.TestCase):

    def setUp(self):        
        self.bibcodes = "2020A&A...642C...1G 2020A&A...637C...3G 2019MNRAS.488.2892P".split()

    def test_export_failures(self):
        with self.assertRaises(ValueError):
            ads.services.export.ads("MOO")
        with self.assertRaises(TypeError):
            ads.services.export.ads(1)
        with self.assertRaises(ValueError):
            ads.services.export.ads([])
    
    def test_export_sort(self):
        no_sort = ads.services.export.ads(self.bibcodes, sort=None)
        title_str = ads.services.export.ads(self.bibcodes, sort="title desc")
        title_order = ads.services.export.ads(self.bibcodes, sort=Document.title.desc())
        
        with open(export_data_path("ads.log"), "r") as fp:
            self.assertEqual(no_sort, fp.read())

        self.assertEqual(title_str, title_order)
        self.assertNotEqual(title_str, no_sort)

        with open(export_data_path("ads-sort-title.log"), "r") as fp:
            self.assertEqual(title_str, fp.read())
        

    def test_export_ads(self):
        data = ads.services.export.ads(self.bibcodes)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("ads.log"), "r") as fp:
            self.assertEqual(data, fp.read())

    def test_export_bibtexabs(self):
        data = ads.services.export.bibtexabs(self.bibcodes)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("bibtexabs.log"), "r") as fp:
            self.assertEqual(data, fp.read())

        data2 = ads.services.export.bibtexabs(self.bibcodes[0], max_author=2, author_cutoff=200, key_format="%1H:%Y%zm", journal_format=3)
        self.assertIsNotNone(data2)
        self.assertIsInstance(data2, str)
        with open(export_data_path("bibtexabs2.log"), "r") as fp:
            self.assertEqual(data2, fp.read())

    def test_export_bibtex(self):
        data = ads.services.export.bibtex(self.bibcodes)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("bibtex.log"), "r") as fp:
            self.assertEqual(data, fp.read())

    def test_export_endnote(self):
        data = ads.services.export.endnote(self.bibcodes)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("endnote.log"), "r") as fp:
            self.assertEqual(data, fp.read())

    def test_export_medlars(self):
        data = ads.services.export.medlars(self.bibcodes)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("medlars.log"), "r") as fp:
            self.assertEqual(data, fp.read())

    def test_export_procite(self):
        data = ads.services.export.procite(self.bibcodes)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("procite.log"), "r") as fp:
            self.assertEqual(data, fp.read())

    def test_export_refworks(self):
        data = ads.services.export.refworks(self.bibcodes)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("refworks.log"), "r") as fp:
            self.assertEqual(data, fp.read())

    def test_export_ris(self):
        data = ads.services.export.ris(self.bibcodes)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("ris.log"), "r") as fp:
            self.assertEqual(data, fp.read())

    def test_export_aastex(self):
        data = ads.services.export.aastex(self.bibcodes)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("aastex.log"), "r") as fp:
            self.assertEqual(data, fp.read())

    def test_export_icarus(self):
        data = ads.services.export.icarus(self.bibcodes)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("icarus.log"), "r") as fp:
            self.assertEqual(data, fp.read())

    def test_export_mnras(self):
        data = ads.services.export.mnras(self.bibcodes)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("mnras.log"), "r") as fp:
            self.assertEqual(data, fp.read())

    def test_export_soph(self):
        data = ads.services.export.soph(self.bibcodes)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("soph.log"), "r") as fp:
            self.assertEqual(data, fp.read())

    def test_export_dcxml(self):
        data = ads.services.export.dcxml(self.bibcodes)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("dcxml.log"), "r") as fp:
            self.assertEqual(data, fp.read())

    def test_export_refxml(self):
        data = ads.services.export.refxml(self.bibcodes)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("refxml.log"), "r") as fp:
            self.assertEqual(data, fp.read())

    def test_export_refabsxml(self):
        data = ads.services.export.refabsxml(self.bibcodes)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("refabsxml.log"), "r") as fp:
            self.assertEqual(data, fp.read())

    def test_export_votable(self):
        data = ads.services.export.votable(self.bibcodes)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("votable.log"), "r") as fp:
            self.assertEqual(data, fp.read())

    def test_export_csl(self):
        data = ads.services.export.csl(self.bibcodes, style="aastex", format=2, journal_format=3)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("csl.log"), "r") as fp:
            self.assertEqual(data, fp.read())

    def test_export_custom(self):
        data = ads.services.export.custom(self.bibcodes, format="%ZEncoding:latex\\bibitem[]  %l %T (%Y) %q, %V, %p-%P.")
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("custom.log"), "r") as fp:
            self.assertEqual(data, fp.read())
        
        # Format keyword is required for custom.
        with self.assertRaises(TypeError):
            ads.services.export.custom(self.bibcodes)
        
    def test_export_ieee(self):
        data = ads.services.export.ieee(self.bibcodes)
        self.assertIsNotNone(data)
        self.assertIsInstance(data, str)
        with open(export_data_path("ieee.log"), "r") as fp:
            self.assertEqual(data, fp.read())



'''
if __name__ == "__main__":
    A = TestExport()
    A.setUp()
    data, data2 = A.test_export_bibtexabs()#max_author=1, journal_format=3, key_format="%1H:%Y%zm")

'''
