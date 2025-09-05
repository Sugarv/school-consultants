# School consultants
Track & monitor school consultant transfers & teacher evaluation process steps.

Coded in Python's [Django](https://www.djangoproject.com), built around [unfold](https://unfoldadmin.com)

The project consists of two apps:
### Evaluation
A web app to make teacher evaluation tracking easier for school consultants. Also a way for directors, supervisors to monitor the evaluation process.

### Metakiniseis (Transfers)
A web app to track & monitor consultant transfers & produce related documents: transfer & payment decisions.

### User roles
The app features 4 discreet user roles with different capabilities each:
- **Secretariat (Γραμματεία)**: Can view/change all consultants' transfers & evaluation steps & produce transfer decisions
- **Financial department (Οικονομικό)**: Can view/change all consultants' transfers & evaluation steps & produce payment transfer decisions
- **Supervisor (Επόπτης)**: Can view/change all consultants' transfers & evaluation steps
- **Consultant (Σύμβουλος)**: Can add/view/change/delete their transfers & evaluation steps

### Run with Docker compose ###

- Copy ```.env-sample``` to ```.env```, changing the desired fields
- Run ```docker compose up -d``` (to create containers and run app - Docker should be installed)
- (Optional) Import Evaluation Step Types: ```docker compose exec app python manage.py loaddata fixtures/initial_step_types.json```
- Run ```docker compose exec app python manage.py createsuperuser``` (to create admin - run after a few minutes to allow app initialization)


### Instructions for development setup

- Create a [virtual environment](https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/) and activate it
- Install requirements: ```pip install -r requirements.txt```
- Migrate DB: ```python manage.py migrate```
- Create a superuser: ```python manage.py createsuperuser```
- Import groups & their permissions: ```python manage.py import_groups --settings=app.settings-dev``` 
- (Optional) Import Evaluation Step Types: ```python manage.py loaddata fixtures/initial_step_types.json```
- (Optional) Import Metakinhseis from csv: ```python manage.py import_metakinhseis {csv_file_path} --settings=app.settings-dev``` (see metakinhsh_import_sample.csv)
- Run the app with: ```python manage.py runserver --settings=app.settings-dev```