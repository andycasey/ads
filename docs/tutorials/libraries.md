# Libraries

ADS Libraries can be used for creating and curating collections of bibliographic records. Libraries can be created or edited through the ADS website, or through the ADS API. This page provides a guide on how to create and manipulate libraries through the `ads` package.

You will need the following imports in order to execute all code blocks on this page:
```python
import ads
from datetime import datetime
```

## Retrieve existing libraries

If you have existing libraries in your ADS account you can immediately select these using the `ads` package. If you want to retrieve a single library you can use {func}`ads.Library.get()`, and if you don't supply any keyword arguments to this function then you will get the first library that is returned by ADS.

Below are a few examples showing how to retrieve libraries from ADS, with various degrees of complexity.

```python
# Retrieve a single library based on an exact query expression.
library = ads.Library.get(name="SDSS-IV")

# Get a single library, but we don't care which one.
library = ads.Library.get()
```

The {func}`ads.Library.get` method is for retrieving a single library. If you want to retrieve all your libraries, or your libraries based on some query expression, then you can use the {class}`ads.Library.select` method:

```python
# Retrieve all my current libraries
libraries = ads.Library.select()

# Retrieve libraries based on a more complex query expression
libraries = ads.Library.select().where(
    ads.Library.description.like("Gaia") & 
    (
        (ads.Library.num_documents > 100) |
        (ads.Library.date_last_modified >= datetime(2021, 12, 1))
    )
)
```

Both of these examples will return an {class}`ads.models.library.LibrarySelect` object. In most cases you probably want to iterate over it to retrieve your libraries:

```python
# Iterate through all my libraries.
for library in libraries:
    print(f"{library.id} {library.name}: {library.description}")

# After you've iterated through the libraries, you can select libraries by their index,
# or iterate over them again without any more API calls made to ADS.
last_library = libraries[-1]

small_libraries = [lib for lib in libraries if lib.num_documents < 5]
```

But you can also apply further operations to the {class}`ads.models.library.LibrarySelect` object, like limit, sort, or filter:

```python
top_5_libraries = ads.Library.select()\
                             .sort(ads.Library.num_documents.desc())\
                             .limit(5)
for library in ads.Library.select():
    print(f"{library.id}: {library.name} has {library.num_documents}")
``` 

In these example, each `library` is an {class}`ads.Library` object that stores the metadata, documents, and permissions about that library. The {class}`ads.Library` object also has a number of method functions that can be used to manipulate the library.


## Creating a new library

You can create a new library locally and add or remove documents, or perform set operations with other libraries. When you're finished, you can save the library to your ADS account using :meth:`ads.Library.save` function.

```python
library = ads.Library(name="Example")

# Perform some operations

# Save the changes to the ADS library
library.save()
```

## Saving your changes to ADS

Any time you make changes to a library, these won't be automatically updated to ADS until you use the {func}`ads.Library.save` function. Examples of changes that you will need to save include:

- Creating a library
- Adding or removing documents, including emptying all documents from a library
- Updating metadata (e.g., name, description)
- Updating permissions

It's okay to `save()` if you don't know whether you need to save or not. If there are no changes that need to be updated, then nothing will happen.

:::{Warning}
If your Python script finishes or crashes before you call {func}`ads.Library.save`, you will not receive any warnings.
:::

## Accessing documents in a library

If you want to access the documents in a library then you can simply iterate over them:

```python
for document in library:
    print(f"{document.bibcode} {document.journal} {document.title}")
```

You can also access documents by an index (e.g., `library[4]`) or slicing (e.g., `library[4:10]`), but this is not recommended because no explicit sort can be given to ADS when we are retrieving the documents in a library.

## Add or remove documents from a library

When it comes to adding or removing documents, the {class}`ads.Library` object behaves a bit like a {class}`set` or {class}`list`. You can `append`, `extend`, `remove`, or `pop` documents to a `ads.Library`, or use the addition or subtraction operators in Python:

```python
library = ads.Library.get(name="Example")

documents = [
    ads.Document.get(bibcode="2000A&AS..143...41K"),
    ads.Document.get(bibcode="1991ASSL..171..139W")
]

# Add the documents to the library.
# There are three ways you can do this. All produce the same result.
# 1. Use the addition operator.
library += documents

# 2. Or use the .extend function for a list of documents.
library.extend(documents)

# 3. Or use the .append function for an individual document.
for document in documents:
    library.append(document)

# You will need to save your library to have the changes reflected on ADS.
library.save()
```

If the document is already in the library then it won't be duplicated. In this way the {class}`ads.Library` object behaves like a {class}`set`, but here you can use addition and subtraction operators, which is unlike a {class}`set` and more like a {class}`list`.

