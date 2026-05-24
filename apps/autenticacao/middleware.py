"""
apps/autenticacao/middleware.py
Middleware de timeout de sessão por inatividade (RNF03 - 15 min)
"""
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages
import logging

logger = logging.getLogger('auditoria')

TIMEOUT_SEGUNDOS = 900  # 15 minutos


class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            ultima = request.session.get('ultima_atividade')
            agora = timezone.now().timestamp()

            if ultima and (agora - ultima) > TIMEOUT_SEGUNDOS:
                email = request.user.email
                ip = request.META.get('REMOTE_ADDR', '')
                logger.info(f'SESSAO_EXPIRADA | email={email} | ip={ip}')
                logout(request)
                messages.warning(request, 'Sua sessão expirou por inatividade. Faça login novamente.')
                return redirect('login')

            request.session['ultima_atividade'] = agora

        return self.get_response(request)
