"""
Route API per il sistema di monitoraggio fotovoltaico.
"""
from flask import Blueprint, jsonify, current_app

# Crea il blueprint per le API
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/plants')
def get_plants():
    """
    Restituisce lo stato di tutti gli impianti.
    
    Returns:
        JSON: Stato di tutti gli impianti
    """
    plant_manager = current_app.config['PLANT_MANAGER']
    return jsonify(plant_manager.get_all_plants())

@api_bp.route('/plants/<plant_id>')
def get_plant(plant_id):
    """
    Restituisce lo stato di un impianto specifico.
    
    Args:
        plant_id (str): ID dell'impianto
    
    Returns:
        JSON: Stato dell'impianto o errore se non trovato
    """
    plant_manager = current_app.config['PLANT_MANAGER']
    plant_data = plant_manager.get_plant(plant_id)
    
    if plant_data:
        return jsonify(plant_data)
    else:
        return jsonify({"error": "Impianto non trovato"}), 404

@api_bp.route('/update')
def update_plants():
    """
    Forza l'aggiornamento di tutti gli impianti.
    
    Returns:
        JSON: Risultato dell'aggiornamento
    """
    plant_manager = current_app.config['PLANT_MANAGER']
    results = plant_manager.update_all_plants()
    
    return jsonify({
        "status": "success", 
        "message": "Aggiornamento completato", 
        "results": results,
        "plants": plant_manager.get_all_plants()
    })

@api_bp.route('/monitoring/start')
def start_monitoring():
    """
    Avvia il monitoraggio in background.
    
    Returns:
        JSON: Risultato dell'operazione
    """
    plant_manager = current_app.config['PLANT_MANAGER']
    success = plant_manager.start_monitoring()
    
    if success:
        return jsonify({"status": "success", "message": "Monitoraggio avviato"})
    else:
        return jsonify({"status": "error", "message": "Monitoraggio già attivo"})

@api_bp.route('/monitoring/stop')
def stop_monitoring():
    """
    Ferma il monitoraggio in background.
    
    Returns:
        JSON: Risultato dell'operazione
    """
    plant_manager = current_app.config['PLANT_MANAGER']
    success = plant_manager.stop_monitoring()
    
    if success:
        return jsonify({"status": "success", "message": "Monitoraggio fermato"})
    else:
        return jsonify({"status": "error", "message": "Monitoraggio non attivo"})

@api_bp.route('/status')
def get_status():
    """
    Restituisce lo stato del sistema di monitoraggio.
    
    Returns:
        JSON: Stato del sistema
    """
    plant_manager = current_app.config['PLANT_MANAGER']
    
    # Calcola statistiche
    plants = plant_manager.get_all_plants()
    total_plants = len(plants)
    online_plants = sum(1 for plant in plants.values() if plant['is_online'] and plant['power'] > 0)
    offline_plants = sum(1 for plant in plants.values() if not plant['is_online'])
    warning_plants = sum(1 for plant in plants.values() if plant['is_online'] and plant['power'] <= 0)
    
    total_power = sum(plant['power'] for plant in plants.values() if plant['is_online'])
    
    return jsonify({
        "status": "active" if plant_manager.monitoring_active else "inactive",
        "update_interval": plant_manager.update_interval,
        "statistics": {
            "total_plants": total_plants,
            "online_plants": online_plants,
            "offline_plants": offline_plants,
            "warning_plants": warning_plants,
            "total_power": round(total_power, 2)
        }
    })