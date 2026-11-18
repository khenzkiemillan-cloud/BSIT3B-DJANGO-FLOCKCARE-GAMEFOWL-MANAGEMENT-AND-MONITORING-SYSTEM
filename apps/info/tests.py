from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Breed, FlockMember, HealthRecord, Medicine, WeightLog, ConditioningSession,
    FinancialEntry, FlockSale,
)


class FlockTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='flock-owner',
            password='test-password',
        )
        self.client.force_login(self.user)
        self.breed = Breed.objects.create(name='Kelso')
        self.bird = FlockMember.objects.create(
            user=self.user,
            tag_number='K-001',
            breed=self.breed,
            gender='Cock',
            status='Active',
            wins=3,
            losses=1,
        )


class DashboardTests(FlockTestCase):
    def test_dashboard_shows_live_flock_statistics(self):
        HealthRecord.objects.create(
            bird=self.bird,
            record_type='Vaccination',
            title='Newcastle booster',
            date_administered=timezone.localdate(),
            next_due_date=timezone.localdate() + timedelta(days=7),
        )

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertEqual(response.context['total_birds'], 1)
        self.assertEqual(response.context['active_birds'], 1)
        self.assertEqual(response.context['total_wins'], 3)
        self.assertEqual(response.context['total_losses'], 1)
        self.assertContains(response, 'K-001')
        self.assertContains(response, 'Newcastle booster')
        self.assertContains(response, reverse('info:info_list'))

    def test_dashboard_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_dashboard_includes_draws_in_fight_totals(self):
        self.bird.draws = 2
        self.bird.save(update_fields=['draws'])

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.context['total_draws'], 2)
        self.assertEqual(response.context['total_fights'], 6)
        self.assertEqual(response.context['win_rate'], 50)
        self.assertContains(response, 'Draws')

    def test_dashboard_surfaces_overdue_conditioning_sessions(self):
        self.bird.status = 'Conditioning'
        self.bird.save(update_fields=['status'])
        ConditioningSession.objects.create(
            bird=self.bird,
            title='Missed roadwork',
            scheduled_date=timezone.localdate() - timedelta(days=1),
        )

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.context['conditioning_overdue_sessions'], 1)
        self.assertContains(response, 'session overdue')


