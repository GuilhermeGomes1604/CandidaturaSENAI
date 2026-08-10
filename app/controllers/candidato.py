import os
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from app.models import Candidato, Email, Telefone
from app.utils import criptografar, descriptografar, calcular_idade, formatar_data, validar_documento, verificar_login, verificar_fase, verificar_tipo_usuario
from app.database import banco

candidato_bp = Blueprint('candidato', __name__, url_prefix='/candidato')

@candidato_bp.route('/cadastro-candidato', methods=['GET'])
# @verificar_fase(['Candidatura'])
# @verificar_login(requer_login=False)
# @verificar_tipo_usuario(['candidato'])
def cadastro_candidato():
    dados = banco.execute_query("SELECT * FROM CURSOS")
    cursos = []
    if dados:
        lista = dados if isinstance(dados, list) else [dados]
        for i in lista:
            curso = {
                'id': i['id'],
                'nome': f"{i['nome']} ({i['sigla']})"
            }
            cursos.append(curso)
    return render_template("candidatos/cadastro-candidato.html")

@candidato_bp.route('/cadastrar-candidato', methods=['POST'])
# @verificar_fase(['Candidatura'])
# @verificar_login(requer_login=False)
# @verificar_tipo_usuario(['candidato'])
def cadastrar_candidato():
    id = banco.execute_query("SELECT COALESCE((SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'candidatos'), 1) AS proximo_id;")

    imagem = request.files.get('imagem')
    nome = request.form.get('nome', '').strip()
    nome_social = request.form.get('nome_social', '').strip()
    cpf = request.form.get('cpf', '').strip()
    senha = request.form.get('senha', '').strip()
    data_nasc = request.form.get('data_nasc', '').strip()
    genero = request.form.get('genero', '').strip()
    cep = request.form.get('cep', '').strip()
    endereco = request.form.get('endereco', '').strip()
    numero = request.form.get('numero', '').strip()
    complemento = request.form.get('complemento', '').strip()
    bairro = request.form.get('bairro', '').strip()
    cidade = request.form.get('cidade', '').strip()
    estado = request.form.get('estado', '').strip()
    escolaridade = request.form.get('escolaridade', '').strip()
    periodo_estudo = request.form.get('periodo_estudo', '').strip()
    ja_estudou = request.form.get('ja_estudou', '').strip()
    email1 = request.form.get('email1', '').strip()
    email2 = request.form.get('email2', '').strip()
    email3 = request.form.get('email3', '').strip()
    numero1 = request.form.get('numero1', '').strip()
    ligacao1 = request.form.get('ligacao1', '').strip()
    whatsapp1 = request.form.get('whatsapp1', '').strip()
    nome_contato1 = request.form.get('nome_contato1', '').strip()
    numero2 = request.form.get('numero2', '').strip()
    ligacao2 = request.form.get('ligacao2', '').strip()
    whatsapp2 = request.form.get('whatsapp2', '').strip()
    nome_contato2 = request.form.get('nome_contato2', '').strip()
    numero3 = request.form.get('numero3', '').strip()
    ligacao3 = request.form.get('ligacao3', '').strip()
    whatsapp3 = request.form.get('whatsapp3', '').strip()
    nome_contato3 = request.form.get('nome_contato3', '').strip()

    if not validar_documento(cpf, 'cpf'):
        flash("CPF inválido!", "erro")
        return redirect(url_for('candidato.cadastro_candidato'))

    if imagem and imagem.filename:
        nome_arquivo = f"candidato_{id}.jpg"
        pasta_candidatos = os.path.join('UPLOAD_FOLDER', 'candidatos')
        os.makedirs(pasta_candidatos, exist_ok=True)
        caminho = os.path.join(pasta_candidatos, nome_arquivo)
        imagem.save(caminho)

    obj = Email()
    obj.id_relativo = id
    obj.tipo = 'candidato' 

    lista_emails = [email1, email2, email3]

    for email in lista_emails:
        if email:
            obj.email = criptografar(email)
            
            banco.execute_non_query(
                'INSERT INTO emails (id_relativo, tipo, email) VALUES (%s, %s, %s)',
                obj.id_relativo, obj.tipo, obj.email
            )

    obj = Telefone()
    obj.id_relativo = id
    obj.tipo = 'candidato' 

    lista_telefones = [
        (numero1, ligacao1, whatsapp1, nome_contato1),
        (numero2, ligacao2, whatsapp2, nome_contato2),
        (numero3, ligacao3, whatsapp3, nome_contato3)
    ]

    for numero, ligacao, whatsapp, nome_contato in lista_telefones:
        
        if numero:
            if ligacao and whatsapp:
                preferencia_contato = "Ambos"
            elif ligacao:
                preferencia_contato = "Ligação"
            else:
                preferencia_contato = "WhatsApp"
            
            obj.numero = criptografar(numero)
            obj.preferencia_contato = preferencia_contato
            obj.nome_contato = nome_contato
            
            banco.execute_non_query(
                """INSERT INTO telefones (id_relativo, tipo, numero, preferencia_contato, nome_contato) VALUES (%s, %s, %s, %s, %s)""",obj.id_relativo, obj.tipo, obj.numero, obj.preferencia_contato, obj.nome_contato)

    contador = 1

    while True:
        id_curso = request.form.get(f"curso_concluido{contador}", '').strip()
        if not id_curso: 
            break

        banco.execute_non_query(
            'INSERT INTO cursos_concluidos (id_candidato, id_curso) VALUES (%s, %s)', 
            id, id_curso
        )
        contador += 1

    obj = Candidato()

    obj.tipo = "candidato"
    obj.nome = criptografar(nome)
    obj.nome_social = criptografar(nome_social)
    obj.cpf = criptografar(cpf)
    obj.senha = generate_password_hash(senha)
    obj.data_nasc = criptografar(data_nasc)
    obj.genero = genero
    obj.cep = criptografar(cep)
    obj.endereco = criptografar(endereco)
    obj.numero = criptografar(numero)
    obj.complemento = criptografar(complemento)
    obj.bairro = criptografar(bairro)
    obj.cidade = criptografar(cidade)
    obj.estado = criptografar(estado)
    obj.escolaridade = escolaridade
    obj.periodo_estudo = periodo_estudo
    obj.ja_estudou = ja_estudou

    banco.execute_non_query('INSERT INTO candidatos (tipo, nome, nome_social, cpf, senha, data_nasc, genero, cep, endereco, numero, complemento, bairro, cidade, estado, escolaridade, periodo_estudo, ja_estudou) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', obj.tipo, obj.nome, obj.nome_social, obj.cpf, obj.senha, obj.data_nasc, obj.genero, obj.cep, obj.endereco, obj.numero, obj.complemento, obj.bairro, obj.cidade, obj.estado, obj.escolaridade, obj.periodo_estudo, obj.ja_estudou)

    session.pop('nome_completo')
    session.pop('cpf')
    session.pop('senha')

    if nome_social != '':
        nome = nome_social.split()[0]
    else:
        nome = nome.split()[0]
    flash(f'Conta criada com sucesso! Seja bem-vindo, {nome}!', 'sucesso')
    return redirect(url_for('candidato.selecao_cursos'))

