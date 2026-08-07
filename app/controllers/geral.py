import os
from flask import Blueprint, Flask, g, render_template, request, redirect, url_for, flash, session, send_from_directory, current_app, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from __init__ import UPLOAD_FOLDER
from models import Admin, Candidato, Empresa, Curso, CursoConcluido, Vaga, Recrutamento, Relatorio, Email, Telefone, Fase
from utils import criptografar, descriptografar, calcular_idade, formatar_data_e_hora, formatar_data, validar_documento, verificar_login, verificar_fase, verificar_tipo_usuario
from database import banco

geral_bp = Blueprint('geral', __name__)

@geral_bp.route('/')
@verificar_login(requer_login=True)
def index():
    if session.get('tipo') == 'candidato':
        selecionou_cursos = banco.execute_query("SELECT IF(id_primeira_opcao IS NOT NULL, 1, 0) AS primeira_opcao FROM candidatos WHERE id = %s", session.get('id'))
        selecionou_cursos = list(selecionou_cursos)
        selecionou_cursos = bool(selecionou_cursos[0][0]) if selecionou_cursos else False

        dados_recrutamento = banco.execute_query("SELECT * FROM recrutamento WHERE id_candidato = %s AND relacao = 'Selecionado'", session.get('id'))
        if dados_recrutamento:
            selecao = True
            id_empresa = dados_recrutamento[0]['id_empresa']
            empresa = banco.execute_query("SELECT nome FROM empresas WHERE id = %s", id_empresa)[0][0]
        else:
            selecao = False
    return render_template('geral.index.html', selecionou_cursos = selecionou_cursos, selecao = selecao, empresa = empresa)

@geral_bp.route('/login', methods=['GET', 'POST'])
@verificar_login(requer_login=False)
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        login = request.form.get('login', '').strip()
        senha = request.form.get('senha', '').strip()

        if not login or not senha:
            flash('Preencha todos os campos obrigatórios.', 'erro')
            return redirect(url_for('geral.login'))
        
        if len(login) == 14 :
            logins = banco.execute_query("""
                SELECT id, nome, cpf, senha, 'admin' AS tipo FROM admins 
                UNION 
                SELECT id, nome, cpf, senha, 'candidato' AS tipo FROM candidatos
            """)

            if logins:
                lista = logins if isinstance(logins, list) else [logins]
                
                for i in lista:
                    if descriptografar(i['cpf']) == login:
                        if check_password_hash(i['senha'], senha):                              
                            session['id'] = i['id']
                            session['nome'] = descriptografar(i['nome'])
                            session['tipo'] = i['tipo']
                            
                            if i['status'] == 'Inativo':
                                tabela = i['tipo'] = "s"
                                banco.execute_non_query("UPDATE %s SET status = 'Inativo' WHERE id = %s", tabela, id)
                                flash(f"Conta reativada com sucesso. Bem-vindo de volta, {session['nome']}!", 'sucesso')
                            else:
                                flash(f"Bem-vindo de volta, {session['nome']}!", 'sucesso')
                            return redirect(url_for('geral.index'))
                        break
        else: 
            logins = banco.execute_query("""
                SELECT id, nome_fantasia AS nome, cnpj, senha, 'empresa' AS tipo FROM empresas
            """)

            if logins:
                lista = logins if isinstance(logins, list) else [logins]
                
                for i in lista:
                    if descriptografar(i['cnpj']) == login:
                        if check_password_hash(i['senha'], senha):
                            session['id'] = i['id']
                            session['nome'] = descriptografar(i['nome']).split()[0]
                            session['tipo'] = "empresa"

                            if i['status'] == 'Inativo':
                                banco.execute_non_query("UPDATE empresas SET status = 'Inativo' WHERE id = %s", id)
                                flash(f"Conta reativada com sucesso. Bem-vindo de volta, representante {session['nome']}!", 'sucesso')
                            else:
                                flash(f"Bem-vindo de volta, representante {session['nome']}!", 'sucesso')
                            return redirect(url_for('geral.index'))
                        break

        flash("CPF/CNPJ ou senha incorretos", "erro")
        return redirect(url_for('geral.login'))

