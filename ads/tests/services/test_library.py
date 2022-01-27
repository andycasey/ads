
import unittest
import random
import string
import os
import ads.config
from ads import Document, Library
from ads.client import APIResponseError

def random_library_name(length=40):
    return "test_" + ''.join(random.choice(string.ascii_lowercase) for i in range(length))


class TestMetaDataChanges(unittest.TestCase):

    def setUp(self):
        self.library = Library.create(name=random_library_name(), public=False)
        # TODO: Test that the metadata fields are lazily loaded?


    def test_public_change(self):
        original = False

        self.library.public = True
        self.library.save()
        self.assertEqual(self.library.public, True)

        # Get a fresh copy to check.
        lib = Library.get(id=self.library.id)
        self.assertEqual(lib.public, True)

    def test_description_change(self):
        old = self.library.description
        new = "some description"

        self.library.description = new
        self.assertEqual(self.library.description, new)
        self.library.save()
        self.assertEqual(self.library.description, new)
        
        lib = Library.get(id=self.library.id)
        self.assertEqual(lib.description, new)

    def test_name_change(self):
        old = self.library.name
        new = random_library_name()
        
        self.library.name = new
        self.assertEqual(self.library.name, new)
        self.library.save()
        self.assertEqual(self.library.name, new)
        
        lib = Library.get(id=self.library.id)
        self.assertEqual(lib.name, new)

        # Check that it fails if we try to create a library of the same name.
        with self.assertRaises(APIResponseError):
            Library.create(name=new)
        
    def test_num_users_change(self):
        self.library.num_users = 3
        with self.assertRaises(ValueError):
            self.library.save()

        # Reset.
        self.library.num_users = 1
        self.library._dirty.remove("num_users")
    
    def test_num_documents_change(self):
        self.library.num_documents = 3
        with self.assertRaises(ValueError):
            self.library.save()

        # Reset.
        self.library.num_documents = 0
        self.library._dirty.remove("num_documents")

    def test_date_created_change(self):
        self.library.date_created = ""    
        with self.assertRaises(ValueError):
            self.library.save()

        # reset.
        self.library._dirty.remove("date_created")

    def test_date_last_modified_change(self):
        self.library.date_last_modified = ""
        with self.assertRaises(ValueError):
            self.library.save()

        self.library._dirty.remove("date_last_modified")

    #def test_id_change(self):
    #    old, new = (f"{self.library.id}", "new")
    #    self.library.id = new
    #    with self.assertRaises(ValueError):
    #        self.library.save()
    #    self.library._dirty.remove("id")
    #    self.library.id = old


