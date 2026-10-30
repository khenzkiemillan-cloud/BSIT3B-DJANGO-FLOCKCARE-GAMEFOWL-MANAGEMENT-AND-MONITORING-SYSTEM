from django.db import models
from django.core.validators import MinValueValidator


class ChickenClassification(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'chicken_classifications'
        ordering = ['name']

    def __str__(self):
        return self.name


class Chicken(models.Model):
    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        SOLD = 'sold', 'Sold'
        DECEASED = 'deceased', 'Deceased'

    chicken_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=Gender.choices)
    hatch_date = models.DateField(null=True, blank=True)
    color = models.CharField(max_length=100, blank=True)
    weight = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    classification = models.ForeignKey(
        ChickenClassification,
        on_delete=models.PROTECT,
        related_name='chickens',
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        db_table = 'chickens'
        ordering = ['chicken_code']

    def __str__(self):
        return f'{self.chicken_code} - {self.name}'


class BreedingRecord(models.Model):
    male_chicken = models.ForeignKey(
        Chicken,
        on_delete=models.PROTECT,
        related_name='male_breeding_records',
    )
    female_chicken = models.ForeignKey(
        Chicken,
        on_delete=models.PROTECT,
        related_name='female_breeding_records',
    )
    breeding_date = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'breeding_records'
        ordering = ['-breeding_date']

    def __str__(self):
        return f'{self.male_chicken} × {self.female_chicken} ({self.breeding_date})'


class HealthRecord(models.Model):
    chicken = models.ForeignKey(
        Chicken,
        on_delete=models.PROTECT,
        related_name='health_records',
    )
    health_condition = models.CharField(max_length=255, blank=True)
    vaccination = models.CharField(max_length=255, blank=True)
    medication = models.CharField(max_length=255, blank=True)
    treatment = models.TextField(blank=True)
    checkup_date = models.DateField()

    class Meta:
        db_table = 'health_records'
        ordering = ['-checkup_date']

    def __str__(self):
        return f'{self.chicken} health record ({self.checkup_date})'


class FeedRecord(models.Model):
    chicken = models.ForeignKey(
        Chicken,
        on_delete=models.PROTECT,
        related_name='feed_records',
    )
    feed_type = models.CharField(max_length=100)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
    )
    feeding_date = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'feed_records'
        ordering = ['-feeding_date']

    def __str__(self):
        return f'{self.chicken} - {self.feed_type} ({self.feeding_date})'


class Supply(models.Model):
    class SupplyType(models.TextChoices):
        FEED = 'feed', 'Feed'
        MEDICINE = 'medicine', 'Medicine'
        MATERIAL = 'material', 'Other material'

    name = models.CharField(max_length=150)
    supply_type = models.CharField(max_length=20, choices=SupplyType.choices)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
    )
    unit = models.CharField(max_length=30)
    minimum_stock = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
    )
    expiration_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'supplies'
        ordering = ['name']

    def __str__(self):
        return self.name


class Expense(models.Model):
    expense_name = models.CharField(max_length=150)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    expense_date = models.DateField()
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'expenses'
        ordering = ['-expense_date']

    def __str__(self):
        return f'{self.expense_name} ({self.expense_date})'