@geral_bp.route('/cadastro', methods=['GET', 'POST'])
@verificar_login(requer_login=False)
def cadastro():
    if request.method == 'GET':
        return render_template('cadastro.html')
    else:
        nome = request.form.get('nome', '').strip()
        login = request.form.get('login', '').strip()
        senha = request.form.get('senha', '').strip()

        if not nome or not login or not senha:
            flash('Preencha todos os campos obrigatórios.', 'erro')
            return redirect(url_for('geral.login'))
        
        fase_atual = banco.execute_query("SELECT fase FROM fase")[0][0]

        if len(login) == 14 :
            if fase_atual == "Preparação":
                flash(f"As inscrições de candidatos ainda não começaram! Fique de olho no cronograma para não perder a abertura.", 'aviso')
                return redirect(url_for('geral.erro'))
            if fase_atual == "Seleção":
                flash(f"Ops! O prazo para novos candidatos já encerrou. Acompanhe os canais de comunicação do SENAI para participar da próxima edição!", 'erro')
                return redirect(url_for('geral.erro'))

            logins = banco.execute_query("""
                SELECT id, nome, cpf, senha, 'admin' AS tipo FROM admins 
                UNION 
                SELECT id, nome, cpf, senha, 'candidato' AS tipo FROM candidatos
            """)

            if logins:
                lista = logins if isinstance(logins, list) else [logins]
                
                for i in lista:
                    if descriptografar(i['cpf']) == login:                             
                        flash(f"Esse CPF já foi registrado.", 'erro')
                        return redirect(url_for('geral.login'))
                                
            session['nome_completo'] = nome
            session['cpf'] = login
            session['senha'] = senha

            return redirect(url_for('candidato.cadastro_candidato'))
        else:
            if fase_atual != "Preparação":
                flash(f"A fase de adesão de empresas já passou. Acompanhe o sistema e comunique o SENAI para participar da próxima edição!", 'erro')
                return redirect(url_for('geral.erro'))

            logins = banco.execute_query("""
                SELECT id, nome_fantasia AS nome, cnpj, senha, 'empresa' AS tipo FROM empresas
            """)

            if logins:
                lista = logins if isinstance(logins, list) else [logins]
                
                for i in lista:
                    if descriptografar(i['cnpj']) == login:                             
                        flash(f"Esse CNPJ já foi registrado.", 'erro')
                        return redirect(url_for('geral.login'))
                                
            session['nome_fantasia'] = nome
            session['cnpj'] = login
            session['senha'] = senha
        
            return redirect(url_for('empresa.cadastro_empresa'))
            
@geral_bp.route('/logout')
@verificar_login(requer_login=True)
def logout():
    session.clear()
    return redirect(url_for('geral.login'))

@geral_bp.route('/esqueci-minha-senha')
@verificar_login(requer_login=False)
def esqueci_senha():
    if request.method == 'GET':
        return render_template('esqueci-minha-senha.html')
    else:
        flash("Sua senha será","info")
        return redirect(url_for('geral.login'))

@geral_bp.route('/usuario', methods=['POST'])
@verificar_login(requer_login=True)
def usuario():
    if session.get('tipo') == 'admin':
        dados = banco.execute_query("SELECT * FROM admins WHERE id = %s",session.get('id'))
        if dados:
            dados = dados[0]
            usuario = {
                'nome': descriptografar(dados['nome']),
                'cpf': descriptografar(dados['cpf']),
                'data_registro': formatar_data_e_hora(dados['data_registro']),
            }
    else:  
        dados_emails = banco.execute_query("SELECT * FROM emails WHERE id_relativo = %s AND tipo = %s", session.get('id'), session.get('tipo'))
        emails = []
        if dados_emails:
            lista = dados_emails if isinstance(dados_emails, list) else [dados_emails]
            for i in lista:
                email = {
                    'email': descriptografar(i['email'])
                }
                emails.append(email)
        dados_telefones = banco.execute_query("SELECT * FROM telefones WHERE id_relativo = %s AND tipo = %s", session.get('id'), session.get('tipo'))
        telefones = []
        if dados_telefones:
            lista = dados_telefones if isinstance(dados_telefones, list) else [dados_telefones]
            for i in lista:
                telefone = {
                    'numero': descriptografar(i['numero']),
                    'preferencia_contato': i['preferencia_contato'],
                    'nome_contato': descriptografar(i['nome_contato'])
                }
                telefones.append(telefone)
        if session.get('tipo') == 'candidato':
            dados = banco.execute_query("SELECT * FROM candidatos WHERE id = %s",session.get('id'))
            if dados:
                dados = dados[0]
                if dados['nome_social']:
                    nome_social = descriptografar(dados['nome_social'])
                else:
                    nome_social = ''
                usuario = {
                    'nome': descriptografar(dados['nome']),
                    'nome_social': nome_social,
                    'cpf': descriptografar(dados['cpf']),
                    'data_nasc': formatar_data(descriptografar(dados['data_nasc'])),
                    'idade': calcular_idade(descriptografar(dados['data_nasc'])),
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
                    'id_primeira_opcao': dados['id_primeira_opcao'],
                    'id_segunda_opcao': dados['id_segunda_opcao'],
                    'id_terceira_opcao': dados['id_terceira_opcao'],
                    'disponibilidade': dados['disponibilidade'],
                    'data_registro': formatar_data_e_hora(dados['data_registro']),
                }
        else:
            dados = banco.execute_query("SELECT * FROM empresas WHERE id = %s",session.get('id'))
            if dados:
                dados = dados[0]
                usuario = {
                    'nome_fantasia': descriptografar(dados['nome_fantasia']),
                    'razao_social': descriptografar(dados['razao_social']),
                    'cnpj': descriptografar(dados['cnpj']),
                    'nome_responsavel': descriptografar(dados['nome_responsavel']),
                    'data_registro': formatar_data_e_hora(dados['data_registro']),
                }
    return render_template('usuario.html', usuario = usuario, emails = emails, telefones = telefones)

