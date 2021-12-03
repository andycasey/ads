def days_ago(n):
    return f"{now()}-{n:.0f}DAYS" if n > 0 else now()
    
def now():
    return "NOW"