from django.db import models
from django.contrib.auth.models import User

class Breed(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class FlockMember(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Conditioning', 'Conditioning'),
        ('Broodcock', 'Broodcock'),
        ('Broodhen', 'Broodhen'),
        ('Retired', 'Retired'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tag_number = models.CharField(max_length=50, unique=True)
    breed = models.ForeignKey(Breed, on_delete=models.SET_NULL, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Stag', 'Stag'), ('Cock', 'Cock'), ('Pullet', 'Pullet'), ('Hen', 'Hen')])
    birth_date = models.DateField(null=True, blank=True)
    sire = models.CharField(max_length=50, blank=True, null=True)
    dam = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    
    # New Performance & Weight fields
    weight_grams = models.PositiveIntegerField(null=True, blank=True, help_text="Weight in grams")
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tag_number} - {self.gender}"

class HealthRecord(models.Model):
    RECORD_TYPES = [
        ('Vaccination', 'Vaccination'),
        ('Deworming', 'Deworming'),
        ('Vitamin', 'Vitamin/Supplement'),
        ('Treatment', 'Injury/Illness Treatment'),
    ]

    bird = models.ForeignKey(FlockMember, on_delete=models.CASCADE, related_name='health_records')
    record_type = models.CharField(max_length=20, choices=RECORD_TYPES)
    title = models.CharField(max_length=100)
    date_administered = models.DateField()
    next_due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bird.tag_number} - {self.title}"