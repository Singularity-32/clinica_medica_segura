"""
apps/recuperacao/models.py
Token seguro para recuperação de senha (req 2.x)
"""
import secrets
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class TokenRecuperacao(models.Model):
    """
    Token criptograficamente seguro para reset de senha.
    - 64 bytes aleatórios via secrets (req 2.2)
    - Expira em 1 hora (req 2.3)
    - Invalidado após uso (req 2.4)
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tokens_recuperacao',
        verbose_name='Usuário',
    )
    token = models.CharField(max_length=128, unique=True, verbose_name='Token')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    expira_em = models.DateTimeField(verbose_name='Expira em')
    usado = models.BooleanField(default=False, verbose_name='Usado?')
    ip_solicitacao = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'token_recuperacao'
        verbose_name = 'Token de Recuperação'

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(64)  # 64 bytes → req 2.2
        if not self.expira_em:
            self.expira_em = timezone.now() + timedelta(hours=1)  # req 2.3
        super().save(*args, **kwargs)

    @property
    def expirado(self):
        return timezone.now() > self.expira_em

    def invalidar(self):
        self.usado = True
        self.save(update_fields=['usado'])

    def __str__(self):
        return f'Token para {self.user.email} | exp={self.expira_em} | usado={self.usado}'
