"""
apps/lgpd/views.py
Direitos do titular LGPD (req 4.8 / 4.9 / 4.10 / 4.11 - RNE04)
"""
import json
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib import messages

from apps.auditoria.utils import registrar_evento

logger = logging.getLogger('auditoria')


@login_required
def painel_lgpd(request):
    """Painel de direitos do titular (req 4.8)."""
    user = request.user
    consentimento = getattr(user, 'consentimento', None)
    return render(request, 'lgpd/painel_lgpd.html', {
        'user': user,
        'consentimento': consentimento,
        'dados_coletados': [
            {'campo': 'Nome completo', 'finalidade': 'Identificação do paciente'},
            {'campo': 'E-mail', 'finalidade': 'Autenticação e comunicação'},
            {'campo': 'Telefone', 'finalidade': 'Contato em caso de urgência'},
            {'campo': 'Dados de agendamento', 'finalidade': 'Gestão de consultas'},
            {'campo': 'Logs de acesso (IP)', 'finalidade': 'Segurança e auditoria'},
        ],
    })


@login_required
def exportar_dados(request):
    """
    Exportação completa dos dados do titular (req 4.9 / RF04).
    Retorna JSON estruturado para download.
    """
    user = request.user
    agendamentos = list(
        user.agendamentos.values('data_hora', 'medico__first_name', 'status', 'criado_em')
    ) if hasattr(user, 'agendamentos') else []

    consentimento = getattr(user, 'consentimento', None)

    dados = {
        'exportado_em': timezone.now().isoformat(),
        'sistema': 'Sistema de Agendamento Clínico Seguro',
        'titular': {
            'id': user.id,
            'nome': user.get_full_name(),
            'email': user.email,
            'telefone': getattr(user.perfil, 'telefone', '') if hasattr(user, 'perfil') else '',
            'data_cadastro': user.date_joined.isoformat(),
        },
        'consentimento': {
            'versao': consentimento.versao_termo if consentimento else None,
            'data': consentimento.data_consentimento.isoformat() if consentimento else None,
            'finalidade': consentimento.finalidade if consentimento else None,
            'status': 'ATIVO' if (consentimento and consentimento.consentiu) else 'REVOGADO',
        },
        'agendamentos': agendamentos,
    }

    registrar_evento(request, 'LGPD_EXPORTACAO', f'Exportação de dados: {user.email}', sucesso=True)
    logger.info(f'LGPD_EXPORTACAO | email={user.email}')

    response = HttpResponse(
        json.dumps(dados, ensure_ascii=False, indent=2, default=str),
        content_type='application/json; charset=utf-8',
    )
    response['Content-Disposition'] = f'attachment; filename="meus_dados_{user.id}.json"'
    return response


@login_required
@require_POST
def excluir_conta(request):
    """
    Exclusão definitiva da conta + revogação do consentimento (req 4.10 / RF05 / RNE04).
    """
    user = request.user
    email = user.email

    # Revogar consentimento antes de deletar
    consentimento = getattr(user, 'consentimento', None)
    if consentimento:
        consentimento.consentiu = False
        consentimento.data_revogacao = timezone.now()
        consentimento.save(update_fields=['consentiu', 'data_revogacao'])

    registrar_evento(request, 'LGPD_EXCLUSAO', f'Exclusão de conta solicitada: {email}', sucesso=True)
    logger.info(f'LGPD_EXCLUSAO | email={email}')

    logout(request)
    user.delete()   # CASCADE apaga perfil, consentimento e agendamentos

    messages.success(request, 'Sua conta e todos os seus dados foram removidos permanentemente.')
    return redirect('login')
