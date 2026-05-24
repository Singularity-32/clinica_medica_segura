"""
apps/agendamento/views.py
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import Agendamento
from apps.auditoria.utils import registrar_evento

logger = logging.getLogger('auditoria')


@login_required
def novo_agendamento(request):
    medicos = User.objects.filter(perfil__tipo='medico').select_related('perfil')

    if request.method == 'POST':
        medico_id = request.POST.get('medico_id')
        data_hora = request.POST.get('data_hora')

        try:
            medico = User.objects.get(pk=medico_id, perfil__tipo='medico')
        except User.DoesNotExist:
            messages.error(request, 'Médico inválido.')
            return redirect('novo_agendamento')

        agendamento = Agendamento.objects.create(
            paciente=request.user,
            medico=medico,
            data_hora=data_hora,
        )
        registrar_evento(request, 'AGENDAMENTO', f'Novo agendamento #{agendamento.pk}', sucesso=True)
        messages.success(request, 'Consulta agendada com sucesso!')
        return redirect('painel')

    return render(request, 'agendamento/novo.html', {'medicos': medicos})


@login_required
@require_POST
def cancelar_agendamento(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk, paciente=request.user)
    agendamento.status = 'cancelado'
    agendamento.save(update_fields=['status'])
    registrar_evento(request, 'AGENDAMENTO', f'Cancelamento #{pk}', sucesso=True)
    messages.info(request, 'Agendamento cancelado.')
    return redirect('painel')
