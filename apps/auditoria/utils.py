"""
apps/auditoria/utils.py
Registro centralizado de eventos de segurança (req 5.1 a 5.4)
"""
import logging
from django.utils import timezone

logger = logging.getLogger('auditoria')


def registrar_evento(request, tipo_evento: str, descricao: str, sucesso: bool = True):
    """
    Registra evento de segurança no log e no modelo de auditoria.
    Usado por todas as views para garantir rastreabilidade (req 5.3 / 5.4).
    """
    from .models import LogAuditoria

    ip = _get_ip(request)
    user = request.user if request.user.is_authenticated else None

    nivel = logging.INFO if sucesso else logging.WARNING
    logger.log(
        nivel,
        f'{tipo_evento} | '
        f'user={getattr(user, "email", "anonimo")} | '
        f'ip={ip} | '
        f'sucesso={sucesso} | '
        f'descricao={descricao}'
    )

    LogAuditoria.objects.create(
        tipo_evento=tipo_evento,
        usuario=user,
        ip_address=ip,
        descricao=descricao,
        sucesso=sucesso,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )


def _get_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR', '')
