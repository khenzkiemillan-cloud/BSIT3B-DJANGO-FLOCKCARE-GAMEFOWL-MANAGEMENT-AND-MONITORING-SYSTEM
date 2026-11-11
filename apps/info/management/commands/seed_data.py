from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.info.models import (
    Breed, FlockMember, Medicine, HealthRecord,
    FightRecord, WeightLog, BreedingPen, ClutchRecord
)
from apps.users.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds realistic gamefowl flock, medicine, health, breeding, and fight records.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Target username to seed. If omitted, seeds for all existing users or creates a default admin.'
        )

    def handle(self, *args, **options):
        today = timezone.localdate()

        # Ensure we have target users
        target_username = options.get('username')
        if target_username:
            users = User.objects.filter(username=target_username)
            if not users.exists():
                self.stderr.write(f"User '{target_username}' not found.")
                return
        else:
            users = User.objects.all()
            if not users.exists():
                self.stdout.write("No users found. Creating default admin account 'admin' / 'admin123456'...")
                u = User.objects.create_superuser('admin', 'admin@flockcare.ph', 'admin123456')
                users = [u]

        # 1. Breeds
        breed_names = [
            'Sweater 5K',
            'Yellow Legged Hatch',
            'Boston Roundhead',
            'Out & Out Kelso',
            'Albany',
            'Regular Grey',
            'Claret Old Master',
            'Radio',
        ]
        breeds = {}
        for name in breed_names:
            b, _ = Breed.objects.get_or_create(name=name)
            breeds[name] = b

        self.stdout.write(self.style.SUCCESS(f"Loaded {len(breeds)} gamefowl breeds."))

        # Seed data for each target user
        for user in users:
            self.stdout.write(f"\n--- Seeding records for user: {user.username} ---")

            # Update User Profile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            if user.username == 'glenn' or not profile.farm_name:
                profile.farm_name = 'Falcon Crest Gamefarm'
                profile.location = 'Lipa City, Batangas, Philippines'
                profile.contact_number = '+63 917 555 4321'
                profile.association_id = 'FIGBA-BAT-2026-088'
                profile.bio = 'Specializing in pure 5K Sweaters, Out & Out Kelsos, and Yellow Legged Hatches since 2017.'
                profile.save()
            elif user.username == 'justine09':
                profile.farm_name = 'Thunderbird Gamefarm'
                profile.location = 'San Fernando, Pampanga'
                profile.contact_number = '+63 920 888 1234'
                profile.association_id = 'RGBA-PAM-2026-104'
                profile.bio = 'Breeding championship bloodlines: Regular Greys, Bostons, and Albanies.'
                profile.save()

            # 2. Flock Members
            flock_configs = [
                {
                    'tag_number': 'SW-101',
                    'breed': breeds['Sweater 5K'],
                    'gender': 'Cock',
                    'status': 'Active',
                    'birth_date': today - timedelta(days=580),
                    'comb_type': 'Pea',
                    'leg_color': 'Yellow',
                    'color': 'Sweater Red / Orange Hackle',
                    'cage_number': 'Cord 01',
                    'weight_grams': 2150,
                    'sire': 'SW-FND-09',
                    'dam': 'SW-HEN-88',
                    'wins': 4,
                    'losses': 0,
                    'draws': 1,
                },
                {
                    'tag_number': 'YLH-202',
                    'breed': breeds['Yellow Legged Hatch'],
                    'gender': 'Cock',
                    'status': 'Conditioning',
                    'birth_date': today - timedelta(days=520),
                    'comb_type': 'Straight',
                    'leg_color': 'Yellow',
                    'color': 'Dark Mahogany / Black Breast',
                    'cage_number': 'Cord 05',
                    'weight_grams': 2200,
                    'sire': 'YLH-001',
                    'dam': 'YLH-HEN-02',
                    'wins': 3,
                    'losses': 1,
                    'draws': 0,
                },
                {
                    'tag_number': 'RH-303',
                    'breed': breeds['Boston Roundhead'],
                    'gender': 'Stag',
                    'status': 'Conditioning',
                    'birth_date': today - timedelta(days=320),
                    'comb_type': 'Pea',
                    'leg_color': 'White',
                    'color': 'Light Orange / Ginger',
                    'cage_number': 'Pen C-02',
                    'weight_grams': 2050,
                    'sire': 'RH-BULL',
                    'dam': 'RH-QUEEN',
                    'wins': 2,
                    'losses': 0,
                    'draws': 0,
                },
                {
                    'tag_number': 'KL-404',
                    'breed': breeds['Out & Out Kelso'],
                    'gender': 'Cock',
                    'status': 'Active',
                    'birth_date': today - timedelta(days=620),
                    'comb_type': 'Pea',
                    'leg_color': 'Yellow',
                    'color': 'High-station Golden Red',
                    'cage_number': 'Cord 11',
                    'weight_grams': 2100,
                    'sire': 'KL-ORIG',
                    'dam': 'KL-MTH',
                    'wins': 5,
                    'losses': 1,
                    'draws': 0,
                },
                {
                    'tag_number': 'ALB-505',
                    'breed': breeds['Albany'],
                    'gender': 'Cock',
                    'status': 'Active',
                    'birth_date': today - timedelta(days=490),
                    'comb_type': 'Straight',
                    'leg_color': 'White',
                    'color': 'Ginger Red',
                    'cage_number': 'Cord 08',
                    'weight_grams': 2250,
                    'sire': 'ALB-SIRE-1',
                    'dam': 'ALB-DAM-1',
                    'wins': 3,
                    'losses': 0,
                    'draws': 0,
                },
                {
                    'tag_number': 'GR-606',
                    'breed': breeds['Regular Grey'],
                    'gender': 'Stag',
                    'status': 'Conditioning',
                    'birth_date': today - timedelta(days=290),
                    'comb_type': 'Pea',
                    'leg_color': 'Lead',
                    'color': 'Silver Grey / Charcoal',
                    'cage_number': 'Pen A-01',
                    'weight_grams': 2080,
                    'sire': 'GR-GREY-01',
                    'dam': 'GR-GREY-02',
                    'wins': 1,
                    'losses': 0,
                    'draws': 0,
                },
                {
                    'tag_number': 'SW-HEN-01',
                    'breed': breeds['Sweater 5K'],
                    'gender': 'Hen',
                    'status': 'Broodhen',
                    'birth_date': today - timedelta(days=700),
                    'comb_type': 'Pea',
                    'leg_color': 'Yellow',
                    'color': 'Red Wheaten',
                    'cage_number': 'Breeding Pen 1',
                    'weight_grams': 1750,
                    'sire': 'SW-FOUNDATION',
                    'dam': 'SW-FOUNDATION-M',
                    'wins': 0,
                    'losses': 0,
                    'draws': 0,
                },
                {
                    'tag_number': 'YLH-HEN-02',
                    'breed': breeds['Yellow Legged Hatch'],
                    'gender': 'Hen',
                    'status': 'Broodhen',
                    'birth_date': today - timedelta(days=680),
                    'comb_type': 'Straight',
                    'leg_color': 'Yellow',
                    'color': 'Partridge Dark Red',
                    'cage_number': 'Breeding Pen 2',
                    'weight_grams': 1800,
                    'sire': 'YLH-SIRE-A',
                    'dam': 'YLH-DAM-A',
                    'wins': 0,
                    'losses': 0,
                    'draws': 0,
                },
                {
                    'tag_number': 'KL-HEN-03',
                    'breed': breeds['Out & Out Kelso'],
                    'gender': 'Hen',
                    'status': 'Broodhen',
                    'birth_date': today - timedelta(days=650),
                    'comb_type': 'Pea',
                    'leg_color': 'Yellow',
                    'color': 'Wheat Golden',
                    'cage_number': 'Breeding Pen 3',
                    'weight_grams': 1720,
                    'sire': 'KL-CHAMP-01',
                    'dam': 'KL-DAM-B',
                    'wins': 0,
                    'losses': 0,
                    'draws': 0,
                },
                {
                    'tag_number': 'SW-PUL-04',
                    'breed': breeds['Sweater 5K'],
                    'gender': 'Pullet',
                    'status': 'Active',
                    'birth_date': today - timedelta(days=220),
                    'comb_type': 'Pea',
                    'leg_color': 'Yellow',
                    'color': 'Light Red',
                    'cage_number': 'Grow-out Pen 4',
                    'weight_grams': 1600,
                    'sire': 'SW-101',
                    'dam': 'SW-HEN-01',
                    'wins': 0,
                    'losses': 0,
                    'draws': 0,
                },
                {
                    'tag_number': 'RAD-707',
                    'breed': breeds['Radio'],
                    'gender': 'Stag',
                    'status': 'Active',
                    'birth_date': today - timedelta(days=310),
                    'comb_type': 'Pea',
                    'leg_color': 'Yellow',
                    'color': 'Red / Black Spangle',
                    'cage_number': 'Pen B-06',
                    'weight_grams': 2120,
                    'sire': 'RAD-ORIG',
                    'dam': 'RAD-DAM-1',
                    'wins': 2,
                    'losses': 1,
                    'draws': 0,
                },
                {
                    'tag_number': 'RET-999',
                    'breed': breeds['Claret Old Master'],
                    'gender': 'Cock',
                    'status': 'Retired',
                    'birth_date': today - timedelta(days=1100),
                    'comb_type': 'Straight',
                    'leg_color': 'White',
                    'color': 'Deep Wine Claret',
                    'cage_number': 'Retirement Pen',
                    'weight_grams': 2300,
                    'sire': 'CL-LEGEND',
                    'dam': 'CL-ROYAL',
                    'wins': 7,
                    'losses': 2,
                    'draws': 0,
                },
            ]

            saved_birds = {}
            for cfg in flock_configs:
                tag = cfg['tag_number']
                bird, _ = FlockMember.objects.update_or_create(
                    user=user,
                    tag_number=tag,
                    defaults=cfg
                )
                saved_birds[tag] = bird

            self.stdout.write(self.style.SUCCESS(f"  -> Created/Updated {len(saved_birds)} flock members."))

            # 3. Sanctioned Fight Records
            sw_101 = saved_birds.get('SW-101')
            if sw_101:
                fights_sw = [
                    {
                        'event_name': 'Derby Fiesta Invitational (San Juan Arena)',
                        'fight_date': today - timedelta(days=120),
                        'weight_grams': 2145,
                        'opponent': 'Thunder Gamefarm / Stag #44',
                        'gaff_type': '2.5 inch High-blade Slasher',
                        'result': 'win',
                        'duration_seconds': 38,
                        'video_url': 'https://youtube.com',
                        'notes': 'Fast off the cords, delivered early body cut in air exchange.',
                    },
                    {
                        'event_name': '4-Cock Derby (Pasay Cockpit Stadium)',
                        'fight_date': today - timedelta(days=85),
                        'weight_grams': 2150,
                        'opponent': 'Black Mamba Aviary',
                        'gaff_type': '2.5 inch Slasher',
                        'result': 'win',
                        'duration_seconds': 52,
                        'video_url': 'https://youtube.com',
                        'notes': 'Excellent counter-cutting on the ropes.',
                    },
                    {
                        'event_name': 'National Cocks Championship',
                        'fight_date': today - timedelta(days=45),
                        'weight_grams': 2155,
                        'opponent': 'Golden Wing Farm / Tag-89',
                        'gaff_type': '2.5 inch Slasher',
                        'result': 'win',
                        'duration_seconds': 24,
                        'video_url': 'https://youtube.com',
                        'notes': 'Lightning shuffle roundhead cross opponent down in one strike.',
                    },
                    {
                        'event_name': 'Mid-Season 5-Cock Masters',
                        'fight_date': today - timedelta(days=14),
                        'weight_grams': 2160,
                        'opponent': 'Blue Dragon Gamefarm',
                        'gaff_type': '2.5 inch Slasher',
                        'result': 'draw',
                        'duration_seconds': 120,
                        'video_url': 'https://youtube.com',
                        'notes': 'Both cocks fought tenaciously to time call (Tinabla).',
                    },
                ]
                for f_cfg in fights_sw:
                    FightRecord.objects.get_or_create(bird=sw_101, event_name=f_cfg['event_name'], defaults=f_cfg)

            kl_404 = saved_birds.get('KL-404')
            if kl_404:
                fights_kl = [
                    {
                        'event_name': 'World Slasher Cup Elimination',
                        'fight_date': today - timedelta(days=140),
                        'weight_grams': 2100,
                        'opponent': 'Firebird Outcross',
                        'gaff_type': '2.5 inch Slasher',
                        'result': 'win',
                        'duration_seconds': 41,
                        'notes': 'Superb lateral movement and timing.',
                    },
                    {
                        'event_name': 'Lipa Mayor\'s Invitational Cup',
                        'fight_date': today - timedelta(days=95),
                        'weight_grams': 2095,
                        'opponent': 'Red Bull Aviary',
                        'gaff_type': '2.5 inch Slasher',
                        'result': 'win',
                        'duration_seconds': 33,
                        'notes': 'Strong bottom fighting and solid gameness.',
                    },
                    {
                        'event_name': 'Luzon 7-Cock Championship',
                        'fight_date': today - timedelta(days=40),
                        'weight_grams': 2120,
                        'opponent': 'Silver Fox Gamefarm',
                        'gaff_type': '2.5 inch Slasher',
                        'result': 'loss',
                        'duration_seconds': 74,
                        'notes': 'Injured left wing early, fought game until the end.',
                    },
                ]
                for f_cfg in fights_kl:
                    FightRecord.objects.get_or_create(bird=kl_404, event_name=f_cfg['event_name'], defaults=f_cfg)

            ylh_202 = saved_birds.get('YLH-202')
            if ylh_202:
                FightRecord.objects.get_or_create(
                    bird=ylh_202,
                    event_name='Pre-Season 3-Stag Classic',
                    defaults={
                        'fight_date': today - timedelta(days=35),
                        'weight_grams': 2190,
                        'opponent': 'Delta Gamefarm',
                        'gaff_type': '2.5 inch Slasher',
                        'result': 'win',
                        'duration_seconds': 44,
                        'notes': 'Power puncher, broke breastplate cleanly.',
                    }
                )

            # 4. Daily Conditioning Weight Logs (Last 7 days)
            cond_birds = [saved_birds.get('YLH-202'), saved_birds.get('RH-303'), saved_birds.get('GR-606')]
            for bird in cond_birds:
                if not bird:
                    continue
                base_w = bird.weight_grams or 2100
                for day_offset in range(7, 0, -1):
                    log_date = today - timedelta(days=day_offset)
                    morning_w = base_w - (day_offset * 10)
                    evening_w = morning_w + 60

                    WeightLog.objects.get_or_create(
                        bird=bird,
                        date=log_date,
                        time_of_day='morning',
                        defaults={'weight_grams': morning_w, 'notes': 'Empty crop moisture drop normal'}
                    )
                    WeightLog.objects.get_or_create(
                        bird=bird,
                        date=log_date,
                        time_of_day='evening',
                        defaults={'weight_grams': evening_w, 'notes': 'Post conditioning grain mix 40g'}
                    )

            # 5. Medicine Cabinet Inventory
            medicines_data = [
                {
                    'name': 'Newcastle Disease Vaccine (LaSota Strain)',
                    'category': 'Vaccine',
                    'unit': 'ml',
                    'stock_quantity': Decimal('250.00'),
                    'low_stock_threshold': Decimal('50.00'),
                    'expiration_date': today + timedelta(days=210),
                    'notes': 'Administer via eye drop / nasal. Store in refrigerator (2-8°C).',
                },
                {
                    'name': 'Fowl Pox Vaccine with Diluent',
                    'category': 'Vaccine',
                    'unit': 'doses',
                    'stock_quantity': Decimal('150.00'),
                    'low_stock_threshold': Decimal('30.00'),
                    'expiration_date': today + timedelta(days=270),
                    'notes': 'Wing web puncture method for 8-12 week stags/pullets.',
                },
                {
                    'name': 'Ivermectin 1% Injectable Solution',
                    'category': 'Dewormer',
                    'unit': 'ml',
                    'stock_quantity': Decimal('35.00'),
                    'low_stock_threshold': Decimal('10.00'),
                    'expiration_date': today + timedelta(days=365),
                    'notes': 'Effective against roundworms, mites, and lice (0.1ml SQ).',
                },
                {
                    'name': 'Albendazole Oral Suspension (Dewormer)',
                    'category': 'Dewormer',
                    'unit': 'ml',
                    'stock_quantity': Decimal('8.00'),  # LOW STOCK
                    'low_stock_threshold': Decimal('15.00'),
                    'expiration_date': today + timedelta(days=120),
                    'notes': 'Low stock! Need 2 more bottles for next herd deworming schedule.',
                },
                {
                    'name': 'Belamyl B-Complex + Liver Extract (B12)',
                    'category': 'Vitamin',
                    'unit': 'ml',
                    'stock_quantity': Decimal('75.00'),
                    'low_stock_threshold': Decimal('20.00'),
                    'expiration_date': today + timedelta(days=380),
                    'notes': 'For muscle tone, red blood cell production, and high stamina during keep.',
                },
                {
                    'name': 'Enrofloxacin 10% Oral Solution',
                    'category': 'Antibiotic',
                    'unit': 'ml',
                    'stock_quantity': Decimal('4.50'),  # LOW STOCK & EXPIRING SOON!
                    'low_stock_threshold': Decimal('10.00'),
                    'expiration_date': today + timedelta(days=18),
                    'notes': 'Expiring soon! Replace immediately for CRD and coryza treatments.',
                },
                {
                    'name': 'Amoxicillin Trihydrate 20% Water Soluble Powder',
                    'category': 'Antibiotic',
                    'unit': 'grams',
                    'stock_quantity': Decimal('80.00'),
                    'low_stock_threshold': Decimal('20.00'),
                    'expiration_date': today + timedelta(days=300),
                    'notes': 'Broad spectrum antibiotic for flock water medication.',
                },
                {
                    'name': 'Reload Plus Oral Energy Drops',
                    'category': 'Vitamin',
                    'unit': 'ml',
                    'stock_quantity': Decimal('28.00'),
                    'low_stock_threshold': Decimal('5.00'),
                    'expiration_date': today + timedelta(days=320),
                    'notes': 'Quick energy and anti-stress booster right before sparring and fighting.',
                },
                {
                    'name': 'Terramycin Aerosol Wound Spray (Gentian Violet)',
                    'category': 'Treatment',
                    'unit': 'ml',
                    'stock_quantity': Decimal('180.00'),
                    'low_stock_threshold': Decimal('40.00'),
                    'expiration_date': today + timedelta(days=450),
                    'notes': 'First aid antiseptic spray for post-sparring wounds.',
                },
                {
                    'name': 'Ketoprofen Anti-inflammatory Solution',
                    'category': 'Treatment',
                    'unit': 'ml',
                    'stock_quantity': Decimal('30.00'),
                    'low_stock_threshold': Decimal('10.00'),
                    'expiration_date': today + timedelta(days=220),
                    'notes': 'Pain relief and swelling reduction after intensive workouts.',
                },
            ]

            for m_cfg in medicines_data:
                Medicine.objects.update_or_create(
                    user=user,
                    name=m_cfg['name'],
                    defaults=m_cfg
                )

            self.stdout.write(self.style.SUCCESS(f"  -> Created/Updated {len(medicines_data)} medicine cabinet items."))

            # 6. Health & Care Schedule Records
            health_records_data = [
                {
                    'bird': saved_birds.get('YLH-202'),
                    'record_type': 'Vaccination',
                    'title': 'Newcastle B1/LaSota Annual Booster',
                    'date_administered': today - timedelta(days=60),
                    'next_due_date': today + timedelta(days=8),  # Upcoming soon
                    'notes': 'Annual booster due next week before derby competition.',
                },
                {
                    'bird': saved_birds.get('RH-303'),
                    'record_type': 'Deworming',
                    'title': 'Ivermectin Routine Deworming',
                    'date_administered': today - timedelta(days=30),
                    'next_due_date': today + timedelta(days=15),  # Upcoming
                    'notes': 'Secondary deworming cycle to eradicate roundworms.',
                },
                {
                    'bird': saved_birds.get('GR-606'),
                    'record_type': 'Vitamin',
                    'title': 'Belamyl B-Complex 0.5ml Injection',
                    'date_administered': today - timedelta(days=7),
                    'next_due_date': today + timedelta(days=3),  # Due in 3 days
                    'notes': 'Conditioning supplement on breast muscle.',
                },
                {
                    'bird': saved_birds.get('SW-101'),
                    'record_type': 'Vaccination',
                    'title': 'Fowl Cholera Injection',
                    'date_administered': today - timedelta(days=120),
                    'next_due_date': today - timedelta(days=5),  # OVERDUE!
                    'notes': 'Overdue cholera booster — vaccinate immediately!',
                },
                {
                    'bird': saved_birds.get('KL-404'),
                    'record_type': 'Treatment',
                    'title': 'Left Wing Muscle Recovery Massage & Liniment',
                    'date_administered': today - timedelta(days=10),
                    'next_due_date': today - timedelta(days=2),  # OVERDUE!
                    'notes': 'Post-fight treatment follow-up overdue.',
                },
                {
                    'bird': saved_birds.get('ALB-505'),
                    'record_type': 'Vitamin',
                    'title': 'Multi-Vitamin Soluble Water Booster',
                    'date_administered': today - timedelta(days=14),
                    'next_due_date': today + timedelta(days=21),
                    'notes': 'Electrolytes and amino acids maintenance.',
                },
            ]

            for h_cfg in health_records_data:
                if h_cfg['bird']:
                    HealthRecord.objects.get_or_create(
                        bird=h_cfg['bird'],
                        title=h_cfg['title'],
                        defaults=h_cfg
                    )

            self.stdout.write(self.style.SUCCESS(f"  -> Created/Updated {len(health_records_data)} health schedule items."))

            # 7. Breeding Pens & Clutches
            sw_cock = saved_birds.get('SW-101')
            sw_hen = saved_birds.get('SW-HEN-01')
            if sw_cock and sw_hen:
                pen1, _ = BreedingPen.objects.get_or_create(
                    user=user,
                    pen_number='Pen 101',
                    defaults={
                        'sire': sw_cock,
                        'dam': sw_hen,
                        'date_paired': today - timedelta(days=75),
                        'status': 'active',
                        'notes': 'Pairing pure 5K Sweater for 2027 bullstag derby candidates.',
                    }
                )
                ClutchRecord.objects.get_or_create(
                    pen=pen1,
                    clutch_number='C-01',
                    defaults={
                        'date_started': today - timedelta(days=60),
                        'eggs_collected': 12,
                        'fertile_eggs': 11,
                        'hatched_count': 10,
                        'hatch_date': today - timedelta(days=39),
                        'notes': 'Wing banded 101-110. Exceptionally high vigor and clean hatches.',
                    }
                )
                ClutchRecord.objects.get_or_create(
                    pen=pen1,
                    clutch_number='C-02',
                    defaults={
                        'date_started': today - timedelta(days=25),
                        'eggs_collected': 10,
                        'fertile_eggs': 9,
                        'hatched_count': 8,
                        'hatch_date': today - timedelta(days=4),
                        'notes': 'Incubated in digital automatic setter.',
                    }
                )

            ylh_cock = saved_birds.get('YLH-202')
            ylh_hen = saved_birds.get('YLH-HEN-02')
            if ylh_cock and ylh_hen:
                pen2, _ = BreedingPen.objects.get_or_create(
                    user=user,
                    pen_number='Pen 102',
                    defaults={
                        'sire': ylh_cock,
                        'dam': ylh_hen,
                        'date_paired': today - timedelta(days=50),
                        'status': 'active',
                        'notes': 'Pure Yellow Legged Hatch speed cross.',
                    }
                )
                ClutchRecord.objects.get_or_create(
                    pen=pen2,
                    clutch_number='C-01',
                    defaults={
                        'date_started': today - timedelta(days=40),
                        'eggs_collected': 14,
                        'fertile_eggs': 13,
                        'hatched_count': 12,
                        'hatch_date': today - timedelta(days=19),
                        'notes': '12 healthy chicks banded with yellow leg markers.',
                    }
                )

            kl_cock = saved_birds.get('KL-404')
            kl_hen = saved_birds.get('KL-HEN-03')
            if kl_cock and kl_hen:
                pen3, _ = BreedingPen.objects.get_or_create(
                    user=user,
                    pen_number='Pen 103',
                    defaults={
                        'sire': kl_cock,
                        'dam': kl_hen,
                        'date_paired': today - timedelta(days=90),
                        'date_separated': today - timedelta(days=20),
                        'status': 'resting',
                        'notes': 'Hen resting for molting period.',
                    }
                )
                ClutchRecord.objects.get_or_create(
                    pen=pen3,
                    clutch_number='C-01',
                    defaults={
                        'date_started': today - timedelta(days=80),
                        'eggs_collected': 8,
                        'fertile_eggs': 8,
                        'hatched_count': 7,
                        'hatch_date': today - timedelta(days=59),
                        'notes': '7 pure Kelso chicks thriving in nursery brooder.',
                    }
                )

            self.stdout.write(self.style.SUCCESS(f"  -> Created/Updated breeding pens and clutches."))

        self.stdout.write(self.style.SUCCESS("\n[SUCCESS] Seed data generated successfully for all flock categories!"))
