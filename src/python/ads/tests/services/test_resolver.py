
import os
import json
import unittest
from ads import Document
from ads.services import resolver

def data_path(basename):
    return os.path.join(os.path.dirname(__file__), "data", basename)


class TestResolver(unittest.TestCase):

    # TODO: Should we make better tests for this? Need an example document that has all these things.
    def setUp(self):
        self.document = Document.get(bibcode="2020A&A...642C...1G")

    def test_external_resources(self):
        resources = resolver.external_resources(self.document)
        self.assertIsNotNone(resources)
        with open(data_path("external_resources.json"), "r") as fp:
            self.assertEqual(resources, json.load(fp))

    def test_close_match(self):
        with self.assertRaises(ValueError):
            resolver.external_resource(self.document, "ads")

    def test_resource_arxiv(self):
        r = resolver.external_resource(self.document, "arxiv")
        self.assertIsInstance(r, dict)
        self.assertEqual(
            json.dumps(r),
            json.dumps({'service': 'http://arxiv.org/abs/642.1', 'action': 'redirect', 'link': 'http://arxiv.org/abs/642.1', 'link_type': 'ARXIV'})
        )
        return r
        
    def test_resource_doi(self):
        r = resolver.external_resource(self.document, "doi")
        self.assertIsInstance(r, dict)
        self.assertEqual(
            json.dumps({'service': 'http://dx.doi.org/10.1051/0004-6361/202039217', 'action': 'redirect', 'link': 'http://dx.doi.org/10.1051/0004-6361/202039217', 'link_type': 'DOI'}),
            json.dumps(r)
        )
        return r

    def test_resource_abstract(self):
        r = resolver.external_resource(self.document, "abstract")
        self.assertIsInstance(r, dict)
        self.assertEqual(
            json.dumps(r),
            json.dumps({'service': '/abs/2020A&A...642C...1G/abstract', 'action': 'redirect', 'link': '/abs/2020A&A...642C...1G/abstract', 'link_type': 'ABSTRACT'})
        )
        return r

    def test_resource_citations(self):
        r = resolver.external_resource(self.document, "citations")
        self.assertIsInstance(r, dict)
        self.assertEqual(
            json.dumps(r),
            json.dumps({'service': '/abs/2020A&A...642C...1G/citations', 'action': 'redirect', 'link': '/abs/2020A&A...642C...1G/citations', 'link_type': 'CITATIONS'})
        )
        return r

    def test_resource_references(self):
        r = resolver.external_resource(self.document, "references")
        self.assertIsInstance(r, dict)
        self.assertEqual(
            json.dumps(r),
            json.dumps({'service': '/abs/2020A&A...642C...1G/references', 'action': 'redirect', 'link': '/abs/2020A&A...642C...1G/references', 'link_type': 'REFERENCES'})
        )
        return r

    def test_resource_coreads(self):
        r = resolver.external_resource(self.document, "coreads")
        self.assertIsInstance(r, dict)
        self.assertEqual(
            json.dumps(r),
            json.dumps({'service': '/abs/2020A&A...642C...1G/coreads', 'action': 'redirect', 'link': '/abs/2020A&A...642C...1G/coreads', 'link_type': 'COREADS'})
        )
        return r

    def test_resource_openurl(self):
        r = resolver.external_resource(self.document, "openurl")
        self.assertIsInstance(r, dict)
        return r

    def test_resource_metrics(self):
        r = resolver.external_resource(self.document, "metrics")
        self.assertIsInstance(r, dict)
        return r

    def test_resource_graphics(self):
        r = resolver.external_resource(self.document, "graphics")
        self.assertIsInstance(r, dict)
        return r

    def test_resource_esource(self):
        r = resolver.external_resource(self.document, "esource")
        self.assertIsInstance(r, dict)
        return r

    def test_resource_pub_pdf(self):
        r = resolver.external_resource(self.document, "pub_pdf")
        self.assertIsInstance(r, dict)
        return r

    def test_resource_pub_html(self):
        r = resolver.external_resource(self.document, "pub_html")
        self.assertIsInstance(r, dict)
        return r

    def test_resource_ejournal(self):
        r = resolver.external_resource(self.document, "ejournal")
        self.assertIsInstance(r, dict)
        return r
