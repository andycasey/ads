"""
Base classes and metaclasses necessary for data models.
"""
from copy import deepcopy

from functools import reduce
import operator

from peewee import ForeignKeyField


class attrdict(dict):
    """ Syntactic sugar. """
    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(attr)
    def __setattr__(self, attr, value): self[attr] = value
    def __iadd__(self, rhs): self.update(rhs); return self
    def __add__(self, rhs): d = attrdict(self); d.update(rhs); return d


# Operators used in SQL expressions that we can use with ADS
OP = attrdict(
    AND='AND',
    OR='OR',
    EQ='=',
    LT='<',
    LTE='<=',
    GT='>',
    GTE='>=',
    NE='!=',
    IN='IN',
    #NOT_IN='NOT IN',
    LIKE='LIKE',
    BETWEEN='BETWEEN',
    BITWISE_NEGATION='~'
)

class Node:
    
    def __init__(self, name=None, doc_string=None, **kwargs):
        self._name = name
        self.doc_string = doc_string

    def __and__(self, rhs):
        return Expression(self, OP.AND, rhs)
    
    def __or__(self, rhs):
        return Expression(self, OP.OR, rhs)
    
    def __rand__(self, rhs):
        return Expression(rhs, OP.AND, self)
    
    def __ror__(self, rhs):
        return Expression(rhs, OP.OR, self)


class WrappedNode(Node):
    def __init__(self, node):
        self.node = node

class NegatedNode(WrappedNode):
    def __invert__(self):
        return self.node

class NodeList(Node):
    def __init__(self, nodes, glue, parentheses=None):
        self.nodes = nodes
        self.glue = glue
        self.parentheses = parentheses
    

    def __query__(self, context):
        if self.parentheses:
            context.literal(self.parentheses[0])

        N = len(self.nodes)
        for i, node in enumerate(self.nodes):
            context.parse(node)
            if N > (i+1):
                context.literal(self.glue)

        if self.parentheses:
            context.literal(self.parentheses[1])

        return context

class NodeRange(Node):
    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper
    
class Ordering(WrappedNode):
    def __init__(self, node, direction):
        super(Ordering, self).__init__(node)
        self.direction = direction

    def __query__(self, context):
        return context.parse(self.node).literal(f" {self.direction} ")


def Asc(node):
    return Ordering(node, "ASC")

def Desc(node):
    return Ordering(node, "DESC")

MODEL_BASE = '_metaclass_helper_'


def with_metaclass(meta, base=object):
    return meta(MODEL_BASE, (base,), {})


class Context:
    # This is a simple context for the ADS API, not a general Context.

    def __init__(self, **options):
        self._query = []
        self._values = []
        self.parentheses = options.get("parentheses", "()")
    
    def __enter__(self):
        self.literal(self.parentheses[0])
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.literal(self.parentheses[-1])
        return None
    
    def literal(self, keyword):
        self._query.append(keyword)
        return self

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.__str__()}>"

    def __str__(self):
        return "".join(self._query)

    def parse(self, obj):
        if isinstance(obj, (Expression, Node)):
            return obj.__query__(self)
        elif obj is not None:
            self.literal(f"{obj}")
        return self


    def __query__(self, lhs, op, rhs, negated):
        """
        Take an expression and represent it as a search query that ADS will understand.
        """
        if (op == OP.NE) ^ negated:
            self.literal("-")

        if op in (OP.EQ, OP.NE):
            self.literal("=")

        self.parse(lhs)

        if op in (OP.EQ, OP.NE, OP.LIKE, OP.LT, OP.LTE, OP.GT, OP.GTE, OP.BETWEEN, OP.IN):
            self.literal(":")
        elif op in (OP.OR, OP.AND):
            self.literal(f" {op} ")
        elif op is None:
            None
        else:
            raise a

        if op in (OP.LT, OP.LTE):
            self.literal("-")
        
        # Some operators require () brackets, and some require [], and some require "".
        if op == OP.BETWEEN:
            self.literal("[")
            self.parse(rhs.lower)
            self.literal(" TO ")
            self.parse(rhs.upper)
            self.literal("]")
        elif op == OP.LT:
            self.parse(rhs - 1)
        elif op == OP.GT:
            self.parse(rhs + 1)
        elif op == OP.IN:
            self.literal("(")
            self.parse(rhs)
            self.literal(")")
        else:
        
            try:
                self.literal(lhs.parentheses[0])
            except AttributeError:
                None
            
            self.parse(rhs)

            try:
                self.literal(lhs.parentheses[1])
            except AttributeError:
                None
        
        if op in (OP.GT, OP.GTE):
            self.literal("-")
            
        return self

        
