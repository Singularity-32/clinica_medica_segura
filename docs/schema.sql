-- ═══════════════════════════════════════════════════════════════════════════════
-- Sistema de Agendamento Clínico Seguro — Schema PostgreSQL
-- Samuel Oliveira Acácio — RGM: 11231100856
-- Engenharia de Software — UMC 2026
--
-- NOTA DE SEGURANÇA (req 3.4 / 3.5):
--   • Hashes de senha gerados pelo Django (PBKDF2+SHA256+salt único por usuário)
--   • IDs sequenciais BigInt — user.id é a chave primária de identidade
--   • Tabelas de log configuradas como append-only via policy (req 5.3)
-- ═══════════════════════════════════════════════════════════════════════════════

-- ── Extensões ────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- para gen_random_uuid() se necessário

-- ── 1. Usuários (Django nativo — auth_user) ───────────────────────────────────
-- Tabela gerenciada pelo Django. Senha = pbkdf2_sha256$<iterações>$<salt>$<hash>
-- NÃO criar manualmente; incluída aqui para documentação do schema.
--
-- CREATE TABLE auth_user (
--   id            BIGSERIAL    PRIMARY KEY,
--   username      VARCHAR(150) NOT NULL UNIQUE,   -- usamos email como username
--   email         VARCHAR(254) NOT NULL UNIQUE,
--   password      VARCHAR(128) NOT NULL,          -- PBKDF2+SHA256+salt (RNF01)
--   first_name    VARCHAR(150) NOT NULL DEFAULT '',
--   last_name     VARCHAR(150) NOT NULL DEFAULT '',
--   is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
--   is_staff      BOOLEAN      NOT NULL DEFAULT FALSE,
--   is_superuser  BOOLEAN      NOT NULL DEFAULT FALSE,
--   date_joined   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
--   last_login    TIMESTAMPTZ
-- );

-- ── 2. Perfil do Usuário ──────────────────────────────────────────────────────
-- PK = user_id (id do auth_user), conforme solicitado
CREATE TABLE IF NOT EXISTS perfil_usuario (
    user_id         BIGINT       PRIMARY KEY
                    REFERENCES auth_user(id) ON DELETE CASCADE,
    telefone        VARCHAR(20)  NOT NULL,
    tipo            VARCHAR(10)  NOT NULL DEFAULT 'paciente'
                    CHECK (tipo IN ('paciente', 'medico')),
    otp_ativo       BOOLEAN      NOT NULL DEFAULT FALSE,
    ultimo_acesso   TIMESTAMPTZ
);

COMMENT ON TABLE  perfil_usuario              IS 'Extensão do usuário Django. PK = user_id (req: identificador do usuário).';
COMMENT ON COLUMN perfil_usuario.user_id      IS 'Chave primária e estrangeira para auth_user.id.';
COMMENT ON COLUMN perfil_usuario.telefone     IS 'Coletado com finalidade específica (LGPD minimização RF01).';
COMMENT ON COLUMN perfil_usuario.otp_ativo    IS 'Indica se o 2FA TOTP foi confirmado (req 1.5).';

-- ── 3. Consentimento LGPD ────────────────────────────────────────────────────
-- PK = user_id (req 4.4 / 4.5 / 4.7)
CREATE TABLE IF NOT EXISTS consentimento_lgpd (
    user_id             BIGINT       PRIMARY KEY
                        REFERENCES auth_user(id) ON DELETE CASCADE,
    versao_termo        VARCHAR(10)  NOT NULL DEFAULT '1.0',
    consentiu           BOOLEAN      NOT NULL DEFAULT TRUE,
    data_consentimento  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    data_revogacao      TIMESTAMPTZ,
    ip_consentimento    INET         NOT NULL,
    user_agent          TEXT         NOT NULL DEFAULT '',
    finalidade          VARCHAR(200) NOT NULL
                        DEFAULT 'Agendamento de consultas médicas e comunicação com o paciente.'
);

COMMENT ON TABLE  consentimento_lgpd                   IS 'Registro de consentimento explícito (LGPD art. 7º, I). PK = user_id.';
COMMENT ON COLUMN consentimento_lgpd.versao_termo      IS 'Versão do termo aceito (req 4.7).';
COMMENT ON COLUMN consentimento_lgpd.data_consentimento IS 'Timestamp do aceite (req 4.7).';
COMMENT ON COLUMN consentimento_lgpd.data_revogacao    IS 'Preenchido ao exercer direito ao esquecimento (req 4.6 / 4.10).';

