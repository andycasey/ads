
""" Interface with the ADS search service. """

from datetime import datetime
from ads.client import Client
from peewee import (Database, Expression, OP, Node, TextField, VirtualField, NodeList, Function, Negated, Field, ForeignKeyField, NotSupportedError, Select)

from ads.models.utils import ArrayValue, ObjectSlice

class SearchInterface(Database):

    def init(self, database=None, *args):
        self.database = database or Client()

    def execute(self, query, **kwargs):
        from ads import Document
        if not isinstance(query, Select):
            raise NotSupportedError("Only SELECT queries are supported.")

        # Query needs to have `bibcode` and `id`.
        for required_field in (Document.bibcode, Document.id):
            for field in query._returning:
                if (isinstance(field, str) and field == required_field.name) \
                or (isinstance(field, Node) and (field.name == required_field.name)):
                    break
            else:
                query._returning.append(required_field)
                        
        # Parse the expression to a Solr search query.
        end_point, kwds = as_solr(query)
        
        with self.database as client:
            response = client.api_request(end_point, **kwds)

        # Return a mock cursor that will iterate over the results.
        return MockCursor(query, response.json["response"]["docs"])

        
class SolrQuery:

    parentheses = "()"

    def __init__(self, expression, remove_top_level_parentheses=True):
        self._solr = []
        self.remove_top_level_parentheses = remove_top_level_parentheses
        self.parse(expression)
        return None


    def parse(self, obj):

        from ads.models import Journal, Affiliation, Document

        if obj is None:
            return self
        
        elif isinstance(obj, datetime):
            repr = obj.strftime("%Y-%m-%dT%H:%M:%SZ")
            self.literal(f'"{repr}"')
        elif isinstance(obj, Function):
            with self:
                self.literal(obj.name)
                self.literal("(")
                N = len(obj.arguments)
                for i, arg in enumerate(obj.arguments):
                    self.parse(arg)
                    if i < N - 1:
                        self.literal(", ")
                self.literal(")")
            return self

        elif isinstance(obj, ArrayValue):
            # TODO: this may not be fully thought out yet.
            return self.literal(obj.value)

        elif isinstance(obj, Expression):
            # Resolve any Journal or Affiliation foreign fields.
            sides = (obj.lhs, obj.rhs)
            for side, other_side in zip(sides, sides[::-1]):
                if isinstance(side, ForeignKeyField) and side.rel_model == Journal:
                    if isinstance(other_side, str):
                        rhs = other_side
                    elif isinstance(other_side, Journal):
                        rhs = other_side.abbreviation
                    else:
                        raise TypeError(f"'{other_side}' should be a {Journal} object (not {type(other_side)})")
                    return self.parse(Expression(Document.bibstem, obj.op, rhs))
                    
                elif isinstance(side, ForeignKeyField) and side.rel_model == Affiliation:
                    if isinstance(other_side, str):
                        # Assume they are referencing by the abbreviation.
                        # TODO: is thjis right?
                        rhs = Affiliation.get(abbreviation=other_side).id
                    elif isinstance(other_side, Affiliation):
                        rhs = other_side.id
                    else:
                        raise TypeError(f"'{other_side}' should be a {Affiliation} object (not {type(other_side)})")
                    return self.parse(Expression(Document.aff_id, obj.op, rhs))
                
                elif getattr(side, "model", None) == Journal:
                    # We are accessing an attribute of Journal. Find the correct Journal(s).
                    js = Journal.select().where(Expression(side, obj.op, other_side))
                    rhs = [j.abbreviation for j in js]
                    if obj.op not in (OP.IN, OP.NOT_IN, OP.ILIKE):
                        rhs, = rhs
                    else:
                        rhs = NodeList(rhs, glue=" OR ")
                    return self.parse(Expression(Document.bibstem, obj.op, rhs))
                    
                elif getattr(side, "model", None) == Affiliation:
                    # We are accessing an attribute of Journal. Find the correct Affiliation(s).
                    affiliations = Affiliation.select().where(Expression(side, obj.op, other_side))
                    rhs = [affiliation.id for affiliation in affiliations]
                    rhs = NodeList(rhs, glue=" OR ", parens=True)
                    return self.parse(Expression(Document.aff_id, obj.op, rhs))

                elif isinstance(side, ObjectSlice):
                    # Deal with any ObjectSlices by wrapping them in a pos() position search
                    if min(side.parts) < 0:
                        raise ValueError(f"ADS Solr (search) service does not support negative indexing for position searches.")
                    return self.parse(
                        Document.pos(
                            Expression(side.node, obj.op, other_side), 
                            *(part + 1 for part in side.parts))
                            # Apache Solr does 1-index not 0-indexing.
                        )

            # If we get here, we have resolved all Journal and Affiliation fields.
            
            if obj.op == OP.NE:
                return self.literal("-")

            with self:
                # If the operator is EQ / NE and the field is a particular kind,
                # then we want exact matching.
                #if obj.op in (OP.EQ, OP.NE) and isinstance(obj.lhs, Field) and obj.lhs.name in ("title", "author"):
                #    self.literal("=")
                if obj.op == OP.EX:
                    self.literal("=")

                self.parse(obj.lhs)
                
                if obj.op in (OP.EQ, OP.EX, OP.NE, OP.LIKE, OP.LT, OP.LTE, OP.GT, OP.GTE, OP.BETWEEN, OP.IN, OP.ILIKE):
                    self.literal(":")
                elif obj.op in (OP.OR, OP.AND):
                    self.literal(f" {obj.op} ")
                else:
                    raise NotImplementedError()
                
            
                # Some operators require () brackets, and some require [], and some require "".

                if obj.op in (OP.BETWEEN, OP.LT, OP.GT, OP.LTE, OP.GTE):
                    self.literal("[")
                    if obj.op == OP.BETWEEN:
                        self.parse(obj.rhs.nodes[0])
                        
                    elif obj.op == OP.GT:
                        self.parse(obj.rhs + 1)
                    elif obj.op == OP.GTE:
                        self.parse(obj.rhs)
                    elif obj.op in (OP.LT, OP.LTE):
                        self.literal("0")
                    self.literal(" TO ")
                    if obj.op == OP.BETWEEN:
                        self.parse(obj.rhs.nodes[-1])
                    elif obj.op == OP.LT:
                        self.parse(obj.rhs - 1)
                    elif obj.op == OP.LTE:
                        self.parse(obj.rhs)
                    elif obj.op in (OP.GT, OP.GTE):
                        # Through trial and error, these fields need a '*'.
                        # It's not just integer fields though: if you give '*' to `id` then it will fall over.
                        if obj.lhs.name in ("author_count", ):
                            self.literal("*")
                    self.literal("]")
                elif obj.op == OP.IN:
                    self.parse(NodeList(obj.rhs, glue=" OR ", parens=True))
                else:
                    rhs = obj.rhs

                    if obj.op == OP.ILIKE and isinstance(rhs, str):
                        rhs = rhs.replace("%", "*")

                    try:
                        if (obj.lhs.field_type == "TEXT" or isinstance(obj.lhs, VirtualField)) \
                        and not obj.lhs.name in ("aff_id", ):
                            self.literal('"')
                            self.parse(rhs)
                            if obj.op == OP.LIKE:
                                self.literal("*")
                            self.literal('"')
                        else:
                            self.parse(rhs)
                    except:
                        self.parse(rhs)
                        if obj.op == OP.LIKE:
                            self.literal("*")
                    
                    else:
                        if obj.lhs.field_type != "TEXT" and obj.op == OP.LIKE:
                            self.literal("*")

                #if obj.op in (OP.GT, OP.GTE):
                #    self.literal("-")

            return self
        
        elif isinstance(obj, Negated):
            return self.literal("-").parse(obj.node)

        elif isinstance(obj, NodeList):
            with self:
                return self.literal(obj.glue.join(obj.nodes))

        elif isinstance(obj, Node):
            return self.literal(obj.name)
        else:
            return self.literal(str(obj))


    def __enter__(self):
        if self.parentheses:
            self.literal(self.parentheses[0])
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.parentheses:
            self.literal(self.parentheses[-1])
        return None

    def __str__(self):
        parts = self._solr
        if self.remove_top_level_parentheses and parts[::len(parts) - 1] == self.parentheses[::1]:
            parts = parts[1:-1]
        return "".join(parts)
        
    def __repr__(self):
        return self.__str__()

    def literal(self, value):
        self._solr.append(value)
        return self



