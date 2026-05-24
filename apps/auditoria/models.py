"""
apps/auditoria/models.py
Log de auditoria persistido em banco (req 5.1 a 5.4)
"""
from django.db import models
from django.contrib.auth.models import User


class LogAuditoria(models.Model):
    TIPOS = [
        ('LOGIN_OK', 'Login bem-sucedido'),
        ('LOGIN_FALHA', 'Falha de login'),
        ('LOGIN_2FA', 'Autenticação 2FA'),
        ('LOGOUT', 'Logout'),
        ('CADASTRO', 'Cadastro'),
        ('RECUPERACAO_SENHA', 'Recuperação de senha'),
        ('LGPD_EXPORTACAO', 'Exportação de dados LGPD'),
        ('LGPD_EXCLUSAO', 'Exclusão de dados LGPD'),
        ('AGENDAMENTO', 'Agendamento'),
        ('BRUTE_FORCE', 'Tentativa de força bruta'),
        ('SESSAO_EXPIRADA', 'Sessão expirada'),
    ]

    tipo_evento = models.CharField(max_length=30, choices=TIPOS, verbose_name='Tipo')
    usuario = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='logs_auditoria',
        verbose_name='Usuário',
    )
    ip_address = models.GenericIPAddressField(verbose_name='IP')
    descricao = models.TextField(verbose_name='Descrição')
    sucesso = models.BooleanField(default=True, verbose_name='Sucesso?')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Timestamp')
    user_agent = models.TextField(blank=True, verbose_name='User-Agent')

    class Meta:
        db_table = 'log_auditoria'
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-timestamp']
        # Protege contra alteração: tabela append-only por design (req 5.3)
        indexes = [
            models.Index(fields=['tipo_evento', 'timestamp']),
            models.Index(fields=['usuario', 'timestamp']),
        ]

    def __str__(self):
        return f'[{self.tipo_evento}] {self.timestamp} - {self.ip_address}'
