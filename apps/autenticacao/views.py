"""
apps/autenticacao/views.py
Autenticação em duas etapas (RNE02), gestão de sessão (RNF03)
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp import devices_for_user
import qrcode
import qrcode.image.svg
import io, base64

from .models import PerfilUsuario, TentativaLogin
from apps.auditoria.utils import registrar_evento

logger = logging.getLogger('auditoria')


def _get_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR', '')


# ─── CADASTRO ─────────────────────────────────────────────────────────────────
@require_http_methods(['GET', 'POST'])
def cadastro(request):
    if request.user.is_authenticated:
        return redirect('painel')

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        email = request.POST.get('email', '').strip().lower()
        telefone = request.POST.get('telefone', '').strip()
        senha = request.POST.get('senha', '')
        senha2 = request.POST.get('senha2', '')
        consentimento = request.POST.get('consentimento')

        erros = []
        if not all([nome, email, telefone, senha]):
            erros.append('Preencha todos os campos obrigatórios.')
        if senha != senha2:
            erros.append('As senhas não coincidem.')
        if len(senha) < 8:
            erros.append('A senha deve ter no mínimo 8 caracteres.')
        if not consentimento:
            erros.append('É obrigatório aceitar os termos para se cadastrar (LGPD).')
        if User.objects.filter(email=email).exists():
            erros.append('Este e-mail já está cadastrado.')

        if erros:
            for e in erros:
                messages.error(request, e)
            return render(request, 'autenticacao/cadastro.html', {'form_data': request.POST})

        # Cria usuário — Django aplica PBKDF2+SHA256+salt automaticamente (RNF01)
        partes = nome.split(' ', 1)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=senha,
            first_name=partes[0],
            last_name=partes[1] if len(partes) > 1 else '',
        )
        PerfilUsuario.objects.create(user=user, telefone=telefone)

        # Registra consentimento LGPD (RNE01, req 4.4 / 4.5 / 4.7)
        from apps.lgpd.models import ConsentimentoLGPD
        ConsentimentoLGPD.objects.create(
            user=user,
            versao_termo='1.0',
            ip_consentimento=_get_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        registrar_evento(request, 'CADASTRO', f'Novo paciente cadastrado: {email}', sucesso=True)
        logger.info(f'CADASTRO_SUCESSO | email={email} | ip={_get_ip(request)}')
        messages.success(request, 'Cadastro realizado! Faça login e configure o 2FA.')
        return redirect('login')

    return render(request, 'autenticacao/cadastro.html')


# ─── LOGIN ETAPA 1 (senha) ────────────────────────────────────────────────────
@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated and request.user.is_verified():
        return redirect('painel')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        senha = request.POST.get('senha', '')
        ip = _get_ip(request)

        user = authenticate(request, username=email, password=senha)

        if user is not None:
            # Senha correta — verificar se tem 2FA configurado
            perfil = getattr(user, 'perfil', None)
            dispositivos = list(devices_for_user(user, confirmed=True))

            if not dispositivos:
                # 2FA não configurado: faz login direto e redireciona para configurar
                login(request, user)
                if perfil:
                    perfil.ultimo_acesso = timezone.now()
                    perfil.save(update_fields=['ultimo_acesso'])
                TentativaLogin.objects.create(
                    usuario_email=email, ip_address=ip, sucesso=True,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                )
                logger.info(f'LOGIN_SENHA_OK_SEM_2FA | email={email} | ip={ip}')
                messages.warning(request, 'Configure o 2FA para maior segurança.')
                return redirect('configurar_2fa')

            # Senha OK → salva user_id na sessão e pede 2FA
            request.session['pre_auth_user_id'] = user.id
            TentativaLogin.objects.create(
                usuario_email=email, ip_address=ip, sucesso=False,
                motivo_falha='', user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            logger.info(f'LOGIN_ETAPA1_OK | email={email} | ip={ip}')
            return redirect('verificar_2fa')
        else:
            TentativaLogin.objects.create(
                usuario_email=email, ip_address=ip, sucesso=False,
                motivo_falha='senha_incorreta',
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            logger.warning(f'LOGIN_FALHA | email={email} | ip={ip} | motivo=senha_incorreta')
            messages.error(request, 'E-mail ou senha inválidos.')

    return render(request, 'autenticacao/login.html')


# ─── LOGIN ETAPA 2 (TOTP 2FA) ─────────────────────────────────────────────────
@require_http_methods(['GET', 'POST'])
def verificar_2fa(request):
    user_id = request.session.get('pre_auth_user_id')
    if not user_id:
        return redirect('login')

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return redirect('login')

    ip = _get_ip(request)

    if request.method == 'POST':
        token = request.POST.get('token', '').strip().replace(' ', '')
        dispositivos = list(devices_for_user(user, confirmed=True))

        verificado = False
        for dispositivo in dispositivos:
            if dispositivo.verify_token(token):
                verificado = True
                break

        if verificado:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            # Marca sessão como verificada pelo OTP
            request.session['otp_device_id'] = dispositivo.persistent_id

            perfil = getattr(user, 'perfil', None)
            if perfil:
                perfil.ultimo_acesso = timezone.now()
                perfil.otp_ativo = True
                perfil.save(update_fields=['ultimo_acesso', 'otp_ativo'])

            # Atualiza tentativa de login como sucesso
            TentativaLogin.objects.filter(
                usuario_email=user.email, sucesso=False, motivo_falha=''
            ).order_by('-timestamp').first() and \
            TentativaLogin.objects.filter(
                usuario_email=user.email, sucesso=False, motivo_falha=''
            ).order_by('-timestamp').update(sucesso=True)

            del request.session['pre_auth_user_id']
            registrar_evento(request, 'LOGIN_2FA', f'Login completo via 2FA: {user.email}', sucesso=True)
            logger.info(f'LOGIN_2FA_OK | email={user.email} | ip={ip}')
            return redirect('painel')
        else:
            TentativaLogin.objects.create(
                usuario_email=user.email, ip_address=ip, sucesso=False,
                motivo_falha='2fa_invalido',
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            logger.warning(f'LOGIN_2FA_FALHA | email={user.email} | ip={ip}')
            messages.error(request, 'Token inválido ou expirado. Tente novamente.')

    return render(request, 'autenticacao/verificar_2fa.html', {'email': user.email})


# ─── CONFIGURAR 2FA ───────────────────────────────────────────────────────────
@login_required
def configurar_2fa(request):
    user = request.user
    dispositivos = list(devices_for_user(user, confirmed=True))

    if request.method == 'POST':
        token = request.POST.get('token', '').strip()
        # Busca dispositivo não confirmado
        try:
            device = TOTPDevice.objects.get(user=user, confirmed=False)
        except TOTPDevice.DoesNotExist:
            messages.error(request, 'Dispositivo não encontrado. Recarregue a página.')
            return redirect('configurar_2fa')

        if device.verify_token(token):
            device.confirmed = True
            device.save()
            perfil = getattr(user, 'perfil', None)
            if perfil:
                perfil.otp_ativo = True
                perfil.save(update_fields=['otp_ativo'])
            logger.info(f'2FA_CONFIGURADO | email={user.email} | ip={_get_ip(request)}')
            messages.success(request, '2FA configurado com sucesso!')
            return redirect('painel')
        else:
            messages.error(request, 'Token inválido. Verifique o app autenticador.')

    # Gera ou recupera dispositivo TOTP pendente
    device, criado = TOTPDevice.objects.get_or_create(
        user=user, confirmed=False,
        defaults={'name': f'TOTP-{user.email}'}
    )

    # Gera QR Code como base64
    uri = device.config_url
    qr = qrcode.make(uri)
    buffer = io.BytesIO()
    qr.save(buffer, format='PNG')
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'autenticacao/configurar_2fa.html', {
        'qr_b64': qr_b64,
        'secret': device.key,
        'ja_configurado': len(dispositivos) > 0,
    })


# ─── LOGOUT ───────────────────────────────────────────────────────────────────
@login_required
@require_POST
def logout_view(request):
    email = request.user.email
    ip = _get_ip(request)
    registrar_evento(request, 'LOGOUT', f'Logout: {email}', sucesso=True)
    logger.info(f'LOGOUT | email={email} | ip={ip}')
    logout(request)   # Invalida sessão completamente (req 1.10)
    messages.info(request, 'Você saiu com segurança.')
    return redirect('login')


# ─── PAINEL ───────────────────────────────────────────────────────────────────
@login_required
def painel(request):
    user = request.user
    perfil = getattr(user, 'perfil', None)
    agendamentos = user.agendamentos.select_related('medico__perfil').order_by('-data_hora')[:10] \
        if hasattr(user, 'agendamentos') else []

    return render(request, 'painel/painel.html', {
        'user': user,
        'perfil': perfil,
        'agendamentos': agendamentos,
        'otp_configurado': list(devices_for_user(user, confirmed=True)) != [],
    })