class FlockMemberPageTests(FlockTestCase):
    def test_info_list_renders_members_and_actions(self):
        response = self.client.get(reverse('info:info_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'info/info_list.html')
        self.assertContains(response, 'K-001')
        self.assertContains(response, 'Kelso')
        self.assertContains(response, reverse('info:info_save_ajax'))

    def test_info_list_search_filters_members(self):
        FlockMember.objects.create(
            user=self.user,
            tag_number='H-002',
            gender='Hen',
            status='Conditioning',
        )

        response = self.client.get(reverse('info:info_list'), {'q': 'Kelso'})

        self.assertContains(response, 'K-001')
        self.assertNotContains(response, 'H-002')

    def test_info_list_page_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse('info:info_list'))

        self.assertEqual(response.status_code, 302)


class FlockMemberAjaxTests(FlockTestCase):
    def test_create_member(self):
        response = self.client.post(reverse('info:info_save_ajax'), {
            'tag_number': 'K-003',
            'breed': self.breed.pk,
            'gender': 'Stag',
            'status': 'Conditioning',
            'birth_date': '2026-01-15',
            'weight_grams': '1850',
            'wins': '2',
            'losses': '0',
            'sire': 'K-001',
            'dam': '',
            'conditioning_start_date': '2026-02-01',
            'target_weight_grams': '2200',
            'conditioning_program': 'Roadwork',
            'conditioning_feed_plan': 'High-protein mix, twice daily',
        })

        self.assertEqual(response.status_code, 200)
        member = FlockMember.objects.get(user=self.user, tag_number='K-003')
        self.assertEqual(member.breed, self.breed)
        self.assertEqual(member.weight_grams, 1850)
        self.assertEqual(member.wins, 2)
        self.assertEqual(member.target_weight_grams, 2200)
        self.assertEqual(member.conditioning_program, 'Roadwork')

    def test_custom_feed_plan_is_saved_from_member_form(self):
        response = self.client.post(reverse('info:info_save_ajax'), {
            'tag_number': 'K-007',
            'gender': 'Stag',
            'status': 'Conditioning',
            'wins': '0',
            'losses': '0',
            'draws': '0',
            'conditioning_start_date': '2026-02-01',
            'target_weight_grams': '2200',
            'conditioning_program': 'Roadwork',
            'conditioning_feed_plan': 'Custom',
            'conditioning_feed_plan_custom': 'Farm mix with coconut oil',
        })

        self.assertEqual(response.status_code, 200)
        member = FlockMember.objects.get(user=self.user, tag_number='K-007')
        self.assertEqual(member.conditioning_feed_plan, 'Farm mix with coconut oil')

    def test_custom_feed_plan_requires_a_name(self):
        response = self.client.post(reverse('info:info_save_ajax'), {
            'tag_number': 'K-008',
            'gender': 'Stag',
            'status': 'Conditioning',
            'wins': '0',
            'losses': '0',
            'draws': '0',
            'conditioning_start_date': '2026-02-01',
            'target_weight_grams': '2200',
            'conditioning_program': 'Roadwork',
            'conditioning_feed_plan': 'Custom',
            'conditioning_feed_plan_custom': '',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('conditioning_feed_plan_custom', response.json()['errors'])
        self.assertFalse(FlockMember.objects.filter(user=self.user, tag_number='K-008').exists())

    def test_conditioning_status_requires_conditioning_details(self):
        response = self.client.post(reverse('info:info_save_ajax'), {
            'tag_number': 'K-005',
            'gender': 'Stag',
            'status': 'Conditioning',
            'wins': '0',
            'losses': '0',
            'draws': '0',
        })

        self.assertEqual(response.status_code, 400)
        errors = response.json()['errors']
        for field_name in (
            'conditioning_start_date',
            'target_weight_grams',
            'conditioning_program',
            'conditioning_feed_plan',
        ):
            self.assertIn(field_name, errors)
        self.assertFalse(FlockMember.objects.filter(user=self.user, tag_number='K-005').exists())

    def test_active_status_does_not_require_conditioning_details(self):
        response = self.client.post(reverse('info:info_save_ajax'), {
            'tag_number': 'K-006',
            'gender': 'Hen',
            'status': 'Active',
            'wins': '0',
            'losses': '0',
            'draws': '0',
        })

        self.assertEqual(response.status_code, 200)
        member = FlockMember.objects.get(user=self.user, tag_number='K-006')
        self.assertIsNone(member.conditioning_start_date)
        self.assertIsNone(member.target_weight_grams)
        self.assertEqual(member.conditioning_program, '')

    def test_duplicate_tag_number_is_rejected(self):
        response = self.client.post(reverse('info:info_save_ajax'), {
            'tag_number': 'k-001',
            'gender': 'Cock',
            'status': 'Active',
            'wins': '0',
            'losses': '0',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('tag number', response.json()['error'].lower())

    def test_update_member(self):
        response = self.client.post(reverse('info:info_save_ajax'), {
            'id': self.bird.pk,
            'tag_number': 'K-001',
            'breed': self.breed.pk,
            'gender': 'Cock',
            'status': 'Retired',
            'wins': '4',
            'losses': '2',
            'sire': '',
            'dam': '',
        })

        self.assertEqual(response.status_code, 200)
        self.bird.refresh_from_db()
        self.assertEqual(self.bird.status, 'Retired')
        self.assertEqual(self.bird.wins, 4)

    def test_cannot_edit_another_users_member(self):
        other_user = get_user_model().objects.create_user(
            username='other-owner',
            password='test-password',
        )
        other_bird = FlockMember.objects.create(
            user=other_user,
            tag_number='X-999',
            gender='Hen',
            status='Active',
        )

        response = self.client.post(reverse('info:info_save_ajax'), {
            'id': other_bird.pk,
            'tag_number': 'X-999',
            'gender': 'Hen',
            'status': 'Retired',
            'wins': '0',
            'losses': '0',
        })

        self.assertEqual(response.status_code, 404)
        other_bird.refresh_from_db()
        self.assertEqual(other_bird.status, 'Active')

    def test_delete_member(self):
        response = self.client.post(reverse('info:info_delete_ajax', args=[self.bird.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(FlockMember.objects.filter(pk=self.bird.pk).exists())

    def test_create_member_with_new_breed(self):
        response = self.client.post(reverse('info:info_save_ajax'), {
            'tag_number': 'K-004',
            'new_breed': 'Sweater',
            'gender': 'Hen',
            'status': 'Active',
            'wins': '0',
            'losses': '0',
        })

        self.assertEqual(response.status_code, 200)
        member = FlockMember.objects.get(user=self.user, tag_number='K-004')
        self.assertEqual(member.breed.name, 'Sweater')

    def test_invalid_member_id_returns_json_404(self):
        response = self.client.post(reverse('info:info_save_ajax'), {
            'id': 'not-a-number',
            'tag_number': 'K-005',
            'gender': 'Hen',
            'status': 'Active',
            'wins': '0',
            'losses': '0',
        })

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], 'Record not found.')

    def test_cannot_delete_another_users_member(self):
        other_user = get_user_model().objects.create_user(
            username='other-delete-owner',
            password='test-password',
        )
        other_bird = FlockMember.objects.create(
            user=other_user,
            tag_number='X-998',
            gender='Hen',
            status='Active',
        )

        response = self.client.post(reverse('info:info_delete_ajax', args=[other_bird.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(FlockMember.objects.filter(pk=other_bird.pk).exists())


class HealthRecordTests(FlockTestCase):
    def test_save_health_record(self):
        response = self.client.post(reverse('info:health_record_save_ajax'), {
            'bird_id': self.bird.pk,
            'record_type': 'Deworming',
            'title': 'Quarterly deworming',
            'date_administered': '2026-11-01',
            'next_due_date': '2027-02-01',
            'notes': 'No adverse reaction.',
        })

        self.assertEqual(response.status_code, 200)
        record = HealthRecord.objects.get(bird=self.bird)
        self.assertEqual(record.title, 'Quarterly deworming')
        self.assertEqual(record.notes, 'No adverse reaction.')

    def test_next_due_date_cannot_precede_administered_date(self):
        response = self.client.post(reverse('info:health_record_save_ajax'), {
            'bird_id': self.bird.pk,
            'record_type': 'Vaccination',
            'title': 'Vaccine',
            'date_administered': '2026-11-01',
            'next_due_date': '2026-10-01',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('next due date', response.json()['error'].lower())

    def test_missing_bird_id_returns_400(self):
        response = self.client.post(reverse('info:health_record_save_ajax'), {
            'record_type': 'Vaccination',
            'title': 'Vaccine',
            'date_administered': '2026-11-01',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('select a bird', response.json()['error'].lower())

    def test_invalid_bird_id_returns_json_404(self):
        response = self.client.post(reverse('info:health_record_save_ajax'), {
            'bird_id': 'not-a-number',
            'record_type': 'Vaccination',
            'title': 'Vaccine',
            'date_administered': '2026-11-01',
        })

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], 'Record not found.')

    def test_health_records_are_scoped_to_owner(self):
        other_user = get_user_model().objects.create_user(
            username='other-health-owner',
            password='test-password',
        )
        other_bird = FlockMember.objects.create(
            user=other_user,
            tag_number='X-997',
            gender='Hen',
            status='Active',
        )

        response = self.client.get(reverse('info:health_records_ajax', args=[other_bird.pk]))

        self.assertEqual(response.status_code, 404)

    def test_update_health_record(self):
        record = HealthRecord.objects.create(
            bird=self.bird,
            record_type='Vaccination',
            title='Old title',
            date_administered='2026-11-01',
        )

        response = self.client.post(reverse('info:health_record_save_ajax'), {
            'bird_id': self.bird.pk,
            'record_id': record.pk,
            'record_type': 'Treatment',
            'title': 'Updated title',
            'date_administered': '2026-11-02',
            'next_due_date': '2026-12-02',
            'notes': 'Recovered.',
        })

        self.assertEqual(response.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.title, 'Updated title')
        self.assertEqual(record.record_type, 'Treatment')
        self.assertEqual(record.notes, 'Recovered.')

    def test_delete_health_record(self):
        record = HealthRecord.objects.create(
            bird=self.bird,
            record_type='Deworming',
            title='Quarterly deworming',
            date_administered='2026-11-01',
        )

        response = self.client.post(
            reverse('info:health_record_delete_ajax', args=[record.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(HealthRecord.objects.filter(pk=record.pk).exists())

    def test_cannot_delete_another_users_health_record(self):
        other_user = get_user_model().objects.create_user(
            username='other-health-record-owner',
            password='test-password',
        )
        other_bird = FlockMember.objects.create(
            user=other_user,
            tag_number='X-995',
            gender='Hen',
            status='Active',
        )
        other_record = HealthRecord.objects.create(
            bird=other_bird,
            record_type='Vaccination',
            title='Private record',
            date_administered='2026-11-01',
        )

        response = self.client.post(
            reverse('info:health_record_delete_ajax', args=[other_record.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(HealthRecord.objects.filter(pk=other_record.pk).exists())

    def test_invalid_record_id_returns_json_404(self):
        response = self.client.post(reverse('info:health_record_save_ajax'), {
            'bird_id': self.bird.pk,
            'record_id': 'not-a-number',
            'record_type': 'Vaccination',
            'title': 'Vaccine',
            'date_administered': '2026-11-01',
        })

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], 'Record not found.')


class HealthSchedulePageTests(FlockTestCase):
    def setUp(self):
        super().setUp()
        self.today = timezone.localdate()
        self.overdue_record = HealthRecord.objects.create(
            bird=self.bird,
            record_type='Vaccination',
            title='Overdue booster',
            date_administered=self.today - timedelta(days=60),
            next_due_date=self.today - timedelta(days=5),
        )
        self.upcoming_record = HealthRecord.objects.create(
            bird=self.bird,
            record_type='Deworming',
            title='Upcoming deworming',
            date_administered=self.today,
            next_due_date=self.today + timedelta(days=7),
        )

    def test_health_page_lists_records_and_counts(self):
        response = self.client.get(reverse('info:health_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'info/health_list.html')
        self.assertEqual(response.context['counts']['total'], 2)
        self.assertEqual(response.context['counts']['overdue'], 1)
        self.assertEqual(response.context['counts']['due_soon'], 1)
        self.assertContains(response, 'Overdue booster')
        self.assertContains(response, 'Upcoming deworming')

    def test_health_page_filters_overdue_records(self):
        response = self.client.get(reverse('info:health_list'), {'state': 'overdue'})

        self.assertContains(response, 'Overdue booster')
        self.assertNotContains(response, 'Upcoming deworming')

    def test_health_page_filters_by_record_type(self):
        response = self.client.get(
            reverse('info:health_list'),
            {'record_type': 'Deworming'},
        )

        self.assertContains(response, 'Upcoming deworming')
        self.assertNotContains(response, 'Overdue booster')

    def test_health_page_only_shows_owner_records(self):
        other_user = get_user_model().objects.create_user(
            username='other-health-page-owner',
            password='test-password',
        )
        other_bird = FlockMember.objects.create(
            user=other_user,
            tag_number='X-994',
            gender='Hen',
            status='Active',
        )
        HealthRecord.objects.create(
            bird=other_bird,
            record_type='Treatment',
            title='Private treatment',
            date_administered=self.today,
        )

        response = self.client.get(reverse('info:health_list'))

        self.assertNotContains(response, 'Private treatment')

    def test_health_page_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse('info:health_list'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)


class MedicineCabinetTests(FlockTestCase):
    def setUp(self):
        super().setUp()
        self.today = timezone.localdate()
        self.low_stock_medicine = Medicine.objects.create(
            user=self.user,
            name='Newcastle vaccine',
            category='Vaccine',
            unit='ml',
            stock_quantity=Decimal('2.00'),
            low_stock_threshold=Decimal('5.00'),
            expiration_date=self.today + timedelta(days=10),
        )
        self.out_of_stock_medicine = Medicine.objects.create(
            user=self.user,
            name='Dewormer syrup',
            category='Dewormer',
            unit='ml',
            stock_quantity=Decimal('0.00'),
            low_stock_threshold=Decimal('1.00'),
            expiration_date=self.today - timedelta(days=2),
        )
        self.healthy_medicine = Medicine.objects.create(
            user=self.user,
            name='Vitamin B complex',
            category='Vitamin',
            unit='tablet',
            stock_quantity=Decimal('100.00'),
            low_stock_threshold=Decimal('5.00'),
            expiration_date=self.today + timedelta(days=365),
        )

    def test_medicine_page_lists_items_and_counts(self):
        response = self.client.get(reverse('info:medicine_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'info/medicine_list.html')
        self.assertEqual(response.context['counts']['total'], 3)
        self.assertEqual(response.context['counts']['low_stock'], 1)
        self.assertEqual(response.context['counts']['out_of_stock'], 1)
        self.assertEqual(response.context['counts']['expiring'], 1)
        self.assertEqual(response.context['counts']['expired'], 1)
        self.assertContains(response, 'Newcastle vaccine')
        self.assertContains(response, 'Dewormer syrup')

    def test_medicine_page_filters_low_stock(self):
        response = self.client.get(reverse('info:medicine_list'), {'state': 'low'})

        self.assertContains(response, 'Newcastle vaccine')
        self.assertNotContains(response, 'Dewormer syrup')
        self.assertNotContains(response, 'Vitamin B complex')

    def test_medicine_page_filters_expired(self):
        response = self.client.get(reverse('info:medicine_list'), {'state': 'expired'})

        self.assertContains(response, 'Dewormer syrup')
        self.assertNotContains(response, 'Newcastle vaccine')

    def test_medicine_page_only_shows_owner_items(self):
        other_user = get_user_model().objects.create_user(
            username='other-medicine-owner',
            password='test-password',
        )
        Medicine.objects.create(
            user=other_user,
            name='Private medicine',
            category='Antibiotic',
            unit='g',
            stock_quantity=Decimal('10.00'),
        )

        response = self.client.get(reverse('info:medicine_list'))

        self.assertNotContains(response, 'Private medicine')

    def test_medicine_page_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse('info:medicine_list'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_create_medicine(self):
        response = self.client.post(reverse('info:medicine_save_ajax'), {
            'name': 'Amoxicillin',
            'category': 'Antibiotic',
            'unit': 'g',
            'stock_quantity': '25.50',
            'low_stock_threshold': '5',
            'expiration_date': str(self.today + timedelta(days=90)),
            'notes': 'Keep dry.',
        })

        self.assertEqual(response.status_code, 200)
        medicine = Medicine.objects.get(user=self.user, name='Amoxicillin')
        self.assertEqual(medicine.stock_quantity, Decimal('25.50'))
        self.assertEqual(medicine.notes, 'Keep dry.')

    def test_update_medicine(self):
        response = self.client.post(reverse('info:medicine_save_ajax'), {
            'id': self.low_stock_medicine.pk,
            'name': 'Newcastle vaccine (updated)',
            'category': 'Vaccine',
            'unit': 'ml',
            'stock_quantity': '12',
            'low_stock_threshold': '3',
            'expiration_date': str(self.today + timedelta(days=30)),
        })

        self.assertEqual(response.status_code, 200)
        self.low_stock_medicine.refresh_from_db()
        self.assertEqual(self.low_stock_medicine.name, 'Newcastle vaccine (updated)')
        self.assertEqual(self.low_stock_medicine.stock_quantity, Decimal('12.00'))

    def test_negative_stock_is_rejected(self):
        response = self.client.post(reverse('info:medicine_save_ajax'), {
            'name': 'Bad stock',
            'category': 'Other',
            'unit': 'ml',
            'stock_quantity': '-1',
            'low_stock_threshold': '0',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('negative', response.json()['error'].lower())

    def test_cannot_edit_another_users_medicine(self):
        other_user = get_user_model().objects.create_user(
            username='other-medicine-edit-owner',
            password='test-password',
        )
        other_medicine = Medicine.objects.create(
            user=other_user,
            name='Other owner medicine',
            category='Other',
            unit='ml',
            stock_quantity=Decimal('1.00'),
        )

        response = self.client.post(reverse('info:medicine_save_ajax'), {
            'id': other_medicine.pk,
            'name': 'Hijacked',
            'category': 'Other',
            'unit': 'ml',
            'stock_quantity': '5',
            'low_stock_threshold': '0',
        })

        self.assertEqual(response.status_code, 404)
        other_medicine.refresh_from_db()
        self.assertEqual(other_medicine.name, 'Other owner medicine')

    def test_restock_medicine(self):
        response = self.client.post(reverse('info:medicine_restock_ajax'), {
            'id': self.out_of_stock_medicine.pk,
            'amount': '10.5',
        })

        self.assertEqual(response.status_code, 200)
        self.out_of_stock_medicine.refresh_from_db()
        self.assertEqual(self.out_of_stock_medicine.stock_quantity, Decimal('10.50'))
        self.assertEqual(response.json()['stock_quantity'], '10.5')

    def test_restock_rejects_invalid_amount(self):
        response = self.client.post(reverse('info:medicine_restock_ajax'), {
            'id': self.low_stock_medicine.pk,
            'amount': '-2',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('greater than zero', response.json()['error'].lower())

    def test_cannot_restock_another_users_medicine(self):
        other_user = get_user_model().objects.create_user(
            username='other-medicine-restock-owner',
            password='test-password',
        )
        other_medicine = Medicine.objects.create(
            user=other_user,
            name='Private restock medicine',
            category='Other',
            unit='ml',
            stock_quantity=Decimal('1.00'),
        )

        response = self.client.post(reverse('info:medicine_restock_ajax'), {
            'id': other_medicine.pk,
            'amount': '5',
        })

        self.assertEqual(response.status_code, 404)

    def test_delete_medicine(self):
        response = self.client.post(
            reverse('info:medicine_delete_ajax', args=[self.healthy_medicine.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Medicine.objects.filter(pk=self.healthy_medicine.pk).exists())

    def test_cannot_delete_another_users_medicine(self):
        other_user = get_user_model().objects.create_user(
            username='other-medicine-delete-owner',
            password='test-password',
        )
        other_medicine = Medicine.objects.create(
            user=other_user,
            name='Private delete medicine',
            category='Other',
            unit='ml',
            stock_quantity=Decimal('1.00'),
        )

        response = self.client.post(
            reverse('info:medicine_delete_ajax', args=[other_medicine.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Medicine.objects.filter(pk=other_medicine.pk).exists())


class FlockListAjaxTests(FlockTestCase):
    def test_list_ajax_honours_search_and_status_filters(self):
        FlockMember.objects.create(
            user=self.user,
            tag_number='H-777',
            gender='Hen',
            status='Conditioning',
        )

        response = self.client.get(
            reverse('info:info_list_ajax'),
            {'q': 'Kelso', 'status': 'Active'},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['total'], 1)
        self.assertEqual(payload['data'][0]['tag_number'], 'K-001')
        self.assertIn('pages', payload)


class PedigreeTests(FlockTestCase):
    def test_pedigree_returns_lineage(self):
        sire = FlockMember.objects.create(
            user=self.user,
            tag_number='S-100',
            gender='Cock',
            status='Broodcock',
            sire='GS-10',
            dam='GD-10',
        )
        dam = FlockMember.objects.create(
            user=self.user,
            tag_number='D-100',
            gender='Hen',
            status='Broodhen',
            sire='GS-20',
            dam='GD-20',
        )
        self.bird.sire = sire.tag_number
        self.bird.dam = dam.tag_number
        self.bird.save()

        response = self.client.get(reverse('info:pedigree_ajax', args=[self.bird.pk]))

        self.assertEqual(response.status_code, 200)
        lineage = response.json()['lineage']
        self.assertEqual(lineage['bird']['tag'], 'K-001')
        self.assertEqual(lineage['sire']['tag'], 'S-100')
        self.assertEqual(lineage['dam']['tag'], 'D-100')
        self.assertEqual(lineage['grand_sire_paternal'], 'GS-10')
        self.assertEqual(lineage['grand_dam_paternal'], 'GD-10')
        self.assertEqual(lineage['grand_sire_maternal'], 'GS-20')
        self.assertEqual(lineage['grand_dam_maternal'], 'GD-20')

    def test_pedigree_is_scoped_to_owner(self):
        other_user = get_user_model().objects.create_user(
            username='other-pedigree-owner',
            password='test-password',
        )
        other_bird = FlockMember.objects.create(
            user=other_user,
            tag_number='X-996',
            gender='Hen',
            status='Active',
        )

        response = self.client.get(reverse('info:pedigree_ajax', args=[other_bird.pk]))

        self.assertEqual(response.status_code, 404)


class MultiUserTagScopingTests(FlockTestCase):
    def test_tag_number_is_scoped_per_user(self):
        other_user = get_user_model().objects.create_user(
            username='other-breeder',
            password='test-password',
        )
        # Both user and other_user should be able to create a bird with tag 'K-001'
        bird2 = FlockMember.objects.create(
            user=other_user,
            tag_number='K-001',
            gender='Hen',
            status='Active',
        )
        self.assertEqual(bird2.tag_number, 'K-001')
        self.assertEqual(self.bird.tag_number, 'K-001')
        self.assertNotEqual(self.bird.user, bird2.user)


class FightRecordTests(FlockTestCase):
    def test_save_fight_record_and_sync_counters(self):
        response = self.client.post(reverse('info:fight_record_save_ajax'), {
            'bird_id': self.bird.pk,
            'event_name': 'Derby Fiesta 2026',
            'fight_date': timezone.localdate(),
            'result': 'win',
            'weight_grams': 2100,
            'opponent': 'Farm X',
        })
        self.assertEqual(response.status_code, 200)
        self.bird.refresh_from_db()
        self.assertEqual(self.bird.wins, 1)
        self.assertEqual(self.bird.losses, 0)
        self.assertEqual(self.bird.draws, 0)

        # Log a loss
        self.client.post(reverse('info:fight_record_save_ajax'), {
            'bird_id': self.bird.pk,
            'event_name': 'Hackfight',
            'fight_date': timezone.localdate(),
            'result': 'loss',
        })
        self.bird.refresh_from_db()
        self.assertEqual(self.bird.wins, 1)
        self.assertEqual(self.bird.losses, 1)

    def test_get_fights_ajax(self):
        from .models import FightRecord
        FightRecord.objects.create(
            bird=self.bird,
            event_name='4-Cock Derby',
            fight_date=timezone.localdate(),
            result='win',
        )
        response = self.client.get(reverse('info:fight_records_ajax', args=[self.bird.pk]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['event_name'], '4-Cock Derby')


class WeightLogTests(FlockTestCase):
    def test_weight_log_creates_and_updates_bird_weight(self):
        response = self.client.post(reverse('info:weight_log_save_ajax'), {
            'bird_id': self.bird.pk,
            'date': timezone.localdate(),
            'time_of_day': 'morning',
            'weight_grams': 1950,
            'notes': 'Normal morning drop',
        })
        self.assertEqual(response.status_code, 200)
        self.bird.refresh_from_db()
        self.assertEqual(self.bird.weight_grams, 1950)


class ConditioningQuickFormTests(FlockTestCase):
    def test_quick_form_puts_bird_in_conditioning(self):
        response = self.client.post(reverse('info:conditioning_save_ajax'), {
            'bird_id': self.bird.pk,
            'conditioning_start_date': '2026-11-15',
            'target_weight_grams': '2150',
            'conditioning_program': 'Roadwork',
            'conditioning_feed_plan': 'High-protein mix, twice daily',
            'weight_grams': '2000',
        })

        self.assertEqual(response.status_code, 200)
        self.bird.refresh_from_db()
        self.assertEqual(self.bird.status, 'Conditioning')
        self.assertEqual(self.bird.conditioning_program, 'Roadwork')
        self.assertEqual(self.bird.target_weight_grams, 2150)
        self.assertEqual(self.bird.weight_grams, 2000)

    def test_custom_program_requires_a_name(self):
        response = self.client.post(reverse('info:conditioning_save_ajax'), {
            'bird_id': self.bird.pk,
            'conditioning_start_date': '2026-11-15',
            'target_weight_grams': '2150',
            'conditioning_program': 'Custom',
            'conditioning_program_custom': '',
            'conditioning_feed_plan': 'High-protein mix, twice daily',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('conditioning_program_custom', response.json()['errors'])
        self.bird.refresh_from_db()
        self.assertEqual(self.bird.status, 'Active')

    def test_custom_program_name_is_saved(self):
        response = self.client.post(reverse('info:conditioning_save_ajax'), {
            'bird_id': self.bird.pk,
            'conditioning_start_date': '2026-11-15',
            'target_weight_grams': '2150',
            'conditioning_program': 'Custom',
            'conditioning_program_custom': 'Beach roadwork',
            'conditioning_feed_plan': 'High-protein mix, twice daily',
        })

        self.assertEqual(response.status_code, 200)
        self.bird.refresh_from_db()
        self.assertEqual(self.bird.conditioning_program, 'Beach roadwork')

    def test_custom_feed_plan_name_is_saved(self):
        response = self.client.post(reverse('info:conditioning_save_ajax'), {
            'bird_id': self.bird.pk,
            'conditioning_start_date': '2026-11-15',
            'target_weight_grams': '2150',
            'conditioning_program': 'Roadwork',
            'conditioning_feed_plan': 'Custom',
            'conditioning_feed_plan_custom': 'Farm blend with copra meal',
        })

        self.assertEqual(response.status_code, 200)
        self.bird.refresh_from_db()
        self.assertEqual(self.bird.conditioning_feed_plan, 'Farm blend with copra meal')

    def test_custom_feed_plan_requires_a_name(self):
        response = self.client.post(reverse('info:conditioning_save_ajax'), {
            'bird_id': self.bird.pk,
            'conditioning_start_date': '2026-11-15',
            'target_weight_grams': '2150',
            'conditioning_program': 'Roadwork',
            'conditioning_feed_plan': 'Custom',
            'conditioning_feed_plan_custom': '',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('conditioning_feed_plan_custom', response.json()['errors'])
        self.bird.refresh_from_db()
        self.assertEqual(self.bird.status, 'Active')

    def test_missing_bird_returns_400(self):
        response = self.client.post(reverse('info:conditioning_save_ajax'), {
            'conditioning_start_date': '2026-11-15',
            'target_weight_grams': '2150',
            'conditioning_program': 'Roadwork',
            'conditioning_feed_plan': 'High-protein mix, twice daily',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_cannot_condition_another_users_bird(self):
        other = get_user_model().objects.create_user(
            username='other-owner', password='test-password'
        )
        other_bird = FlockMember.objects.create(
            user=other,
            tag_number='OTHER-001',
            gender='Stag',
            status='Active',
        )

        response = self.client.post(reverse('info:conditioning_save_ajax'), {
            'bird_id': other_bird.pk,
            'conditioning_start_date': '2026-11-15',
            'target_weight_grams': '2150',
            'conditioning_program': 'Roadwork',
            'conditioning_feed_plan': 'High-protein mix, twice daily',
        })

        self.assertEqual(response.status_code, 404)
        other_bird.refresh_from_db()
        self.assertEqual(other_bird.status, 'Active')


class ConditioningWorkflowTests(FlockTestCase):
    def start_conditioning(self, **overrides):
        data = {
            'bird_id': self.bird.pk,
            'conditioning_start_date': '2026-11-15',
            'target_weight_grams': '2150',
            'conditioning_program': 'Roadwork',
            'conditioning_feed_plan': 'High-protein mix, twice daily',
        }
        data.update(overrides)
        return self.client.post(reverse('info:conditioning_save_ajax'), data)

    def test_starting_weight_is_saved_as_a_log(self):
        response = self.start_conditioning(weight_grams='2000')

        self.assertEqual(response.status_code, 200)
        log = self.bird.weight_logs.get()
        self.assertEqual(log.weight_grams, 2000)
        self.assertIn('conditioning start', log.notes.lower())
        self.bird.refresh_from_db()
        self.assertEqual(self.bird.weight_grams, 2000)

    def test_deleting_a_newer_log_does_not_erase_starting_weight(self):
        self.start_conditioning(weight_grams='2000')
        newer_log = WeightLog.objects.create(
            bird=self.bird,
            date=timezone.localdate(),
            time_of_day='morning',
            weight_grams=1980,
        )

        response = self.client.post(
            reverse('info:weight_log_delete_ajax', args=[newer_log.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.bird.refresh_from_db()
        self.assertEqual(self.bird.weight_grams, 2000)

    def test_standard_session_plan_is_seeded(self):
        response = self.start_conditioning(conditioning_target_date='2026-12-15')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['sessions_created'], 7)
        sessions = list(self.bird.conditioning_sessions.all())
        self.assertEqual(len(sessions), 7)
        self.assertEqual(sessions[-1].title, 'Pre-event rest & final check')
        self.assertEqual(str(sessions[-1].scheduled_date), '2026-12-14')

    def test_starting_again_does_not_duplicate_sessions(self):
        self.start_conditioning()
        response = self.start_conditioning(target_weight_grams='2100')

        self.assertEqual(response.json()['sessions_created'], 0)
        self.assertEqual(self.bird.conditioning_sessions.count(), 6)

    def test_future_start_date_is_rejected(self):
        future = timezone.localdate() + timedelta(days=2)
        response = self.start_conditioning(conditioning_start_date=str(future))

        self.assertEqual(response.status_code, 400)
        self.assertIn('conditioning_start_date', response.json()['errors'])

    def test_target_date_must_follow_start_date(self):
        response = self.start_conditioning(conditioning_target_date='2026-11-01')

        self.assertEqual(response.status_code, 400)
        self.assertIn('conditioning_target_date', response.json()['errors'])

    def test_unrealistic_target_weight_is_rejected(self):
        response = self.start_conditioning(
            weight_grams='2000', target_weight_grams='4000',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('target_weight_grams', response.json()['errors'])

    def test_conditioning_dashboard_page_renders(self):
        self.start_conditioning()

        response = self.client.get(reverse('info:conditioning_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'info/conditioning_list.html')
        self.assertContains(response, 'Conditioning Workflow')
        self.assertContains(response, 'id="quickConditioningForm"')
        self.assertContains(response, self.bird.tag_number)

    def test_conditioning_dashboard_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse('info:conditioning_list'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)


class ConditioningSessionTests(FlockTestCase):
    def setUp(self):
        super().setUp()
        self.client.post(reverse('info:conditioning_save_ajax'), {
            'bird_id': self.bird.pk,
            'conditioning_start_date': '2026-11-15',
            'target_weight_grams': '2150',
            'conditioning_program': 'Roadwork',
            'conditioning_feed_plan': 'High-protein mix, twice daily',
        })
        self.session = self.bird.conditioning_sessions.first()

    def test_session_list_returns_plan_and_progress(self):
        response = self.client.get(
            reverse('info:conditioning_sessions_ajax', args=[self.bird.pk])
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['bird_tag'], self.bird.tag_number)
        self.assertEqual(len(data['data']), 6)
        self.assertEqual(data['data'][0]['title'], self.session.title)

    def test_marking_session_completed_sets_completed_at(self):
        response = self.client.post(reverse('info:conditioning_session_save_ajax'), {
            'id': self.session.pk,
            'bird_id': self.bird.pk,
            'title': self.session.title,
            'scheduled_date': str(self.session.scheduled_date),
            'phase': self.session.phase,
            'session_type': self.session.session_type,
            'status': 'completed',
        })

        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, 'completed')
        self.assertIsNotNone(self.session.completed_at)

    def test_session_can_be_deleted(self):
        response = self.client.post(
            reverse('info:conditioning_session_delete_ajax', args=[self.session.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.bird.conditioning_sessions.filter(pk=self.session.pk).exists())

    def test_cannot_edit_another_users_session(self):
        other = get_user_model().objects.create_user(
            username='other-session-owner', password='test-password'
        )
        other_bird = FlockMember.objects.create(
            user=other, tag_number='OTHER-002', gender='Stag', status='Conditioning',
        )
        other_session = ConditioningSession.objects.create(
            bird=other_bird,
            title='Other plan',
            scheduled_date=timezone.localdate(),
        )

        response = self.client.post(reverse('info:conditioning_session_save_ajax'), {
            'id': other_session.pk,
            'bird_id': other_bird.pk,
            'title': 'Hijacked',
            'scheduled_date': str(other_session.scheduled_date),
            'status': 'completed',
        })

        self.assertEqual(response.status_code, 404)
        other_session.refresh_from_db()
        self.assertEqual(other_session.title, 'Other plan')


class InlineQuickFormRenderTests(FlockTestCase):
    def test_flock_page_renders_quick_member_form(self):
        response = self.client.get(reverse('info:info_list'))
        self.assertContains(response, 'id="quickMemberForm"')

    def test_conditioning_page_renders_conditioning_requirements_instead_of_quick_member_form(self):
        response = self.client.get(reverse('info:info_list'), {'status': 'Conditioning'})
        self.assertContains(response, 'id="quickConditioningForm"')
        self.assertNotContains(response, 'id="quickMemberForm"')

    def test_conditioning_forms_render_preset_diet_plan_options(self):
        conditioning_page = self.client.get(reverse('info:conditioning_list'))
        self.assertContains(conditioning_page, 'id="quick_cond_feed"')
        self.assertContains(conditioning_page, 'High-protein pellets, twice daily')
        self.assertContains(conditioning_page, 'id="quick_cond_feed_custom"')

        flock_page = self.client.get(reverse('info:info_list'), {'status': 'Conditioning'})
        self.assertContains(flock_page, 'Booster mash with vitamins')
        self.assertContains(flock_page, 'id="quick_cond_feed_custom"')
        self.assertContains(flock_page, 'id="member_conditioning_feed_plan"')
        self.assertContains(flock_page, 'id="member_conditioning_feed_plan_custom"')

    def test_dashboard_does_not_render_quick_member_form(self):
        response = self.client.get(reverse('dashboard'))
        self.assertNotContains(response, 'id="quickMemberForm"')
        self.assertNotContains(response, 'Add flock member')

    def test_breeding_page_renders_quick_pen_form(self):
        response = self.client.get(reverse('info:breeding_list'))
        self.assertContains(response, 'id="quickPenForm"')

    def test_breeding_page_binds_quick_pen_script_inside_turbo_frame(self):
        response = self.client.get(reverse('info:breeding_list'))
        html = response.content.decode()

        # The save handler must live inside the Turbo frame; scripts rendered
        # after </turbo-frame> never run when the page is opened from the sidebar.
        save_url_position = html.index(reverse('info:breeding_pen_save_ajax'))
        self.assertLess(html.index('id="quickPenForm"'), save_url_position)
        self.assertLess(save_url_position, html.index('</turbo-frame>'))

    def test_health_page_renders_quick_health_form(self):
        response = self.client.get(reverse('info:health_list'))
        self.assertContains(response, 'id="quickHealthForm"')

    def test_medicine_page_renders_quick_medicine_form(self):
        response = self.client.get(reverse('info:medicine_list'))
        self.assertContains(response, 'id="quickMedicineForm"')


class BreedingModuleTests(FlockTestCase):
    def test_new_pen_record_appears_on_breeding_page(self):
        hen = FlockMember.objects.create(
            user=self.user,
            tag_number='HEN-002',
            gender='Hen',
            status='Broodhen',
        )

        response = self.client.post(reverse('info:breeding_pen_save_ajax'), {
            'pen_number': 'Pen-9Z',
            'sire': self.bird.pk,
            'dam': hen.pk,
            'date_paired': timezone.localdate(),
            'status': 'active',
        })
        self.assertEqual(response.status_code, 200)

        page = self.client.get(reverse('info:breeding_list'))
        self.assertContains(page, 'Pen-9Z')
        self.assertContains(page, self.bird.tag_number)
        self.assertContains(page, hen.tag_number)

    def test_breeding_pen_and_clutch_workflow(self):
        hen = FlockMember.objects.create(
            user=self.user,
            tag_number='HEN-001',
            gender='Hen',
            status='Broodhen',
        )
        # Create breeding pen
        response = self.client.post(reverse('info:breeding_pen_save_ajax'), {
            'pen_number': 'Pen-1A',
            'sire': self.bird.pk,
            'dam': hen.pk,
            'date_paired': timezone.localdate(),
            'status': 'active',
        })
        self.assertEqual(response.status_code, 200)

        from .models import BreedingPen
        pen = BreedingPen.objects.get(pen_number='Pen-1A')
        self.assertEqual(pen.sire, self.bird)
        self.assertEqual(pen.dam, hen)

        # Log clutch
        response = self.client.post(reverse('info:clutch_save_ajax'), {
            'pen_id': pen.pk,
            'clutch_number': '1',
            'date_started': timezone.localdate(),
            'eggs_collected': 10,
            'fertile_eggs': 8,
            'hatched_count': 7,
        })
        self.assertEqual(response.status_code, 200)
        clutch = pen.clutches.first()
        self.assertEqual(clutch.hatchability_rate, 87.5)


class PedigreeCertificateTests(FlockTestCase):
    def test_pedigree_certificate_renders(self):
        response = self.client.get(reverse('info:pedigree_certificate', args=[self.bird.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Certificate of Pedigree')
        self.assertContains(response, self.bird.tag_number)


class FlockSaleTests(FlockTestCase):
    def record_sale(self, **overrides):
        data = {
            'bird': self.bird.pk,
            'buyer_name': 'Juan Dela Cruz',
            'buyer_contact': '0917 555 0100',
            'sale_date': str(timezone.localdate()),
            'amount': '8500.00',
            'notes': 'Delivered at the farm',
        }
        data.update(overrides)
        return self.client.post(reverse('info:sale_save_ajax'), data)

    def test_record_sale_creates_income_and_marks_bird_sold(self):
        response = self.record_sale()

        self.assertEqual(response.status_code, 200)
        sale = FlockSale.objects.get(user=self.user)
        self.assertEqual(sale.bird, self.bird)
        self.assertEqual(sale.amount, Decimal('8500.00'))
        entry = sale.financial_entry
        self.assertIsNotNone(entry)
        self.assertEqual(entry.entry_type, FinancialEntry.TYPE_INCOME)
        self.assertEqual(entry.category, 'Bird Sale')
        self.assertEqual(entry.amount, sale.amount)
        self.assertEqual(entry.bird, self.bird)
        self.bird.refresh_from_db()
        self.assertEqual(self.bird.status, 'Sold')

    def test_sales_page_lists_sales_and_totals(self):
        self.record_sale()

        response = self.client.get(reverse('info:sales_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'info/sales_list.html')
        self.assertContains(response, 'Juan Dela Cruz')
        self.assertContains(response, self.bird.tag_number)
        self.assertEqual(response.context['total_revenue'], Decimal('8500.00'))
        self.assertEqual(response.context['counts']['birds_sold'], 1)

    def test_sales_page_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse('info:sales_list'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_update_sale_syncs_financial_entry(self):
        self.record_sale()
        sale = FlockSale.objects.get()

        response = self.client.post(reverse('info:sale_save_ajax'), {
            'id': sale.pk,
            'bird': self.bird.pk,
            'buyer_name': 'Maria Santos',
            'sale_date': str(timezone.localdate()),
            'amount': '9000.00',
        })

        self.assertEqual(response.status_code, 200)
        sale.refresh_from_db()
        self.assertEqual(sale.buyer_name, 'Maria Santos')
        self.assertEqual(sale.financial_entry.amount, Decimal('9000.00'))
        self.assertEqual(FinancialEntry.objects.filter(user=self.user).count(), 1)

    def test_delete_sale_removes_income_and_restores_bird(self):
        self.record_sale()
        sale = FlockSale.objects.get()

        response = self.client.post(reverse('info:sale_delete_ajax', args=[sale.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(FlockSale.objects.exists())
        self.assertFalse(FinancialEntry.objects.exists())
        self.bird.refresh_from_db()
        self.assertEqual(self.bird.status, 'Active')

    def test_cannot_sell_another_users_bird(self):
        other = get_user_model().objects.create_user(
            username='other-sale-owner', password='test-password'
        )
        other_bird = FlockMember.objects.create(
            user=other, tag_number='OTHER-003', gender='Stag', status='Active',
        )

        response = self.record_sale(bird=other_bird.pk)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(FlockSale.objects.exists())

    def test_future_sale_date_is_rejected(self):
        future = timezone.localdate() + timedelta(days=2)

        response = self.record_sale(sale_date=str(future))

        self.assertEqual(response.status_code, 400)
        self.assertIn('sale_date', response.json()['errors'])


class BreedQuickAddTests(FlockTestCase):
    def post_breed(self, name):
        return self.client.post(reverse('info:breed_create_ajax'), {'name': name})

    def test_create_breed_returns_new_option(self):
        response = self.post_breed('Sweater')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['name'], 'Sweater')
        self.assertTrue(data['created'])
        self.assertTrue(Breed.objects.filter(pk=data['id'], name='Sweater').exists())

    def test_existing_breed_is_reused_case_insensitively(self):
        response = self.post_breed('kelso')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['created'])
        self.assertEqual(data['id'], self.breed.pk)
        self.assertEqual(data['name'], 'Kelso')
        self.assertEqual(Breed.objects.filter(name__iexact='kelso').count(), 1)

    def test_blank_breed_name_is_rejected(self):
        response = self.post_breed('   ')

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_overlong_breed_name_is_rejected(self):
        response = self.post_breed('A' * 101)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Breed.objects.filter(name='A' * 101).exists())

    def test_breed_creation_requires_login(self):
        self.client.logout()

        response = self.post_breed('New Breed')

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)
        self.assertFalse(Breed.objects.filter(name='New Breed').exists())


