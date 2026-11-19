from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.template.loader import get_template
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.info.models import FlockMember, HealthRecord, Medicine


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


class TopbarNavigationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='handler',
            password='secret1234',
        )
        self.client.force_login(self.user)
        self.bird = FlockMember.objects.create(
            user=self.user,
            tag_number='K-001',
            gender='Cock',
            status='Active',
        )

    def test_topbar_renders_search_quick_add_and_alert_frame(self):
        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'data-topbar-search')
        self.assertContains(
            response,
            f'<turbo-frame id="topbar-alerts" src="{reverse("nav_alerts")}"',
            html=False,
        )
        self.assertContains(response, 'Quick add')

    def test_nav_alerts_reports_overdue_stock_and_expiry_issues(self):
        today = timezone.localdate()
        HealthRecord.objects.create(
            bird=self.bird,
            record_type='Vaccination',
            title='Late booster',
            date_administered=today - timedelta(days=40),
            next_due_date=today - timedelta(days=2),
        )
        Medicine.objects.create(
            user=self.user,
            name='Low vaccine',
            category='Vaccine',
            unit='ml',
            stock_quantity=Decimal('1.00'),
            low_stock_threshold=Decimal('5.00'),
        )
        Medicine.objects.create(
            user=self.user,
            name='Expired dewormer',
            category='Dewormer',
            unit='ml',
            stock_quantity=Decimal('10.00'),
            expiration_date=today - timedelta(days=1),
        )

        response = self.client.get(reverse('nav_alerts'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'theme/partials/topbar_alerts.html')
        self.assertContains(response, '<turbo-frame id="topbar-alerts">')
        alerts = response.context['nav_alerts']
        self.assertEqual(alerts['overdue_count'], 1)
        self.assertEqual(alerts['low_stock_count'], 1)
        self.assertEqual(alerts['expired_count'], 1)
        self.assertEqual(alerts['total'], 3)
        self.assertContains(response, 'Late booster')
        self.assertContains(response, 'Low vaccine')
        self.assertContains(response, 'Expired dewormer')

    def test_single_alert_label_uses_singular_grammar(self):
        Medicine.objects.create(
            user=self.user,
            name='Only low stock item',
            category='Vaccine',
            unit='ml',
            stock_quantity=Decimal('0.00'),
            low_stock_threshold=Decimal('1.00'),
        )

        response = self.client.get(reverse('nav_alerts'))

        self.assertContains(response, '1 alert needs attention')

    def test_due_soon_tasks_count_as_alerts_instead_of_empty_state(self):
        today = timezone.localdate()
        HealthRecord.objects.create(
            bird=self.bird,
            record_type='Vaccination',
            title='Upcoming booster',
            date_administered=today,
            next_due_date=today + timedelta(days=10),
        )

        response = self.client.get(reverse('nav_alerts'))

        alerts = response.context['nav_alerts']
        self.assertEqual(alerts['due_soon_count'], 1)
        self.assertEqual(alerts['total'], 1)
        self.assertContains(response, 'Upcoming booster')
        self.assertNotContains(response, "You're all caught up")

    def test_nav_alerts_ignores_other_users_items(self):
        other_user = get_user_model().objects.create_user(
            username='other-handler',
            password='secret1234',
        )
        Medicine.objects.create(
            user=other_user,
            name='Private low stock item',
            category='Vaccine',
            unit='ml',
            stock_quantity=Decimal('0.00'),
            low_stock_threshold=Decimal('1.00'),
        )

        response = self.client.get(reverse('nav_alerts'))

        self.assertEqual(response.context['nav_alerts']['total'], 0)
        self.assertNotContains(response, 'Private low stock item')

    def test_nav_alerts_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse('nav_alerts'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)
