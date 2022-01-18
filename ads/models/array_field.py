
from peewee import ColumnBase, Field, IntegerField, NodeList, Node, SQL, Expression, OP, Value

ACONTAINS = '@>'
ACONTAINED_BY = '<@'
ACONTAINS_ANY = '&&'

# TODO: Refactor all this to just take the bare bones of what we need, and to make sure it
#       works nicely with Solr and SQLite.

class _LookupNode(ColumnBase):
    def __init__(self, node, parts):
        self.node = node
        self.parts = parts
        super(_LookupNode, self).__init__()

    def clone(self):
        return type(self)(self.node, list(self.parts))

    def __hash__(self):
        return hash((self.__class__.__name__, id(self)))

class ObjectSlice(_LookupNode):
    @classmethod
    def create(cls, node, value):
        if isinstance(value, slice):
            parts = [value.start or 0, value.stop or 0]
        elif isinstance(value, int):
            parts = [value]
        elif isinstance(value, Node):
            parts = value
        else:
            # Assumes colon-separated integer indexes.
            parts = [int(i) for i in value.split(':')]
        return cls(node, parts)

    def __sql__(self, ctx):
        ctx.sql(self.node)
        if isinstance(self.parts, Node):
            ctx.literal('[').sql(self.parts).literal(']')
        else:
            ctx.literal('[%s]' % ':'.join(str(p + 1) for p in self.parts))
        return ctx

    def __getitem__(self, value):
        return ObjectSlice.create(self, value)

class IndexedFieldMixin(object):
    default_index_type = 'GIN'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('index', True)  # By default, use an index.
        super(IndexedFieldMixin, self).__init__(*args, **kwargs)


class ArrayField(IndexedFieldMixin, Field):
    passthrough = True

    def __init__(self, field_class=IntegerField, field_kwargs=None,
                 dimensions=1, convert_values=False, *args, **kwargs):
        self.__field = field_class(**(field_kwargs or {}))
        self.dimensions = dimensions
        self.convert_values = convert_values
        self.field_type = self.__field.field_type
        super(ArrayField, self).__init__(*args, **kwargs)

    def bind(self, model, name, set_attribute=True):
        ret = super(ArrayField, self).bind(model, name, set_attribute)
        self.__field.bind(model, '__array_%s' % name, False)
        return ret

    def ddl_datatype(self, ctx):
        data_type = self.__field.ddl_datatype(ctx)
        return NodeList((data_type, SQL('[]' * self.dimensions)), glue='')

    def db_value(self, value):
        if value is None or isinstance(value, Node):
            return value
        elif self.convert_values:
            return self._process(self.__field.db_value, value, self.dimensions)
        else:
            return value if isinstance(value, list) else list(value)

    def python_value(self, value):
        if self.convert_values and value is not None:
            conv = self.__field.python_value
            if isinstance(value, list):
                return self._process(conv, value, self.dimensions)
            else:
                return conv(value)
        else:
            return value

    def _process(self, conv, value, dimensions):
        dimensions -= 1
        if dimensions == 0:
            return [conv(v) for v in value]
        else:
            return [self._process(conv, v, dimensions) for v in value]

    def __getitem__(self, value):
        return ObjectSlice.create(self, value)

    def _e(op):
        def inner(self, rhs):
            return Expression(self, op, ArrayValue(self, rhs))
        return inner
    __eq__ = _e(OP.EQ)
    __ne__ = _e(OP.NE)
    __gt__ = _e(OP.GT)
    __ge__ = _e(OP.GTE)
    __lt__ = _e(OP.LT)
    __le__ = _e(OP.LTE)
    __hash__ = Field.__hash__

    def contains(self, *items):
        return Expression(self, ACONTAINS, ArrayValue(self, items))

    def contains_any(self, *items):
        return Expression(self, ACONTAINS_ANY, ArrayValue(self, items))

    def contained_by(self, *items):
        return Expression(self, ACONTAINED_BY, ArrayValue(self, items))


class ArrayValue(Node):
    def __init__(self, field, value):
        self.field = field
        self.value = value

    def __sql__(self, ctx):
        return (ctx
                .sql(Value(self.value, unpack=False))
                .literal('::')
                .sql(self.field.ddl_datatype(ctx)))
