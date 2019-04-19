# Tailored

The master branch represents all changes up to and including the day of the deadline, Wednesday 22 March 2019.

### Environment Requiments

Python 3.6 or later is required for the web application to run. Earlier 3.x versions will not work and will result in syntax errors.

##### Additional Packages

These packages can all be installed in a single command: pip install -r requirements.txt

- Django v1.11.20

Installation: pip install django

- django-registration-redux v2.5

Installation: pip install django-registration-redux

- django-cleanup v3.2.0

Installation: pip install django-cleanup

- Pillow v5.4.1

Installation: pip install pillow

- pytz v2018.9

Installation: pip install pytz

#### Additional technologies and libraries used:

- Jquery
- JavaScript
- Bootstrap4
- animate Css library
- Poppins font
- Select2 Css library
- Used an example template found [here](https://colorlib.com/preview/theme/karl/index.html).

### Running the Population Script

You need to make migrations first:
- python manage.py makemigrations

You then need to migrate:
- python manage.py migrate

Finally you run the population script:
- python populate_tailored.py



### Testing
-	python manage.py test tailored

## PythonAnywhere
Url :  [tailored.pythonanywhere.com](https://tailored.pythonanywhere.com)