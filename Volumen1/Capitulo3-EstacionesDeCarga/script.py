import os
import sys
import xml.etree.ElementTree as ET

# confirma que traci puede ser encontrado
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
    print(f"SUMO_HOME encontrado. Herramientas añadidas desde: {tools}")
else:
    sys.exit("Por favor declara la variable de entorno 'SUMO_HOME'")

import traci
from sumolib import checkBinary
from sumolib import checkBinary

def ensure_output_dir():
    if not os.path.exists("resultados"):
        os.makedirs("resultados")

def get_charging_stations(xml_file):
    """Parsea el archivo XML y devuelve una lista de IDs de las estaciones."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    # Asumiendo que no hay namespaces complejos
    stations = [child.get('id') for child in root.findall('chargingStation')]
    return stations

def create_temp_charging_file(original_file, temp_file, id_to_exclude):
    """Crea un archivo XML temporal excluyendo una estación específica."""
    tree = ET.parse(original_file)
    root = tree.getroot()
    
    # Encontrar y remover la estación
    for station in root.findall('chargingStation'):
        if station.get('id') == id_to_exclude:
            root.remove(station)
            break
            
    tree.write(temp_file)

def run_simulation():
    # 1. Preparar entorno
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("Por favor declara la variable de entorno 'SUMO_HOME'")

    ensure_output_dir()
    
    # 2. Obtener todas las estaciones
    all_stations = get_charging_stations("chargingStations.add.xml")
    print(f"Se encontraron {len(all_stations)} estaciones de carga.")
    
    sumo_binary = checkBinary("sumo")

    # 3. Iterar sobre cada estación
    for station_id in all_stations:
        print(f"--- Iniciando simulación desactivando estación: {station_id} ---")
        
        # Nombre del archivo temporal para esta iteración
        temp_charging_file = "temp_chargingStations.xml"
        
        # Crear el archivo XML sin la estación actual
        create_temp_charging_file("chargingStations.add.xml", temp_charging_file, station_id)
        
        # Construir la lista de archivos adicionales
        # Reemplazamos el original por el temporal y añadimos los otros (busStops, output)
        current_additionals = [temp_charging_file] + ["busStops.add.xml", "output.add.xml"]
        additional_files_str = ",".join(current_additionals)
        
        # Definir nombres de salida únicos para que no se sobrescriban
        tripinfo_out = os.path.join("resultados", f"tripinfo_sin_{station_id}.xml")
        stopinfo_out = os.path.join("resultados", f"stopinfo_sin_{station_id}.xml")
        stats_out = os.path.join("resultados", f"estadisticas_sin_{station_id}.xml")

        # Argumentos para TraCi
        # Nota: Los argumentos de línea de comandos sobrescriben a los del .sumocfg
        sumo_args = [
            sumo_binary,
            "-c", "simulacion.sumocfg",
            "--additional-files", additional_files_str,
            "--tripinfo-output", tripinfo_out,
            "--stop-output", stopinfo_out,
            "--statistic-output", stats_out,
            "--no-step-log", "true" # Para reducir ruido en consola
        ]
        
        # Iniciar TraCi
        traci.start(sumo_args)
        
        # Ejecutar simulación paso a paso
        step = 0
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            step += 1
            
        traci.close()
        print(f"Simulación finalizada para {station_id}. Resultados guardados.")

    # Limpieza del archivo temporal al final
    if os.path.exists("temp_chargingStations.xml"):
        os.remove("temp_chargingStations.xml")
        print("Limpieza completada.")

if __name__ == "__main__":
    run_simulation()