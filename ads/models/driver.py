import json
import re
from collections import namedtuple
from peewee import (Database, NotSupportedError, SqliteDatabase, Select, Insert, Update, Delete)


Cursor = namedtuple("Cursor", ["lastrowid", "rowcount"], defaults=[1])


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


class SearchDatabase(Database):
    def init(self, database, *args):
        self.database = database

    def execute(self, query, **kwargs):
        if not isinstance(query, Select):
            raise NotSupportedError("Only SELECT queries are supported.")
        
        # Parse the expression to a Solr search query.
        raise a




class LibraryDatabase(Database):

    def init(self, database, *args):
        self.database = database

    def execute(self, query, **kwargs):
        print(f"executing {query}")

        if isinstance(query, Select):
            # If there is an expression given that has a specific ID, then we should retrieve that
            # because it may be a public library that is not owned by the user.

            # The standard query to biblib/libraries/<id> will give us the first 20 bibcodes, 
            # unless we specify how many we want. We don't know how many documents are in the
            # library, so let's pick a large number and if it's more than that we can refresh
            #max_peek_limit = 1_000
            #params = dict(rows=max_peek_limit)            

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
