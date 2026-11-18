from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Breed, FlockMember, HealthRecord, Medicine, WeightLog,
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
        self.assertContains(response, 'K-001')
        self.assertContains(response, 'Newcastle booster')
        self.assertContains(response, reverse('info:info_list'))

    def test_dashboard_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)


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
            status='Active',
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
            'status': 'Active',
            'birth_date': '2026-01-15',
            'weight_grams': '1850',
            'sire': 'K-001',
            'dam': '',
        })

        self.assertEqual(response.status_code, 200)
        member = FlockMember.objects.get(user=self.user, tag_number='K-003')
        self.assertEqual(member.breed, self.breed)
        self.assertEqual(member.weight_grams, 1850)

    def test_duplicate_tag_number_is_rejected(self):
        response = self.client.post(reverse('info:info_save_ajax'), {
            'tag_number': 'k-001',
            'gender': 'Cock',
            'status': 'Active',
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
            'sire': '',
            'dam': '',
        })

        self.assertEqual(response.status_code, 200)
        self.bird.refresh_from_db()
        self.assertEqual(self.bird.status, 'Retired')

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
    def make_medicine(self, **overrides):
        data = {
            'user': self.user,
            'name': 'Ivermectin',
            'category': 'Dewormer',
            'unit': 'ml',
            'stock_quantity': Decimal('10.00'),
            'low_stock_threshold': Decimal('2.00'),
        }
        data.update(overrides)
        return Medicine.objects.create(**data)

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

    def test_saving_health_record_deducts_medicine_stock(self):
        medicine = self.make_medicine()

        response = self.client.post(reverse('info:health_record_save_ajax'), {
            'bird_id': self.bird.pk,
            'record_type': 'Deworming',
            'title': 'Ivermectin routine deworming',
            'medicine': medicine.pk,
            'quantity_used': '2.5',
            'date_administered': '2026-11-01',
        })

        self.assertEqual(response.status_code, 200)
        medicine.refresh_from_db()
        record = HealthRecord.objects.get(bird=self.bird)
        self.assertEqual(record.medicine, medicine)
        self.assertEqual(record.quantity_used, Decimal('2.50'))
        self.assertEqual(medicine.stock_quantity, Decimal('7.50'))

    def test_insufficient_stock_blocks_health_record(self):
        medicine = self.make_medicine(stock_quantity=Decimal('1.00'))

        response = self.client.post(reverse('info:health_record_save_ajax'), {
            'bird_id': self.bird.pk,
            'record_type': 'Deworming',
            'title': 'Ivermectin routine deworming',
            'medicine': medicine.pk,
            'quantity_used': '2',
            'date_administered': '2026-11-01',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('not enough', response.json()['error'].lower())
        self.assertFalse(HealthRecord.objects.exists())
        medicine.refresh_from_db()
        self.assertEqual(medicine.stock_quantity, Decimal('1.00'))

    def test_editing_health_record_restores_and_rededucts_stock(self):
        medicine = self.make_medicine()

        self.client.post(reverse('info:health_record_save_ajax'), {
            'bird_id': self.bird.pk,
            'record_type': 'Deworming',
            'title': 'Ivermectin routine deworming',
            'medicine': medicine.pk,
            'quantity_used': '2',
            'date_administered': '2026-11-01',
        })
        record = HealthRecord.objects.get(bird=self.bird)

        response = self.client.post(reverse('info:health_record_save_ajax'), {
            'bird_id': self.bird.pk,
            'record_id': record.pk,
            'record_type': 'Deworming',
            'title': 'Ivermectin routine deworming',
            'medicine': medicine.pk,
            'quantity_used': '5',
            'date_administered': '2026-11-01',
        })

        self.assertEqual(response.status_code, 200)
        medicine.refresh_from_db()
        record.refresh_from_db()
        self.assertEqual(record.quantity_used, Decimal('5.00'))
        self.assertEqual(medicine.stock_quantity, Decimal('5.00'))

    def test_switching_medicine_restores_previous_stock(self):
        old_medicine = self.make_medicine(name='Old dewormer')
        new_medicine = self.make_medicine(name='New dewormer')

        self.client.post(reverse('info:health_record_save_ajax'), {
            'bird_id': self.bird.pk,
            'record_type': 'Deworming',
            'title': 'Deworming',
            'medicine': old_medicine.pk,
            'quantity_used': '3',
            'date_administered': '2026-11-01',
        })
        record = HealthRecord.objects.get(bird=self.bird)

        response = self.client.post(reverse('info:health_record_save_ajax'), {
            'bird_id': self.bird.pk,
            'record_id': record.pk,
            'record_type': 'Deworming',
            'title': 'Deworming',
            'medicine': new_medicine.pk,
            'quantity_used': '1',
            'date_administered': '2026-11-01',
        })

        self.assertEqual(response.status_code, 200)
        old_medicine.refresh_from_db()
        new_medicine.refresh_from_db()
        self.assertEqual(old_medicine.stock_quantity, Decimal('10.00'))
        self.assertEqual(new_medicine.stock_quantity, Decimal('9.00'))

    def test_delete_health_record_restores_medicine_stock(self):
        medicine = self.make_medicine()

        self.client.post(reverse('info:health_record_save_ajax'), {
            'bird_id': self.bird.pk,
            'record_type': 'Deworming',
            'title': 'Deworming',
            'medicine': medicine.pk,
            'quantity_used': '4',
            'date_administered': '2026-11-01',
        })
        record = HealthRecord.objects.get(bird=self.bird)

        response = self.client.post(
            reverse('info:health_record_delete_ajax', args=[record.pk])
        )

        self.assertEqual(response.status_code, 200)
        medicine.refresh_from_db()
        self.assertEqual(medicine.stock_quantity, Decimal('10.00'))

    def test_quantity_without_medicine_is_rejected(self):
        response = self.client.post(reverse('info:health_record_save_ajax'), {
            'bird_id': self.bird.pk,
            'record_type': 'Deworming',
            'title': 'Deworming',
            'quantity_used': '2',
            'date_administered': '2026-11-01',
        })

        self.assertEqual(response.status_code, 400)
        self.assertFalse(HealthRecord.objects.exists())

    def test_cannot_use_another_users_medicine(self):
        other_user = get_user_model().objects.create_user(
            username='other-medicine-owner',
            password='test-password',
        )
        other_medicine = Medicine.objects.create(
            user=other_user,
            name='Private dewormer',
            category='Dewormer',
            stock_quantity=Decimal('10.00'),
        )

        response = self.client.post(reverse('info:health_record_save_ajax'), {
            'bird_id': self.bird.pk,
            'record_type': 'Deworming',
            'title': 'Deworming',
            'medicine': other_medicine.pk,
            'quantity_used': '1',
            'date_administered': '2026-11-01',
        })

        self.assertEqual(response.status_code, 400)
        self.assertFalse(HealthRecord.objects.exists())

    def test_batch_health_deducts_total_stock(self):
        medicine = self.make_medicine()
        second_bird = FlockMember.objects.create(
            user=self.user,
            tag_number='K-002',
            gender='Stag',
            status='Active',
        )

        response = self.client.post(reverse('info:batch_action_ajax'), {
            'action': 'batch_health',
            'ids[]': [self.bird.pk, second_bird.pk],
            'record_type': 'Deworming',
            'title': 'Batch deworming',
            'medicine': medicine.pk,
            'quantity_used': '3',
            'date_administered': '2026-11-01',
        })

        self.assertEqual(response.status_code, 200)
        medicine.refresh_from_db()
        self.assertEqual(medicine.stock_quantity, Decimal('4.00'))
        self.assertEqual(HealthRecord.objects.count(), 2)

    def test_batch_health_rejects_insufficient_total_stock(self):
        medicine = self.make_medicine(stock_quantity=Decimal('5.00'))
        second_bird = FlockMember.objects.create(
            user=self.user,
            tag_number='K-003',
            gender='Stag',
            status='Active',
        )

        response = self.client.post(reverse('info:batch_action_ajax'), {
            'action': 'batch_health',
            'ids[]': [self.bird.pk, second_bird.pk],
            'record_type': 'Deworming',
            'title': 'Batch deworming',
            'medicine': medicine.pk,
            'quantity_used': '3',
            'date_administered': '2026-11-01',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('not enough', response.json()['error'].lower())
        medicine.refresh_from_db()
        self.assertEqual(medicine.stock_quantity, Decimal('5.00'))
        self.assertFalse(HealthRecord.objects.exists())

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

    def test_flock_and_health_pages_render_with_cabinet_medicine(self):
        Medicine.objects.create(
            user=self.user,
            name='Test vaccine',
            category='Vaccine',
            unit='dose',
            stock_quantity=Decimal('5.00'),
        )

        for page_name in ('info:info_list', 'info:health_list'):
            with self.subTest(page=page_name):
                response = self.client.get(reverse(page_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Test vaccine')

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
            status='Retired',
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


class InlineQuickFormRenderTests(FlockTestCase):
    def test_flock_page_renders_quick_member_form(self):
        response = self.client.get(reverse('info:info_list'))
        self.assertContains(response, 'id="quickMemberForm"')
        self.assertContains(response, 'class="collapse" id="quickMemberFormCollapse"')
        self.assertContains(response, 'data-bs-target="#quickMemberFormCollapse"')

    def test_dashboard_does_not_render_quick_member_form(self):
        response = self.client.get(reverse('dashboard'))
        self.assertNotContains(response, 'id="quickMemberForm"')
        self.assertNotContains(response, 'Add flock member')

    def test_breeding_page_renders_quick_pen_form(self):
        response = self.client.get(reverse('info:breeding_list'))
        self.assertContains(response, 'id="quickPenForm"')
        self.assertContains(response, 'class="collapse" id="quickPenFormCollapse"')
        self.assertContains(response, 'data-bs-target="#quickPenFormCollapse"')

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
        self.assertContains(response, 'class="collapse" id="quickHealthFormCollapse"')
        self.assertContains(response, 'data-bs-target="#quickHealthFormCollapse"')

    def test_medicine_page_renders_quick_medicine_form(self):
        response = self.client.get(reverse('info:medicine_list'))
        self.assertContains(response, 'id="quickMedicineForm"')
        self.assertContains(response, 'class="collapse" id="quickMedicineFormCollapse"')
        self.assertContains(response, 'data-bs-target="#quickMedicineFormCollapse"')


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


