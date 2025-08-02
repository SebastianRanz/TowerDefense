
import json
import os


def retrieve_map_data():
    """
    Retrieves map data from the JSON file.
    
    Returns:
        list: A list of maps with their details.
    """
    
    maps_file_path = os.path.join(os.path.dirname(__file__), 'map_data', 'maps.json')

    if not os.path.exists(maps_file_path):
        raise FileNotFoundError(f"Map data file not found at {maps_file_path}")
    
    with open(maps_file_path, 'r') as file:
        maps_data = json.load(file)
    
    if not isinstance(maps_data, list):
        raise ValueError("Map data should be a list of maps")
    
    return maps_data

def retrieve_tower_data():
    tower_data_file_path = os.path.join(os.path.dirname(__file__), 'tower_data', 'tower_data.json')

    if not os.path.exists(tower_data_file_path):
        raise FileNotFoundError(f"Tower Data file not found at {tower_data_file_path}")
    
    with open(tower_data_file_path, 'r') as file:
        tower_data = json.load(file)
    
    if not isinstance(tower_data, list):
        raise ValueError("Tower Data should be a list of maps")
    
    return tower_data