@candidato_bp.route('/selecao-cursos')
# @verificar_fase(['Candidatura'])
# @verificar_login(requer_login=False)
# @verificar_tipo_usuario(['candidato'])
def selecao_cursos():
    data_nasc = banco.execute_query("SELECT data_nasc FROM candidatos WHERE id = %s", session.get('id'))[0][0]
    data_nasc = formatar_data(descriptografar(data_nasc))
    idade = calcular_idade(data_nasc)
    nascimento = datetime.strptime(data_nasc, '%Y-%m-%d').date()
    aniversario_24 = date(nascimento.year + 24, nascimento.month, nascimento.day)
    hoje = date.today()
    meses_faltantes = (aniversario_24.year - hoje.year) * 12 + (aniversario_24.month - hoje.month)
    if hoje.day > aniversario_24.day:
        meses_faltantes -= 1

    dados = banco.execute_query("""
    SELECT * FROM cursos WHERE status = "Ativo" 
    AND id IN (SELECT DISTINCT id_cursos FROM vagas WHERE status = 'Ativo') 
    AND id NOT IN (SELECT DISTINCT id_curso FROM cursos_concluidos WHERE id_candidato = %s) 
    AND NOT EXISTS (SELECT 1 FROM candidatos WHERE id_candidato = %s AND (periodo_estudo = horario OR (periodo_estudo = 'Integral' AND horario IN ('Manhã', 'Tarde'))))""",
    session.get('id'), session.get('id'))
    cursos = []
    if dados:
        lista = dados if isinstance(dados, list) else [dados]
        for i in lista:
            if i['duracao'] < meses_faltantes and i['idade_minima'] >= idade:
                curso = {
                    'id': i['id'],
                    'nome': f"{i['nome']} ({i['sigla']})",
                    'horario': i['horario'],
                    'duracao': i['duracao']
                }
            cursos.append(curso)
    return render_template("candidatos/selecionar-curso.html", cursos = cursos)

@candidato_bp.route('/selecionar-curso')
# @verificar_fase(['Candidatura'])
# @verificar_login(requer_login=False)
# @verificar_tipo_usuario(['candidato'])
def selecionar_curso(id_primeira_opcao, id_segunda_opcao, id_terceira_opcao):
    banco.execute_non_query("UPDATE candidatos SET id_primeira_opcao = %s, id_segunda_opcao = %s, id_terceira_opcao = %s WHERE id = %s", id_primeira_opcao, id_segunda_opcao, id_terceira_opcao, session.get('id'))
    return redirect(url_for('geral.index'))

@candidato_bp.route('/excluir-candidato/<int:id>')
# @verificar_fase(['Candidatura'])
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin','candidato'])
def excluir_candidato(id):
    banco.execute_non_query("UPDATE candidatos SET status = 'Inativo' WHERE id = %s", id)
    return '', 204