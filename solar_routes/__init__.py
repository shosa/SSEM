"""
Package per le route del sistema di monitoraggio fotovoltaico.
"""
from flask import Blueprint, render_template

# Importa il blueprint delle API
from solar_routes.api import api_bp

# Crea il blueprint principale
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    Route principale che renderizza la dashboard.
    
    Returns:
        str: HTML renderizzato
    """
    return render_template('index.html')

# Lista di tutti i blueprint
blueprints = [main_bp, api_bp]

__all__ = ['blueprints']