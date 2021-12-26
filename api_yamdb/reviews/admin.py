import inspect

from django.contrib import admin
from reviews import models

for name, obj in inspect.getmembers(models, inspect.isclass):
    if vars(obj)['__module__'] == 'reviews.models':
        admin.site.register(obj)
