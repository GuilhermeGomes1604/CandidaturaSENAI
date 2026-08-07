class Admin():
    def __init__(self):
        self.id = 0
        self.tipo = ""
        self.nome = ""
        self.cpf = ""
        self.senha = ""
        self.data_registro = ""
        self.status = ""

class Candidato():
    def __init__(self):
        self.id = 0
        self.tipo = ""
        self.nome = ""
        self.nome_social = ""
        self.cpf = ""
        self.senha = ""
        self.data_nasc = ""
        self.genero = ""
        self.cep = ""
        self.endereco = ""
        self.numero = 0
        self.complemento = ""
        self.bairro = ""
        self.cidade = ""
        self.estado = ""
        self.escolaridade = ""
        self.periodo_estudo = ""
        self.ja_estudou = ""
        self.id_primeira_opcao = 0
        self.id_segunda_opcao = 0
        self.id_terceira_opcao = 0
        self.disponibilidade = ""
        self.data_registro = ""
        self.status = ""

class Empresa():
    def __init__(self):
        self.id = 0
        self.nome_fantasia = ""
        self.razao_social = ""
        self.cnpj = ""
        self.senha = ""
        self.nome_responsavel = ""
        self.selecao_encerrada = 0
        self.data_registro = ""
        self.status = ""

class Curso():
    def __init__(self):
        self.id = 0
        self.nome = ""
        self.sigla = ""
        self.horario = ""
        self.detalhamento = ""
        self.idade_minima = 0
        self.duracao = 0 
        self.vagas = 0
        self.data_registro = ""
        self.status = ""

class CursoConcluido():
    def __init__(self):
        self.id_candidato = 0
        self.id_curso = 0 

class Vaga():
    def __init__(self):
        self.id_empresa = 0
        self.id_curso = 0
        self.quantidade = 0
        self.status = ""

class Recrutamento():
    def __init__(self):
        self.id_candidato = 0
        self.id_empresa = 0
        self.relacao = ""
        self.data_interacao = ""

class Relatorio():
    def __init__(self):
        self.id = 0
        self.nome = ""
        self.data_registro = ""

class Email():
    def __init__(self):
        self.id_relativo = 0
        self.tipo = ""
        self.email = ""

class Telefone():
    def __init__(self):
        self.id_relativo = 0
        self.tipo = ""
        self.numero = ""
        self.preferencia_contato = ""
        self.nome_contato = ""

class Fase():
    def __init__(self):
        self.fase = ""