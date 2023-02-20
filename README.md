# unfinite-backend
The actual backend that we'll use. Using Django to serve the React frontend as well as the API. 

# Installation:

Run the following to get an environment set-up:
`python -m pip install venv`
`python -m venv env`
On windows: `.\env\Scripts\activate`
Unix: `source /env/bin/activate`
`pip install -r requirements.txt`
Great. Now, to get the Django project going. You can immediately try the following. The first one creates a superuser account for you to use, and the second just starts up the webapp:
`cd unfinite-backend/`
`python manage.py createsuperuser`
`python manage.py runserver`
If one of those doesn't work, it's probably because there's no database. To fix this, just do:
`python manage.py migrate`
Now, you can try the createsuperuser and runserver commands again. It should work! It will be accessible at `http://localhost:8000`, locally.