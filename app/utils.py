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
