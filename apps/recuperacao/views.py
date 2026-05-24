"""
apps/recuperacao/views.py
Fluxo de recuperação de senha seguro (req 2.1 a 2.7)
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from .models import TokenRecuperacao

logger = logging.getLogger('auditoria')


def _get_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR', '')


@require_http_methods(['GET', 'POST'])
def solicitar_recuperacao(request):
    """Etapa 1: solicita e-mail → gera token e envia link (req 2.1 / 2.6)."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        ip = _get_ip(request)

        # Resposta genérica (evita enumeração de e-mails)
        logger.info(f'RECUPERACAO_SOLICITADA | email={email} | ip={ip}')

        try:
            user = User.objects.get(email=email)
            # Invalida tokens antigos não usados
            TokenRecuperacao.objects.filter(user=user, usado=False).update(usado=True)

            token_obj = TokenRecuperacao.objects.create(user=user, ip_solicitacao=ip)
            link = f"{request.scheme}://{request.get_host()}/recuperacao/resetar/{token_obj.token}/"

            send_mail(
                subject='Redefinição de senha - Clínica Segura',
                message=(
                    f'Olá, {user.first_name}!\n\n'
                    f'Recebemos uma solicitação para redefinir sua senha.\n'
                    f'Clique no link abaixo (válido por 1 hora):\n\n{link}\n\n'
                    f'Se você não solicitou isso, ignore este e-mail.\n\n'
                    f'Equipe Clínica Segura'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
            logger.info(f'RECUPERACAO_TOKEN_GERADO | email={email} | ip={ip}')
        except User.DoesNotExist:
            logger.info(f'RECUPERACAO_EMAIL_NAO_ENCONTRADO | email={email} | ip={ip}')

        messages.success(
            request,
            'Se este e-mail estiver cadastrado, você receberá as instruções em breve.'
        )
        return redirect('login')

    return render(request, 'autenticacao/recuperar_senha.html')


@require_http_methods(['GET', 'POST'])
def resetar_senha(request, token):
    """Etapa 2: valida token e permite nova senha (req 2.3 / 2.4 / 2.5 / 2.7)."""
    try:
        token_obj = TokenRecuperacao.objects.get(token=token, usado=False)
    except TokenRecuperacao.DoesNotExist:
        logger.warning(f'RECUPERACAO_TOKEN_INVALIDO | token={token[:10]}... | ip={_get_ip(request)}')
        messages.error(request, 'Link inválido ou já utilizado.')
        return redirect('solicitar_recuperacao')

    # Verifica expiração (req 2.5)
    if token_obj.expirado:
        token_obj.invalidar()
        logger.warning(f'RECUPERACAO_TOKEN_EXPIRADO | email={token_obj.user.email}')
        messages.error(request, 'Este link expirou. Solicite um novo.')
        return redirect('solicitar_recuperacao')

    if request.method == 'POST':
        senha = request.POST.get('senha', '')
        senha2 = request.POST.get('senha2', '')

        if senha != senha2:
            messages.error(request, 'As senhas não coincidem.')
            return render(request, 'autenticacao/resetar_senha.html')

        if len(senha) < 8:
            messages.error(request, 'A senha deve ter no mínimo 8 caracteres.')
            return render(request, 'autenticacao/resetar_senha.html')

        user = token_obj.user
        user.set_password(senha)
        user.save()
        token_obj.invalidar()  # Invalida após uso (req 2.4)

        logger.info(f'RECUPERACAO_SUCESSO | email={user.email} | ip={_get_ip(request)}')
        messages.success(request, 'Senha redefinida com sucesso! Faça login.')
        return redirect('login')

    return render(request, 'autenticacao/resetar_senha.html', {'token': token})
