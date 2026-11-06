from django.contrib import admin
from .models import Breed, FlockMember, HealthRecord

admin.site.register(Breed)
admin.site.register(FlockMember)
admin.site.register(HealthRecord)