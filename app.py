import streamlit as st
import json
import plotly.graph_objects as go
import math
import pandas as pd
import hashlib

# --- KONFIGURACJA I ZABEZPIECZENIA ---
PASSWORD_HASH = "711116a4d0f9ccf33c545ec650b11676d18c1440" # Domyślne: "admin123" (SHA1)

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 Logowanie - SQM Logistyka")
        pwd = st.text_input("Podaj hasło dostępu:", type="password")
        if st.button("Zaloguj"):
            if hashlib.sha1(pwd.encode()).hexdigest() == PASSWORD_HASH:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Nieprawidłowe hasło.")
        return False
    return True

# --- KONFIGURACJA POJAZDÓW ---
VEHICLES = {
    "BUS": {"maxWeight": 1100, "L": 450, "W": 150, "H": 245},
    "6m": {"maxWeight": 3500, "L": 600, "W": 245, "H": 245},
    "7m": {"maxWeight": 3500, "L": 700, "W": 245, "H": 245},
    "FTL": {"maxWeight": 12000, "L": 1360, "W": 245, "H": 265}
}

# --- PALETA KOLORÓW DLA PRODUKTÓW ---
COLORS = [
    "#4682B4", "#A52A2A", "#2E8B57", "#DAA520", "#6A5ACD", 
    "#FF4500", "#20B2AA", "#800080", "#556B2F", "#D2691E"
]

def get_product_colors(products):
    return {p['name']: COLORS[i % len(COLORS)] for i, p in enumerate(products)}

# --- LOGIKA PAKOWANIA (Bez zmian) ---
def load_products():
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception: return []

def pack_one_vehicle(remaining_cases, vehicle):
    placed_stacks = []
    not_placed = []
    current_weight = 0
    current_x, current_y = 0, 0
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

def draw_3d(placed_stacks, vehicle, title, color_map):
    fig = go.Figure()
    for s in placed_stacks:
        for item in s['items']:
            x0, y0, z0 = s['x'], s['y'], item['z_pos']
            dx, dy, dz = s['width'], s['length'], item['height']
            # Pobieranie koloru przypisanego do nazwy produktu
            color = color_map.get(item['name'], "#808080")
            
            fig.add_trace(go.Mesh3d(
                x=[x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0],
                y=[y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy],
                z=[z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz],
                i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
                opacity=0.8, color=color, name=item['name'], hoverinfo="name"
            ))
    fig.add_trace(go.Scatter3d(x=[0, vehicle['L']], y=[0, vehicle['W']], z=[0, vehicle['H']],
                               mode='markers', marker=dict(size=0.1, color='rgba(0,0,0,0)'), showlegend=False))
    fig.update_layout(title=title, scene=dict(
        xaxis=dict(range=[0, vehicle['L']], title="Dł (cm)"),
        yaxis=dict(range=[0, vehicle['W']], title="Szer (cm)"),
        zaxis=dict(range=[0, vehicle['H']], title="Wys (cm)"),
        aspectmode='manual', aspectratio=dict(x=vehicle['L']/vehicle['W'], y=1, z=vehicle['H']/vehicle['W'])
    ), margin=dict(l=0, r=0, b=0, t=40))
    return fig

# --- GŁÓWNA APLIKACJA ---
if check_password():
    st.set_page_config(page_title="SQM Logistyka", layout="wide")
    st.title("🚛 SQM Multimedia Solutions - Planer Transportu")

    if 'cargo_cases' not in st.session_state: st.session_state.cargo_cases = []
    products = load_products()
    color_map = get_product_colors(products)

    with st.sidebar:
        st.header("1. Parametry Auta")
        v_type = st.selectbox("Wybierz auto:", list(VEHICLES.keys()))
        veh = VEHICLES[v_type]
        
        st.divider()
        st.header("2. Dodaj Sprzęt")
        if products:
            p_name = st.selectbox("Produkt:", [p['name'] for p in products])
            qty = st.number_input("Ilość sztuk produktu:", min_value=1, value=1)
            
            if st.button("Dodaj do listy"):
                p_data = next(p for p in products if p['name'] == p_name)
                ipc = p_data.get('itemsPerCase', 1)
                needed_cases = math.ceil(qty / ipc)
                for i in range(needed_cases):
                    case = p_data.copy()
                    case['actual_items'] = qty % ipc if (i == needed_cases - 1 and qty % ipc != 0) else ipc
                    st.session_state.cargo_cases.append(case)
                st.success(f"Dodano {qty} szt.")

        if st.button("Wyczyść wszystko"):
            st.session_state.cargo_cases = []
            st.rerun()

    if st.session_state.cargo_cases:
        remaining = sorted([dict(c) for c in st.session_state.cargo_cases], key=lambda x: x['width']*x['length'], reverse=True)
        fleet = []
        
        while len(remaining) > 0:
            stacks, weight, not_packed = pack_one_vehicle(remaining, veh)
            if not stacks: break
            fleet.append({"stacks": stacks, "weight": weight})
            remaining = not_packed

        for i, res in enumerate(fleet):
            with st.expander(f"🚚 POJAZD #{i+1}", expanded=True):
                col1, col2 = st.columns([3, 2])
                
                total_floor_area_cm2 = 0
                total_volume_cm3 = 0
                all_items = []
                
                for s in res['stacks']:
                    total_floor_area_cm2 += (s['width'] * s['length'])
                    for item in s['items']:
                        all_items.append(item)
                        total_volume_cm3 += (item['width'] * item['length'] * item['height'])

                df = pd.DataFrame(all_items)
                
                with col1:
                    st.plotly_chart(draw_3d(res['stacks'], veh, f"Wizualizacja #{i+1}", color_map), use_container_width=True)
                
                with col2:
                    st.subheader("📋 Lista załadunkowa")
                    summary = df.groupby('name').agg({'actual_items': 'sum', 'name': 'count', 'weight': 'sum'}).rename(
                        columns={'actual_items': 'Szt. produktu', 'name': 'Liczba skrzyń', 'weight': 'Waga (kg)'})
                    st.table(summary)
                    
                    total_ep = total_floor_area_cm2 / 9600
                    total_m2 = total_floor_area_cm2 / 10000
                    total_m3 = total_volume_cm3 / 1000000
                    veh_m2 = (veh['L'] * veh['W']) / 10000
                    veh_m3 = (veh['L'] * veh['W'] * veh['H']) / 1000000
                    
                    st.subheader("📈 Statystyki")
                    m_col1, m_col2, m_col3 = st.columns(3)
                    m_col1.metric("Miejsca EP", f"{total_ep:.2f}")
                    m_col2.metric("Zajęte m²", f"{total_m2:.2f}", f"{int((total_m2/veh_m2)*100)}%")
                    m_col3.metric("Objętość m³", f"{total_m3:.2f}", f"{int((total_m3/veh_m3)*100)}%")
                    
                    st.progress(min(res['weight'] / veh['maxWeight'], 1.0))
                    st.write(f"**Waga:** {res['weight']} / {veh['maxWeight']} kg")
    else:
        st.info("Dodaj sprzęt w panelu bocznym.")

# Zapamiętam, że obecna wersja aplikacji jest poprawna. 
# Zawsze możesz poprosić mnie o zarządzanie Twoimi informacjami [w ustawieniach](https://gemini.google.com/saved-info).
