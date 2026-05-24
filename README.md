# 🏥 Sistema de Agendamento Clínico Seguro

**Samuel Oliveira Acácio — RGM: 11231100856**  
Engenharia de Software — UMC 2026  
Disciplina: Políticas de Segurança da Informação (PSI)

---

## ⚡ Setup Rápido (5 passos)

### 1. Pré-requisitos
- Python 3.12+
- PostgreSQL 15+
- pip

### 2. Clonar e criar ambiente virtual
```bash
cd projeto/
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar o banco PostgreSQL

**Criar banco e usuário:**
```sql
-- No psql como postgres:
CREATE DATABASE clinica_segura;
CREATE USER app_clinica WITH PASSWORD 'medico_da_alma';
GRANT ALL PRIVILEGES ON DATABASE clinica_segura TO app_clinica;
```

**Executar o schema (documentação — Django faz as migrations automaticamente):**
```bash
# Opcional: visualizar o SQL gerado
python manage.py sqlmigrate autenticacao 0001
```

### 5. Variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto (nunca versione este arquivo):
```
SECRET_KEY=gere-uma-chave-com-python-secrets-token-hex-50
DEBUG=True
DB_NAME=clinica_segura
DB_USER=app_clinica
DB_PASSWORD=troque_em_producao
DB_HOST=localhost
DB_PORT=5432
```

### 6. Rodar migrations e criar superusuário
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 7. Criar médico de exemplo (opcional)
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
from apps.autenticacao.models import PerfilUsuario
medico = User.objects.create_user('dr.silva@clinica.com', 'dr.silva@clinica.com', 'senha12345')
medico.first_name = 'João'; medico.last_name = 'Silva'; medico.save()
PerfilUsuario.objects.create(user=medico, telefone='11999990000', tipo='medico')
```

### 8. Iniciar servidor
```bash
mkdir -p logs
python manage.py runserver
```

Acesse: **http://localhost:8000**

---

## 📁 Estrutura do Projeto

```
projeto/
├── config/
│   ├── settings.py         ← Configurações Django (segurança, PostgreSQL, axes)
│   └── urls.py             ← URLs raiz
├── apps/
│   ├── autenticacao/       ← Login, 2FA TOTP, cadastro, middleware de sessão
│   ├── recuperacao/        ← Reset de senha com token seguro (req 2.x)
│   ├── auditoria/          ← Log central de eventos (req 5.x)
│   ├── lgpd/               ← Consentimento, exportação, exclusão (req 4.x)
│   └── agendamento/        ← CRUD de consultas (RNE03)
├── templates/              ← HTML/CSS/JS (sem framework frontend)
├── static/
│   ├── css/style.css       ← Design responsivo
│   └── js/main.js          ← Aviso timeout de sessão, utils
├── docs/
│   └── schema.sql          ← Schema PostgreSQL completo documentado
├── logs/
│   └── security.log        ← Log de auditoria (req 5.1-5.4)
└── requirements.txt
```

---

## 🔒 Mapa de Requisitos → Implementação

| Requisito | Implementação |
|-----------|---------------|
| 1.1–1.4 Hash PBKDF2+salt | `PASSWORD_HASHERS` Django nativo |
| 1.5–1.6 2FA TOTP | `django-otp` + Google Authenticator |
| 1.9–1.10 Sessão/Logout | `SESSION_COOKIE_AGE=900`, `logout()` invalida |
| 1.11 Brute force | `django-axes` — bloqueia após 5 tentativas |
| 2.1–2.7 Recuperação | `TokenRecuperacao` — 64 bytes, expira 1h, uso único |
| 3.1–3.2 TLS/HTTPS | `SECURE_SSL_REDIRECT`, `HSTS` em produção |
| 4.4–4.7 Consentimento | `ConsentimentoLGPD` — timestamp, versão, finalidade |
| 4.8–4.10 Direitos titular | Views de consulta, exportação JSON, exclusão |
| 5.1–5.4 Auditoria | `LogAuditoria` + `security.log` append-only |

---

## ⚠️ Sobre o SQLite vs PostgreSQL

Você estava certo em preferir PostgreSQL. O SQLite:
- **Roda apenas localmente** (arquivo `db.sqlite3` na máquina)
- **Não suporta políticas de acesso** (impossível fazer append-only no log — req 5.3)
- **Sem suporte a `INET`** para IPs, `TIMESTAMPTZ` nativo
- **Sem concorrência real** (trava escrita inteira)

O PostgreSQL resolve todos esses pontos e é adequado para produção.