To remove a document:
```python
# To remove a single document
library.remove(documents[-1])

# Remove a document based on its index
library.pop(0) 

# Empty the library of all documents
library.empty()

# You will need to save your library to have the changes reflected on ADS.
library.save()
```

## Metadata

Each library has associated metadata. Some of these are read-only:

- `id`: A unique identifier string for this library, provided by ADS.
- `num_users`: The number of users with access to this library.
- `num_documents`: The number of documents in the library.
- `date_created`: The UTC date when the library was created.
- `date_last_modified`: The UTC date when the library was last modified.

These metadata fields can be edited by the owner or by an administrator of the library:

- `name`: The name given to the library.
- `description`: A short description of the library.
- `public`: A boolean indicating whether the library is publicly accessible.
- `owner`: The ADS username that owns this library. (See [transfer ownership of a library](#transfer-ownership-of-a-library))

You can access all of these fields as attributes of the {class}`ads.Library` class. For example:

```python
# Retrieve any single library.
library = ads.Library.get()

print(
f"""
{library.id} {library.name} has:
 - {library.num_users} users 
 - {library.num_documents} documents
The library is owned by {library.owner} is {'public' if library.public else 'private'}.
The library description is: {library.description}
"""
)
```

If you want to change the `name`, `description`, or `public` field of a library then you can directly edit the attribute of the {class}`ads.Library` object, and then save your changes. An exception will be raised if you try to edit any of the read-only metadata fields.

```python
# Update the library metadata.
library.name = "New name"
library.description = "A new description"
library.public = not library.public

# Save the changes to ADS.
library.save()
```

Changing the `library.owner` will transfer the ownership of the library to another user. See [transfer ownership of a library](#transfer-ownership-of-a-library).

## Permissions

You can give specific permissions for other ADS users to be able to read, write, or administer your library. You can view the permissions for a library with the `permissions` attribute, which is essentially a Python dictionary with email addresses as keys, and a list of permissions as values. For example:

```python
{
  "andrew.casey@monash.edu": [
    "owner"
  ],
  "ada.lovelace@gmail.com": [
    "read", "write", "admin"
  ]
}
```

If you want to modify the permissions of a library then you can directly edit the `library.permissions` attribute, and save the library. For example:

```python
# An exception will be raised if bob@gmail.com does not have an ADS account.
library.permissions["bob@gmail.com"] = ["read"]
library.save()
```

The valid permission keys you can assign to a user are `read`, `write`, and `admin`. You can see that `owner` is also a permission key, but you cannot change the owner by editing the `library.permissions` dictionary. To do that you need to [transfer ownership of a library](#transfer-ownership-of-a-library).


## Perform set operations on one or more libraries

union = set(library_a).union(library_b)



## Transfer ownership of a library

You can transfer the ownership of your library to another ADS user. The owner of the library is given by the {func}`ads.Library.owner` property. To transfer ownership you can simply change the value in {func}`ads.Library.owner`, and save the library. 

The func:`ads.Library.owner` property is a little counter-intuitive. For libraries that you have read (or higher) access, the {func}`ads.Library.owner` property returns the ADS **username** of the account that owns the library. However, if you want to transfer the ownership of a library to another user, you need to change `ads.Library.owner` to be the **email address** that the new owner uses for their ADS account. 

After the transfer has occurred, if the new owner were to retrieve the `Library` then they would see their ADS **username** in this field, even though you needed to provide their **email address** to make the transfer happen. If you supply an invalid email address, or an email address that is not associated with any ADS account, then an exception will be raised.

Let's create a new library and transfer the ownership to another user:

```python
# Create a new library.
library = ads.Library()

# Add a document.
library += ads.Document.get(bibcode="2000A&AS..143...41K")

# Transfer the ownership to another ADS user.
library.owner = "ada.lovelace@gmail.com"

# Everything we have done so far has been performed locally.
# We will need to save this library to push the changes to ADS.
library.save()

# If there is an ADS account associated with the email address above, 
# then the transfer will be successful, and any operations we want to
# make on this library will now be forbidden by ADS!
# (See warning below)
library.refresh()
```

:::{Warning}
Once you transfer ownership of a library to another user you will **immediately** lose all read and write access to that library.

The moment that someone else owns the library, you cannot give yourself read, write, or admin permissions. And if you own the library, then you cannot edit your own permissions. That means if you want to transfer ownership of a library to another user and keep some permissions (e.g., read-only), you have two options:

1. Ask the new owner to update the library permissions.

2. If Alice is transferring a library to Bob, but Bob will be unable to give read permissions to Alice, then Alice will need a second ADS account (Charlie). First, Alice will need to make Charlie an administrator of the library. Then Alice can transfer ownership of the library to Bob. After that, Charlie can give Alice read permissions on the library. For example:
```python
# By default, Alice is using her own ADS token.
alice_email_address = "alice@gmail.com"
alice_token = ads.config.token 

# Bob will be the new owner of the library.
bob_email_address = "bob@gmail.com"

# This is the ADS token for Alice's second account, Charlie.
charlie_email_address = "alice+charlie@gmail.com"
charlie_token = "..." 

# Alice creates a library, and gives Charlie administrator access.
lib = ads.Library()
lib.permissions.update({
    charlie_email_address: ["admin", "read", "write"]
})
lib.save()

# Alice transfers the ownership to Bob.
lib.owner = bob_email_address
lib.save()

# Retrieve the transferred library by the ADS identifier.
# This library is owned by Bob, but Charlie has admin permissions.
ads.config.token = charlie_token # Use Charlie's account.
transferred_lib = ads.Library.get(id=lib.id)

# Give Alice read-only permissions.
transferred_lib.permissions.update({
    alice_email_address: ["read"]
})
transferred_lib.save()
```
:::


## Delete a library

Using {func}`ads.Library.empty` will remove all documents from a library, but the library itself will still exist with zero documents. If you want to delete a library from ADS, you can use {func}`ads.Library.delete`:

```python
# Create a temporary library.
library = ads.Library.create(name="Temporary library")

# Delete it!
library.delete()
```

The `library` object will still exist in your Python script, but any further modifications you make to the `libary` will result in an error, because ADS has deleted the library from their server.


## Querying with `ads.Document` and `ads.Library`

You can combine searches for documents in libraries without much user effort. (Instead, the `ads` package is doing the work for you.) If you wanted to search among documents in a library for those published in 2020, here's what it might look like:

```python
library = ads.Library.get()
documents = ads.Document.select()\
                        .where(ads.Document.in_(library) \
                            & (ads.Document.year == 2020)
                        )
```

That kind of query is so simple that you could do the same thing locally:

```python
documents = list(filter(lambda doc: doc.year == 2020, library.documents))
```

But for a query with ADS fields or operators that are searchable but not viewable, you can use the {class}`ads.Document` and {class}`ads.Library` object relational mappers to execute them. Here are some examples:

```python
# Find documents in this library that are trending in exoplanets.
trending_exo_docs = ads.Document.select()\
                                .where(
                                    ads.Document.trending("exoplanets") \
                                    &   ads.Document.in_(library)
                                )\
                                .order_by(
                                    ads.Document.read_count.desc()
                                )

# Match for some keyword in the virtual `all` field, which checks:
# author_norm, alternate_title, bibcode, doi, identifier.
jwst_docs = ads.Document.select()\
                        .where(
                            ads.Document.all.like("JWST") \
                            &   ads.Document.in_(library)
                        )

# Find recent documents that match some keywords but are not in a library.
gaia_library = ads.Library.get(name="Gaia EDR3 papers")
gaia_docs = ads.Document.select()\
                        .where(
                            ads.Document.abs.like("Gaia") \
                            &   (not ads.Document.in_(gaia_library)) \
                            &   (ads.Document.date >= gaia_library.last_modified_date)
                        )
```

### How does this work?

Most users don't need to know how this works. But if you're interested, read on. 

The expressions given in the `.where()` clause are parsed by the {class}`ads.models.document.DocumentSelect` object into a search string that ADS can understand. Most search requests to the ADS API use the [`/search/query`](https://ui.adsabs.harvard.edu/help/api/api-docs.html#get-/search/query) endpoint. But there are limitations on this endpoint. For example, if we wanted to search for documents that match the "JWST" phrase and are also in some library, then we have to construct an ADS search string like ```all:JWST AND bibcode:(A OR B OR C OR ...)```, where `A`, `B`, `C`, etc are bibcodes of documents that are in the library. Making an ADS search with a term like `bibcode:(A OR B OR C OR ...)` is prohibitively expensive, and the standard `/search/query` endpoint will raise an exception if the search is going to be too expensive.

Instead, if the expression in `.where()` includes a many-comparison restriction on `ads.Document.bibcode` then the {class}`ads.models.document.DocumentSelect` will use the [`/search/bigquery`](https://ui.adsabs.harvard.edu/help/api/api-docs.html#post-/search/bigquery) ADS API endpoint, which allows for efficient searching given a list of many bibcodes. This endpoint has different parameters, restrictions, and rate limits than the standard endpoint, but the `ads` package manages all of this for you. Hopefully, you should never even know which endpoint was used.