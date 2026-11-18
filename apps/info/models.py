from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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

    CONDITIONING_PHASES = [
        ('foundation', 'Foundation / Rest'),
        ('workout', 'Roadwork & Exercise'),
        ('sparring', 'Sparring / Live Work'),
        ('peak', 'Peak / Fight Prep'),
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

    # Conditioning requirements
    conditioning_start_date = models.DateField(null=True, blank=True, help_text="Date the bird entered conditioning")
    target_weight_grams = models.PositiveIntegerField(null=True, blank=True, help_text="Target fight weight in grams")
    conditioning_program = models.CharField(max_length=100, blank=True, help_text="Conditioning regimen (e.g. Roadwork, Sparring)")
    conditioning_feed_plan = models.CharField(max_length=255, blank=True, help_text="Feed / diet plan during conditioning")
    conditioning_phase = models.CharField(
        max_length=20, choices=CONDITIONING_PHASES, default='foundation', blank=True,
        help_text="Current phase of the conditioning program",
    )
    conditioning_target_date = models.DateField(
        null=True, blank=True, help_text="Target derby or fight date"
    )
    conditioning_notes = models.TextField(blank=True, help_text="Notes for the current conditioning program")
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

    @property
    def conditioning_days(self):
        """Number of days since the bird entered conditioning."""
        if not self.conditioning_start_date:
            return 0
        return max((timezone.localdate() - self.conditioning_start_date).days, 0)

    @property
    def weight_to_target(self):
        """Grams still needed to reach the target weight (negative if over)."""
        if self.weight_grams is None or self.target_weight_grams is None:
            return None
        return self.target_weight_grams - self.weight_grams

    @property
    def conditioning_baseline_weight(self):
        """First weight recorded since conditioning started."""
        if not self.pk:
            return self.weight_grams
        logs = self.weight_logs.all()
        if self.conditioning_start_date:
            logs = logs.filter(date__gte=self.conditioning_start_date)
        first_log = logs.order_by('date', 'created_at').first()
        return first_log.weight_grams if first_log else self.weight_grams

    @property
    def conditioning_progress_pct(self):
        """Percent of the weight gap closed since the conditioning baseline."""
        baseline = self.conditioning_baseline_weight
        target = self.target_weight_grams
        current = self.weight_grams
        if baseline is None or target is None or current is None:
            return None
        if baseline == target:
            return 100 if current == target else 0
        progress = (current - baseline) / (target - baseline) * 100
        return max(0, min(100, round(progress)))


class ConditioningSession(models.Model):
    """One scheduled workout, rest day, or checkpoint in a conditioning plan."""

    PHASE_CHOICES = FlockMember.CONDITIONING_PHASES
    SESSION_TYPES = [
        ('weigh_in', 'Weigh-in'),
        ('roadwork', 'Roadwork'),
        ('sparring', 'Sparring'),
        ('feed_control', 'Feed control'),
        ('free_range', 'Free range'),
        ('cage_rest', 'Cage rest'),
        ('water_work', 'Water work'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
    ]

    bird = models.ForeignKey(
        FlockMember, on_delete=models.CASCADE, related_name='conditioning_sessions'
    )
    phase = models.CharField(max_length=20, choices=PHASE_CHOICES, default='foundation')
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='weigh_in')
    title = models.CharField(max_length=120)
    scheduled_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='planned')
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_date', 'created_at']
        indexes = [
            models.Index(fields=['bird', 'scheduled_date']),
            models.Index(fields=['bird', 'status']),
        ]

    def __str__(self):
        return f"{self.bird.tag_number} - {self.title} ({self.scheduled_date})"

    @property
    def is_overdue(self):
        return self.status == 'planned' and self.scheduled_date < timezone.localdate()


def conditioning_session_counts(user, today=None):
    """Return planned conditioning session counts for one user's flock."""
    today = today or timezone.localdate()
    planned = ConditioningSession.objects.filter(
        bird__user=user, bird__status='Conditioning', status='planned',
    )
    return {
        'overdue': planned.filter(scheduled_date__lt=today).count(),
        'due_today': planned.filter(scheduled_date=today).count(),
        'upcoming': planned.filter(
            scheduled_date__gt=today,
            scheduled_date__lte=today + timedelta(days=7),
        ).count(),
    }


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


class FinancialEntry(models.Model):
    TYPE_EXPENSE = 'expense'
    TYPE_INCOME = 'income'
    TYPE_CHOICES = [
        (TYPE_EXPENSE, 'Expense'),
        (TYPE_INCOME, 'Income'),
    ]

    EXPENSE_CATEGORIES = [
        ('Feed', 'Feed & Supplements'),
        ('Medicine', 'Medicine & Health'),
        ('Equipment', 'Equipment & Supplies'),
        ('Transport', 'Transport'),
        ('Entry Fee', 'Entry Fee'),
        ('Labor', 'Labor'),
        ('Utilities', 'Utilities'),
        ('Other', 'Other Expense'),
    ]
    INCOME_CATEGORIES = [
        ('Bird Sale', 'Bird Sale'),
        ('Prize Money', 'Prize Money'),
        ('Stud Fee', 'Stud Fee'),
        ('Other', 'Other Income'),
    ]
    CATEGORY_CHOICES = EXPENSE_CATEGORIES + INCOME_CATEGORIES

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='financial_entries')
    bird = models.ForeignKey(
        'FlockMember', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='financial_entries',
        help_text='Optional flock member related to this entry (e.g. bird sale, treatment cost, entry fee).'
    )
    entry_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_EXPENSE)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='Feed')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.CharField(max_length=200)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'entry_type']),
        ]

    def __str__(self):
        sign = '-' if self.entry_type == self.TYPE_EXPENSE else '+'
        return f"{sign}{self.amount} - {self.description}"


class FlockSale(models.Model):
    """A bird sold out of the flock, synced with the financial tracker."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flock_sales')
    bird = models.ForeignKey(
        FlockMember, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sales', help_text='Flock member that was sold.',
    )
    buyer_name = models.CharField(max_length=150)
    buyer_contact = models.CharField(
        max_length=100, blank=True, help_text='Phone, email, or address of the buyer',
    )
    sale_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True)
    financial_entry = models.OneToOneField(
        FinancialEntry, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='flock_sale', help_text='Income entry generated for this sale.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sale_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'sale_date']),
        ]

    def __str__(self):
        tag = self.bird.tag_number if self.bird_id else 'Unknown bird'
        return f'{tag} sold to {self.buyer_name} ({self.amount})'
