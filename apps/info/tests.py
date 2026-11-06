from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Breed, FlockMember, HealthRecord


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
        })

        self.assertEqual(response.status_code, 200)
        member = FlockMember.objects.get(user=self.user, tag_number='K-003')
        self.assertEqual(member.breed, self.breed)
        self.assertEqual(member.weight_grams, 1850)
        self.assertEqual(member.wins, 2)

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


class FlockExportTests(FlockTestCase):
    def test_export_contains_user_flock(self):
        response = self.client.get(reverse('info:export_flock_csv'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        content = response.content.decode('utf-8-sig')
        self.assertIn('Tag Number', content)
        self.assertIn('K-001', content)
        self.assertIn('Kelso', content)