@geral_bp.route('/editar-dados', methods=['POST'])
@verificar_login(requer_login=True)
def editar_dados():
    dados = banco.execute_query("SELECT FROM %s WHERE id = %s", f"{session.get('tipo')} = 's'", session.get('id') )[0]
    if session.get('tipo') == "admin":
        dados = {
            'nome': descriptografar(dados['nome']),
            'cpf': descriptografar(dados['cpf'])
        }
    dados_emails = banco.execute_query("SELECT * FROM emails WHERE id_relativo = %s AND tipo = %s", session.get('id'), session.get('tipo'))
    emails = []
    if dados_emails:
        lista = dados_emails if isinstance(dados_emails, list) else [dados_emails]
        for i in lista:
            email = {
                'email': descriptografar(i['email'])
            }
            emails.append(email)
    dados_telefones = banco.execute_query("SELECT * FROM telefones WHERE id_relativo = %s AND tipo = %s", id, session.get('tipo'))
    telefones = []
    if dados_telefones:
        lista = dados_telefones if isinstance(dados_telefones, list) else [dados_telefones]
        for i in lista:
            telefone = {
                'numero': descriptografar(i['numero']),
                'preferencia_contato': i['preferencia_contato'],
                'nome_contato': descriptografar(i['nome_contato'])
            }
            telefones.append(telefone)
    elif session.get('tipo') == 'candidato':
        # Eu ia enviar os cursos já feitos também, mas fiquei com preguiça de adicionar. Acha que vai fazer falta o candidato não poder mudar? Ia dar um puta trabalho...
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
    else:
        dados = {
            'nome_fantasia': descriptografar(dados['nome_fantasia']),
            'razao_social': descriptografar(dados['razao_social']),
            'cpf': descriptografar(dados['cpf']),
            'nome_responsavel': descriptografar(dados['nome_responsavel'])
        }
    return render_template('editar-dados.html', dados = dados)

