import streamlit as st
import json
import plotly.graph_objects as go
import math
import pandas as pd

# --- 1. ZABEZPIECZENIA (HASŁO Z SECRETS) ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.set_page_config(page_title="Logistics Dept", layout="centered")
        st.title("🔐 Logistics Department")
        st.subheader("Planer Transportu")
        
        try:
            # Pobranie hasła ze Streamlit Cloud Secrets
            master_password = str(st.secrets["password"])
        except Exception:
            st.error("🔒 Błąd konfiguracji: Nie znaleziono klucza 'password' w Streamlit Secrets.")
            return False

        pwd = st.text_input("Podaj hasło dostępu:", type="password")
        if st.button("Zaloguj"):
            if pwd == master_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Nieprawidłowe hasło.")
        return False
    return True

# --- 2. KONFIGURACJA I DANE ---
VEHICLES = {
    "BUS": {"maxWeight": 1100, "L": 450, "W": 150, "H": 245},
    "6m": {"maxWeight": 3500, "L": 600, "W": 245, "H": 245},
    "7m": {"maxWeight": 3500, "L": 700, "W": 245, "H": 245},
    "FTL": {"maxWeight": 12000, "L": 1360, "W": 245, "H": 265}
}

COLOR_PALETTE = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", 
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
]

def load_products():
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return sorted(data, key=lambda x: x['name'])
    except:
        return []

# --- 3. LOGIKA PAKOWANIA ---
def pack_one_vehicle(remaining_cases, vehicle):
    placed_stacks = []
    not_placed = []
    current_weight, current_x, current_y, max_w_row = 0, 0, 0, 0

    for case in remaining_cases:
        if current_weight + case['weight'] > vehicle['maxWeight']:
            not_placed.append(case)
            continue

        added = False
        # Próba dołożenia na istniejący stos (sztaplowanie)
        if case.get('canStack', True):
            for s in placed_stacks:
                if (s['canStackBase'] and case['width'] == s['width'] and 
                    case['length'] == s['length'] and (s['currentH'] + case['height']) <= vehicle['H']):
                    item_copy = case.copy()
                    item_copy['z_pos'] = s['currentH']
                    s['items'].append(item_copy)
                    s['currentH'] += case['height']
                    current_weight += case['weight']
                    added = True
                    break
        
        # Jeśli nie dodano do stosu, postaw nową skrzynię na podłodze
        if not added:
            if current_y + case['length'] > vehicle['W']:
                current_y, current_x = 0, current_x + max_w_row
                max_w_row = 0
            
            if current_x + case['width'] <= vehicle['L']:
                item_copy = case.copy()
                item_copy['z_pos'] = 0
                placed_stacks.append({
                    'x': current_x, 'y': current_y, 
                    'width': case['width'], 'length': case['length'],
                    'currentH': case['height'], 
                    'canStackBase': case.get('canStack', True),
                    'items': [item_copy]
                })
                current_y += case['length']
                max_w_row = max(max_w_row, case['width'])
                current_weight += case['weight']
            else:
                not_placed.append(case)
    return placed_stacks, current_weight, not_placed

# --- 4. WIZUALIZACJA 3D ---
def draw_3d(placed_stacks, vehicle, color_map):
    fig = go.Figure()

    for s in placed_stacks:
        for item in s['items']:
            x0, y0, z0 = s['x'], s['y'], item['z_pos']
            dx, dy, dz = s['width'], s['length'], item['height']
            
            fig.add_trace(go.Mesh3d(
                x=[x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0],
                y=[y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy],
                z=[z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz],
                i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
                opacity=0.9, color=color_map.get(item['name'], "#808080"), 
                name=item['name'], hoverinfo="name", showlegend=False
            ))
            
    fig.update_layout(scene=dict(
        xaxis=dict(range=[0, vehicle['L']], title="Dł (cm)"),
        yaxis=dict(range=[0, vehicle['W']], title="Szer (cm)"),
        zaxis=dict(range=[0, vehicle['H']], title="Wys (cm)"),
        aspectmode='manual', aspectratio=dict(x=vehicle['L']/vehicle['W'], y=1, z=vehicle['H']/vehicle['W'])
    ), margin=dict(l=0, r=0, b=0, t=0))
    return fig

