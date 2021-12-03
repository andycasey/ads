from peewee import (_BoundModelsContext, Context, ModelBase, ModelAlias, ModelRaw, ModelSelect, Node, DoesNotExist, with_metaclass, SqliteDatabase, Model, Value)

database = SqliteDatabase("models.db")


class LocalModel(Model):
    class Meta:
        database = database


class ADSAPI:

    context_class = Context
    field_types = {}
    operations = {}
    param = "?"
    quote = '""'
    
    def __init__(self, *args, **kwargs):
        print(f"in adsapi.__init__")
        return None

    def init(self, database, **kwargs):
        print(f"ADSAPI.init({database}, **{kwargs})")

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
        print(f"ADSAPI.connect")

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


class ADSModel(Model):
    class Meta:
        database = ADSAPI()