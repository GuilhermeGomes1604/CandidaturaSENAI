import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash
import pdfkit
from app.models import Admin, Candidato, Empresa, Curso, Email, Telefone
from app.utils import criptografar, descriptografar, calcular_idade, formatar_data_e_hora, formatar_data, validar_documento, verificar_login, verificar_tipo_usuario
from app.database import banco

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/admins')
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def admins():
    dados = banco.execute_query("SELECT * FROM admins")
    admins = []
    if dados:
        lista = dados if isinstance(dados, list) else [dados]
        for i in lista:
            admin = {
                'id': i['id'],
                'nome': descriptografar(i['nome']),
                'cpf': descriptografar(i['cpf'])
            }
            admins.append(admin)
    return render_template('admins/admins.html', admins=admins)

@admin_bp.route('/admin/<int:id>')
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def admin(id):
    dados = banco.execute_query("SELECT * FROM admins WHERE id = %s", id )[0]
    admin = {
        'id': dados['id'],
        'nome': descriptografar(dados['nome']),
        'cpf': descriptografar(dados['cpf'])
    }
    return render_template('admins/admin.html', admin = admin)

@admin_bp.route('/cadastro-admin')
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def cadastro_admin():
    return render_template('admins/cadastrar-admin.html')

@admin_bp.route('/cadastrar-admin', methods=['POST'])
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def cadastrar_admin():
    id = banco.execute_query("SELECT COALESCE((SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'admins'), 1) AS proximo_id")

    imagem = request.files.get('imagem')
    nome = request.form.get('nome', '').strip()
    cpf = request.form.get('cpf', '').strip()
    senha = request.form.get('senha', '').strip()

    if not validar_documento(cpf, 'cpf'):
        flash("CPF inválido!", "erro")
        return redirect(url_for('admin.cadastro_admin'))

    if imagem and imagem.filename:
        nome_arquivo = f"admin_{id}.jpg"
        pasta_admins = os.path.join('UPLOAD_FOLDER', 'admins')
        os.makedirs(pasta_admins, exist_ok=True)
        caminho = os.path.join(pasta_admins, nome_arquivo)
        imagem.save(caminho)

    obj = Admin()

    obj.tipo = "admin"
    obj.nome = criptografar(nome)
    obj.cpf = criptografar(cpf)
    obj.senha = generate_password_hash(senha)

    banco.execute_non_query('INSERT INTO admins (tipo, nome, cpf, senha) VALUES (%s, %s, %s, %s)', obj.tipo, obj.nome, obj.cpf, obj.senha)

    flash(f'Conta de {nome} criada com sucesso!', 'sucesso')
    return redirect(url_for('geral.index'))

@admin_bp.route('/edicao-admin/<int:id>', methods=['POST'])
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def edicao_admin(id):
    dados = banco.execute_query("SELECT * FROM admins WHERE id = %s", id )[0]
    dados = {
        'id': dados['id'],
        'nome': descriptografar(dados['nome']),
        'cpf': descriptografar(dados['cpf'])
    }
    return render_template('admins/editar-admin.html', dados = dados)

@admin_bp.route('/editar-admin/<int:id>', methods=['POST'])
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def editar_admin(id):
    imagem = request.files.get('imagem')
    nome = request.form.get('nome', '').strip()
    cpf = request.form.get('cpf', '').strip()
    senha = request.form.get('senha', '').strip()

    if not validar_documento(cpf, 'cpf'):
        flash("CPF inválido!", "erro")
        return redirect(url_for('admin.cadastrar_admin'))

    if imagem and imagem.filename:
        nome_arquivo = f"admin_{id}.jpg"
        pasta_admins = os.path.join('UPLOAD_FOLDER', 'admins')
        os.makedirs(pasta_admins, exist_ok=True)
        caminho = os.path.join(pasta_admins, nome_arquivo)
        imagem.save(caminho)

    if session.get('id') == id:
        session['nome'] = nome.split()[0]

    obj = Admin()

    obj.nome = criptografar(nome)
    obj.cpf = criptografar(cpf)
    obj.senha = generate_password_hash(senha)

    banco.execute_non_query('UPDATE admins SET nome = %s, cpf = %s WHERE id = %s', obj.nome, obj.cpf, id)

    flash(f'Conta de {nome} editada com sucesso!', 'sucesso')
    return redirect(url_for('admin.admin', id = id))

