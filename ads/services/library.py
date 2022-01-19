
"""A library service offered by ADS."""

import json
import re
from collections import ChainMap, namedtuple
from peewee import (Database, SqliteDatabase, Select, Insert, Update, Delete)

from ads.client import Client
from ads.utils import flatten

Cursor = namedtuple("Cursor", ["lastrowid", "rowcount"], defaults=[1])


class LibraryInterface(Database):

    def init(self, database=None, *args):
        self.database = database or Client()

    def execute(self, query, **kwargs):
        print(f"executing {query}")

        if isinstance(query, Select):
            # TODO If there is an expression given that has a specific ID, then we should retrieve that
            # because it may be a public library that is not owned by the user.

            with self.database as client:
                response = client.api_request("biblib/libraries")

            # Now bind the model to an in-memory database.
            model = query.model
            local_database = SqliteDatabase(":memory:")
            with local_database.bind_ctx([model]):
                local_database.create_tables([model])

                for kwds in response.json["libraries"]:
                    model.create(**kwds)

                local_query = model.select()\
                                .where(query._where)\
                                .order_by(query._order_by)\
                                .limit(query._limit)

                return local_query.execute().cursor

        elif isinstance(query, Insert):
            field_names = {"name", "description", "public", "bibcode"}
            data = { k.name: v for k, v in query._insert.items() if k.name in field_names }

            # TODO: Warn about ignored fields.
            with self.database as client:
                response = client.api_request(
                    f"biblib/libraries",
                    method="post",
                    data=json.dumps(data)
                )

            return Cursor(response.json["id"])


        elif isinstance(query, (Update, Delete)):
            # TODO: Check that the where expression is by ID only, or its forbidden.
            library_id = query._where.rhs
            assert query._where.lhs.name == "id" and query._where.op == "="

            if isinstance(query, Update):            
                data = { k.name: v for k, v in query._update.items() }
                
                # Update metadata.
                metadata_field_names = {"name", "description", "public"}
                dirty_metadata_field_names = set(data).intersection(metadata_field_names)
                if dirty_metadata_field_names:
                    update_metadata = { k: data[k] for k in dirty_metadata_field_names }
                    with self.database as client:
                        client.api_request(
                            f"biblib/documents/{library_id}",
                            data=json.dumps(update_metadata),
                            method="put"
                        )
                    print(f"Updated metadata {update_metadata}")
                
                # Update permissions.
                if "permissions" in data:
                    _, all_permission_kinds = valid_permissions([])
                    for email in data["permissions"]:
                        print(f"Updating permission for {email}")
                        update_permissions = dict(
                            email=email, 
                            permission={ kind: False for kind in all_permission_kinds}
                        )
                        permission_kinds = data["permissions"].get(email, [])
                        if permission_kinds:
                            update_permissions["permission"].update(
                                dict(zip(permission_kinds, [True] * len(permission_kinds)))
                            )

                        with self.database as client:
                            client.api_request(
                                f"biblib/permissions/{library_id}",
                                data=json.dumps(update_permissions),
                                method="post"
                            )

                        print(f"Update permissions for  {update_permissions}")

                # Update owner.
                if "owner" in data:
                    owner = data["owner"]
                    if not valid_email_address(owner):
                        raise ValueError(f"Invalid email address for new owner: '{owner}'")
                    
                    with self.database as client:
                        client.api_request(
                            f"biblib/documents/{library_id}",
                            data=json.dumps(dict(email=owner)),
                            method="post"
                        )

                return Cursor(library_id)
                
            
            elif isinstance(query, Delete):
                with self.database as client:
                    # I assumed that this endpoint would be biblib/libraries/{id},
                    # but it is actually biblib/documents/{id}. I don't know why.
                    # The documentation correctly says biblib/documents/{id}, but
                    # the naming convention is not what I expected.
                    # TODO: Email ADS team about this.
                    #f"biblib/libraries/{self.id}",                    
                    client.api_request(f"biblib/documents/{library_id}", method="delete")
                return Cursor(library_id)


def valid_email_address(email: str) -> bool:
    """
    Check whether an email address looks valid.
    
    :param email:
        An email address.
    """
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def valid_permissions(values):
    permissions = ("read", "write", "admin")
    unknown = set(values).difference(permissions)
    is_valid = (len(unknown) == 0)
    return (is_valid, permissions)


def requires_bibcodes(func):
    def inner(library, *args, **kwargs):
        try:
            library.__data__["bibcodes"]
        except KeyError:
            library.refresh()
        finally:
            return func(library, *args, **kwargs)
    return inner


class Permissions(dict):
    
    def __init__(self, library):
        self._library = library
        self._dirty = set()
        return None

    def __setitem__(self, item, value):
        value = list(set(flatten(value)))
        if not valid_email_address(item):
            raise ValueError(f"Invalid email address '{item}'")
        is_valid, valid_values = valid_permissions(value)
        if not is_valid:
            raise ValueError(f"Invalid permissions among '{value}': must contain only {valid_values}")
        self._set_dirty(item)
        super().__setitem__(item, value)


    def _set_dirty(self, item):
        self._dirty.add(item)
        self._library._dirty.add("permissions")


    def __delitem__(self, item):
        self._set_dirty(item)
        super().__delitem__(item)


    def refresh(self):
        with Client() as client:
            response = client.api_request(f"biblib/permissions/{self._library.id}")
        self.update(dict(ChainMap(*response.json)))
        return response
