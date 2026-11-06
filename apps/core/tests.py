from django.contrib.auth import get_user_model
from django.template.loader import get_template
from django.test import TestCase
from django.urls import reverse


class AdminRegistrationTests(TestCase):
    def test_legacy_and_flock_models_are_accessible_in_admin(self):
        admin = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='secret1234',
        )
        self.client.force_login(admin)

        admin_urls = [
            'admin:core_chicken_changelist',
            'admin:core_chickenclassification_changelist',
            'admin:core_breedingrecord_changelist',
            'admin:core_healthrecord_changelist',
            'admin:core_feedrecord_changelist',
            'admin:core_supply_changelist',
            'admin:core_expense_changelist',
            'admin:info_breed_changelist',
            'admin:info_flockmember_changelist',
            'admin:info_healthrecord_changelist',
        ]

        for url_name in admin_urls:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)


class HomeViewTests(TestCase):
    def test_home_renders_for_authenticated_user(self):
        user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='secret1234',
        )

        self.client.force_login(user)
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertContains(response, '<turbo-frame id="main-content"')
        self.assertContains(response, 'data-turbo-action="advance"')
        users_url = reverse('users:user_list')
        self.assertContains(
            response,
            f'href="{users_url}" data-turbo-frame="main-content"',
            html=False,
        )
        flock_url = reverse('info:info_list')
        self.assertContains(
            response,
            f'href="{flock_url}" data-turbo-frame="main-content"',
            html=False,
        )

    def test_base_layout_does_not_load_unused_chart_libraries(self):
        user = get_user_model().objects.create_user(username='admin', password='secret1234')

        self.client.force_login(user)
        response = self.client.get(reverse('dashboard'))

        self.assertNotContains(response, 'apexcharts.min.js')
        self.assertNotContains(response, 'jsvectormap.min.js')
        self.assertNotContains(response, 'chart-visitors')

    def test_public_sidebar_template_exists(self):
        self.assertIsNotNone(get_template('theme/public_sidebar.html'))

    def test_non_superuser_does_not_see_users_navigation(self):
        user = get_user_model().objects.create_user(
            username='handler',
            password='secret1234',
        )

        self.client.force_login(user)
        response = self.client.get(reverse('dashboard'))

        self.assertNotContains(response, f'href="{reverse("users:user_list")}"')

    def test_home_requires_login(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 302)

    def test_dashboard_uses_dashboard_url(self):
        self.assertEqual(reverse('dashboard'), '/dashboard/')


class AuthenticationRedirectTests(TestCase):
    def setUp(self):
        self.password = 'FlockCare!2026'
        self.user = get_user_model().objects.create_user(
            username='handler',
            password=self.password,
        )

    def test_login_redirects_to_safe_next_url(self):
        response = self.client.post(reverse('login'), {
            'username': self.user.username,
            'password': self.password,
            'next': reverse('info:info_list'),
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('info:info_list'))

    def test_login_ignores_external_next_url(self):
        response = self.client.post(reverse('login'), {
            'username': self.user.username,
            'password': self.password,
            'next': 'https://malicious.example/steal',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_login_page_preserves_next_in_form(self):
        response = self.client.get(reverse('login'), {'next': reverse('info:info_list')})

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'<input type="hidden" name="next" value="{reverse("info:info_list")}">',
            html=True,
        )

    def test_register_page_renders(self):
        response = self.client.get(reverse('register'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/register.html')
        self.assertContains(response, 'name="confirm_password"')

    def test_register_redirects_to_safe_next_url(self):
        response = self.client.post(reverse('register'), {
            'username': 'new-handler',
            'first_name': 'New',
            'last_name': 'Handler',
            'email': 'new-handler@example.com',
            'password': self.password,
            'confirm_password': self.password,
            'next': reverse('info:info_list'),
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('info:info_list'))
