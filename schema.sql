CREATE DATABASE IF NOT EXISTS if_clubes
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE if_clubes;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(254) NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    tipo ENUM('aluno', 'responsavel', 'administrador') NOT NULL DEFAULT 'aluno',
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_usuarios_email (email)
);

CREATE TABLE IF NOT EXISTS clubes (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome VARCHAR(120) NOT NULL,
    descricao TEXT NOT NULL,
    categoria VARCHAR(80) NOT NULL,
    local VARCHAR(180) NOT NULL,
    horarios VARCHAR(180) NOT NULL,
    responsavel_id INT UNSIGNED NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_clubes_nome (nome),
    KEY idx_clubes_categoria (categoria),
    CONSTRAINT fk_clubes_responsavel
        FOREIGN KEY (responsavel_id) REFERENCES usuarios (id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS membros_clubes (
    usuario_id INT UNSIGNED NOT NULL,
    clube_id INT UNSIGNED NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (usuario_id, clube_id),
    KEY idx_membros_clubes_clube (clube_id),
    CONSTRAINT fk_membros_clubes_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_membros_clubes_clube
        FOREIGN KEY (clube_id) REFERENCES clubes (id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS eventos (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome VARCHAR(120) NOT NULL,
    descricao TEXT NOT NULL,
    data_hora DATETIME NOT NULL,
    local VARCHAR(180) NOT NULL,
    clube_id INT UNSIGNED NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_eventos_data_hora (data_hora),
    KEY idx_eventos_clube (clube_id),
    CONSTRAINT fk_eventos_clube
        FOREIGN KEY (clube_id) REFERENCES clubes (id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS presencas_eventos (
    usuario_id INT UNSIGNED NOT NULL,
    evento_id INT UNSIGNED NOT NULL,
    confirmado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (usuario_id, evento_id),
    KEY idx_presencas_eventos_evento (evento_id),
    CONSTRAINT fk_presencas_eventos_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_presencas_eventos_evento
        FOREIGN KEY (evento_id) REFERENCES eventos (id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS publicacoes (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    conteudo TEXT NOT NULL,
    autor_id INT UNSIGNED NOT NULL,
    clube_id INT UNSIGNED NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_publicacoes_clube (clube_id),
    CONSTRAINT fk_publicacoes_autor
        FOREIGN KEY (autor_id) REFERENCES usuarios (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_publicacoes_clube
        FOREIGN KEY (clube_id) REFERENCES clubes (id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comentarios (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    conteudo VARCHAR(1500) NOT NULL,
    autor_id INT UNSIGNED NOT NULL,
    publicacao_id INT UNSIGNED NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_comentarios_publicacao (publicacao_id),
    CONSTRAINT fk_comentarios_autor
        FOREIGN KEY (autor_id) REFERENCES usuarios (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_comentarios_publicacao
        FOREIGN KEY (publicacao_id) REFERENCES publicacoes (id)
        ON DELETE CASCADE
);