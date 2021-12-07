from peewee import Node, Context, Expression, Field, is_model, State, ModelSelect, OP, NodeList, Entity, AliasManager, Function, fn, is_model, Negated
from peewee import *

from ads.models.journal import Journal
from ads.models.affiliation import Affiliation
# Monkey patch Field.bind so that we can make docstrings available.


def __bind(self, model, name, set_attribute=True):
    self.model = model
    self.name = self.safe_name = name
    self.column_name = self.column_name or name
    if set_attribute:
        setattr(model, name, self.accessor_class(model, self, name))
        getattr(model, name).__doc__ = self.help_text


Field.bind = __bind


def is_expression_referencing_model_or_model_field(expression, model):
    for side in (expression.lhs, expression.rhs):
        if (isinstance(side, ForeignKeyField) and side.rel_model == model) \
        or isinstance(side, model) or getattr(side, "model", None) == model:
            return True
    return False
        

def parse_expression_referencing_journal(expression):
    # Examples:
    #   Document.abbreviation == "ApJ"
    #   Document.title == "The Astrophysical Journal"
    #   Document.journal == Journal.get(abbreviation="ApJ")
    # We need to translate these to:
    #   Document.bibstem == Journal.abbreviation

    from ads.models.document import Document

    for side in (expression.lhs, expression.rhs):
        other_side = expression.rhs if side is expression.lhs else expression.lhs

        if isinstance(side, ForeignKeyField) and side.rel_model == Journal:
            # We have a ForeignKeyField referencing a Journal.
            # The right hand side should be a Journal object.
            if not isinstance(other_side, Journal):
                raise TypeError(f"'{other_side}' should be a {Journal} object (not {type(other_side)})")
            
            return Expression(Document.bibstem, expression.op, other_side.abbreviation)
        
        if getattr(side, "model", None) == Journal:
            # We are accessing an attribute of Journal. Find the correct Journal(s).
            journals = Journal.select().where(Expression(side, expression.op, other_side))
            abbreviations = [journal.abbreviation for journal in journals]
            if expression.op not in (OP.IN, OP.NOT_IN):
                abbreviations = abbreviations[0]
            else:
                abbreviations = NodeList(abbreviations, glue=" OR ")
            return Expression(Document.bibstem, expression.op, abbreviations)

    raise TypeError(f"{expression} is not a valid expression")


def parse_expression_referencing_affiliation(expression):
    from ads.models.document import Document

    for side in (expression.lhs, expression.rhs):
        other_side = expression.rhs if side is expression.lhs else expression.lhs

        if isinstance(side, ForeignKeyField) and side.rel_model == Affiliation:
            # We have a ForeignKeyField referencing an Affiliation.

            if not isinstance(other_side, Affiliation):
                raise TypeError(f"'{other_side}' should be an {Affiliation} object (not {type(other_side)})")

            return Expression(Document.aff_id, expression.op, other_side.id)

        if getattr(side, "model", None) == Affiliation:
            # We are accessing an attribute of Journal. Find the correct Journal(s).
            affiliations = Affiliation.select().where(Expression(side, expression.op, other_side))
            aff_ids = [affiliation.id for affiliation in affiliations]
            aff_ids = NodeList(aff_ids, glue=" OR ", parens=True)
            return Expression(Document.aff_id, expression.op, aff_ids)            

