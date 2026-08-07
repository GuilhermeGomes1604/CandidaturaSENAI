from flask import Blueprint, Flask, g, render_template, request, redirect, url_for, flash, session, send_from_directory, current_app, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from __init__ import UPLOAD_FOLDER
from models import Admin, Candidato, Empresa, Curso, CursoConcluido, Vaga, Recrutamento, Relatorio, Email, Telefone, Fase
from utils import criptografar, descriptografar, calcular_idade, formatar_data_e_hora, formatar_data, validar_documento, verificar_login, verificar_fase, verificar_tipo_usuario
from database import banco

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
def x():
    pass

@admin_bp.route('/excluir_admin/<int:id>')
@verificar_login(requer_login=False)
@verificar_tipo_usuario(['admin'])
def excluir_admin(id):
    banco.execute_non_query("UPDATE admins SET status = 'Inativo' WHERE id = %s", id)
    return '', 204