@admin_bp.route('/alterar-fase', methods=['GET','POST'])
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def alterar_fase():
    fase = request.args.get('fase')
    if fase is not None:
        banco.execute_non_query("UPDATE fase SET fase = %s", fase)
        if fase == "Divulgação":
            dados = banco.execute_query("SELECT * FROM empresas")
            lista = dados if isinstance(dados, list) else [dados]
            for i in lista:
                candidatos = []
                for i in lista:
                    dados_candidatos = banco.execute_query("SELECT * FROM candidatos WHERE id IN (SELECT id_candidato FROM recrutamento WHERE id_empresa = %s)", i[0])
                    if not dados_candidatos:
                        flash("Nenhuma empresa selecionou candidatos ainda!","aviso")
                    lista_candidatos = dados_candidatos if isinstance(dados_candidatos, list) else [dados_candidatos]
                    for c in lista_candidatos:
                        candidato = {
                            'nome': descriptografar(c['nome_social']) if i('nome_social') else descriptografar(i['nome']),
                            'cpf': descriptografar(c['cpf']),
                            'idade': calcular_idade(descriptografar(c['data_nasc']))
                        }
                    candidatos.append(candidato)
                html = render_template('template-relatorio.html', empresa = {descriptografar(i['nome_fantasia'])}, candidatos = candidatos)
    
                pasta_raiz = os.path.dirname(current_app.root_path)
                pasta_reports = os.path.join(pasta_raiz, 'reports')
                os.makedirs(pasta_reports, exist_ok=True)
                caminho_pdf = os.path.join(pasta_reports, 'relatorio_candidatos.pdf')
                pdfkit.from_string(html, caminho_pdf)
                banco.execute_non_query("INSERT INTO relatorios (nome) VALUES (%s)",criptografar(f"Contratações - {descriptografar(i['nome_fantasia'])}"))
        return redirect(url_for('admin.alterar_fase')) 
    return render_template('admins/fase.html')

@admin_bp.route('/relatorios')
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def relatorios():
    dados = banco.execute_query("SELECT * FROM relatorios")
    relatorios = []
    if dados:
        lista = dados if isinstance(dados, list) else [dados]
        for i in lista:
            relatorio = {
                'id': i['id'],
                'nome': descriptografar(i['nome']),
                'data_registro': i['data_registro']
            }
            relatorios.append(relatorio)
    return render_template('admins/relatorios.html', relatorios = relatorios)

@admin_bp.route('/cadastro-curso')
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def cadastro_curso():
    return render_template('admins/cadastrar-curso.html')

@admin_bp.route('/cadastrar-curso', methods=['POST'])
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def cadastrar_curso():
    nome = request.form.get('nome', '').strip()
    sigla = request.form.get('sigla', '').strip()
    horario = request.form.get('horario', '').strip()
    detalhamento = request.form.get('detalhamento', '').strip()
    idade_minima = request.form.get('idade-minima', '').strip()
    duracao = request.form.get('duracao', '').strip()
    vagas = request.form.get('vagas', '').strip()

    obj = Curso()

    obj.nome = nome
    obj.sigla = sigla
    obj.horario = horario
    obj.detalhamento = detalhamento
    obj.idade_minima = idade_minima
    obj.duracao = duracao
    obj.vagas = vagas

    banco.execute_non_query('INSERT INTO cursos (nome, sigla, horario, detalhamento, idade_minima, duracao, vagas) VALUES (%s, %s, %s, %s, %s, %s, %s)', obj.nome, obj.sigla, obj.horario, obj.detalhamento, obj.idade_minima, obj.duracao, obj.vagas)

    flash(f'Curso registrado com sucesso!', 'sucesso')
    return redirect(url_for('geral.cursos'))

