import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    help = "Export groups and permissions to a JSON file"

    def handle(self, *args, **kwargs):
        data = []
        for group in Group.objects.all():
            permissions = group.permissions.values_list('codename', flat=True)
            data.append({
                'group': group.name,
                'permissions': list(permissions),
            })
        with open('fixtures/groups_permissions.json', 'w') as file:
            json.dump(data, file, indent=4)
        self.stdout.write(self.style.SUCCESS("Exported groups and permissions to groups_permissions.json"))
        