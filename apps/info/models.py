from django.db import models
from django.contrib.auth.models import User


class Breed(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

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

    GENDER_CHOICES = [
        ('Stag', 'Stag'),
        ('Cock', 'Cock'),
        ('Pullet', 'Pullet'),
        ('Hen', 'Hen'),
    ]

    COMB_CHOICES = [
        ('Pea', 'Pea Comb'),
        ('Straight', 'Straight / Single Comb'),
        ('Strawberry', 'Strawberry Comb'),
        ('Walnut', 'Walnut Comb'),
        ('Cushion', 'Cushion Comb'),
        ('Other', 'Other'),
    ]

    LEG_COLOR_CHOICES = [
        ('Yellow', 'Yellow'),
        ('Green', 'Green'),
        ('White', 'White'),
        ('Blue/Slate', 'Blue / Slate'),
        ('Lead', 'Lead / Dark'),
        ('Other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flock_members')
    tag_number = models.CharField(max_length=50)
    breed = models.ForeignKey(Breed, on_delete=models.SET_NULL, null=True, blank=True, related_name='birds')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    birth_date = models.DateField(null=True, blank=True)
    sire = models.CharField(max_length=50, blank=True, null=True)
    dam = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')

    # Physical characteristics
    comb_type = models.CharField(max_length=20, choices=COMB_CHOICES, default='Pea', blank=True)
    leg_color = models.CharField(max_length=20, choices=LEG_COLOR_CHOICES, default='Yellow', blank=True)
    color = models.CharField(max_length=100, blank=True, help_text="Plumage / feather color")
    cage_number = models.CharField(max_length=50, blank=True, help_text="Pen, cord, or coop identifier")
    image = models.FileField(upload_to='birds/', blank=True, null=True, help_text="Photo of bird")

    # Performance & Weight
    weight_grams = models.PositiveIntegerField(null=True, blank=True, help_text="Weight in grams")
    wins = models.PositiveIntegerField(default=0, blank=True)
    losses = models.PositiveIntegerField(default=0, blank=True)
    draws = models.PositiveIntegerField(default=0, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'tag_number'], name='unique_user_tag_number')
        ]
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'tag_number']),
        ]

    def __str__(self):
        return f"{self.tag_number} - {self.gender} ({self.status})"

    @property
    def total_fights(self):
        return self.wins + self.losses + self.draws

    @property
    def win_rate(self):
        if self.total_fights:
            return round((self.wins / self.total_fights) * 100)
        return 0


class Medicine(models.Model):
    CATEGORY_CHOICES = [
        ('Vaccine', 'Vaccine'),
        ('Dewormer', 'Dewormer'),
        ('Vitamin', 'Vitamin / Supplement'),
        ('Antibiotic', 'Antibiotic'),
        ('Treatment', 'Treatment / First aid'),
        ('Other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medicines')
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Vaccine')
    unit = models.CharField(max_length=20, default='ml')
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    low_stock_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expiration_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['user', 'expiration_date']),
        ]

    def __str__(self):
        return f"{self.name} ({self.stock_quantity} {self.unit})"


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

    class Meta:
        ordering = ['-date_administered', '-created_at']
        indexes = [
            models.Index(fields=['bird', 'next_due_date']),
        ]

    def __str__(self):
        return f"{self.bird.tag_number} - {self.title}"


class FightRecord(models.Model):
    RESULT_CHOICES = [
        ('win', 'Win'),
        ('loss', 'Loss'),
        ('draw', 'Draw / Tinabla'),
        ('cancelled', 'Cancelled'),
    ]

    bird = models.ForeignKey(FlockMember, on_delete=models.CASCADE, related_name='fight_records')
    event_name = models.CharField(max_length=150, help_text="Derby, Hackfight, or Event name")
    fight_date = models.DateField()
    weight_grams = models.PositiveIntegerField(null=True, blank=True, help_text="Weight at fight time in grams")
    opponent = models.CharField(max_length=150, blank=True, help_text="Opponent tag or farm name")
    gaff_type = models.CharField(max_length=100, blank=True, help_text="Slasher knife specs")
    result = models.CharField(max_length=10, choices=RESULT_CHOICES)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in seconds")
    video_url = models.URLField(blank=True, help_text="Link to fight video / recording")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fight_date', '-created_at']

    def __str__(self):
        return f"{self.bird.tag_number} - {self.event_name} ({self.get_result_display()})"


class WeightLog(models.Model):
    TIME_OF_DAY = [
        ('morning', 'Morning (Empty crop)'),
        ('evening', 'Evening (After feeding)'),
    ]

    bird = models.ForeignKey(FlockMember, on_delete=models.CASCADE, related_name='weight_logs')
    date = models.DateField()
    time_of_day = models.CharField(max_length=10, choices=TIME_OF_DAY, default='morning')
    weight_grams = models.PositiveIntegerField()
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.bird.tag_number} - {self.weight_grams}g on {self.date}"


class BreedingPen(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active Pairing'),
        ('resting', 'Resting'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='breeding_pens')
    pen_number = models.CharField(max_length=50)
    sire = models.ForeignKey(FlockMember, on_delete=models.CASCADE, related_name='sire_pens')
    dam = models.ForeignKey(FlockMember, on_delete=models.CASCADE, related_name='dam_pens')
    date_paired = models.DateField()
    date_separated = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_paired', '-created_at']

    def __str__(self):
        return f"Pen {self.pen_number}: {self.sire.tag_number} x {self.dam.tag_number}"


class ClutchRecord(models.Model):
    pen = models.ForeignKey(BreedingPen, on_delete=models.CASCADE, related_name='clutches')
    clutch_number = models.CharField(max_length=50, blank=True)
    date_started = models.DateField()
    eggs_collected = models.PositiveIntegerField(default=0)
    fertile_eggs = models.PositiveIntegerField(default=0)
    hatched_count = models.PositiveIntegerField(default=0)
    hatch_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_started', '-created_at']

    @property
    def hatchability_rate(self):
        if self.fertile_eggs > 0:
            return round((self.hatched_count / self.fertile_eggs) * 100, 1)
        return 0.0
