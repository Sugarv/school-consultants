import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    help = "Import groups and permissions from a JSON file"

    def handle(self, *args, **kwargs):
        with open('fixtures/groups_permissions.json', 'r') as file:
            data = json.load(file)
            for entry in data:
                group, created = Group.objects.get_or_create(name=entry['group'])
                permissions = Permission.objects.filter(codename__in=entry['permissions'])
                group.permissions.set(permissions)
                group.save()
        self.stdout.write(self.style.SUCCESS("Imported groups and permissions from groups_permissions.json"))