class Expression(Node):
        
    def __init__(self, lhs, op, rhs, flat=False, negated=False):
        self.lhs = lhs
        self.op = op
        self.rhs = rhs
        self.flat = flat
        self.negated = negated
    
    def __repr__(self):
        return f"<Expression: {self.__query__()}>"

    def __query__(self, context=None):
        """ Generate the query syntax"""
        if context is None:
            context = Context()

        with context:
            q = context.__query__(self.lhs, self.op, self.rhs, self.negated)
        
        q = q.__str__()
        if q.startswith("(") and q.endswith(")"):
            q = q[1:-1]
        return q

    def __call__(self):
        return self.__query__()

    def __invert__(self):
        return Expression(
            lhs=self.lhs, 
            op=self.op, 
            rhs=self.rhs, 
            flat=self.flat,
            negated=not self.negated
        )



class FieldAccessor:
    def __init__(self, model, field, name):
        self.model = model
        self.field = field
        self.name = name

    def __get__(self, instance, instance_type=None):
        if instance is not None:
            # This is the place where we'd use lazy loading for fields.
            return instance.__data__.get(self.name)
        return self.field

    def __set__(self, instance, value):
        # TODO: Don't allow the user to try to set things!
        instance.__data__[self.name] = value
        instance._dirty.add(self.name)



class Field(Node):

    accessor_class = FieldAccessor
    
    def _invalid_expression(op):
        def inner(op):
            raise ValueError(f"{op} is not a valid searchable operation for this field type")
        return inner

    def __eq__(self, rhs):
        return Expression(self, OP.EQ, rhs)

    def __ne__(self, rhs):
        return Expression(self, OP.NE, rhs)

    def __hash__(self):
        return hash(f"{self.name}.{self.model.__name__}")

    def __repr__(self):
        if hasattr(self, "model") and getattr(self, "name", None):
            return f"<{type(self).__name__}: {self.model.__name__}.{self.name}>"
        return f"<{type(self).__name__}: (unbound)>"

    def bind(self, model, name, set_attribute=True):
        self.model = model
        self.name = name
        if set_attribute:
            setattr(model, name, self.accessor_class(model, self, name))
            getattr(model, name).__doc__ = self.doc_string
    
    def __query__(self, context):
        return context.literal(self._name or self.name)

    def asc(self):
        return Asc(self)

    def desc(self):
        return Desc(self)

    __pos__ = asc    
    __neg__ = desc
    __lt__ = _invalid_expression(OP.LT)
    __le__ = _invalid_expression(OP.LTE)
    __gt__ = _invalid_expression(OP.GT)
    __ge__ = _invalid_expression(OP.GTE)



class IntegerField(Field):

    field_type = 'INT'

    def adapt(self, value):
        try:
            return int(value)
        except ValueError:
            return value

    def __gt__(self, rhs):
        return Expression(self, OP.GT, rhs)

    def __lt__(self, rhs):
        return Expression(self, OP.LT, rhs)
    
    def __ge__(self, rhs):
        return Expression(self, OP.GTE, rhs)
    
    def __le__(self, rhs):
        return Expression(self, OP.LTE, rhs)

    def between(self, low, high):
        return Expression(self, OP.BETWEEN, NodeRange(low, high))

    def like(self, value):
        return Expression(self, OP.LIKE, value)
    

