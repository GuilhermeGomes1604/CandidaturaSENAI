import os
from flask import Blueprint, Flask, g, render_template, request, redirect, url_for, flash, session, send_from_directory, current_app, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
# from __init__ import UPLOAD_FOLDER
from app.models import Admin, Candidato, Empresa, Curso, CursoConcluido, Vaga, Recrutamento, Relatorio, Email, Telefone, Fase
from app.utils import criptografar, descriptografar, calcular_idade, formatar_data_e_hora, formatar_data, validar_documento, verificar_login, verificar_fase, verificar_tipo_usuario
from app.database import banco

empresa_bp = Blueprint('empresa', __name__, url_prefix='/empresa')

@empresa_bp.route('/cadastro-empresa')
@verificar_fase(['Preparacao','Candidatura'])
@verificar_login(requer_login=False)
@verificar_tipo_usuario(['empresa'])
def cadastro_empresa():
    return render_template("empresas/cadastro-empresa.html")

@empresa_bp.route('/cadastrar-empresa', methods=['POST'])
@verificar_fase(['Candidatura'])
@verificar_login(requer_login=False)
@verificar_tipo_usuario(['empresa'])
def cadastrar_empresa():
    resultado_id = banco.execute_query("SELECT seq + 1 FROM sqlite_sequence WHERE name = 'empresas'")
    if resultado_id:
        lista_id = resultado_id if isinstance(resultado_id, list) else [resultado_id]
        id = lista_id[0][0]
        
    imagem = request.files.get('imagem')
    nome_fantasia = request.form.get('nome_fantasia', '').strip()
    razao_social = request.form.get('razao_social', '').strip()
    cnpj = request.form.get('cnpj', '').strip()
    senha = request.form.get('senha', '').strip()
    nome_responsavel = request.form.get('nome_responsavel', '').strip()
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

    if imagem and imagem.filename:
        nome_arquivo = f"empresa_{id}.jpg"
        pasta_empresas = os.path.join('UPLOAD_FOLDER', 'empresas')
        os.makedirs(pasta_empresas, exist_ok=True)
        caminho = os.path.join(pasta_empresas, nome_arquivo)
        imagem.save(caminho)

    obj = Email()
    obj.id_relativo = id
    obj.tipo = 'empresa' 

    lista_emails = [email1, email2, email3]

    for email in lista_emails:
        if email:
            obj.email = email 
            
            banco.execute_non_query(
                'INSERT INTO emails (id_relativo, tipo, email) VALUES (%s, %s, %s)',
                obj.id_relativo, obj.tipo, obj.email
            )

    obj = Telefone()
    obj.id_relativo = id
    obj.tipo = 'empresa' 

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
            
            obj.numero = numero
            obj.preferencia_contato = preferencia_contato
            obj.nome_contato = nome_contato
            
            banco.execute_non_query(
                """INSERT INTO telefones (id_relativo, tipo, numero, preferencia_contato, nome_contato) VALUES (%s, %s, %s, %s, %s)""",obj.id_relativo, obj.tipo, obj.numero, obj.preferencia_contato, obj.nome_contato)
            
    obj = Empresa()

    obj.nome_fantasia = criptografar(nome_fantasia)
    obj.razao_social = criptografar(razao_social)
    obj.cnpj = criptografar(cnpj)
    obj.senha = generate_password_hash(senha)
    obj.nome_responsavel = criptografar(nome_responsavel)

    banco.execute_non_query(banco.execute_non_query('INSERT INTO empresas (nome_fantasia, razao_social, cnpj, senha, nome_responsavel) VALUES (%s, %s, %s, %s, %s)', obj.nome_fantasia, obj.razao_social, obj.cnpj, obj.senha, obj.nome_responsavel))

    session.pop('nome_fantasia')
    session.pop('cnpj')
    session.pop('senha')

    flash(f'Conta criada com sucesso! Seja bem-vindo, representante {nome_fantasia}!', 'sucesso')
    return redirect(url_for('candidato.selecao_cursos'))

@empresa_bp.route('/marcar-candidato/<int:id>')
@verificar_login(requer_login=True)
@verificar_tipo_usuario(['empresa'])
def marcar_candidato(id):
    dados = banco.execute_query("SELECT * FROM recrutamento WHERE id_empresa = %s AND id_candidato = %s", session.get('id'), id)
    if not dados:
        banco.execute_non_query("INSERT INTO recrutamento (id_candidato, id_empresa, relacao) VALUES (%s, %s, 'Marcado')", id, session.get('id'))
    elif dados[0]['relacao'] == 'Marcado':
        banco.execute_non_query("DELETE FROM recrutamento WHERE id_candidato = %s and id_empresa = %s", id, session.get('id'))
    return '', 204

@empresa_bp.route('/selecionar-candidato/<int:id>')
@verificar_fase(['Selecao'])
@verificar_login(requer_login=True)
@verificar_tipo_usuario(['empresa'])
def selecionar_candidato(id):
    dados = banco.execute_query("SELECT * FROM recrutamento WHERE id_empresa = %s AND id_candidato = %s", session.get('id'), id)
    if not dados:
        banco.execute_non_query("INSERT INTO recrutamento (id_candidato, id_empresa, relacao) VALUES (%s, %s, 'Marcado')", id, session.get('id'))
        banco.execute_non_query("UPDATE candidatos SET disponibilidade = 'Indisponível' WHERE id = %s", id)
    elif dados[0]['relacao'] == 'Marcado':
        banco.execute_non_query("UPDATE recrutamento SET relacao = 'Selecionado' WHERE id_candidato = %s and id_empresa = %s", id, session.get('id'))
        banco.execute_non_query("UPDATE candidatos SET disponibilidade = 'Indisponível' WHERE id = %s", id)
    else:
        banco.execute_non_query("DELETE FROM recrutamento WHERE id_candidato = %s and id_empresa = %s", id, session.get('id'))
        banco.execute_non_query("UPDATE candidatos SET disponibilidade = 'Disponível' WHERE id = %s", id)
    return '', 204

@empresa_bp.route('/excluir_empresa/<int:id>')
@verificar_fase(['Preparação'])
@verificar_login(requer_login=True)
@verificar_tipo_usuario(['admin','empresa'])
def excluir_empresa(id):
    banco.execute_non_query("UPDATE empresas SET status = 'Inativo' WHERE id = %s", id)
    banco.execute_non_query("UPDATE vagas SET status = 'Inativo' WHERE id = %s", id)
    return '', 204