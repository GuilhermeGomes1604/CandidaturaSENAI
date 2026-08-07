import os, pymysql
from flask import g

class Database():

    def __init__(self):
        self.host = os.environ.get('DB_HOST', 'localhost')
        self.user = os.environ.get('DB_USER', 'seu_usuario')
        self.password = os.environ.get('DB_PASSWORD', 'sua_senha')
        self.database = os.environ.get('DB_NAME', 'nome_do_banco')
        self.port = int(os.environ.get('DB_PORT', 3306))

    def get_conn(self):
        if 'db' not in g:
            g.db = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                cursorclass=pymysql.cursors.DictCursor 
            )
        return g.db

    def execute_non_query(self, sql, *params):
        conn = self.get_conn()
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
        conn.commit()

    def execute_query(self, sql, *params):
        conn = self.get_conn()
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()

banco = Database()

def init_db():
    banco.execute_non_query("""
        CREATE TABLE IF NOT EXISTS admins (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tipo CHAR(5) NOT NULL DEFAULT "admin",
            nome VARCHAR(255) NOT NULL,
            cpf VARCHAR(255) NOT NULL,
            senha VARCHAR(255) NOT NULL,
            data_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(7) NOT NULL DEFAULT "Ativo" -- Ativo/Inativo
        )
    """)

    banco.execute_non_query("""
        CREATE TABLE IF NOT EXISTS candidatos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tipo CHAR(9) NOT NULL DEFAULT "candidato",
            nome VARCHAR(255) NOT NULL,
            nome_social VARCHAR(255),
            cpf VARCHAR(255) NOT NULL,
            senha VARCHAR(255) NOT NULL,
            data_nasc VARCHAR(255) NOT NULL, -- Data de Nascimento
            genero VARCHAR(9) NOT NULL, -- Masculino/Feminino
            cep VARCHAR(255) NOT NULL,
            endereco VARCHAR(255) NOT NULL,
            numero INT NOT NULL,
            complemento VARCHAR(255) NOT NULL,
            bairro VARCHAR(255) NOT NULL,
            cidade VARCHAR(255) NOT NULL,
            estado VARCHAR(255) NOT NULL,
            escolaridade VARCHAR(255) NOT NULL,
            periodo_estudo VARCHAR(8), -- Manhã/Tarde/Noite/Integral (Período do dia em que o candidato estuda, para evitar choque de horários com o curso). 
            ja_estudou VARCHAR(255) NOT NULL, -- Se o aluno já estudou no SENAI anteriormente. Usado para evitar que o usuário se candidate para um curso já feito por ele.
            id_primeira_opcao INT,  -- Primeira opção de curso
            id_segunda_opcao INT, -- Segunda opção de curso (Opcional)
            id_terceira_opcao INT, -- Terceira opção de curso (Opcional)
            disponibilidade VARCHAR(12) NOT NULL DEFAULT "Disponível-", -- Disponível/Indisponível (Disponibilidade para contratação).
            data_registro DAETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(7) NOT NULL DEFAULT "Ativo" -- Ativo/Inativo
        )
    """)

    banco.execute_non_query("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome_fantasia VARCHAR(255) NOT NULL,
            razao_social VARCHAR(255) NOT NULL,
            cnpj VARCHAR(255) NOT NULL,
            senha VARCHAR(255) NOT NULL,
            nome_responsavel VARCHAR(255) NOT NULL, -- Nome do responsável pela criação da conta.
            selecao_encerrada CHAR(1) NOT NULL DEFAULT '0', -- 0 = "Não", 1 = "Sim"
            data_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(7) NOT NULL DEFAULT "Ativo" -- Ativo/Inativo
        )
    """)

    banco.execute_non_query("""
        CREATE TABLE IF NOT EXISTS cursos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(150) NOT NULL,
            sigla VARCHAR(10) NOT NULL,
            horario VARCHAR(5) NOT NULL, -- Manhã/Tarde/Noite
            detalhamento TEXT NOT NULL, -- Descrição do curso.
            idade_minima INT NOT NULL,
            duracao INT NOT NULL, -- Em meses
            vagas INT NOT NULL,
            data_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(7) NOT NULL DEFAULT "Ativo" -- Ativo/Inativo
        )
    """)

    banco.execute_non_query("""
        CREATE TABLE IF NOT EXISTS cursos_concluidos ( -- Tabela relacional conectando candidatos com cursos já feitos por eles. Novamente, usado para evitar que ele se candidate para o mesmo curso novamente.
            id_candidato INT NOT NULL,
            id_curso INT NOT NULL,
            PRIMARY KEY (id_candidato, id_curso)
            FOREIGN KEY (id_candidato) REFERENCES candidatos(id),
            FOREIGN KEY (id_curso) REFERENCES cursos(id)
)
    """)

    banco.execute_non_query("""
        CREATE TABLE IF NOT EXISTS vagas ( -- Tabela relacional conectando uma empresa com o curso que ela requisitou vagas, junto com a quantidade dessas vagas.
            id_empresa INT NOT NULL,
            id_curso INT NOT NULL,
            quantidade INT NOT NULL,
            status VARCHAR(7) NOT NULL DEFAULT, "Ativo" -- Ativo/Inativo
            PRIMARY KEY (id_empresa, id_curso)
            FOREIGN KEY (id_empresa) REFERENCES empresas(id),
            FOREIGN KEY (id_curso) REFERENCES cursos(id)
        )
    """)

    banco.execute_non_query("""
        CREATE TABLE IF NOT EXISTS recrutamentos (
            id_candidato INT NOT NULL,
            id_empresa INT NOT NULL,
            relacao VARCHAR(11) NOT NULL, -- Marcado/Selecionado (A relação entre aluno e empresa. "Marcado" seria quando a empresa marca o candidato com interesse, enquanto "Selecionado" seria quando a empresa selecionar o aluno definitivamente para o processo seletivo. Somente essa última opção é visível para o candidato).
            detalhamento TEXT,
            data_interacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Data em que a interação foi feita. Essencialmente idênticas às colunas "data_registro".
            PRIMARY KEY (id_candidato, id_empresa)
            FOREIGN KEY (id_candidato) REFERENCES candidatos(id),
            FOREIGN KEY (id_empresa) REFERENCES empresas(id),
        )
    """)

    banco.execute_non_query("""
        CREATE TABLE IF NOT EXISTS relatorios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            data_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    banco.execute_non_query("""
        CREATE TABLE IF NOT EXISTS emails (
            id_relativo INT NOT NULL,
            tipo VARCHAR(11) NOT NULL, -- Se o "id_relativo" é de um candidato ou de uma empresa.
            email VARCHAR(255) NOT NULL
        )
    """)

    banco.execute_non_query("""
        CREATE TABLE IF NOT EXISTS telefones (
            id_relativo INT NOT NULL,
            tipo VARCHAR(11) NOT NULL, -- Se o "id_relativo" é de um candidato ou de uma empresa.
            numero VARCHAR(255) NOT NULL,
            preferencia_contato VARCHAR(8) NOT NULL, -- Ligação/WhatsApp/Ambos
            nome_contato VARCHAR(100) NOT NULL -- "Tratar com:"
        )
    """)

    banco.execute_non_query("""
        CREATE TABLE IF NOT EXISTS fase (
            fase VARCHAR(11) NOT NULL -- Preparação/Candidatura/Seleção (As fases do sistema)
        )
    """)

    banco.execute_non_query(""" -- Insere a fase inicial padrão, "Preparação", na tabela "fase".
        INSERT INTO fase (fase)
        SELECT 'Preparação' FROM DUAL
        WHERE NOT EXISTS (SELECT 1 FROM fase);
    """)