class DateField(Field):

    field_type = "DATE"

    def __gt__(self, rhs):
        return Expression(self, OP.GT, rhs)

    def __lt__(self, rhs):
        return Expression(self, OP.LT, rhs)
    
    def __ge__(self, rhs):
        return Expression(self, OP.GTE, rhs)
    
    def __le__(self, rhs):
        return Expression(self, OP.LTE, rhs)

    def between(self, low, high):
        return Expression(self, OP.BETWEEN, NodeRange(low, high))

    def like(self, value):
        return Expression(self, OP.LIKE, value)


class DateTimeField(DateField):

    field_type = "DATETIME"



class StringField(Field):

    parentheses = "\"\""

    def adapt(self, value):
        if isinstance(value, str):
            return value
        return str(value)

    def like(self, rhs):
        return Expression(self, OP.LIKE, rhs)


class Function(Field):
    
    def __init__(self, arguments, keyword_arguments=None, **kwargs):
        super(Function, self).__init__(**kwargs)
        self.arguments = arguments
        self.keyword_arguments = keyword_arguments or ()
    
    def __call__(self, *args):
        # Check the number of arguments.
        # TODO: Surely we could do this with some kind of wrapped function or something?
        if len(args) < len(self.arguments):
            N = len(self.arguments) - len(args)
            missing = self.arguments[-N:]
            if N > 1:
                s = "s"
                pos_str = ", ".join([f"'{arg}'" for arg in missing[:-1]])
                pos_str += f" and '{missing[-1]}'"
            else:
                s = ""
                pos_str = f"'{missing[0]}'"
            raise TypeError(f"{self}() missing {N} required positional argument{s}: {pos_str}")
        if len(args) > (len(self.arguments) + len(self.keyword_arguments)):
            A, K = len(self.arguments), len(self.keyword_arguments)
            if self.keyword_arguments is None:
                N = f"{A}"
            else:
                N = f"from {A} to {A+K}"
            raise TypeError(f"{self}() takes {N} positional arguments but {len(args)} were given")
        return Expression(self, None, NodeList(args, ", ", parentheses="()"))


class Metadata:
    def __init__(self, model):
        self.model = model
        self.fields = {}
        self.name = model.__name__.lower()


    def add_field(self, field_name, field, set_attribute=True):
        if field_name in self.fields:
            self.remove_field(field_name)
        field.bind(self.model, field_name, set_attribute)
    

    def remove_field(self, field_name):
        if field_name not in self.fields:
            return        
        self.fields.pop(field_name)



class ModelBase(type):

    def __new__(cls, name, bases, attrs):
        if name == MODEL_BASE or bases[0].__name__ == MODEL_BASE:
            return super(ModelBase, cls).__new__(cls, name, bases, attrs)
        
        for b in bases:
            if not hasattr(b, "_meta"):
                continue

            for k, v in b.__dict__.items():
                if k in attrs: continue
                if isinstance(v, FieldAccessor) and not v.field.primary_key:
                    attrs[k] = deepcopy(v.field)

        Meta = Metadata

        cls = super(ModelBase, cls).__new__(cls, name, bases, attrs)
        cls.__data__ = cls.__rel__ = None

        cls._meta = Meta(cls)

        fields = []
        for key, value in cls.__dict__.items():
            if isinstance(value, Field):
                fields.append((key, value))

        for name, field in fields:
            cls._meta.add_field(name, field)
        return cls


    def __repr__(self):
        return f"<Model: {self.__name__}>"

    def __str__(self):
        try:
            k, v = next(iter(self.__data__.items()))
        except:
            return f"<Model {self.__name__}: empty>"
        else:
            return f"<Model {self.__name__}: {k}={v}>"


class Model(with_metaclass(ModelBase, Node)):
    def __init__(self, *args, **kwargs):
        self.__data__ = {}
        self._dirty = set(self.__data__)
        self.__rel__ = {}

        for k, v in kwargs.items():
            setattr(self, k, v)




class ModelSelect:

    def __init__(self, fields, where=None, ):
        self.fields = fields
        self._where = where
        self._order_by = None

    def where(self, *expressions):
        if self._where is not None:
            expressions = (self._where,) + expressions
        self._where = reduce(operator.and_, expressions)
        return self

    def order_by(self, ordering):
        self._order_by = ordering
        return self