def as_solr(query, bibcode_limit=10):
    """
    Translate a ORM query expression for the ADS Apache Solr search service.
    """
        
    start, rows = (query._offset or 0, query._limit)
    sort = ", ".join(
        [f"{order.node.name} {order.direction}" for order in (query._order_by or ())]
    ) or None
    
    fields = []
    for field in query._returning:
        try:
            fields.append(field.name)
        except AttributeError:
            fields.append(field)

    # Steps:
    # - Figure out if we need BigQuery.
    # - TODO: Do we have more than one 'bibcode IN'? If so, be inclusive.

    # Do we need BigQuery?
    use_bigquery = counter(query._where, count_bibcodes) > bibcode_limit
    if use_bigquery:
        # Remove the bibcodes from the expression so they are don't appear in the search query.
        #print("WARNING: you're living dangeriously")
        end_point = "/search/bigquery"
        
        params = dict(
            q="*:*",
            wt="json", # TODO: Do we need this?
            fq="{!bitset}",
            fl=fields,
            sort=sort,
            start=start,
            rows=rows
        )
        kwds = dict(
            method="post", 
            params=params, 
            #data=json.dumps(dict(bibcode=query._where.rhs)),#"\n".join(data),
            # By default we supply the content-type as application/json, because most service
            # end points need that. But if we supply that content-type to bigquery, then it
            # expects a JSON object, but giving `json.dumps(dict(bibcode=query._where.rhs))` returns
            # nothing. So instead we will give 'bibcode\n...' and over-write the content-type headers
            # Email the ADS team about this.
            data="\n".join(["bibcode"] + query._where.rhs),
            headers={"Content-Type": "big-query/csv"}
        )
    else:
        expression = query._where
        if expression is None:
            # No expression given. If we supply no search expression to ADS then it will complain.
            # Let's give a dummy expression to retrieve all.
            q = "*:*"
        else:
            q = SolrQuery(expression)
        end_point = "/search/query"

        params = dict(
            q=f"{q}",
            fl=fields,
            fq=None,
            sort=sort,
            start=start,
            rows=rows,
        )

        kwds = dict(method="get", params=params)

    #print(end_point, kwds)
    return (end_point, kwds)
    



def counter(expression, callable, total=0):
    if expression is None:
        return 0

    if isinstance(expression.lhs, Expression) or isinstance(expression.rhs, Expression):
        return counter(expression.lhs, callable, total=total) \
             + counter(expression.rhs, callable)
    else:
        return callable(expression, total=total)

    


def count_bibcodes(expression, total=0):
    for side in (expression.lhs, expression.rhs):
        other_side = expression.rhs if expression.lhs == side else expression.lhs
        try:
            if side.name == "bibcode":
                if expression.op == "=":
                    return total + 1
                elif expression.op == "IN":
                    return total + len(other_side)
        except:
            continue
    return total



def field_names(query):
    names = []
    for field in query._returning:
        name = field if isinstance(field, str) else field.name
        names.append(name)
    return names

class MockCursor:
    
    # TODO: Where should this go?

    def __init__(self, query, results, **kwargs):
        self._query = query
        self._results = results
        self._index = 0
        self.description = []
        for name in field_names(self._query):
            self.description.append(tuple([name] + [None] * 6))

    def fetchone(self):
        try:
            result = self._results[self._index]
        except IndexError:
            return None
        else:
            self._index += 1
            return tuple([result.get(name, None) for name in field_names(self._query)])

    def close(self):
        pass
