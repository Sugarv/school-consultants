import csv
from django.core.management.base import BaseCommand
from metakinhseis.models import Metakinhsh
from symvouloi.models import User
from datetime import datetime
from app.utils import get_school_year
from dateutil import parser

class Command(BaseCommand):
    help = 'Imports metakinhseis from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The CSV file to import')

    def handle(self, *args, **options):
        csv_file = options['csv_file']

        saves = 0
        fails = 0
        skipped = 0

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    date_from = parser.parse(row['date_from']).date()
                    date_to = parser.parse(row['date_to']).date()
                    from_location = row['from']
                    to_location = row['to']
                    km = float(row['km'])
                    egkrish = row['egkrish']
                    pragmat = row['pragmat']
                    xeirisths = row['xeirisths']
                    aitiologia = row['aitiologia']
                    surname = row['surname']

                    # Find consultant by surname
                    consultant = User.objects.filter(last_name__iexact=surname).first()
                    if not consultant:
                        self.stdout.write(self.style.ERROR(f'Consultant with surname "{surname}" not found. Skipping row.'))
                        skipped += 1
                        continue
                    
                    sch_year = get_school_year(date_from)

                    metakinhsh = Metakinhsh(
                        date_from=date_from,
                        date_to=date_to,
                        metak_from=from_location,
                        metak_to=to_location,
                        km=km,
                        egkrish=egkrish,
                        pragmat=pragmat,
                        handler=xeirisths,
                        aitiologia=aitiologia,
                        consultant=consultant,
                        school_year=sch_year
                    )

                    # check if metakinhsh exists:
                    if Metakinhsh.objects.filter(date_from=date_from, date_to=date_to, consultant=consultant, aitiologia=aitiologia).exists():
                        self.stdout.write(self.style.ERROR(f'Metakinhsh already exists for {consultant.last_name} from {date_from} to {date_to}. Skipping row.'))
                        skipped += 1
                        continue

                    # print(vars(metakinhsh))
                    metakinhsh._skip_email = True
                    metakinhsh.save()
                    saves += 1

                    self.stdout.write(self.style.SUCCESS(f'Successfully imported metakinhsh for {consultant.last_name} from {date_from} to {date_to}'))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error importing row: {e}'))
                    fails += 1

            print(f'{saves} saved, {fails} failed, {skipped} skipped')
            self.stdout.write(self.style.SUCCESS('Import completed.'))