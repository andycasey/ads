from peewee import Expression

def days_ago(n):
    return f"{now()}-{n:.0f}DAYS" if n > 0 else now()
    
def now():
    return "NOW"


def expression_contains(expression, field, operator=None):
    for side in (expression.lhs, expression.rhs):
        if isinstance(side, Expression) and expression_contains(side, field, operator):
            return True

        if isinstance(side, type(field)) \
        and side.model == field.model \
        and side.name == field.name \
        and (operator is None or expression.op == operator):
            return True
    return False