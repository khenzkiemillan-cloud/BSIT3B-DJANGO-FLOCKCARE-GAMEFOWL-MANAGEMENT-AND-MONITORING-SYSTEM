from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class HomeViewTests(TestCase):
    def test_home_renders_for_authenticated_user(self):
        user = get_user_model().objects.create_user(username='admin', password='secret1234')

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

    def test_home_requires_login(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 302)

    def test_dashboard_uses_dashboard_url(self):
        self.assertEqual(reverse('dashboard'), '/dashboard/')
