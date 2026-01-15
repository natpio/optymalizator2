import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
import numpy as np

# --- KONFIGURACJA POJAZDÓW (Zgodna z Twoją logiką) ---
VEHICLES = {
    "BUS": {"L": 450, "W": 170, "H": 200, "max_weight": 1100},
    "Solówka 6m": {"L": 600, "W": 245, "H": 250, "max_weight": 3500},
    "Solówka 7m": {"L": 700, "W": 245, "H": 250, "max_weight": 3500},
    "FTL (TIR)": {"L": 1360, "W": 245, "H": 270, "max_weight": 24000}
}

# --- ŁADOWANIE DANYCH ---
def load_products():
    with open('products.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# --- FUNKCJA RYSOWANIA 3D ---
def draw_3d_loading(placed_items, vehicle_dims, title):
    fig = go.Figure()

    # Rysowanie obrysu naczepy (półprzezroczysty prostopadłościan)
    l, w, h = vehicle_dims['L'], vehicle_dims['W'], vehicle_dims['H']
    
    # Każdy załadowany element jako bryła
    for item in placed_items:
        # Współrzędne x, y, z (z to wysokość od podłogi)
        x0, y0, z0 = item['x'], item['y'], item['z']
        dx, dy, dz = item['width'], item['length'], item['height']

        fig.add_trace(go.Mesh3d(
            x=[x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0],
            y=[y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy],
            z=[z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz],
            i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
            j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
            k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
            opacity=0.8,
            color='#8B4513' if not item.get('canStack') else '#4682B4',
            name=item['name'],
            showlegend=True
        ))

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis=dict(range=[0, l], title="Długość (cm)"),
            yaxis=dict(range=[0, w], title="Szerokość (cm)"),
            zaxis=dict(range=[0, h], title="Wysokość (cm)"),
            aspectmode='manual',
            aspectratio=dict(x=l/w, y=1, z=h/w)
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )
    return fig

# --- LOGIKA APLIKACJI STREAMLIT ---
st.set_page_config(page_title="SQM Load Planner 3D", layout="wide")
st.title("📦 SQM Multimedia Solutions - Planer Załadunku 3D")

products = load_products()
product_names = [p['name'] for p in products]

# Sidebar - Wybór floty
st.sidebar.header("Ustawienia Transportu")
selected_vehicle_name = st.sidebar.selectbox("Wybierz pojazd:", list(VEHICLES.keys()))
vehicle = VEHICLES[selected_vehicle_name]

# Formularz dodawania produktów
st.subheader("Dodaj sprzęt do załadunku")
if 'cargo' not in st.session_state:
    st.session_state.cargo = []

col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    choice = st.selectbox("Produkt z bazy:", product_names)
with col2:
    qty = st.number_input("Ilość:", min_value=1, value=1)
with col3:
    if st.button("Dodaj do listy"):
        prod_data = next(item for item in products if item["name"] == choice)
        for _ in range(qty):
            st.session_state.cargo.append(prod_data.copy())

# Wyświetlanie listy i obliczenia
if st.session_state.cargo:
    df_cargo = pd.DataFrame(st.session_state.cargo)
    st.write(f"Suma elementów: {len(df_cargo)} | Całkowita waga: {df_cargo['weight'].sum()} kg")
    
    if st.button("Wyczyść listę"):
        st.session_state.cargo = []
        st.rerun()

    # --- UPROSZCZONY ALGORYTM PAKOWANIA (Shelf Packing) ---
    # Logika identyczna z Twoim HTML: Sortowanie -> Układanie rzędami
    sorted_cargo = sorted(st.session_state.cargo, key=lambda x: x['width'] * x['length'], reverse=True)
    
    placed_items = []
    current_x = 0
    current_y = 0
    max_y_in_row = 0
    total_weight = 0
    
    for item in sorted_cargo:
        if total_weight + item['weight'] > vehicle['max_weight']:
            continue # Przekroczenie DMC
            
        # Sprawdzenie czy mieści się w obecnym rzędzie (szerokość)
        if current_y + item['length'] > vehicle['W']:
            current_y = 0
            current_x += max_y_in_row
            max_y_in_row = 0
            
        # Sprawdzenie czy mieści się na długość naczepy
        if current_x + item['width'] <= vehicle['L']:
            item['x'] = current_x
            item['y'] = current_y
            item['z'] = 0 # Na podłodze (tu można dodać logikę canStack)
            placed_items.append(item)
            
            current_y += item['length']
            max_y_in_row = max(max_y_in_row, item['width'])
            total_weight += item['weight']

    # Wizualizacja 3D
    st.plotly_chart(draw_3d_loading(placed_items, vehicle, f"Załadunek: {selected_vehicle_name}"), use_container_width=True)
    
    # Raport zajętości
    used_area = sum([(i['width']*i['length']) for i in placed_items]) / 10000
    total_area = (vehicle['L'] * vehicle['W']) / 10000
    st.info(f"Wykorzystana powierzchnia: {used_area:.2f} m² / {total_area:.2f} m² ({(used_area/total_area)*100:.1f}%)")
else:
    st.info("Dodaj produkty, aby zobaczyć wizualizację załadunku.")
