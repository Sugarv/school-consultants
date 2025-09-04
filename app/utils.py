from datetime import datetime, date

def is_member(user, group):
    """
    Check if the user is a member of a specific group.
    """
    return group in user.groups.values_list('name', flat=True)

def is_member_of_many(user, groups):
    """
    Check if the user is a member of any group in a given comma-separated list.
    """
    group_list = [g.strip() for g in groups.split(',')]  # Ensure no leading/trailing spaces
    return user.groups.filter(name__in=group_list).exists()

# Return user fullname & role
def environment_callback(request):
    if not request.user.is_authenticated:
        return
    try:
        display_name = request.user.get_full_name() or request.user.username
        role = list(request.user.groups.values_list('name',flat = True)).pop() or ''
    except:
        return ['admin', "danger"]

    return [f'{display_name} - {role}', "info"]

# Decide school year based on date
def get_school_year(d, fmt="%d-%m-%Y"):
    # If d is a string → parse it
    if isinstance(d, str):
        d = datetime.strptime(d, fmt).date()
    elif isinstance(d, datetime):
        d = d.date()
    elif not isinstance(d, date):
        raise TypeError("Input must be str, datetime, or date")

    cutoff = date(d.year, 9, 1)  # 1st September of same year

    if d >= cutoff:
        return f"{d.year}-{d.year+1}"
    else:
        return f"{d.year-1}-{d.year}"
    

def get_current_school_year(today=None):
        if today is None:
            today = date.today()
        cutoff = date(today.year, 9, 1)
        if today >= cutoff:
            return f"{today.year}-{today.year+1}"
        else:
            return f"{today.year-1}-{today.year}"