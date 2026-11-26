from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Notification

User = get_user_model()
HOST = {"HTTP_HOST": "localhost"}


class NotificationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("user", password="Pass1234!", role="DIRECTION", is_staff=True)

    def test_send_and_list(self):
        Notification.send(self.user, "Bienveni", body="Kont ou kreye.")
        self.client.login(username="user", password="Pass1234!")
        response = self.client.get("/notifikasyon/", **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bienveni")

    def test_mark_read_and_badge_count(self):
        Notification.send(self.user, "Nouvo bagay")
        self.client.login(username="user", password="Pass1234!")
        liste = self.client.get("/notifikasyon/", **HOST)
        self.assertContains(liste, 'class="badge rounded-pill text-bg-danger">1')
        n = Notification.objects.get(recipient=self.user)
        response = self.client.post(f"/notifikasyon/lu/{n.pk}/", **HOST)
        self.assertEqual(response.status_code, 302)
        n.refresh_from_db()
        self.assertTrue(n.is_read)

    def test_cannot_read_others_notification(self):
        other = User.objects.create_user("other", password="Pass1234!")
        n = Notification.send(other, "Sekre")
        self.client.login(username="user", password="Pass1234!")
        response = self.client.post(f"/notifikasyon/lu/{n.pk}/", **HOST)
        self.assertEqual(response.status_code, 403)
