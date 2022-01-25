
import unittest
import random
import string
from ads import Document, Library
from ads.client import APIResponseError

def random_library_name(length=40):
    return "test_" + ''.join(random.choice(string.ascii_lowercase) for i in range(length))


class TestCleanUp(unittest.TestCase):

    def test_delete_all_test_libraries(self):
        # Failed tests have a tendency to build up libraries named "test_*".
        for library in Library.select():
            if library.name.startswith("test_"):
                library.delete()
        

class TestLibraryDocuments(unittest.TestCase):

    def test_document_add_del(self):

        lib = Library(name=random_library_name())    
        docs = Document.select().where(Document.year == 2005).order_by(Document.citation_count.desc()).limit(10)
        docs = list(docs)

        lib.documents.extend(docs)
        lib.save()

        lib2 = Library.get(id=lib.id)
        self.assertEqual(len(lib2.documents), len(lib.documents))

        chosen_doc = docs[5]
        lib.documents.remove(chosen_doc)
        lib.save()
        self.assertEqual(lib.num_documents, 9)

        lib3 = Library.get(id=lib.id)
        self.assertEqual(len(lib3.documents), len(lib.documents))
        self.assertEqual(lib3.num_documents, lib.num_documents)
        A = " ".join(sorted([doc.bibcode for doc in lib.documents]))
        B = " ".join(sorted([doc.bibcode for doc in lib3.documents]))
        self.assertEqual(A, B)

        lib.delete()
    

class TestLibrarySetOperations(unittest.TestCase):

    def setUp(self):
        docs_2005 = Document.select().where(Document.year == 2005).order_by(Document.citation_count.desc()).limit(10)
        docs_2006 = Document.select().where(Document.year == 2006).order_by(Document.citation_count.desc()).limit(10)
        docs_both = Document.select()\
                            .where(
                                (Document.year == 2005) | (Document.year == 2006)
                            )\
                            .order_by(Document.citation_count.desc())\
                            .limit(10)
                        
                            
        self.lib_2005 = Library(
            name=random_library_name(),
            documents=docs_2005
        )
        self.lib_2006 = Library(
            name=random_library_name(),
            documents=docs_2006
        )
        
        with self.assertRaises(ValueError):
            # Cannot perform set operations on libraries that don't exist on ADS yet.
            self.lib_2005.intersection(self.lib_2006)
        with self.assertRaises(ValueError):
            # Cannot perform set operations on libraries that don't exist on ADS yet.
            self.lib_2006.intersection(self.lib_2005)
        
        self.lib_2005.save()
        
        with self.assertRaises(ValueError):
            # Cannot perform set operations on libraries that don't exist on ADS yet.
            self.lib_2005.intersection(self.lib_2006)
        with self.assertRaises(ValueError):
            # Cannot perform set operations on libraries that don't exist on ADS yet.
            self.lib_2006.intersection(self.lib_2005)

        self.lib_2006.save()

        self.lib_both = Library.create(
            name=random_library_name(),
            documents=docs_both
        )

    def test_repr(self):
        self.assertIsInstance(str(self.lib_both), str)
        self.assertIsInstance(str(self.lib_both.__repr__()), str)
    
    def test_intersection(self):    
        d = set(self.lib_both).intersection(self.lib_2005)
        self.assertGreater(len(d), 0)
        lib_intersection_both_2005 = self.lib_both.intersection(self.lib_2005)
        self.assertIsNotNone(lib_intersection_both_2005.id)
        self.assertEqual(len(d), lib_intersection_both_2005.num_documents)
        self.assertEqual(
            " ".join(sorted([doc.bibcode for doc in d])),
            " ".join(sorted([doc.bibcode for doc in lib_intersection_both_2005.documents]))
        )
        lib_intersection_both_2005.delete()

    def test_union(self):
        d = set(self.lib_both).union(self.lib_2006)
        self.assertGreater(len(d), 0)
        lib_union_both_2005 = self.lib_both.union(self.lib_2006)
        self.assertIsNotNone(lib_union_both_2005.id)
        self.assertEqual(len(d), lib_union_both_2005.num_documents)
        self.assertEqual(
            " ".join(sorted([doc.bibcode for doc in d])),
            " ".join(sorted([doc.bibcode for doc in lib_union_both_2005.documents]))
        )
        lib_union_both_2005.delete()

    def test_difference_AB(self):
        d = set(self.lib_both).difference(self.lib_2005)
        self.assertGreater(len(d), 0)
        lib_difference_both_2005 = self.lib_both.difference(self.lib_2005)
        self.assertIsNotNone(lib_difference_both_2005.id)
        self.assertEqual(len(d), lib_difference_both_2005.num_documents)
        self.assertEqual(
            " ".join(sorted([doc.bibcode for doc in d])),
            " ".join(sorted([doc.bibcode for doc in lib_difference_both_2005.documents]))
        )
        lib_difference_both_2005.delete()

    def test_difference_BA(self):
        d = set(self.lib_2005).difference(self.lib_both)
        self.assertGreater(len(d), 0)
        lib_difference_2005_both = self.lib_2005.difference(self.lib_both)
        self.assertIsNotNone(lib_difference_2005_both.id)
        self.assertEqual(len(d), lib_difference_2005_both.num_documents)
        self.assertEqual(
            " ".join(sorted([doc.bibcode for doc in d])),
            " ".join(sorted([doc.bibcode for doc in lib_difference_2005_both.documents]))
        )
        lib_difference_2005_both.delete()

    def test_copy_and_empty(self):
        A = Library.create()
        self.lib_both.copy(A)

        A_ = Library.get(id=A.id)
        self.assertEqual(A_.num_documents, self.lib_both.num_documents)
        self.assertGreater(A_.num_documents, 0)

        A_.empty()

        A__ = Library.get(id=A.id)
        self.assertEqual(A__.num_documents, 0)
        
        B = Library.get(id=self.lib_both.id)
        self.assertEqual(self.lib_both.num_documents, B.num_documents)

        A.delete()





class TestLibraryService(unittest.TestCase):

        

    def test_create_library_with_documents(self):
        N = 3
        name = random_library_name()
        docs = Document.select().limit(N)
        lib = Library(
            name=name,
            documents=docs
        )
        lib.save()

        self.assertIsNotNone(lib.id)
        self.assertEqual(N, len(lib.documents))
        self.assertEqual(N, lib.num_documents)
        self.assertEqual(name, lib.name)
        # TODO: Put in some checks for library description, created time, etc.
        #       Currently these will be None, but we should retrieve them.
        lib.delete()



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