@geral_bp.route('/edicao-dados', methods=['POST'])
@verificar_login(requer_login=True)
def edicao_dados():
    match session.get('tipo'):
        case 'admin':
            imagem = request.files.get('imagem')
            nome = request.form.get('nome_fantasia', '').strip()
            cpf = request.form.get('cnpj', '').strip()

            if imagem and imagem.filename:
                nome_arquivo = f"admin_{session.get('id')}.jpg"
                pasta_admins = os.path.join('UPLOAD_FOLDER', 'admins')
                os.makedirs(pasta_admins, exist_ok=True)
                caminho = os.path.join(pasta_admins, nome_arquivo)
                imagem.save(caminho)

            obj = Admin()

            obj.nome = criptografar(nome)
            obj.cpf = criptografar(cpf)

            banco.execute_non_query("UPDATE admins SET nome = %s, cpf = %s WHERE id = %s", obj.nome, obj.cpf, session.get('id'))
        case 'candidato':
            imagem = request.files.get('imagem')
            nome = request.form.get('nome_fantasia', '').strip()
            nome_social = request.form.get('cnpj', '').strip()
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

            if imagem and imagem.filename:
                nome_arquivo = f"candidato_{session.get('id')}.jpg"
                pasta_candidatos = os.path.join('UPLOAD_FOLDER', 'candidatos')
                os.makedirs(pasta_candidatos, exist_ok=True)
                caminho = os.path.join(pasta_candidatos, nome_arquivo)
                imagem.save(caminho)

            
            banco.execute_non_query("DELETE FROM emails WHERE id_relativo = %s AND tipo = 'candidato'", session.get('id'))
            obj = Email()
            obj.id_relativo = session.get('id')
            obj.tipo = 'candidato' 
        
            lista_emails = [email1, email2, email3]
        
            for email in lista_emails:
                if email:
                    obj.email = email 
                    
                    banco.execute_non_query(
                        'INSERT INTO emails (id_relativo, tipo, email) VALUES (%s, %s, %s)',
                        obj.id_relativo, obj.tipo, obj.email
                    )
            
            banco.execute_non_query("DELETE FROM telefones WHERE id_relativo = %s AND tipo = 'candidato'", session.get('id'))
            obj = Telefone()
            obj.id_relativo = session.get('id')
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
                    
                    obj.numero = numero
                    obj.preferencia_contato = preferencia_contato
                    obj.nome_contato = nome_contato
                    
                    banco.execute_non_query(
                        """INSERT INTO telefones (id_relativo, tipo, numero, preferencia_contato, nome_contato) VALUES (%s, %s, %s, %s, %s)""",obj.id_relativo, obj.tipo, obj.numero, obj.preferencia_contato, obj.nome_contato)
                        
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
        
            banco.execute_non_query('UPDATE candidatos SET tipo = %s, nome = %s, nome_social = %s, cpf = %s, data_nasc = %s, genero = %s, cep = %s, endereco = %s, numero = %s, complemento = %s, bairro = %s, cidade = %s, estado = %s, escolaridade = %s, periodo_estudo = %s, ja_estudou = %s WHERE id = %s', obj.tipo, obj.nome, obj.nome_social, obj.cpf, obj.data_nasc, obj.genero, obj.cep, obj.endereco, obj.numero, obj.complemento, obj.bairro, obj.cidade, obj.estado, obj.escolaridade, obj.periodo_estudo, obj.ja_estudou, session.get('id'))
        case 'empresa':
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
                nome_arquivo = f"empresa_{session.get('id')}.jpg"
                pasta_empresas = os.path.join('UPLOAD_FOLDER', 'empresas')
                os.makedirs(pasta_empresas, exist_ok=True)
                caminho = os.path.join(pasta_empresas, nome_arquivo)
                imagem.save(caminho)

            banco.execute_non_query("DELETE FROM emails WHERE id_relativo = %s AND tipo = 'empresa'", session.get('id'))
            obj = Email()
            obj.id_relativo = session.get('id')
            obj.tipo = 'empresa' 

            lista_emails = [email1, email2, email3]

            for email in lista_emails:
                if email:
                    obj.email = email 
                    
                    banco.execute_non_query(
                        'INSERT INTO emails (id_relativo, tipo, email) VALUES (%s, %s, %s)',
                        obj.id_relativo, obj.tipo, obj.email
                    )
            
            banco.execute_non_query("DELETE FROM telefones WHERE id_relativo = %s AND tipo = 'empresa'", session.get('id'))
            obj = Telefone()
            obj.id_relativo = session.get('id')
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
            obj.nome_responsavel = criptografar(nome_responsavel)
        
            banco.execute_non_query('UPDATE empresas SET nome_fantasia = %s, razao_social = %s, cnpj = %s, nome_responsavel = %s WHERE id = %s', obj.nome_fantasia, obj.razao_social, obj.cnpj, obj.nome_responsavel, session.get('id'))
    return redirect(url_for('geral.usuario'))

@geral_bp.route('/cursos')
@verificar_login(requer_login=True)
@verificar_tipo_usuario('admin','empresa')
def cursos():
    return render_template('cursos.html')

