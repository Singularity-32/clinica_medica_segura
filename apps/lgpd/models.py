"""
apps/lgpd/models.py
Consentimento e direitos do titular (req 4.x)
"""
from django.db import models
from django.contrib.auth.models import User


class ConsentimentoLGPD(models.Model):
    """
    Registro de consentimento explícito (req 4.4 / 4.5 / 4.6 / 4.7).
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,       # user_id como PK
        related_name='consentimento',
        verbose_name='Usuário',
    )
    versao_termo = models.CharField(max_length=10, default='1.0', verbose_name='Versão do Termo')
    consentiu = models.BooleanField(default=True, verbose_name='Consentiu?')
    data_consentimento = models.DateTimeField(auto_now_add=True, verbose_name='Data do Consentimento')
    data_revogacao = models.DateTimeField(null=True, blank=True, verbose_name='Data da Revogação')
    ip_consentimento = models.GenericIPAddressField(verbose_name='IP do Consentimento')
    user_agent = models.TextField(blank=True, verbose_name='User-Agent')

    # Finalidade associada (req 4.2)
    finalidade = models.CharField(
        max_length=200,
        default='Agendamento de consultas médicas e comunicação com o paciente.',
        verbose_name='Finalidade',
    )

    class Meta:
        db_table = 'consentimento_lgpd'
        verbose_name = 'Consentimento LGPD'
        verbose_name_plural = 'Consentimentos LGPD'

    def __str__(self):
        status = 'ATIVO' if self.consentiu else 'REVOGADO'
        return f'[{status}] {self.user.email} - v{self.versao_termo}'
