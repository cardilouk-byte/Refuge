from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Department, StaffPosition

User = get_user_model()


class DepartmentTest(TestCase):
    def setUp(self):
        User.objects.create_superuser("adm", "a@a.ht", "Pass1234!")
        self.client.login(username="adm", password="Pass1234!")

    def test_tree_renders_hierarchy(self):
        direction = Department.objects.create(name="Direction Générale", kind="DIRECTION")
        Department.objects.create(name="Secrétariat", kind="ADMINISTRATION", parent=direction)
        response = self.client.get("/organigramme/")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn("Direction Générale", body)
        self.assertIn("Secrétariat", body)

    def test_create_department(self):
        response = self.client.post("/organigramme/depatman/nouveau/", {
            "name": "Bibliothèque", "code": "BIB", "kind": "APPUI",
            "head_title": "Bibliothécaire", "order": 0, "is_active": "on",
        })
        self.assertRedirects(response, "/organigramme/")
        self.assertTrue(Department.objects.filter(name="Bibliothèque").exists())

    def test_delete_department_with_children_blocked(self):
        parent = Department.objects.create(name="Parent")
        Department.objects.create(name="Enfant", parent=parent)
        response = self.client.post(f"/organigramme/depatman/{parent.pk}/supprimer/")
        self.assertRedirects(response, "/organigramme/")
        self.assertTrue(Department.objects.filter(pk=parent.pk).exists())

    def test_staff_position_person_name(self):
        dept = Department.objects.create(name="Direction")
        position = StaffPosition.objects.create(
            department=dept, title="Directeur", external_name="Jean Baptiste", is_head=True,
        )
        self.assertEqual(position.person_name, "Jean Baptiste")
