import streamlit as st
import json
import plotly.graph_objects as go
import math
import pandas as pd

# --- 1. ZABEZPIECZENIA ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.set_page_config(page_title="Logistics Dept", layout="centered")
        st.title("🔐 Logistics Department")
        st.subheader("Planer Transportu")
        
        try:
            # Hasło pobierane ze Streamlit Secrets
            master_password = str(st.secrets["password"])
        except Exception:
            st.error("🔒 Brak konfiguracji hasła głównego w Streamlit Secrets.")
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

# --- 2. KONFIGURACJA POJAZDÓW ---
VEHICLES = {
    "BUS": {"maxWeight": 1100, "L": 450, "W": 150, "H": 245},
    "6m": {"maxWeight": 3500, "L": 600, "W": 245, "H": 245},
    "7m": {"maxWeight": 3500, "L": 700, "W": 245, "H": 245},
    "FTL": {"maxWeight": 24000, "L": 1360, "W": 245, "H": 265}
}

COLOR_PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]

def load_products():
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            return sorted(json.load(f), key=lambda x: x['name'])
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
        # Logika "mieszania": szuka stosu o identycznych wymiarach podstawy
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
        
        if not added:
            if current_y + case['length'] > vehicle['W']:
                current_y, current_x = 0, current_x + max_w_row
                max_w_row = 0
            
            if current_x + case['width'] <= vehicle['L']:
                item_copy = case.copy()
                item_copy['z_pos'] = 0
                placed_stacks.append({
                    'x': current_x, 'y': current_y, 'width': case['width'], 'length': case['length'],
                    'currentH': case['height'], 'canStackBase': case.get('canStack', True),
                    'items': [item_copy]
                })
                current_y += case['length']
                max_w_row = max(max_w_row, case['width'])
                current_weight += case['weight']
            else:
                not_placed.append(case)
    return placed_stacks, current_weight, not_placed

# --- 4. RYSOWANIE 3D ---
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
                opacity=0.9, color=color_map.get(item['name'], "#808080"), name=item['name'], showlegend=False
            ))
    fig.update_layout(scene=dict(
        xaxis=dict(range=[0, vehicle['L']], title="Dł (cm)"),
        yaxis=dict(range=[0, vehicle['W']], title="Szer (cm)"),
        zaxis=dict(range=[0, vehicle['H']], title="Wys (cm)"),
        aspectmode='manual', aspectratio=dict(x=vehicle['L']/vehicle['W'], y=1, z=vehicle['H']/vehicle['W'])
    ), margin=dict(l=0, r=0, b=0, t=0))
    return fig

# --- 5. INTERFEJS ---
if check_password():
    if 'setup' not in st.session_state:
        st.set_page_config(page_title="Logistics Dept", layout="wide")
        st.session_state.setup = True

    st.title("🚛 Logistics Department: Planer Transportu")
    if 'cargo' not in st.session_state: 
        st.session_state.cargo = []
    
    prods = load_products()
    if 'color_map' not in st.session_state:
        st.session_state.color_map = {p['name']: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, p in enumerate(prods)}

    with st.sidebar:
        st.header("1. Pojazd")
        v_name = st.selectbox("Wybierz auto:", list(VEHICLES.keys()))
        veh = VEHICLES[v_name]
        
        st.divider()
        st.header("2. Dodaj Sprzęt")
        selected_p = st.selectbox("Produkt:", [p['name'] for p in prods], index=None, placeholder="Szukaj produktu...")
        qty = st.number_input("Sztuk:", min_value=1, value=1)
        
        if st.button("Dodaj do planu", use_container_width=True) and selected_p:
            p_data = next(p for p in prods if p['name'] == selected_p)
            ipc = p_data.get('itemsPerCase', 1)
            num_cases = math.ceil(qty / ipc)
            for i in range(num_cases):
                c = p_data.copy()
                # Obliczanie faktycznej ilości sztuk w ostatniej skrzyni
                if i == num_cases - 1 and qty % ipc != 0:
                    c['actual_items'] = qty % ipc
                else:
                    c['actual_items'] = ipc
                st.session_state.cargo.append(c)
            st.rerun()

        st.divider()
        st.header("3. Lista Załadunkowa")
        if st.session_state.cargo:
            # Wyświetlanie listy z opcją usuwania
            for idx, item in enumerate(st.session_state.cargo):
                col_name, col_del = st.columns([4, 1])
                col_name.write(f"{idx+1}. {item['name']}")
                if col_del.button("❌", key=f"del_{idx}"):
                    st.session_state.cargo.pop(idx)
                    st.rerun()
            
            if st.button("Wyczyść wszystko", use_container_width=True, type="secondary"):
                st.session_state.cargo = []
                st.rerun()
        else:
            st.info("Lista jest pusta.")

    # --- WIZUALIZACJA I STATYSTYKI ---
    if st.session_state.cargo:
        # Sortowanie dla optymalnego pakowania (od największej podstawy)
        rem = sorted([dict(c) for c in st.session_state.cargo], key=lambda x: x['width']*x['length'], reverse=True)
        fleet = []
        while rem:
            s, w, n = pack_one_vehicle(rem, veh)
            if not s: break
            fleet.append({"stacks": s, "weight": w})
            rem = n

        for i, res in enumerate(fleet):
            with st.expander(f"🚚 POJAZD #{i+1}", expanded=True):
                c1, c2 = st.columns([3, 2])
                
                # Przygotowanie danych do tabeli
                all_items_in_veh = [item for s in res['stacks'] for item in s['items']]
                df = pd.DataFrame(all_items_in_veh)
                
                floor_cm2 = sum(s['width']*s['length'] for s in res['stacks'])
                vol_cm3 = sum(item['width']*item['length']*item['height'] for item in all_items_in_veh)
                veh_floor_cm2 = veh['L'] * veh['W']
                veh_vol_cm3 = veh['L'] * veh['W'] * veh['H']

                with c1:
                    st.plotly_chart(draw_3d(res['stacks'], veh, st.session_state.color_map), use_container_width=True, key=f"v_{i}")
                
                with c2:
                    st.subheader("📋 Specyfikacja")
                    summ = df.groupby('name').agg({
                        'actual_items': 'sum', 
                        'name': 'count', 
                        'weight': 'sum'
                    }).rename(columns={
                        'actual_items': 'Sztuk sprzętu', 
                        'name': 'Liczba skrzyń', 
                        'weight': 'Waga (kg)'
                    })
                    # Użycie dataframe zamiast table, aby uniknąć ucinania listy
                    st.dataframe(summ, use_container_width=True)
                    
                    st.subheader("📈 Wykorzystanie")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Miejsca EP", f"{floor_cm2/9600:.2f}")
                    m2.metric("Powierzchnia", f"{floor_cm2/10000:.2f} m²", f"{int((floor_cm2/veh_floor_cm2)*100)}%")
                    m3.metric("Objętość", f"{vol_cm3/1000000:.2f} m³", f"{int((vol_cm3/veh_vol_cm3)*100)}%")
                    
                    st.write(f"**Waga ładunku:** {res['weight']} / {veh['maxWeight']} kg")
                    st.progress(min(res['weight'] / veh['maxWeight'], 1.0))
    else:
        st.info("Dodaj produkty z panelu po lewej stronie, aby rozpocząć planowanie.")
