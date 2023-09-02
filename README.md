# vw_storages

1. clone the repo
2. pip insatall -r requirement.txt
3. create .env and add your azure credentials
4. run python manage.py runserver , celery -A azure_api worker -l info and celery -A swarm worker -l info on 3 different terminals
5. then you can test/use the APIs by creating api keys from admin

Thanks