class ADSContext(Context):
    # This is a simple context for the ADS API, not a general Context.

    def __init__(self, **settings):
        self.stack = []
        self._sql = []
        self._values = []
        self.alias_manager = AliasManager()

        default_settings = dict(quote="{}")
        self.state = State(**{**settings, **default_settings})


    def sql(self, obj):
        #print("Context", type(obj), isinstance(obj, Table), isinstance(obj, Expression), isinstance(obj, (Node, Context)), is_model(obj))
        if isinstance(obj, (Table, )):
            return self

        if isinstance(obj, Expression):
            return self.parse_expression(obj)
        elif isinstance(obj, (Node, Context)):
            return obj.__sql__(self)
        #elif is_model(obj):
        #    return obj._meta.table.__sql__(self)
        else:
            return self.sql(Value(obj))

    def literal(self, keyword):
        if keyword == ".": # Hack to avoid . in table.column format instead of inheriting from Column.
            return self
        keyword = keyword.strip("{}") # Fake quotes for the parser.
        self._sql.append(keyword)
        #print(f"Adding literal: {keyword}")
        return self


    def parse_expression(self, expression):

        # Special handling for Journal objects.
        if is_expression_referencing_model_or_model_field(expression, Journal):
            new_expression = parse_expression_referencing_journal(expression)
            return self.parse_expression(new_expression)

        if is_expression_referencing_model_or_model_field(expression, Affiliation):
            return self.parse_expression(parse_expression_referencing_affiliation(expression))    

        if (expression.op == OP.NE): #^ expression.negated:
            self.literal("-")
        
        if expression.op in (OP.EQ, OP.NE):
            self.literal("=")
        
        self.parse(expression.lhs)

        if expression.op in (OP.EQ, OP.NE, OP.LIKE, OP.LT, OP.LTE, OP.GT, OP.GTE, OP.BETWEEN, OP.IN):
            self.literal(":")
        elif expression.op in (OP.OR, OP.AND):
            self.literal(f" {expression.op} ")
        elif expression.op is None:
            None
        else:
            raise a

        if expression.op in (OP.LT, OP.LTE):
            self.literal("-")
        
        # Some operators require () brackets, and some require [], and some require "".
        if expression.op == OP.BETWEEN:
            self.literal("[")
            self.parse(expression.rhs.nodes[0])
            self.literal(" TO ")
            self.parse(expression.rhs.nodes[-1])
            self.literal("]")
        elif expression.op == OP.LT:
            self.parse(expression.rhs - 1)
        elif expression.op == OP.GT:
            self.parse(expression.rhs + 1)
        elif expression.op == OP.IN:
            #self.literal("(")
            self.parse(NodeList(expression.rhs, glue=" OR ", parens=True))
            #self.literal(")")
        else:
        
            try:
                self.literal(expression.lhs.parentheses[0])
            except AttributeError:
                None
            
            self.parse(expression.rhs)

            try:
                self.literal(expression.lhs.parentheses[1])
            except AttributeError:
                None
        
        if expression.op in (OP.GT, OP.GTE):
            self.literal("-")
            
        return self


    @property
    def scope(self):
        return self.state.scope



class ADSAPI:

    context_class = ADSContext
    field_types = {}
    operations = {}
    param = "?"
    quote = "  "
    
    def init(self, database, **kwargs):
        pass
        #print(f"ADSAPI.init({database}, **{kwargs})")

    def __enter__(self):
        if self.is_closed():
            self.connect()
        ctx = self.atomic()
        self._state.ctx.append(ctx)
        ctx.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ctx = self._state.ctx.pop()
        try:
            ctx.__exit__(exc_type, exc_val, exc_tb)
        finally:
            if not self._state.ctx:
                self.close()
    
    def connect(self):
        #print(f"ADSAPI.connect")
        None

    def execute(self, query, **kwargs):
        #print(f"ADSAPI.execute {query} {kwargs}")
        return query.__str__()


    def get_sql_context(self, **options):
        return self.context_class(quote="", **options)

    def close(self):
        with self._lock:
            if self.deferred:
                raise InterfaceError('Error, database must be initialized '
                                     'before opening a connection.')
            if self.in_transaction():
                raise OperationalError('Attempting to close database while '
                                       'transaction is open.')
            is_open = not self._state.closed
            try:
                if is_open:
                    with __exception_wrapper__:
                        self._close(self._state.conn)
            finally:
                self._state.reset()
            return is_open

    def _close(self, conn):
        conn.close()

    def is_closed(self):
        return self._state.closed

    def is_connection_usable(self):
        return not self._state.closed

    def connection(self):
        if self.is_closed():
            self.connect()
        return self._state.conn

    def cursor(self, commit=None):
        if self.is_closed():
            if self.autoconnect:
                self.connect()
            else:
                raise InterfaceError('Error, database connection not opened.')
        return self._state.conn.cursor()

