"""
apps/agendamento/models.py
Agendamento mínimo (RNE03 / RF03)
"""
from django.db import models
from django.contrib.auth.models import User


class Agendamento(models.Model):
    STATUS = [
        ('agendado', 'Agendado'),
        ('cancelado', 'Cancelado'),
        ('realizado', 'Realizado'),
    ]

    paciente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='agendamentos',
        verbose_name='Paciente',
    )
    medico = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='consultas',
        limit_choices_to={'perfil__tipo': 'medico'},
        verbose_name='Médico',
    )
    data_hora = models.DateTimeField(verbose_name='Data e Hora')
    status = models.CharField(max_length=15, choices=STATUS, default='agendado')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'agendamento'
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'
        ordering = ['-data_hora']

    def __str__(self):
        return f'{self.paciente.get_full_name()} → Dr. {self.medico.get_full_name()} | {self.data_hora}'
