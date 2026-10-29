from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Info


class InfoContactAndStatusTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='info-owner',
            password='test-password',
        )
        self.client.force_login(self.user)

    def test_create_info_saves_phone_and_marital_status(self):
        response = self.client.post(reverse('info:info_save_ajax'), {
            'name': 'Alex Example',
            'age': '30',
            'address': 'Example Street',
            'email': 'alex@example.com',
            'phone_number': '+1 555 0100',
            'marital_status': Info.MaritalStatus.MARRIED,
        })

        self.assertEqual(response.status_code, 200)
        info = Info.objects.get(user=self.user, name='Alex Example')
        self.assertEqual(info.phone_number, '+1 555 0100')
        self.assertEqual(info.marital_status, Info.MaritalStatus.MARRIED)
        self.assertEqual(response.json()['phone_number'], '+1 555 0100')
        self.assertEqual(response.json()['marital_status'], Info.MaritalStatus.MARRIED)

        list_response = self.client.get(reverse('info:info_list_ajax'))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()['data'][0]['phone_number'], '+1 555 0100')
        self.assertEqual(list_response.json()['data'][0]['marital_status'], Info.MaritalStatus.MARRIED)

        detail_response = self.client.get(reverse('info:info_get_ajax', args=[info.pk]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()['phone_number'], '+1 555 0100')
        self.assertEqual(detail_response.json()['marital_status'], Info.MaritalStatus.MARRIED)

    def test_save_rejects_unknown_marital_status(self):
        response = self.client.post(reverse('info:info_save_ajax'), {
            'name': 'Alex Example',
            'age': '30',
            'address': 'Example Street',
            'marital_status': 'unknown',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('status', response.json()['error'])