@geral_bp.route('/api/dados-cursos')
@verificar_login(requer_login=True)
@verificar_tipo_usuario('admin','empresa')
def api_dados_cursos():
    pesquisa = request.args.get('pesquisa', '').split()
    status = request.args.get('status', '')
    horarios = request.args.getlist('horario')

    query = "SELECT * FROM cursos WHERE 1=1"
    parametros = []

    if pesquisa: 
        for palavra in pesquisa:
            query += " AND (nome LIKE %s OR sigla LIKE %s OR detalhamento LIKE %s)"
            termo = f"%{palavra}%" 
            parametros.extend([termo, termo, termo])

    if status:
        query += " AND status = %s"
        parametros.append(status)

    if horarios:
        placeholders = ', '.join(['%s'] * len(horarios))
        query += f" AND horario IN ({placeholders})"
        parametros.extend(horarios)

    dados = banco.execute_query(query, tuple(parametros))
    cursos = []
    if dados:
        lista = dados if isinstance(dados, list) else [dados]
        for i in lista:
            curso = {
                'id': i['id'],
                'nome': i['nome'],
                'sigla': i['sigla'],
                'horario': i['horario'],
                'detalhamento': i['detalhamento'],
                'idade_minima': i['idade_minima'],
                'duracao': i['duracao'],
                'vagas': i['vagas'],
                'data_registro': formatar_data_e_hora(i['data_registro']),
                'status': i['status']
            }
            cursos.append(curso)
    return jsonify({
        'cursos': cursos
    })

@geral_bp.route('/curso/<int:id>')
@verificar_login(requer_login=True)
@verificar_tipo_usuario('admin','empresa')
def curso(id):
    dados = banco.execute_query("SELECT * FROM cursos WHERE id = %s",id)
    if dados:
        dados = dados[0]
        curso = {
            'id': id,
            'nome': dados['nome'],
            'sigla': dados['sigla'],
            'horario': dados['horario'],
            'detalhamento': dados['detalhamento'],
            'idade_minima': dados['idade_minima'],
            'duracao': dados['duracao'],
            'vagas': dados['vagas'],
            'data_registro': formatar_data_e_hora(dados['data_registro']),
            'status': dados['status']
        }
    return render_template('cursos.html', curso = curso)

@geral_bp.route('/candidatos')
@verificar_login(requer_login=True)
@verificar_tipo_usuario('admin','empresa')
def candidatos():
    dados = banco.execute_query("SELECT * FROM cursos WHERE status == 'ativo'")
    cursos = []
    if dados:
        lista = dados if isinstance(dados, list) else [dados]
        for i in lista:
            if len(i['data_registro']) > 10:
                data_registro = formatar_data_e_hora(i['data_registro'])
            else:
                data_registro = formatar_data(i['data_registro'])
            curso = {
                'id': i['id'],
                'nome': i['nome'],
                'sigla': i['sigla'],
                'horario': i['horario'],
                'turma': i['turma'],
                'detalhamento': i['detalhamento'],
                'data_registro': data_registro
            }
            cursos.append(curso)
    return render_template('candidatos.html')

