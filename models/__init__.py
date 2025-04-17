"""
Package per i modelli di dati del sistema di monitoraggio fotovoltaico.
"""
# Utilizziamo import assoluti invece di relativi
from models.plant import Plant
from models.aurora_plant import AuroraVisionPlant
from models.fusion_plant import FusionSolarPlant

__all__ = ['Plant', 'AuroraVisionPlant', 'FusionSolarPlant']