# Cannot test library ownership transfer because I seem to get 500 errors now
# I don't think the code has changed,.. it used to work.
# Email the ADS team about this.
class TestLibraryOwnershipTransfer(unittest.TestCase):

    def setUp(self):
        self.alice_owner = os.environ.get("ALICE_ADS_OWNER", None)
        self.alice_email = os.environ.get("ALICE_EMAIL", None)
        self.alice_token = os.environ.get("ALICE_ADS_API_TOKEN", None)
        self.bob_owner = os.environ.get("BOB_ADS_OWNER", None)
        self.bob_email = os.environ.get("BOB_EMAIL", None)
        self.bob_token = os.environ.get("BOB_ADS_API_TOKEN", None)

    def test_alice_and_bob(self):
        self.assertIsNotNone(self.alice_owner)
        self.assertIsNotNone(self.alice_token)
        self.assertIsNotNone(self.bob_owner)
        self.assertIsNotNone(self.bob_token)
        self.assertIsNotNone(self.alice_email)
        self.assertIsNotNone(self.bob_email)

    def test_transfer_to_alice(self):
        name = random_library_name()
        library = Library.create(name=name)

        # Transfer to Alice.
        library.owner = self.alice_email
        library.save()

        # Check that we can't access it anymore.
        with self.assertRaises(APIResponseError):
            Library.get(id=library.id)

        # Check that Alice can access it.
        existing_token = os.environ.get("ADS_API_TOKEN")
        os.environ["ADS_API_TOKEN"] = self.alice_token

        lib = Library.get(id=library.id)
        self.assertEqual(lib.name, name)
        self.assertEqual(lib.owner, self.alice_owner)

        # Test that transfer needs email address
        lib.owner = "MOOO"
        with self.assertRaises(ValueError):
            lib.save()

        lib.delete()
        os.environ["ADS_API_TOKEN"] = existing_token


    def test_transfer_with_permissions(self):
        # Alice creates account.
        # Alice gives Bob read/write permission.
        # Alice transfers to Charlie.
        # Check that Bob still has read/write permission.
        existing_token = os.environ.get("ADS_API_TOKEN")

        # Alice
        os.environ["ADS_API_TOKEN"] = self.alice_token
        name = random_library_name()
        lib = Library.create(name=name)

        # Give bob read/write permission.
        permissions = ["read", "write", "admin"]
        lib.permissions[self.bob_email] = permissions
        lib.save()

        # Alice transfers to me.
        lib.owner = "andrew.casey@monash.edu"
        lib.save()

        # Check that I can access it.
        os.environ["ADS_API_TOKEN"] = existing_token
        my_lib = Library.get(id=lib.id)
        self.assertEqual(my_lib.name, name)

        # Check that Bob still has permissions
        self.assertIn(self.bob_email, my_lib.permissions)
        for permission in permissions:
            self.assertIn(permission, my_lib.permissions[self.bob_email])

        # Check that Alice can't access it.
        os.environ["ADS_API_TOKEN"] = self.alice_token
        with self.assertRaises(APIResponseError):
            Library.get(id=lib.id)

        # Get Bob to change the name.
        os.environ["ADS_API_TOKEN"] = self.bob_token

        # Edit permission of a library
        # of https://ui.adsabs.harvard.edu/help/api/api-docs.html#post-/biblib/permissions/-library_id-
        # makes it seem like admins could add people with read access, but that doesn't seem allowed.
        # Email the ADS team about this.

        new_name = "new_name_" + random_library_name(10)
        bob_lib = Library.get(id=lib.id)
        bob_lib.name = new_name
        bob_lib.save()

        '''        
        #bob_lib.permissions[self.alice_email] = ["read"]
        #bob_lib.save()

        # Check Alice can access it now.
        os.environ["ADS_API_TOKEN"] = self.alice_token
        alice_lib = Library.get(id=lib.id)

        self.assertEqual(alice_lib.name, name)
        '''
        os.environ["ADS_API_TOKEN"] = existing_token

        # Check the name is what bob set it as.
        lib = Library.get(id=lib.id)
        self.assertEqual(lib.name, new_name)

        # As owner, delete the library.
        my_lib.delete()


class TestLibraryDocuments(unittest.TestCase):

    def setUp(self):
        self.N = 10
        self.documents = list(
            Document.select()\
                    .where(Document.year == 2005)\
                    .order_by(Document.citation_count.desc())\
                    .limit(self.N)
        )

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

    
    def test_document_set(self):
        lib = Library(name=random_library_name())

        lib.documents = self.documents
        lib.save()

        lib2 = Library.get(id=lib.id)
        self.assertEqual(lib2.num_documents, lib.num_documents)
        self.assertEqual(lib2.num_documents, self.N)


    def test_create_with_documents(self):            
        # Examples of how documents can be set.
        lib_A = Library.create(
            name="A_" + random_library_name(10),
            documents=self.documents
        )
        self.assertEqual(lib_A.num_documents, self.N)
        self.assertEqual(len(lib_A.documents), self.N)

        lib_A.delete()
    
    def test_documents_extend(self):
        lib_C = Library.create(
            name="C_" + random_library_name(10),
        )
        lib_C.documents.extend(self.documents)
        lib_C.save()

        self.assertEqual(lib_C.num_documents, self.N)

        lib = Library.get(id=lib_C.id)
        self.assertEqual(lib.num_documents, lib_C.num_documents)

        lib_C.delete()

    
    def test_create_from_set_operation(self):

        lib_A = Library.create(
            name=random_library_name(),
            documents=self.documents[:7]
        )
        lib_B = Library.create(
            name=random_library_name(),
            documents=self.documents[-7:]
        )

        K = len(set(lib_A).intersection(lib_B))
        lib_C = lib_A.intersection(lib_B)
        self.assertGreater(K, 0)
        self.assertEqual(lib_C.num_documents, K)

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


