from django.test import TestCase
from django.contrib.auth.models import User

class HashSenhaTest(TestCase):
    def test_senha_armazenada_como_hash(self):
        """RNF01: senha nunca armazenada em texto claro."""
        user = User.objects.create_user(
            username="teste@clinica.com",
            password="SenhaSegura123"
        )
        self.assertNotEqual(user.password, "SenhaSegura123")
        self.assertTrue(user.password.startswith("pbkdf2_sha256$"))

    def test_salts_unicos_por_usuario(self):
        """Req 1.3: salt criptográfico único por usuário."""
        u1 = User.objects.create_user("u1@c.com", password="MesmaSenha123")
        u2 = User.objects.create_user("u2@c.com", password="MesmaSenha123")
        self.assertNotEqual(u1.password, u2.password)