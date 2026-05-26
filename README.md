# 🏥 Sistema de Agendamento Clínico Seguro

# 🏥 Sistema de Agendamento Clínico Seguro

**Samuel Oliveira Acácio — RGM: 11231100856**
Engenharia de Software — UMC 2026
Disciplina: Políticas de Segurança da Informação (PSI)
Professor: Dr. Fabiano Bezerra Menegidio

---

## ✅ Pré-requisitos

Antes de começar, certifique-se de ter instalado na sua máquina:

- [Python 3.12+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/download/win)
- [VS Code](https://code.visualstudio.com/) *(opcional, mas recomendado)*

> **Banco de dados:** não é necessário instalar nada. O sistema utiliza PostgreSQL hospedado em nuvem (Render), já configurado e pronto para uso.

---

## 🚀 Como rodar o projeto (passo a passo)

Abra o terminal e execute os comandos abaixo **um por vez**:

### 1. Clonar o repositório
```bash
git clone https://github.com/Singularity-32/clinica_medica_segura.git
cd clinica_medica_segura
```

### 2. Criar e ativar o ambiente virtual
```bash
python -m venv venv
venv\Scripts\activate
```

> Quando ativado, aparece `(venv)` no início da linha do terminal.

### 3. Instalar as dependências
```bash
pip install -r requirements.txt
pip install "psycopg[binary]"
pip install dj-database-url
```

### 4. Criar a pasta de logs
```bash
md logs
```

### 5. Rodar as migrations
```bash
python manage.py migrate
```

### 6. Criar um usuário administrador
```bash
python manage.py createsuperuser
```

### 7. Criar um médico de teste (para testar agendamento)
```bash
python manage.py shell
```

Cole no shell e pressione Enter:
```python
from django.contrib.auth.models import User
from apps.autenticacao.models import PerfilUsuario
m = User.objects.create_user('dr.silva@clinica.com', 'dr.silva@clinica.com', 'Senha12345')
m.first_name = 'João'; m.last_name = 'Silva'; m.save()
PerfilUsuario.objects.create(user=m, telefone='11999990000', tipo='medico')
exit()
```

### 8. Iniciar o servidor
```bash
python manage.py runserver
```

Acesse no navegador: **http://localhost:8000**

> Mantenha o terminal aberto enquanto usa o sistema.

---

## 🔐 Fluxo de testes de segurança

| # | O que testar | Como fazer |
|---|---|---|
| 1 | Cadastro + consentimento LGPD | Clique em "Cadastre-se" e observe o checkbox obrigatório |
| 2 | Autenticação em duas etapas (2FA) | Após cadastro, configure o 2FA com Google Authenticator |
| 3 | Bloqueio por força bruta | Tente logar 5 vezes com senha errada |
| 4 | Agendamento de consulta | Clique em "Agendar" e selecione Dr. João Silva |
| 5 | Exportação de dados (LGPD) | Clique em "Meus Dados" → "Baixar meus dados (JSON)" |
| 6 | Exclusão de conta | Clique em "Meus Dados" → "Excluir minha conta" |
| 7 | Tentar logar após exclusão | Use o e-mail excluído — sistema rejeita (dados removidos) |

---

## 🗂️ Estrutura do Projeto

```
clinica_medica_segura/
├── apps/
│   ├── autenticacao/     → Login, 2FA, cadastro, sessão
│   ├── recuperacao/      → Reset de senha com token seguro
│   ├── auditoria/        → Log central de eventos de segurança
│   ├── lgpd/             → Consentimento, exportação, exclusão
│   └── agendamento/      → Agendamento de consultas
├── config/
│   └── settings.py       → Configurações do sistema
├── templates/            → Telas HTML
├── static/               → CSS e JavaScript
├── docs/
│   └── schema.sql        → Schema do banco documentado
└── requirements.txt      → Dependências do projeto
```

---

## 🔒 Requisitos de Segurança Implementados

| Requisito | Implementação |
|---|---|
| Hash de senhas (PBKDF2-SHA256 + salt único) | Django PASSWORD_HASHERS |
| Autenticação de dois fatores (2FA TOTP) | django-otp + Google Authenticator |
| Bloqueio após 5 tentativas inválidas | django-axes |
| Sessão expira em 15 min de inatividade | SESSION_COOKIE_AGE = 900 |
| Comunicação HTTPS em produção | SECURE_SSL_REDIRECT |
| Log de auditoria append-only | security.log + tabela log_auditoria |
| Consentimento explícito (LGPD) | Checkbox obrigatório no cadastro |
| Exportação de dados (LGPD Art. 18) | Download JSON |
| Exclusão definitiva (LGPD Art. 18) | CASCADE no banco + revogação |

---

## ⚙️ Informações Técnicas

- **Framework:** Django 6.0.5 (Python)
- **Banco de dados:** PostgreSQL 16 (hospedado no Render — nuvem)
- **2FA:** TOTP via django-otp (Google Authenticator)
- **Proteção brute force:** django-axes
- **Frontend:** HTML5 + CSS3 + JavaScript puro
- **Repositório:** https://github.com/Singularity-32/clinica_medica_segura
