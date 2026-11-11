from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    farm_name = models.CharField(max_length=150, blank=True, default='')
    contact_number = models.CharField(max_length=30, blank=True, default='')
    location = models.CharField(max_length=200, blank=True, default='')
    association_id = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="FIGBA, NFGB, or local club membership ID",
    )
    bio = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.user.username} ({self.farm_name or 'No farm name'})"


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            UserProfile.objects.create(user=instance)
