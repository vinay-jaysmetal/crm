docker run -it --rm redis redis-cli -h host.docker.internal -p 6379

## Build the image

```docker-compose build```

### What it does:

Looks at your Dockerfile

Installs Python, Django, and other dependencies (like from requirements.txt)

Creates a Docker image for your Django app

### When to run it:

✅ Only when your Dockerfile or requirements.txt changes

❌ Not needed every time you reopen your project

## Start container and create project (if not already created)

`docker-compose run web django-admin startproject jaysmetal_backend .`

### What it does:

Runs the command inside the container to create a new Django project.

The . at the end means: "create the project here (in current directory)"

### When to run it:

✅ Only once — when you’re starting a new Django project

❌ Not needed if you already have your Django project code

### Run server

`docker-compose up`

### What it does:

Starts both the web (Django) and db (PostgreSQL) services

Uses the image built in step 1

Runs your app on http://localhost:8000/

### When to run it:

✅ Every time you want to start working on your project

Think of this like `python manage.py runserver`, but Dockerized


## ✅ So What Do You Need Every Time?

After initial setup:

`docker-compose up`

This is the only command you run every time to start working again.

If you make changes to dependencies (like adding a new package), then:

`docker-compose build  # Only needed if Dockerfile or requirements.txt changes`


## 💡 Next Steps

```
# Build the image
docker-compose build

# Start container and create project (if not already created)
docker-compose run web django-admin startproject myproject .

# Run server
docker-compose up
```

# Others Docker commands

### Make migrations:

`docker-compose run web python manage.py makemigrations`


### Create a superuser:

`docker-compose run web python manage.py createsuperuser`

### Open a shell:

DJANGO `docker-compose run web python manage.py shell`

DATABASE `docker-compose exec db psql -U postgres`

## Backup and Restore

### using dumpdata and loaddata:

`docker-compose run web python manage.py dumpdata`

`docker-compose run web python manage.py loaddata`

### Using docker-compose exec:

`docker-compose exec web python manage.py dumpdata`

`docker-compose exec web python manage.py loaddata`

### Using pg_dump and pg_restore:

`docker-compose exec db pg_dump -U postgres jaysmetal_db > backup.sql`

`docker-compose exec db pg_restore -U postgres -d jaysmetal_db backup.sql`

### Using pg_dump and pg_restore compressed:

`docker-compose exec db pg_dump -U postgres -Fc jaysmetal_db > jaysmetal_db_backup.dump`

`docker-compose exec db pg_restore -U postgres -d jaysmetal_db jaysmetal_db_backup.dump`

Note this cause error sometimes

so better

`docker exec jaysmetal_backend_db_1 pg_dump -U postgres -Fc jaysmetal_db -f /tmp/jaysmetal_db_backup.dump`

now copy it from docker to ec2

`docker cp jaysmetal_backend_db_1:/tmp/jaysmetal_db_backup.dump ./jaysmetal_db_backup_$(date +%F).dump`



`pg_restore -U postgres -d jaysmetal_db jaysmetal_db_backup.dump`


## optionally download from ec2


`scp -i "Keys\JaysmetalCanadaCentralKey.pem" ubuntu@ip:/home/ubuntu/jaysmetal_db_backup.dump .`

## Run Docker 


if already running

```
docker-compose down
``` 

```
docker-compose up -d --build
```

## Celery Run

mac or linux - Both worker and beat
```
celery -A jaysmetal_backend worker -B --loglevel=info
```

windows - worker
```
celery -A jaysmetal_backend worker --loglevel=info --pool=solo
```

windows - beat
```
celery -A jaysmetal_backend beat --loglevel=info
```

## Git Workflow

```
               [feature/login-api]
                        │
                        ▼
[feature/*] ─────► [develop] ─────► [main]
   Rough Work      Staging/QA       Production


```


BE: 15.223.6.59
test


## SSH 

Sandbox 

ssh -i Keys\JaysmetalCanadaCentralKey.pem ubuntu@35.183.71.63

live

ssh -i Keys\JaysmetalCanadaCentralKey.pem ubuntu@15.156.202.112

# TO Upgrade EC2

stop docker

stop instance

updage instance 

start docker


DB and media backup not mandatory

docker run -d --name redis -p 6379:6379 redis:latest


## IntegrityError at /admin/department_app/departmentmodel/add/ FIX

```
python manage.py dbshell
```


```
BEGIN;
SELECT setval(
    pg_get_serial_sequence('"department_app_departmentmodel"','id'),
    coalesce(max("id"), 1),
    max("id") IS NOT null
)
FROM "department_app_departmentmodel";
COMMIT;
```


## Management command for report

Run Commands in Exact Order

```
# 1. Make migrations for new models
python manage.py makemigrations fablist_app

# 2. Apply migrations
python manage.py migrate

# 3. Test command shows up
python manage.py help

# 4. Dry run first
python manage.py populate_fab_reports --dry-run

# 5. Run for real
python manage.py populate_fab_reports --days=30
```