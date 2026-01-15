import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go

# --- STAŁE POJAZDÓW Z TWOJEGO PLIKU ---
VEHICLES = {
    "BUS": {"L": 450, "W": 170, "H": 200, "max_weight": 1100},
    "Solówka 6m": {"L": 600, "W": 245, "H": 250, "max_weight": 3500},
    "Solówka 7m": {"L": 700, "W": 245, "H": 250, "max_weight": 3500},
    "FTL (TIR)": {"L": 1360, "W": 245, "H": 270, "max_weight": 24000}
}

def load_products():
    with open('products.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# --- KLUCZOWA LOGIKA Z PLIKU HTML ---
def run_sqm_algorithm(items, vehicle):
    # 1. Tworzenie stosów (identycznie jak w Twoim JS)
    stacks = []
    # Kopiujemy przedmioty, żeby nie zmieniać oryginałów
    remaining_items = [dict(i) for i in items]
    
    # Próba stackowania
    for item in remaining_items:
        stacked = False
        if item.get('canStack', False):
            for s in stacks:
                # Warunki z Twojego kodu: ta sama podstawa i canStack
                if (s['width'] == item['width'] and 
                    s['length'] == item['length'] and 
                    s['total_height'] + item['height'] <= vehicle['H']):
                    s['items'].append(item)
                    s['total_height'] += item['height']
                    s['total_weight'] += item['weight']
                    stacked = True
                    break
        
        if not stacked:
            stacks.append({
                'width': item['width'],
                'length': item['length'],
                'total_height': item['height'],
                'total_weight': item['weight'],
                'items': [item]
            })

    # 2. Sortowanie stosów po powierzchni (B x L)
    stacks.sort(key=lambda s: s['width'] * s['length'], reverse=True)

    # 3. Rozmieszczanie (Shelf Packing)
    placed_stacks = []
    current_x = 0
    current_y = 0
    max_width_in_row = 0
    current_weight = 0

    for s in stacks:
        # Sprawdzenie wagi całkowitej
        if current_weight + s['total_weight'] > vehicle['max_weight']:
            continue
            
        # Czy mieści się w rzędzie (na szerokość W)
        if current_y + s['length'] > vehicle['W']:
            current_y = 0
            current_x += max_width_in_row
            max_width_in_row = 0

        # Czy mieści się na długość naczepy (L)
        if current_x + s['width'] <= vehicle['L']:
            s['x'] = current_x
            s['y'] = current_y
            placed_stacks.append(s)
            
            current_y += s['length']
            max_width_in_row = max(max_width_in_row, s['width'])
            current_weight += s['total_weight']

    return placed_stacks

# --- WIZUALIZACJA 3D ---
def draw_3d(placed_stacks, vehicle):
    fig = go.Figure()
    
    for s in placed_stacks:
        current_z = 0
        for item in s['items']:
            # Rysujemy każdy element w stosie
            fig.add_trace(go.Mesh3d(
                x=[s['x'], s['x']+s['width'], s['x']+s['width'], s['x'], s['x'], s['x']+s['width'], s['x']+s['width'], s['x']],
                y=[s['y'], s['y'], s['y']+s['length'], s['y']+s['length'], s['y'], s['y'], s['y']+s['length'], s['y']+s['length']],
                z=[current_z, current_z, current_z, current_z, current_z+item['height'], current_z+item['height'], current_z+item['height'], current_z+item['height']],
                i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
                j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
                k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
                opacity=0.9,
                flatshading=True,
                color="#4682B4" if item.get('canStack') else "#A52A2A",
                name=item['name']
            ))
            current_z += item['height']

    fig.update_layout(scene=dict(
        aspectmode='manual',
        aspectratio=dict(x=vehicle['L']/vehicle['W'], y=1, z=vehicle['H']/vehicle['W'])
    ))
    return fig

# --- INTERFEJS STREAMLIT ---
st.title("SQM Planer Załadunku (Logika 1:1)")
# ... (tutaj dodawanie produktów jak wcześniej) ...