@admin_bp.route('/edicao-curso/<int:id>', methods=['POST'])
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def edicao_curso(id):
    dados = banco.execute_query("SELECT * FROM cursos WHERE id = %s", id )[0]
    dados = {
        'id': id,
        'nome': dados['nome'],
        'sigla': dados['sigla'],
        'horario': dados['horario'],
        'detalhamento': dados['detalhamento'],
        'idade_minima': dados['idade_minima'],
        'duracao': dados['duracao'],
        'vagas': dados['vagas']
    }
    return render_template('admins/editar-curso.html', dados = dados)

@admin_bp.route('/editar-curso/<int:id>', methods=['POST'])
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def editar_curso(id):
    nome = request.form.get('nome', '').strip()
    sigla = request.form.get('sigla', '').strip()
    horario = request.form.get('horario', '').strip()
    detalhamento = request.form.get('detalhamento', '').strip()
    idade_minima = request.form.get('idade-minima', '').strip()
    duracao = request.form.get('duracao', '').strip()
    vagas = request.form.get('vagas', '').strip()

    obj = Curso()

    obj.nome = nome
    obj.sigla = sigla
    obj.horario = horario
    obj.detalhamento = detalhamento
    obj.idade_minima = idade_minima
    obj.duracao = duracao
    obj.vagas = vagas

    banco.execute_non_query('UPDATE cursos SET nome = %s, sigla = %s, horario = %s, detalhamento = %s, idade_minima = %s, duracao = %s, vagas = %s WHERE id = %s', obj.nome, obj.sigla, obj.horario, obj.detalhamento, obj.idade_minima, obj.duracao, obj.vagas, id)

    flash(f'Curso editado com sucesso!', 'sucesso')
    return redirect(url_for('geral.curso', id = id))

@admin_bp.route('/excluir-curso/<int:id>')
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def excluir_curso(id):
    banco.execute_non_query("UPDATE cursos SET status = 'Inativo' WHERE id = %s", id)
    return '', 204

@admin_bp.route('/edicao-candidato/<int:id>', methods=['POST'])
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def edicao_candidato(id):
    dados = banco.execute_query("SELECT FROM candidatos WHERE id = %s", id )[0]
    dados = {
        'nome': descriptografar(dados['nome']),
        'nome_social': descriptografar(dados['nome_social']),
        'cpf': descriptografar(dados['cpf']),
        'data_nasc': formatar_data(descriptografar(dados['data_nasc'])),
        'genero': dados['genero'],
        'cep': descriptografar(dados['cep']),
        'endereco': descriptografar(dados['endereco']),
        'numero': descriptografar(dados['numero']),
        'complemento': descriptografar(dados['complemento']),
        'bairro': descriptografar(dados['bairro']),
        'cidade': descriptografar(dados['cidade']),
        'estado': descriptografar(dados['estado']), 
        'escolaridade': dados['escolaridade'],
        'periodo_estudo': dados['periodo_estudo'],
        'ja_estudou': dados['ja_estudou'],
        'disponibilidade': dados['disponibilidade'],
    }
    return render_template('admins/editar-candidato.html', dados = dados)

