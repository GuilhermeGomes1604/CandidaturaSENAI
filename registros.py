import os
from cryptography.fernet import Fernet
from werkzeug.security import generate_password_hash
from app.database import banco
fernet = Fernet('v3VLBlphJa_qXwvMLIigB04uSrCDMNNVFUy0vHWxPHU=')

def criptografar(texto):
    if not texto: return ""
    return fernet.encrypt(texto.encode()).decode()

def descriptografar(texto):
    if not texto: return ""
    try:
        return fernet.decrypt(texto.encode()).decode()
    except Exception:
        return texto

def CriarAdmin():
    nome = "Administrador"
    cpf = "000.000.000-00"
    senha = "12345678"
    print(f"INSERT INTO admins (nome, cpf, senha) VALUES ('{criptografar(nome)}', '{criptografar(cpf)}', '{generate_password_hash(senha)}')")

print(descriptografar('gAAAAABqe0osRmYMmwmmapsa-x5c7RVIXM6A1Uu5K-IjJ6QEnOXA4S7_XwG2kHaLzWn_QdS1ltVpQ-m0N-JGRafLiNmAF9xQRo_hLdaSdu8KAJqUup4joRE='))