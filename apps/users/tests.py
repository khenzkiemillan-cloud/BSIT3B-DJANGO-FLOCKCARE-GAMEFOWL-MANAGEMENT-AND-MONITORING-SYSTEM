from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()

STRONG_PASSWORD = 'FlockCare!2026'


class UserManagementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password=STRONG_PASSWORD,
        )
        self.client.force_login(self.admin)

    def test_user_list_renders_add_user_control(self):
        response = self.client.get(reverse('users:user_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/list.html')
        self.assertContains(response, 'Add User')
        self.assertContains(response, 'data-mode="create"')

    def test_create_user_via_ajax(self):
        response = self.client.post(reverse('users:user_save_ajax'), {
            'username': 'handler',
            'first_name': '  Juan  ',
            'last_name': 'Dela Cruz',
            'email': 'handler@example.com',
            'password': STRONG_PASSWORD,
            'is_active': 'true',
            'is_staff': 'false',
        })

        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username='handler')
        self.assertEqual(user.first_name, 'Juan')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_created_user_password_is_hashed(self):
        self.client.post(reverse('users:user_save_ajax'), {
            'username': 'handler',
            'email': 'handler@example.com',
            'password': STRONG_PASSWORD,
            'is_active': 'true',
            'is_staff': 'false',
        })

        user = User.objects.get(username='handler')
        self.assertNotEqual(user.password, STRONG_PASSWORD)
        self.assertTrue(user.check_password(STRONG_PASSWORD))

    def test_duplicate_username_is_rejected_case_insensitively(self):
        User.objects.create_user(username='ExistingUser', password=STRONG_PASSWORD)

        response = self.client.post(reverse('users:user_save_ajax'), {
            'username': 'existinguser',
            'password': STRONG_PASSWORD,
            'is_active': 'true',
            'is_staff': 'false',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('username', response.json()['error'].lower())

    def test_invalid_email_is_rejected(self):
        response = self.client.post(reverse('users:user_save_ajax'), {
            'username': 'handler',
            'email': 'not-an-email',
            'password': STRONG_PASSWORD,
            'is_active': 'true',
            'is_staff': 'false',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('valid email', response.json()['error'].lower())

    def test_weak_password_is_rejected(self):
        response = self.client.post(reverse('users:user_save_ajax'), {
            'username': 'handler',
            'password': '123',
            'is_active': 'true',
            'is_staff': 'false',
        })

        self.assertEqual(response.status_code, 400)

    def test_update_without_password_keeps_existing_password(self):
        user = User.objects.create_user(
            username='handler',
            password=STRONG_PASSWORD,
            is_active=True,
        )

        response = self.client.post(reverse('users:user_save_ajax'), {
            'id': user.pk,
            'username': 'handler',
            'email': 'handler@example.com',
            'password': '',
            'is_active': 'true',
            'is_staff': 'true',
        })

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_staff)
        self.assertTrue(user.check_password(STRONG_PASSWORD))

    def test_cannot_deactivate_own_account(self):
        response = self.client.post(reverse('users:user_save_ajax'), {
            'id': self.admin.pk,
            'username': self.admin.username,
            'email': self.admin.email,
            'is_active': 'false',
            'is_staff': 'true',
        })

        self.assertEqual(response.status_code, 400)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_cannot_delete_own_account(self):
        response = self.client.post(
            reverse('users:user_delete_ajax', args=[self.admin.pk])
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())

    def test_non_superuser_cannot_manage_users(self):
        staff = User.objects.create_user(
            username='staff-user',
            password=STRONG_PASSWORD,
            is_staff=True,
        )
        self.client.force_login(staff)

        response = self.client.get(reverse('users:user_list'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('dashboard'), response.url)

    def test_unknown_user_id_returns_404(self):
        response = self.client.post(reverse('users:user_save_ajax'), {
            'id': 'not-a-number',
            'username': 'handler',
            'password': STRONG_PASSWORD,
            'is_active': 'true',
        })

        self.assertEqual(response.status_code, 404)
        self.assertIn('not found', response.json()['error'].lower())


class UserProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='breeder-one',
            email='breeder@example.com',
            password=STRONG_PASSWORD,
        )
        self.client.force_login(self.user)

    def test_profile_page_renders_for_logged_in_user(self):
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')
        self.assertContains(response, 'Farm Profile &amp; Settings')

    def test_profile_updates_farm_and_user_details(self):
        response = self.client.post(reverse('users:profile'), {
            'first_name': 'Carlos',
            'last_name': 'Santos',
            'email': 'carlos@example.com',
            'farm_name': 'Santos Gamefarm',
            'contact_number': '+63 912 345 6789',
            'location': 'Batangas, Philippines',
            'association_id': 'FIGBA-2026-99',
            'bio': 'Sweater and Roundhead specialist.',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Carlos')
        self.assertEqual(self.user.profile.farm_name, 'Santos Gamefarm')
        self.assertEqual(self.user.profile.association_id, 'FIGBA-2026-99')