@admin_bp.route('/editar-candidato/<int:id>', methods=['POST'])
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def editar_candidato(id):
    imagem = request.files.get('imagem')
    nome = request.form.get('nome_fantasia', '').strip()
    nome_social = request.form.get('cnpj', '').strip()
    cpf = request.form.get('cpf', '').strip()
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
        return redirect(url_for('geral.editar_dados'))

    cpfs = banco.execute_query("""
        SELECT id, nome, cpf, senha, 'admin' AS tipo FROM admins 
        UNION 
        SELECT id, nome, cpf, senha, 'candidato' AS tipo FROM candidatos
    """)

    if cpfs:
        lista = cpfs if isinstance(cpfs, list) else [cpfs]
        for i in lista:
            if descriptografar(i['cpf']) == cpf and i['id'] != id:
                flash("Esse CPF já foi registrado!","erro")
                return redirect(url_for('geral.editar_dados'))
            
    if imagem and imagem.filename:
        nome_arquivo = f"candidato_{id}.jpg"
        pasta_candidatos = os.path.join('UPLOAD_FOLDER', 'candidatos')
        os.makedirs(pasta_candidatos, exist_ok=True)
        caminho = os.path.join(pasta_candidatos, nome_arquivo)
        imagem.save(caminho)

    banco.execute_non_query("DELETE FROM emails WHERE id_relativo = %s AND tipo = 'candidato'", id)
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
    
    banco.execute_non_query("DELETE FROM telefones WHERE id_relativo = %s AND tipo = 'candidato'", id)
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
                
    obj = Candidato()

    obj.tipo = "candidato"
    obj.nome = criptografar(nome)
    obj.nome_social = criptografar(nome_social)
    obj.cpf = criptografar(cpf)
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

    banco.execute_non_query('UPDATE candidatos SET tipo = %s, nome = %s, nome_social = %s, cpf = %s, data_nasc = %s, genero = %s, cep = %s, endereco = %s, numero = %s, complemento = %s, bairro = %s, cidade = %s, estado = %s, escolaridade = %s, periodo_estudo = %s, ja_estudou = %s WHERE id = %s', obj.tipo, obj.nome, obj.nome_social, obj.cpf, obj.data_nasc, obj.genero, obj.cep, obj.endereco, obj.numero, obj.complemento, obj.bairro, obj.cidade, obj.estado, obj.escolaridade, obj.periodo_estudo, obj.ja_estudou, id)  
    flash(f'Candidato editado com sucesso!', 'sucesso')
    return redirect(url_for('geral.candidato', id = id))

@admin_bp.route('/excluir-candidato/<int:id>')
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def excluir_candidato(id):
    banco.execute_non_query("UPDATE candidatos SET status = 'Inativo' WHERE id = %s", id)
    return '', 204

@admin_bp.route('/empresas')
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def empresas():
    dados = banco.execute_query("SELECT * FROM empresas")
    empresas = []
    if dados:
        lista = dados if isinstance(dados, list) else [dados]
        for i in lista:
            empresa = {
                'id': i['id'],
                'nome_fantasia': descriptografar(i['nome_fantasia']),
                'razao_social': descriptografar(i['razao_social']),
            }
            empresas.append(empresa)
    return render_template('admins/empresas.html', empresas = empresas)

@admin_bp.route('/empresa/<int:id>')
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def empresa(id):
    dados = banco.execute_query("SELECT * FROM empresas WHERE id = %s", id)[0]
    empresa = {
        'id': dados['id'],
        'nome_fantasia': descriptografar(dados['nome_fantasia']),
        'razao_social': descriptografar(dados['razao_social']),
        'cpnj': descriptografar(dados['cnpj']),
        'nome_responsavel': descriptografar(dados['nome_responsavel']),
        'data_registro': formatar_data_e_hora(dados['data_registro'])
    }
    return render_template('admins/empresa.html', empresa = empresa)

@admin_bp.route('/edicao-empresa/<int:id>', methods=['POST'])
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def edicao_empresa(id):
    dados = banco.execute_query("SELECT FROM empresas WHERE id = %s", id )[0]
    dados = {
        'nome_fantasia': descriptografar(dados['nome_fantasia']),
        'razao_social': descriptografar(dados['razao_social']),
        'cpf': descriptografar(dados['cpf']),
        'nome_responsavel': descriptografar(dados['nome_responsavel'])
    }
    return render_template('admins/editar-empresa.html', dados = dados)