@geral_bp.route('/api/dados-candidatos')
@verificar_login(requer_login=True)
@verificar_tipo_usuario('admin', 'empresa')
def api_dados_candidatos():
    pesquisa = request.args.get('pesquisa', '').split()
    situacao = request.args.get('situacao', '')
    horarios = request.args.getlist('horario')
    cursos = request.args.getlist('cursos')
    tipo_cursos = request.args.getlist('tipo_cursos')

    query = "SELECT * FROM candidatos WHERE status = 'Ativo'"
    parametros = []

    if pesquisa: 
        for palavra in pesquisa:
            query += " AND (nome LIKE %s OR nome_social LIKE %s)"
            termo = f"%{palavra}%"
            parametros.extend([termo, termo])

    if situacao:
        query += " AND situacao = %s"
        parametros.append(situacao)

    if horarios:
        placeholders = ', '.join(['%s'] * len(horarios))
        query += f" AND horario NOT IN ({placeholders})"
        parametros.extend(horarios)

    if session.get('tipo') == 'admin' and cursos:
        placeholders_tipo = ', '.join(['%s'] * len(cursos))
        resultado_cursos = banco.execute_query(
            f"SELECT id FROM cursos WHERE tipo IN ({placeholders_tipo})", 
            tuple(cursos)
        )
        
        if resultado_cursos:
            cursos = resultado_cursos if isinstance(resultado_cursos, list) else [resultado_cursos]
            ids = [c['id'] for c in cursos]
            
            if ids:
                placeholders_ids = ', '.join(['%s'] * len(ids))
                query += f""" AND (id_primeira_opcao IN ({placeholders_ids})
                OR id_segunda_opcao IN ({placeholders_ids})
                OR id_terceira_opcao IN ({placeholders_ids}))"""
                parametros.extend(ids * 3)

    elif session.get('tipo') == 'empresa' and tipo_cursos:
        cursos_vagas = banco.execute_query("SELECT id_curso FROM vagas WHERE id_empresa = %s", session.get('id'))

        placeholders_tipo = ', '.join(['%s'] * len(cursos_vagas))
        resultado_cursos = banco.execute_query(
            f"SELECT id FROM cursos WHERE tipo IN ({placeholders_tipo})", 
            tuple(cursos_vagas)
        )
        
        if resultado_cursos:
            cursos_vagas = resultado_cursos if isinstance(resultado_cursos, list) else [resultado_cursos]
            ids = [c['id'] for c in cursos_vagas]
            
            if ids:
                placeholders_ids = ', '.join(['%s'] * len(ids))
                query += f""" AND (id_primeira_opcao IN ({placeholders_ids})
                OR id_segunda_opcao IN ({placeholders_ids})
                OR id_terceira_opcao IN ({placeholders_ids}))"""
                parametros.extend(ids * 3)

    dados = banco.execute_query(query, tuple(parametros))
    candidatos = []
    
    if dados:
        lista = dados if isinstance(dados, list) else [dados]
        for i in lista:
            nome = descriptografar(i['nome']) if i('nome') else ""
            nome_social = descriptografar(i['nome_social']) if i('nome_social') else ""
            
            if pesquisa:
                corresponde = True
                for palavra in pesquisa:
                    palavra_minuscula = palavra.lower()
                    if (palavra_minuscula not in nome) and (palavra_minuscula not in nome_social):
                        corresponde = False
                        break
                
                if not corresponde:
                    continue
            periodo_livre = ["Manhã","Tarde","Noite"]
            if i['periodo_estudo']:
                if i['periodo_estudo'] == "Integral":
                    periodo_livre = ["Noite"]
                else:
                    periodo_livre.remove(i['periodo_estudo'])
            
            relacao = banco.execute_query("SELECT relacao FROM recrutamento WHERE id_candidato = %s", i['id'])
            if relacao:
                relacao = relacao[0][0]
            else:
                relacao = None

            candidato = {
                'id': i['id'],
                'nome': descriptografar(i['nome_social']) if i('nome_social') else descriptografar(i['nome']),
                'idade': calcular_idade(descriptografar(i['data_nasc'])),
                'escolaridade': i['escolaridade'],
                'periodo_livre': periodo_livre,
                'ja_estudou': i['ja_estudou'],
                'id_primeira_opcao': i['id_primeira_opcao'],
                'id_segunda_opcao': i['id_segunda_opcao'],
                'id_terceira_opcao': i['id_terceira_opcao'],
                'disponibilidade': i['disponibilidade'],
                'relacao': relacao 
            }
            candidatos.append(candidato)
            
    return jsonify({
        'candidatos': candidatos
    })
 
