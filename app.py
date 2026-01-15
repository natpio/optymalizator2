import streamlit as st
import json
import plotly.graph_objects as go
import math
import pandas as pd

# --- DANE POJAZDÓW 1:1 Z TWOJEGO PLIKU HTML ---
VEHICLES = {
    "BUS": {"maxPallets": 8, "maxWeight": 1100, "L": 450, "W": 150, "H": 245},
    "6m": {"maxPallets": 14, "maxWeight": 3500, "L": 600, "W": 245, "H": 245},
    "7m": {"maxPallets": 16, "maxWeight": 3500, "L": 700, "W": 245, "H": 245},
    "FTL": {"maxPallets": 31, "maxWeight": 12000, "L": 1360, "W": 245, "H": 265}
}

def load_products():
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

# --- LOGIKA PAKOWANIA JEDNEGO POJAZDU (Shelf-Packing) ---
def pack_one_vehicle(remaining_cases, vehicle):
    placed_stacks = []
    not_placed = []
    current_weight = 0
    current_x = 0
    current_y = 0
    max_width_in_row = 0

    for case in remaining_cases:
        if current_weight + case['weight'] > vehicle['maxWeight']:
            not_placed.append(case)
            continue

        added_to_stack = False
        if case.get('canStack', True):
            for s in placed_stacks:
                if (s['canStackBase'] and case['width'] == s['width'] and 
                    case['length'] == s['length'] and (s['currentHeight'] + case['height']) <= vehicle['H']):
                    
                    case_copy = case.copy()
                    case_copy['z_pos'] = s['currentHeight']
                    s['items'].append(case_copy)
                    s['currentHeight'] += case['height']
                    current_weight += case['weight']
                    added_to_stack = True
                    break
        
        if not added_to_stack:
            if current_y + case['length'] > vehicle['W']:
                current_y = 0
                current_x += max_width_in_row
                max_width_in_row = 0
            
            if current_x + case['width'] <= vehicle['L']:
                case_copy = case.copy()
                case_copy['z_pos'] = 0
                new_stack = {
                    'x': current_x, 'y': current_y,
                    'width': case['width'], 'length': case['length'],
                    'currentHeight': case['height'],
                    'canStackBase': case.get('canStack', True),
                    'items': [case_copy]
                }
                placed_stacks.append(new_stack)
                current_y += case['length']
                max_width_in_row = max(max_width_in_row, case['width'])
                current_weight += case['weight']
            else:
                not_placed.append(case)

    return placed_stacks, current_weight, not_placed

# --- WIZUALIZACJA 3D (Z POPRAWIONĄ SKALĄ AUTA) ---
def draw_3d(placed_stacks, vehicle, title):
    fig = go.Figure()
    
    # Rysowanie skrzyń
    for s in placed_stacks:
        for item in s['items']:
            x0, y0, z0 = s['x'], s['y'], item['z_pos']
            dx, dy, dz = s['width'], s['length'], item['height']
            
            # Kolor: Błękitny dla stackowalnych, Brązowy dla ciężkich/nie-stackowalnych
            color = "#4682B4" if item.get('canStack') else "#A52A2A"
            
            fig.add_trace(go.Mesh3d(
                x=[x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0],
                y=[y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy],
                z=[z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz],
                i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
                opacity=0.8, color=color, name=item['name'],
                hovertemplate=f"<b>{item['name']}</b><br>Pozycja: {x0}x{y0}cm<br>Waga: {item['weight']}kg"
            ))

    # Obramowanie naczepy (kontur)
    fig.add_trace(go.Box(x=[0, vehicle['L']], y=[0, vehicle['W']], z=[0, vehicle['H']], opacity=0, showlegend=False))

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis=dict(range=[0, vehicle['L']], title="Długość"),
            yaxis=dict(range=[0, vehicle['W']], title="Szerokość"),
            zaxis=dict(range=[0, vehicle['H']], title="Wysokość"),
            aspectmode='manual',
            # Klucz do czytelności: aspectratio zachowuje proporcje typu pojazdu
            aspectratio=dict(x=vehicle['L']/vehicle['W'], y=1, z=vehicle['H']/vehicle['W'])
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )
    return fig

# --- INTERFEJS ---
st.set_page_config(page_title="SQM Logistyka", layout="wide")
st.title("🚛 SQM Multimedia - Planer Floty")

if 'cargo_cases' not in st.session_state: st.session_state.cargo_cases = []
products = load_products()

with st.sidebar:
    st.header("1. Wybierz Typ Pojazdu")
    v_type = st.selectbox("Domyślne auto:", list(VEHICLES.keys()))
    veh = VEHICLES[v_type]
    
    st.divider()
    st.header("2. Dodaj Sprzęt")
    p_name = st.selectbox("Produkt:", [p['name'] for p in products])
    total_items = st.number_input("Ilość sztuk:", min_value=1, value=1)
    
    if st.button("Dodaj do planu"):
        p_data = next(p for p in products if p['name'] == p_name)
        ipc = p_data.get('itemsPerCase', 1)
        needed_cases = math.ceil(total_items / ipc)
        
        for _ in range(needed_cases):
            case = p_data.copy()
            case['original_qty'] = total_items # zapamiętujemy ile sztuk dodano
            st.session_state.cargo_cases.append(case)
        st.success(f"Dodano {total_items} szt. = {needed_cases} skrzyń.")

    if st.button("Wyczyść wszystko"):
        st.session_state.cargo_cases = []
        st.rerun()

# PROCESOWANIE WYNIKÓW
if st.session_state.cargo_cases:
    remaining = sorted([dict(c) for c in st.session_state.cargo_cases], key=lambda x: x['width'] * x['length'], reverse=True)
    fleet = []
    
    while len(remaining) > 0:
        stacks, weight, not_packed = pack_one_vehicle(remaining, veh)
        if not stacks: break
        fleet.append({"stacks": stacks, "weight": weight})
        remaining = not_packed

    st.header(f"📊 Potrzebne pojazdy: {len(fleet)} x {v_type}")

    for i, res in enumerate(fleet):
        with st.expander(f"🚚 Pojazd #{i+1} - Kliknij by rozwinąć", expanded=(i==0)):
            col_chart, col_list = st.columns([1, 1])
            
            with col_chart:
                st.plotly_chart(draw_3d(res['stacks'], veh, f"Plan auta #{i+1}"), use_container_width=True)
                st.write(f"**Wykorzystanie wagi:** {res['weight']} / {veh['maxWeight']} kg")
            
            with col_list:
                st.subheader("📋 Lista załadunkowa (Sztuki skrzyń)")
                
                # Przygotowanie danych do czytelnej tabeli
                items_in_vehicle = []
                for s in res['stacks']:
                    for item in s['items']:
                        items_in_vehicle.append(item)
                
                if items_in_vehicle:
                    df = pd.DataFrame(items_in_vehicle)
                    # Grupowanie takich samych skrzyń
                    summary = df.groupby('name').agg({
                        'name': 'count',
                        'width': 'first',
                        'length': 'first',
                        'height': 'first',
                        'weight': 'sum'
                    }).rename(columns={'name': 'Liczba skrzyń', 'weight': 'Waga łączna (kg)'})
                    
                    st.table(summary)
                    
                    st.info("💡 Legenda wizualizacji:\n- **Niebieski:** Case'y stackowalne\n- **Brązowy:** Case'y ciężkie / bez stackowania")
else:
    st.info("Dodaj produkty, aby zobaczyć planowanie wielu aut i listę sprzętu.")