@admin_bp.route('/editar-empresa/<int:id>', methods=['POST'])
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def editar_empresa(id):
    imagem = request.files.get('imagem')
    nome_fantasia = request.form.get('nome_fantasia', '').strip()
    razao_social = request.form.get('razao_social', '').strip()
    cnpj = request.form.get('cnpj', '').strip()
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

    if not validar_documento(cnpj, 'cnpj'):
        flash("CNPJ inválido!", "erro")
        return redirect(url_for('geral.editar_dados'))

    cnpjs = banco.execute_query("SELECT id, nome_fantasia AS nome, cnpj, senha, 'empresa' AS tipo FROM empresas")

    if cnpjs:
        lista = cnpjs if isinstance(cnpjs, list) else [cnpjs]
        for i in lista:
            if descriptografar(i['cnpj']) == cnpj and i['id'] != id:
                flash("Esse CNPJ já foi registrado!","erro")
                return redirect(url_for('geral.editar_dados'))
            
    if imagem and imagem.filename:
        nome_arquivo = f"empresa_{id}.jpg"
        pasta_empresas = os.path.join('UPLOAD_FOLDER', 'empresas')
        os.makedirs(pasta_empresas, exist_ok=True)
        caminho = os.path.join(pasta_empresas, nome_arquivo)
        imagem.save(caminho)

    banco.execute_non_query("DELETE FROM emails WHERE id_relativo = %s AND tipo = 'empresa'", id)
    obj = Email()
    obj.id_relativo = id
    obj.tipo = 'empresa' 

    lista_emails = [email1, email2, email3]

    for email in lista_emails:
        if email:
            obj.email = criptografar(email) 
            
            banco.execute_non_query(
                'INSERT INTO emails (id_relativo, tipo, email) VALUES (%s, %s, %s)',
                obj.id_relativo, obj.tipo, obj.email
            )
    
    banco.execute_non_query("DELETE FROM telefones WHERE id_relativo = %s AND tipo = 'empresa'", id)
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
            
            obj.numero = criptografar(numero)
            obj.preferencia_contato = preferencia_contato
            obj.nome_contato = nome_contato
            
            banco.execute_non_query(
                """INSERT INTO telefones (id_relativo, tipo, numero, preferencia_contato, nome_contato) VALUES (%s, %s, %s, %s, %s)""",obj.id_relativo, obj.tipo, obj.numero, obj.preferencia_contato, obj.nome_contato)
                
    obj = Empresa()

    obj.nome_fantasia = criptografar(nome_fantasia)
    obj.razao_social = criptografar(razao_social)
    obj.cnpj = criptografar(cnpj)
    obj.nome_responsavel = criptografar(nome_responsavel)

    banco.execute_non_query('UPDATE empresas SET nome_fantasia = %s, razao_social = %s, cnpj = %s, nome_responsavel = %s WHERE id = %s', obj.nome_fantasia, obj.razao_social, obj.cnpj, obj.nome_responsavel, id)
    flash(f'Empresa editada com sucesso!', 'sucesso')
    return redirect(url_for('admin.empresa', id = id))

@admin_bp.route('/restauracao-senha')
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def restauracao_senha():
    dados = banco.execute_query("SELECT * FROM requisicoes_mudanca_senha")
    requisicoes = []
    if dados:
        lista = dados if isinstance(dados, list) else [dados]
        for i in lista:
            requisicao = {
                'nome': descriptografar(i['nome']),
                'login': descriptografar(i['login'])
            }
            requisicoes.append(requisicao)
    return render_template('admins/restauracao-senha.html', requisicoes = requisicoes)

@admin_bp.route('/restaurar-senha/<login>/<senha>')
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def restaurar_senha(login, senha):
    logins = banco.execute_query("""
        SELECT id, nome, cpf AS documento, senha, 'admins' AS tabela FROM admins 
        UNION 
        SELECT id, nome, cpf AS documento, senha, 'candidatos' AS tabela FROM candidatos
        UNION
        SELECT id, nome_fantasia AS nome, cnpj AS documento, senha, 'empresas' AS tabela FROM empresas
    """)

    if logins:
        lista = logins if isinstance(logins, list) else [logins]
        
        for i in lista:
            if descriptografar(i['documento']) == login:
                tabela = {i['tabela']}
    senha = generate_password_hash(senha)
    
    banco.execute_non_query("UPDATE %s SET nome = %s, cpf = %s WHERE id = %s", tabela, senha)
    banco.execute_non_query("DELETE FROM requisicoes_mudanca_senha WHERE login = %s", login)

    flash(f'Senha atualizada com sucesso!', 'sucesso')
    return redirect(url_for('admin.restauracao_senha'))

@admin_bp.route('/excluir-admin/<int:id>')
# @verificar_login(requer_login=True)
# @verificar_tipo_usuario(['admin'])
def excluir_admin(id):
    banco.execute_non_query("UPDATE admins SET status = 'Inativo' WHERE id = %s", id)
    return '', 204