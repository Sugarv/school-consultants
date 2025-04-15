import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User

class Command(BaseCommand):
    help = "Import groups and permissions from a JSON file"

    def handle(self, *args, **kwargs):
        with open('fixtures/groups_permissions.json', 'r') as file:
            data = json.load(file)
            for entry in data:
                group_name = entry['group']
                group, created = Group.objects.get_or_create(name=group_name)
                permissions = Permission.objects.filter(codename__in=entry['permissions'])
                group.permissions.set(permissions)
                group.save()

                if group_name != 'Σύμβουλοι':
                    username = group_name + '1'
                    password = username + '-pass'
                    user, created = User.objects.get_or_create(username=username)
                    if created:
                        user.set_password(password)
                        user.is_staff = True
                        user.save()
                    user.groups.add(group)
        self.stdout.write(self.style.SUCCESS("Imported groups, permissions and created users from groups_permissions.json"))