@geral_bp.route('/candidato/<int:id>')
@verificar_login(requer_login=True)
@verificar_tipo_usuario('admin','empresa')
def candidato(id):
    dados = banco.execute_query("SELECT * FROM candidato WHERE id = %s",id)[0]
    if dados:
        lista = dados if isinstance(dados, list) else [dados]
        for i in lista:
            dados_recrutamento = banco.execute_query("SELECT * FROM recrutamento WHERE id_candidato = %s", id, 'candidato')[0]
            if dados_recrutamento:
                id_empresa = dados_recrutamento['id_empresa']
                empresa = banco.execute_query("SELECT nome FROM empresas WHERE id = %s",id_empresa)[0][0]
                detalhamento = dados_recrutamento['detalhamento']
                relacao = dados_recrutamento['relacao']

            candidato = {
                'id': id,
                'nome': descriptografar(dados['nome']),
                'nome_social': descriptografar(dados['nome_social']),
                'cpf': descriptografar(dados['cpf']),
                'data_nasc': formatar_data(descriptografar(dados['data_nasc'])),
                'idade': calcular_idade(descriptografar(dados['data_nasc'])),
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
                'empresa': empresa,
                'detalhamento': detalhamento,
                'relacao': relacao,
                'data_registro': formatar_data_e_hora(dados['data_registro'])
            }

            cursos_selecionados = []
            
            primeira_opcao = banco.execute_query("SELECT nome, sigla FROM cursos WHERE id = %s", dados['id_primeira_opcao'])[0]
            nome = primeira_opcao['nome']
            sigla = primeira_opcao['sigla']
            curso = {
                'nome': nome,
                'sigla': sigla
            }
            cursos_selecionados.append(curso)
            if dados['id_segunda_opcao']:
                segunda_opcao = banco.execute_query("SELECT nome, sigla FROM cursos WHERE id = %s", dados['id_primeira_opcao'])[0]
                nome = segunda_opcao['nome']
                sigla = segunda_opcao['sigla']
                curso = {
                    'nome': nome,
                    'sigla': sigla
                }
                cursos_selecionados.append(curso)
                if dados['id_terceira_opcao']:
                    terceira_opcao = banco.execute_query("SELECT nome, sigla FROM cursos WHERE id = %s", dados['id_primeira_opcao'])[0]
                    nome = terceira_opcao['nome']
                    sigla = terceira_opcao['sigla']
                    curso = {
                        'nome': nome,
                        'sigla': sigla
                    }
                    cursos_selecionados.append(curso)            

    dados_emails = banco.execute_query("SELECT * FROM emails WHERE id_relativo = %s AND tipo = %s", id, 'candidato')
    emails = []
    if dados_emails:
        lista = dados_emails if isinstance(dados_emails, list) else [dados_emails]
        for i in lista:
            email = {
                'email': descriptografar(i['email'])
            }
            emails.append(email)

    dados_telefones = banco.execute_query("SELECT * FROM telefones WHERE id_relativo = %s AND tipo = %s", id, 'candidato')
    telefones = []
    if dados_telefones:
        lista = dados_telefones if isinstance(dados_telefones, list) else [dados_telefones]
        for i in lista:
            telefone = {
                'numero': descriptografar(i['numero']),
                'preferencia_contato': i['preferencia_contato'],
                'nome_contato': descriptografar(i['nome_contato'])
            }
            telefones.append(telefone)

    dados_telefones = banco.execute_query("SELECT * FROM telefones WHERE id_relativo = %s AND tipo = %s", id, 'candidato')
    telefones = []
    if dados_telefones:
        lista = dados_telefones if isinstance(dados_telefones, list) else [dados_telefones]
        for i in lista:
            telefone = {
                'numero': descriptografar(i['numero']),
                'preferencia_contato': i['preferencia_contato'],
                'nome_contato': descriptografar(i['nome_contato'])
            }
            telefones.append(telefone)
    return render_template('candidato.html', candidato = candidato, emails = emails, telefones = telefones, cursos_selecionados = cursos_selecionados)

@geral_bp.route('/vagas/<int:id>')
@verificar_login(requer_login=True)
@verificar_tipo_usuario('admin','empresa')
def vagas(id):
    dados = banco.execute_query("SELECT * FROM empresas WHERE id = ?", id)[0]
    empresa = {
        'id': id,
        'nome': dados['nome']
    }
    dados_cursos = banco.execute_query("SELECT * FROM cursos")
    cursos = []
    if dados_cursos:
        lista = dados_cursos if isinstance(dados_cursos, list) else [dados_cursos]
        for i in lista:
            curso = {
                'id': i['id'],
                'nome': f"{i['nome']} ({i['sigla']})",
                'duracao': i['duracao']
            }
            cursos.append(curso)
    return render_template('vagas.html', empresa = empresa, cursos = cursos)

@geral_bp.route('/marcados/<int:id>')
@verificar_login(requer_login=True)
@verificar_tipo_usuario('admin','empresa')
def marcados(id):
    empresa = banco.execute_query("SELECT nome_fantasia FROM empresas WHERE id = %s", id)[0][0]
    empresa = empresa.split()[0]
    dados = banco.execute_query("SELECT * FROM candidatos WHERE id IN (SELECT id_candidato FROM recrutamento WHERE id_empresa = %s and relacao = 'Marcado')", id)
    candidatos = []
    
    if dados:
        lista = dados if isinstance(dados, list) else [dados]
        for i in lista:
            periodo_livre = ["Manhã","Tarde","Noite"]
            if i['periodo_estudo']:
                if i['periodo_estudo'] == "Integral":
                    periodo_livre = ["Noite"]
                else:
                    periodo_livre.remove(i['periodo_estudo'])

            relacao = banco.execute_query("SELECT relacao FROM recrutamento WHERE id_candidato = %s", i['id'])
            if relacao:
                relacao = relacao[0][0]
            else:
                relacao = None

            candidato = {
                'id': i['id'],
                'nome': descriptografar(i['nome_social']) if i('nome_social') != '' else descriptografar(i['nome']),
                'idade': calcular_idade(descriptografar(i['data_nasc'])),
                'escolaridade': i['escolaridade'],
                'periodo_livre': periodo_livre,
                'ja_estudou': i['ja_estudou'],
                'id_primeira_opcao': i['id_primeira_opcao'],
                'id_segunda_opcao': i['id_segunda_opcao'],
                'id_terceira_opcao': i['id_terceira_opcao'],
                'disponibilidade': i['disponibilidade'],
                'relacao': relacao
            }
            candidatos.append(candidato)
    return render_template('empresas.marcados.html', candidatos = candidatos, empresa = empresa)

