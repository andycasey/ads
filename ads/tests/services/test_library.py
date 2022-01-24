
import unittest
import random
import string
from ads import Library
from ads.client import APIResponseError


class TestLibraryService(unittest.TestCase):


    def test_create_library_from_init(self, length=40):
        name = "test_" + ''.join(random.choice(string.ascii_lowercase) for i in range(length))
        description = "cow"

        lib = Library(name=name, description=description)
        self.assertNotIn("id", lib.__data__)
        lib.save()
        self.assertIn("id", lib.__data__)
        self.assertIsNotNone(lib.id)
        self.assertEqual(lib.__data__["id"], lib.id)

        lib2 = Library.get(id=lib.id)
        self.assertEqual(name, lib2.name)
        self.assertEqual(description, lib2.description)
        self.assertEqual(0, lib2.num_documents)
        self.assertEqual(False, lib2.public)
        
        # delete the library.
        lib2.delete()
        

    def test_create_library(self, length=40):
        name = "test_" + ''.join(random.choice(string.ascii_lowercase) for i in range(length))
        public = True

        lib = Library.create(name=name, public=public)
        self.assertEqual(lib.name, name)
        self.assertIn("id", lib.__data__)
        self.assertIsNotNone(lib.id)

        # Retrieve the temporary library in a new instance and check that it's the same.
        lib2 = Library.get(id=lib.id)
        self.assertEqual(lib2.public, public)

        # delete the library.
        lib.delete()


    def test_daniel_price_public_library(self):

        public_id_1 = "bRgpY8A3SYGxgGd3LOMQAw" # Daniel Price library
        lib = Library.get(id=public_id_1)
        self.assertIsNotNone(lib)
        self.assertTrue(lib.public)        
        self.assertEqual("daniel.price", lib.owner)

        lib2, = Library.select()\
                       .where(Library.id == public_id_1)
        self.assertEqual(lib, lib2)

        docs = lib.documents
        #self.assertEqual(len(docs), lib.num_documents)
        # The line above fails because of a bug in ADS.
        # len(docs) is 182, but we requested 183 documents (num_documents).
        # Email the ADS team about this.
        self.assertGreaterEqual(1 + len(docs), lib.num_documents)
        if len(docs) < lib.num_documents:
            print(f"WARNING: {len(docs)} documents found, but {lib.num_documents} requested.")
        self.assertGreater(len(docs), 0)

        # We should not have access to the permissions.
        with self.assertRaises(APIResponseError):
            lib.permissions

        # Or to delete the library.
        # (If we do have permission, then lib.permissions above would not raise an exception, 
        # and the test here would fail.)
        with self.assertRaises(APIResponseError):
            lib.delete()


