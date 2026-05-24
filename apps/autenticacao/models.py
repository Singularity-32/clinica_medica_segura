"""
apps/autenticacao/models.py
Perfil estendido do usuário - chave primária = id do User (OneToOne)
"""
import uuid
from django.db import models
from django.contrib.auth.models import User


class PerfilUsuario(models.Model):
    """
    Extensão do User nativo do Django.
    Chave primária: id do User (OneToOneField → user_id como PK da tabela).
    Dados pessoais mínimos conforme RF01 / RNE01.
    """
    # ── PK = id do User (req: chave primária como identificador do usuário) ──
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,       # user_id É a PK desta tabela
        related_name='perfil',
        verbose_name='Usuário',
    )

    # ── Dados pessoais mínimos (RF01 - minimização LGPD) ─────────────────────
    telefone = models.CharField(max_length=20, verbose_name='Telefone')
    tipo = models.CharField(
        max_length=10,
        choices=[('paciente', 'Paciente'), ('medico', 'Médico')],
        default='paciente',
        verbose_name='Tipo de usuário',
    )

    # ── Controle de sessão (req 1.9 / 1.10) ──────────────────────────────────
    ultimo_acesso = models.DateTimeField(null=True, blank=True)

    # ── 2FA Status (req 1.5) ─────────────────────────────────────────────────
    otp_ativo = models.BooleanField(default=False, verbose_name='2FA ativo')

    class Meta:
        db_table = 'perfil_usuario'
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'

    def __str__(self):
        return f'{self.user.get_full_name()} ({self.tipo})'


class TentativaLogin(models.Model):
    """
    Registro de tentativas de login para auditoria (req 5.1 / 5.2).
    Complementa o django-axes com registro próprio no banco.
    """
    usuario_email = models.EmailField(verbose_name='E-mail tentado')
    ip_address = models.GenericIPAddressField(verbose_name='IP de origem')
    sucesso = models.BooleanField(default=False, verbose_name='Sucesso?')
    motivo_falha = models.CharField(
        max_length=100, blank=True,
        choices=[
            ('senha_incorreta', 'Senha incorreta'),
            ('2fa_invalido', '2FA inválido'),
            ('conta_bloqueada', 'Conta bloqueada'),
            ('sessao_expirada', 'Sessão expirada'),
        ],
        verbose_name='Motivo da falha',
    )
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Timestamp')
    user_agent = models.TextField(blank=True, verbose_name='User-Agent')

    class Meta:
        db_table = 'tentativa_login'
        verbose_name = 'Tentativa de Login'
        verbose_name_plural = 'Tentativas de Login'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['usuario_email', 'timestamp']),
        ]

    def __str__(self):
        status = 'OK' if self.sucesso else 'FALHA'
        return f'[{status}] {self.usuario_email} @ {self.ip_address} - {self.timestamp}'