-- ── 4. Token de Recuperação de Senha ─────────────────────────────────────────
-- Token criptograficamente seguro (req 2.2 / 2.3 / 2.4)
CREATE TABLE IF NOT EXISTS token_recuperacao (
    id              BIGSERIAL    PRIMARY KEY,
    user_id         BIGINT       NOT NULL
                    REFERENCES auth_user(id) ON DELETE CASCADE,
    token           VARCHAR(128) NOT NULL UNIQUE,   -- secrets.token_urlsafe(64)
    criado_em       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    expira_em       TIMESTAMPTZ  NOT NULL,           -- NOW() + INTERVAL '1 hour'
    usado           BOOLEAN      NOT NULL DEFAULT FALSE,
    ip_solicitacao  INET
);

COMMENT ON TABLE  token_recuperacao         IS 'Tokens de recuperação de senha (req 2.2-2.7). Invalidados após uso.';
COMMENT ON COLUMN token_recuperacao.token   IS '64 bytes aleatórios via secrets.token_urlsafe (req 2.2).';
COMMENT ON COLUMN token_recuperacao.expira_em IS 'Expiração em 1 hora (req 2.3).';
COMMENT ON COLUMN token_recuperacao.usado   IS 'Marcado TRUE após uso único (req 2.4).';

-- ── 5. Agendamentos ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agendamento (
    id          BIGSERIAL    PRIMARY KEY,
    paciente_id BIGINT       NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    medico_id   BIGINT       NOT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    data_hora   TIMESTAMPTZ  NOT NULL,
    status      VARCHAR(15)  NOT NULL DEFAULT 'agendado'
                CHECK (status IN ('agendado', 'cancelado', 'realizado')),
    criado_em   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agendamento_paciente ON agendamento(paciente_id);
CREATE INDEX IF NOT EXISTS idx_agendamento_medico   ON agendamento(medico_id);
CREATE INDEX IF NOT EXISTS idx_agendamento_data     ON agendamento(data_hora);

-- ── 6. Tentativas de Login (auditoria específica de auth) ────────────────────
CREATE TABLE IF NOT EXISTS tentativa_login (
    id              BIGSERIAL    PRIMARY KEY,
    usuario_email   VARCHAR(254) NOT NULL,
    ip_address      INET         NOT NULL,
    sucesso         BOOLEAN      NOT NULL DEFAULT FALSE,
    motivo_falha    VARCHAR(100) NOT NULL DEFAULT '',
    timestamp       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    user_agent      TEXT         NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_tentativa_ip        ON tentativa_login(ip_address, timestamp);
CREATE INDEX IF NOT EXISTS idx_tentativa_email     ON tentativa_login(usuario_email, timestamp);

COMMENT ON TABLE tentativa_login IS 'Log de tentativas de login para auditoria (req 5.1 / 5.2).';

-- ── 7. Log de Auditoria Central ──────────────────────────────────────────────
-- Tabela append-only: sem UPDATE, sem DELETE (req 5.3)
CREATE TABLE IF NOT EXISTS log_auditoria (
    id          BIGSERIAL    PRIMARY KEY,
    tipo_evento VARCHAR(30)  NOT NULL,
    usuario_id  BIGINT       REFERENCES auth_user(id) ON DELETE SET NULL,
    ip_address  INET         NOT NULL,
    descricao   TEXT         NOT NULL,
    sucesso     BOOLEAN      NOT NULL DEFAULT TRUE,
    timestamp   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    user_agent  TEXT         NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_log_tipo      ON log_auditoria(tipo_evento, timestamp);
CREATE INDEX IF NOT EXISTS idx_log_usuario   ON log_auditoria(usuario_id, timestamp);

COMMENT ON TABLE log_auditoria IS 'Log central de auditoria de segurança (req 5.1-5.4). Append-only por policy.';

-- ── 8. Policy append-only para log_auditoria (req 5.3 — proteção contra alteração) ──
-- Impede UPDATE e DELETE na tabela de log (requer superuser na criação)
DO $$
BEGIN
  -- Cria role de aplicação se não existir
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_clinica') THEN
    CREATE ROLE app_clinica LOGIN PASSWORD 'troque_em_producao';
  END IF;
END $$;

GRANT SELECT, INSERT ON log_auditoria TO app_clinica;
-- Sem GRANT de UPDATE/DELETE → append-only garantido por permissão (req 5.3)

REVOKE UPDATE, DELETE ON log_auditoria FROM PUBLIC;

-- ── Grants gerais para a role de aplicação ───────────────────────────────────
GRANT SELECT, INSERT, UPDATE, DELETE ON
    perfil_usuario, consentimento_lgpd, token_recuperacao,
    agendamento, tentativa_login
TO app_clinica;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_clinica;

-- ── Fim do Schema ─────────────────────────────────────────────────────────────
