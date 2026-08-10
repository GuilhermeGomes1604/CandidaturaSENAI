import os
from datetime import datetime, date
from flask import redirect, url_for, flash, session
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from validate_docbr import CPF, CNPJ
from functools import wraps
from app.database import banco

load_dotenv()

CHAVE = os.getenv('CHAVE_FERNET').encode()
fernet = Fernet(CHAVE)

def criptografar(texto):
    if not texto: return ""
    return fernet.encrypt(texto.encode()).decode()

def descriptografar(texto):
    if not texto: return ""
    try:
        return fernet.decrypt(texto.encode()).decode()
    except Exception:
        return texto

def calcular_idade(data_nasc_str):
    data_nasc = datetime.strptime(data_nasc_str, '%Y-%m-%d').date()
    hoje = datetime.today().date()
    idade = hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))
    return idade

def formatar_data_e_hora(data_e_hora):
    if not data_e_hora:
        return ""
    if isinstance(data_e_hora, datetime):
        return data_e_hora.strftime("%d/%m/%Y, às %Hh%M")
    try:
        dt = datetime.strptime(data_e_hora, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        dt = datetime.strptime(data_e_hora, "%Y-%m-%d %H:%M")
    return dt.strftime("%d/%m/%Y, às %Hh%M")

def formatar_data(data):
    if not data:
        return ""
    if isinstance(data, date):
        return data.strftime("%d/%m/%Y")
    try:
        ano, mes, dia = data.split("-")
        return f"{dia}/{mes}/{ano}"
    except (ValueError, AttributeError):
        return str(data) 

def validar_documento(documento, tipo):
    doc = "".join(filter(str.isdigit, str(documento)))
    if tipo == "cpf":
        validador = CPF()
        if validador.validate(doc):
            return True, "CPF válido!"
        return False, "CPF inválido."
    elif tipo == "cnpj":
        validador = CNPJ()
        if validador.validate(doc):
            return True, "CNPJ válido!"
        return False, "CNPJ inválido."
    return False, "Tipo de documento não suportado."

def verificar_login(requer_login=True):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            login = 'id' in session
            if requer_login:
                if not login:
                    flash("Por favor, faça login para acessar esta página.", "aviso")
                    return redirect(url_for('geral.login'))
            else:
                if login:
                    flash("Você já está logado!", "info")
                    return redirect(url_for('geral.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def verificar_fase(fases_permitidas):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            fase_atual = banco.execute_query("SELECT fase FROM fase")[0]['fase']
            fases_validas = [fases_permitidas] if isinstance(fases_permitidas, str) else fases_permitidas
            if fase_atual not in fases_validas:
                flash(f"Acesso negado para esta fase do sistema.", "erro")
                return redirect(url_for('geral.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def verificar_tipo_usuario(*tipos):
    permitidos = []
    for item in tipos:
        if isinstance(item, (list, tuple)):
            permitidos.extend(item)
        else:
            permitidos.append(item)
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('tipo') not in permitidos:
                flash(f"Você não pode acessar essa página com uma conta de {session.get('tipo')}.", "erro")
                return redirect(url_for('geral.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator