"""
apps/autenticacao/utils.py
Handler de lockout do django-axes e utilitários
"""
import logging
from django.http import HttpResponse
from django.shortcuts import render

logger = logging.getLogger('auditoria')


def axes_lockout_handler(request, credentials, *args, **kwargs):
    """
    Chamado pelo django-axes quando o usuário atinge o limite de tentativas (RNF02).
    Registra no log de auditoria e retorna resposta de bloqueio.
    """
    email = credentials.get('username', 'desconhecido')
    ip = request.META.get('REMOTE_ADDR', '')
    logger.warning(
        f'BRUTE_FORCE_BLOQUEIO | email={email} | ip={ip} | '
        f'limite=5 tentativas atingido | acao=bloqueio_1h'
    )
    return render(request, 'autenticacao/bloqueado.html', {
        'email': email,
        'tempo_bloqueio': '1 hora',
    }, status=429)