@geral_bp.route('/selecionados/<int:id>')
@verificar_login(requer_login=True)
@verificar_tipo_usuario('admin','empresa')
def selecionados(id):
    empresa = banco.execute_query("SELECT nome_fantasia FROM empresas WHERE id = %s", id)[0][0]
    empresa = empresa.split()[0]
    dados = banco.execute_query("SELECT * FROM candidatos WHERE id IN (SELECT id_candidato FROM recrutamento WHERE id_empresa = %s and relacao = 'Selecionado')", id)
    candidatos = []
    
    if dados:
        lista = dados if isinstance(dados, list) else [dados]
        for i in lista:
            periodo_livre = ["Manhã","Tarde","Noite"]
            if i['periodo_estudo']:
                if i['periodo_estudo'] == "Integral":
                    periodo_livre = ["Noite"]
                else:
                    periodo_livre.remove(i['periodo_estudo'])

            relacao = banco.execute_query("SELECT relacao FROM recrutamento WHERE id_candidato = %s", i['id'])
            if relacao:
                relacao = relacao[0][0]
            else:
                relacao = None

            candidato = {
                'id': i['id'],
                'nome': descriptografar(i['nome_social']) if i('nome_social') != '' else descriptografar(i['nome']),
                'idade': calcular_idade(descriptografar(i['data_nasc'])),
                'escolaridade': i['escolaridade'],
                'periodo_livre': periodo_livre,
                'ja_estudou': i['ja_estudou'],
                'id_primeira_opcao': i['id_primeira_opcao'],
                'id_segunda_opcao': i['id_segunda_opcao'],
                'id_terceira_opcao': i['id_terceira_opcao'],
                'disponibilidade': i['disponibilidade'],
                'relacao': relacao
            }
            candidatos.append(candidato)
    return render_template('empresas.selecionados.html', candidatos = candidatos, empresa = empresa)

@geral_bp.route('/exibir-imagem-usuario')
def exibir_imagem_usuario(id):
    match session.get('tipo'):
        case 'admin':
            nome_arquivo = f"admin_{id}.jpg"
            pasta = os.path.join(current_app.config['UPLOAD_FOLDER'], 'admins')
        case 'candidato':
            nome_arquivo = f"candidato_{id}.jpg"
            pasta = os.path.join(current_app.config['UPLOAD_FOLDER'], 'candidatos')
        case 'empresa':
            nome_arquivo = f"candidato _{id}.jpg"
            pasta = os.path.join(current_app.config['UPLOAD_FOLDER'], 'admins')
    caminho_completo = os.path.join(pasta, nome_arquivo)
    if os.path.exists(caminho_completo):
        return send_from_directory(pasta, nome_arquivo)
    return send_from_directory('static/img', 'icone_avatar_padrao.png')

@geral_bp.route('/exibir-imagem-candidato/<int:id>')
def exibir_imagem_candidato(id):
    nome_arquivo = f'candidato_{id}.jpg'
    pasta = os.path.join(current_app.config['UPLOAD_FOLDER'], 'candidatos')
    caminho = os.path.join(pasta, nome_arquivo)
    if os.path.exists(caminho):
        return send_from_directory(pasta, nome_arquivo)
    return send_from_directory('static/img', 'icone_avatar_padrao.png')

@geral_bp.route('/exibir-imagem-empresa/<int:id>')
def exibir_imagem_empresa(id):
    nome_arquivo = f"empresa_{id}.jpg"
    pasta = os.path.join(current_app.config['UPLOAD_FOLDER'], 'empresas')
    caminho_completo = os.path.join(pasta, nome_arquivo)
    if os.path.exists(caminho_completo):
        return send_from_directory(pasta, nome_arquivo)
    return send_from_directory('static/img', 'icone_avatar_padrao.png')

@geral_bp.route('/erro')
def erro():
    if '_flashes' not in session or not session['_flashes']:
        return redirect(request.referrer or url_for('geral.index'))
    return render_template('erro.html')