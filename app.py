import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go

# --- DANE POJAZDÓW (DOKŁADNIE Z TWOJEGO PLIKU HTML) ---
# Format: Vehicle(name, maxPallets, maxWeightKg, loadLengthCm, loadWidthCm, loadHeightCm)
VEHICLES = {
    "BUS": {
        "name": "BUS",
        "max_pallets": 8,
        "max_weight": 1100,
        "L": 450,
        "W": 150,  # W Twoim kodzie szerokość to 150
        "H": 245   # W Twoim kodzie wysokość to 245
    },
    "6m": {
        "name": "Solówka 6m",
        "max_pallets": 14,
        "max_weight": 3500,
        "L": 600,
        "W": 245,
        "H": 245
    },
    "7m": {
        "name": "Solówka 7m",
        "max_pallets": 16,
        "max_weight": 3500,
        "L": 700,
        "W": 245,
        "H": 245
    },
    "FTL": {
        "name": "FTL",
        "max_pallets": 31,
        "max_weight": 12000, # W Twoim kodzie limit to 12 ton
        "L": 1360,
        "W": 245,
        "H": 265
    }
}

def load_products():
    with open('products.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# --- ALGORYTM LOGISTYCZNY (ODZWIERCIEDLENIE TWOJEGO JS) ---
def calculate_load_sqm(items_to_load, vehicle):
    # 1. Przygotowanie listy pojedynczych elementów
    all_single_items = []
    for item in items_to_load:
        all_single_items.append(dict(item))
    
    # Sortowanie jak w JS: największa powierzchnia (area) na początek
    all_single_items.sort(key=lambda x: x['width'] * x['length'], reverse=True)

    # 2. Tworzenie stosów (Stacking)
    placed_stacks = []
    current_vehicle_weight = 0
    
    # Symulacja wolnych przestrzeni (Uproszczony Shelf Packing jak w Twoim kodzie)
    # W Pythonie implementujemy logikę: x to długość (L), y to szerokość (W)
    current_x = 0
    current_y = 0
    max_width_in_row = 0

    for item in all_single_items:
        # Sprawdzenie czy pojedynczy element nie przekracza limitu wagi auta
        if current_vehicle_weight + item['weight'] > vehicle['max_weight']:
            continue

        placed_on_stack = False
        
        # Próba dołożenia do istniejącego stosu
        if item.get('canStack', True):
            for s in placed_stacks:
                if (s['canStackBase'] and 
                    item['length'] <= s['length'] and 
                    item['width'] <= s['width'] and 
                    (s['currentHeight'] + item['height']) <= vehicle['H']):
                    
                    item['z'] = s['currentHeight']
                    s['items'].append(item)
                    s['currentHeight'] += item['height']
                    current_vehicle_weight += item['weight']
                    placed_on_stack = True
                    break
        
        # Jeśli nie dodano do stosu, kładziemy na podłogę (nowy stos)
        if not placed_on_stack:
            # Sprawdzenie czy mieści się w rzędzie (szerokość W)
            if current_y + item['length'] > vehicle['W']:
                current_y = 0
                current_x += max_width_in_row
                max_width_in_row = 0
            
            # Sprawdzenie czy mieści się na długość (L)
            if (current_x + item['width'] <= vehicle['L'] and 
                current_y + item['length'] <= vehicle['W']):
                
                item['z'] = 0
                new_stack = {
                    'x': current_x,
                    'y': current_y,
                    'width': item['width'],
                    'length': item['length'],
                    'currentHeight': item['height'],
                    'canStackBase': item.get('canStack', True),
                    'items': [item]
                }
                placed_stacks.append(new_stack)
                
                current_y += item['length']
                max_width_in_row = max(max_width_in_row, item['width'])
                current_vehicle_weight += item['weight']

    return placed_stacks, current_vehicle_weight

# --- WIZUALIZACJA 3D ---
def draw_3d(placed_stacks, vehicle):
    fig = go.Figure()
    
    for s in placed_stacks:
        for item in s['items']:
            x0, y0, z0 = s['x'], s['y'], item['z']
            dx, dy, dz = s['width'], s['length'], item['height']
            
            fig.add_trace(go.Mesh3d(
                x=[x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0],
                y=[y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy],
                z=[z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz],
                i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
                j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
                k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
                opacity=0.8,
                color="#4682B4" if item.get('canStack') else "#A52A2A",
                name=item['name']
            ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[0, vehicle['L']], title="Długość (L)"),
            yaxis=dict(range=[0, vehicle['W']], title="Szerokość (W)"),
            zaxis=dict(range=[0, vehicle['H']], title="Wysokość (H)"),
            aspectmode='manual',
            aspectratio=dict(x=vehicle['L']/vehicle['W'], y=1, z=vehicle['H']/vehicle['W'])
        ),
        margin=dict(l=0, r=0, b=0, t=30)
    )
    return fig

# --- INTERFEJS STREAMLIT ---
st.set_page_config(page_title="SQM Loader", layout="wide")
st.title("📦 SQM Planer Załadunku")

if 'cargo' not in st.session_state:
    st.session_state.cargo = []

products = load_products()

with st.sidebar:
    st.header("1. Wybierz Pojazd")
    v_key = st.selectbox("Typ auta:", list(VEHICLES.keys()))
    veh = VEHICLES[v_key]
    st.info(f"Limit: {veh['max_weight']} kg | {veh['L']}x{veh['W']}x{veh['H']} cm")
    
    st.header("2. Dodaj ładunek")
    p_name = st.selectbox("Produkt:", [p['name'] for p in products])
    qty = st.number_input("Ilość:", min_value=1, value=1)
    if st.button("Dodaj do listy"):
        p_data = next(p for p in products if p['name'] == p_name)
        for _ in range(qty):
            st.session_state.cargo.append(p_data.copy())
            
    if st.button("Wyczyść listę"):
        st.session_state.cargo = []
        st.rerun()

# Obliczenia i wyniki
if st.session_state.cargo:
    stacks, total_w = calculate_load_sqm(st.session_state.cargo, veh)
    
    col_chart, col_res = st.columns([2, 1])
    
    with col_chart:
        st.plotly_chart(draw_3d(stacks, veh), use_container_width=True)
        
    with col_res:
        st.subheader("Podsumowanie")
        st.metric("Waga całkowita", f"{total_w} kg", f"Limit: {veh['max_weight']} kg")
        
        # Obliczanie zajętości paletowej (identycznie jak w Twoim HTML)
        total_area_cm2 = sum(s['width'] * s['length'] for s in stacks)
        pallet_equiv = total_area_cm2 / (120 * 80)
        st.metric("Miejsca paletowe", f"{pallet_equiv:.2f}", f"Limit: {veh['max_pallets']}")
        
        st.write("### Szczegóły stosów:")
        for idx, s in enumerate(stacks):
            with st.expander(f"Stos #{idx+1} ({s['width']}x{s['length']})"):
                for item in s['items']:
                    st.text(f"- {item['name']} (H: {item['height']} cm)")
else:
    st.info("Dodaj produkty z lewego panelu, aby zobaczyć optymalizację.")