# --- 5. INTERFEJS GŁÓWNY ---
if check_password():
    if 'setup_done' not in st.session_state:
        st.set_page_config(page_title="Logistics Department", layout="wide")
        st.session_state.setup_done = True

    st.title("🚛 Logistics Department: Planer Transportu")
    
    if 'cargo' not in st.session_state: st.session_state.cargo = []
    
    products_list = load_products()
    
    # Inicjalizacja stałych kolorów dla produktów w sesji
    if 'color_map' not in st.session_state:
        st.session_state.color_map = {p['name']: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, p in enumerate(products_list)}

    with st.sidebar:
        st.header("1. Parametry Auta")
        v_name = st.selectbox("Typ pojazdu:", list(VEHICLES.keys()))
        veh = VEHICLES[v_name]
        st.divider()
        
        st.header("2. Dodaj Sprzęt")
        # Wyszukiwarka produktów
        selected_p = st.selectbox(
            "Wyszukaj i wybierz produkt:", 
            options=[p['name'] for p in products_list],
            index=None,
            placeholder="Wpisz nazwę sprzętu..."
        )
        qty = st.number_input("Liczba sztuk:", min_value=1, value=1)
        
        if st.button("Dodaj do planu", use_container_width=True) and selected_p:
            p_data = next(p for p in products_list if p['name'] == selected_p)
            ipc = p_data.get('itemsPerCase', 1)
            num_cases = math.ceil(qty / ipc)
            for i in range(num_cases):
                case = p_data.copy()
                case['actual_items'] = qty % ipc if (i == num_cases - 1 and qty % ipc != 0) else ipc
                st.session_state.cargo.append(case)
            st.success(f"Dodano: {selected_p}")
        
        if st.button("Wyczyść listę załadunkową", use_container_width=True):
            st.session_state.cargo = []
            st.rerun()

    # Wyświetlanie wyników
    if st.session_state.cargo:
        # Sortowanie od największych (według powierzchni podstawy)
        remaining = sorted([dict(c) for c in st.session_state.cargo], key=lambda x: x['width']*x['length'], reverse=True)
        fleet = []
        
        while remaining:
            stacks, weight, not_packed = pack_one_vehicle(remaining, veh)
            if not stacks: break
            fleet.append({"stacks": stacks, "weight": weight})
            remaining = not_packed

        for i, res in enumerate(fleet):
            with st.expander(f"🚚 POJAZD #{i+1} - Raport", expanded=True):
                col1, col2 = st.columns([3, 2])
                with col1:
                    # Unikalny klucz wykresu zapobiega błędom DuplicateElementId
                    st.plotly_chart(
                        draw_3d(res['stacks'], veh, st.session_state.color_map), 
                        use_container_width=True, 
                        key=f"p_{i}_{len(st.session_state.cargo)}"
                    )
                with col2:
                    st.subheader("📋 Zawartość")
                    all_items = [item for s in res['stacks'] for item in s['items']]
                    df = pd.DataFrame(all_items)
                    summary = df.groupby('name').agg({'actual_items':'sum', 'weight':'sum'}).rename(
                        columns={'actual_items':'Sztuk', 'weight':'Waga (kg)'})
                    st.table(summary)
                    
                    # Obliczenia powierzchni (tylko podstawy stosów)
                    floor_area = sum(s['width'] * s['length'] for s in res['stacks'])
                    total_ep = floor_area / 9600
                    
                    st.subheader("📈 Wykorzystanie")
                    m1, m2 = st.columns(2)
                    m1.metric("Miejsca EP", f"{total_ep:.2f}")
                    m2.metric("Waga", f"{res['weight']} kg", f"{veh['maxWeight']} kg max")
                    st.progress(min(res['weight'] / veh['maxWeight'], 1.0))
    else:
        st.info("System gotowy. Zacznij od dodania sprzętu w panelu bocznym.")
