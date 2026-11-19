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
        ('Broodcock', 'Broodcock'),
        ('Broodhen', 'Broodhen'),
        ('Retired', 'Retired'),
        ('Sold', 'Sold'),
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

    # Weight tracking
    weight_grams = models.PositiveIntegerField(null=True, blank=True, help_text="Weight in grams")

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


class Medicine(models.Model):
    """An inventory item: medicine cabinet, feeds, equipment, or farm supplies."""

    ITEM_TYPE_CHOICES = [
        ('medicine', 'Medicine Cabinet'),
        ('feed', 'Feeds & Nutrition'),
        ('equipment', 'Equipment'),
        ('supply', 'Other Supplies'),
    ]

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
    item_type = models.CharField(
        max_length=20,
        choices=ITEM_TYPE_CHOICES,
        default='medicine',
        help_text='Inventory section: medicine, feed, equipment, or other supply.',
    )
    category = models.CharField(max_length=50, default='Other')
    unit = models.CharField(max_length=30, default='pcs')
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    low_stock_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expiration_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['user', 'item_type']),
            models.Index(fields=['user', 'expiration_date']),
        ]

    def __str__(self):
        return f"{self.name} ({self.stock_quantity} {self.unit})"

    CATEGORY_ICONS = {
        'Vaccine': 'fa-syringe',
        'Dewormer': 'fa-bug-slash',
        'Vitamin': 'fa-capsules',
        'Antibiotic': 'fa-pills',
        'Treatment': 'fa-kit-medical',
        'Other': 'fa-prescription-bottle-medical',
    }

    @property
    def type_display(self):
        return dict(self.ITEM_TYPE_CHOICES).get(self.item_type, 'Medicine')

    @property
    def category_icon(self):
        """Font Awesome icon that matches the cabinet category."""
        return self.CATEGORY_ICONS.get(self.category, 'fa-prescription-bottle-medical')

    @property
    def stock_status(self):
        """Return ``ok``, ``low`` or ``out`` for stock-level styling."""
        stock = self.stock_quantity or 0
        if stock <= 0:
            return 'out'
        if stock <= (self.low_stock_threshold or 0):
            return 'low'
        return 'ok'

    @property
    def stock_level_percent(self):
        """Fill level for the stock meter, scaled to 4x the alert threshold.

        The bar reaches full only when stock is at least four times the
        low-stock alert level, which keeps low supplies visually obvious.
        """
        stock = float(self.stock_quantity or 0)
        if stock <= 0:
            return 0
        threshold = float(self.low_stock_threshold or 0)
        scale = max(threshold * 4, stock, 1)
        return max(4, min(100, round(stock / scale * 100)))


# Model alias for clean domain naming
InventoryItem = Medicine


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
    medicine = models.ForeignKey(
        'Medicine', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='health_records',
        help_text='Cabinet medicine used for this treatment (optional).',
    )
    quantity_used = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, blank=True,
        help_text='Amount taken from the medicine cabinet stock.',
    )
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

    @property
    def total_clutches(self):
        return len(self.clutches.all())

    @property
    def total_eggs(self):
        return sum(clutch.eggs_collected for clutch in self.clutches.all())

    @property
    def total_fertile_eggs(self):
        return sum(clutch.fertile_eggs for clutch in self.clutches.all())

    @property
    def total_hatched(self):
        return sum(clutch.hatched_count for clutch in self.clutches.all())

    @property
    def fertility_rate(self):
        if self.total_eggs:
            return round((self.total_fertile_eggs / self.total_eggs) * 100, 1)
        return 0.0

    @property
    def hatchability_rate(self):
        if self.total_fertile_eggs:
            return round((self.total_hatched / self.total_fertile_eggs) * 100, 1)
        return 0.0


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
