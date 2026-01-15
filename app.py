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

# --- 2. KONFIGURACJA POJAZDÓW (Poprawiona na realne wartości) ---
VEHICLES = {
    "BUS": {"maxWeight": 1100, "L": 450, "W": 170, "H": 245}, # Szerokość poprawiona z 150 na 170
    "6m": {"maxWeight": 3500, "L": 600, "W": 245, "H": 245},
    "7m": {"maxWeight": 3500, "L": 700, "W": 245, "H": 245},
    "FTL": {"maxWeight": 24000, "L": 1360, "W": 245, "H": 265} # Waga poprawiona z 12t na 24t
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
    
    # Przechowywanie danych jako DataFrame dla łatwiejszej edycji
    if 'cargo_df' not in st.session_state:
        st.session_state.cargo_df = pd.DataFrame(columns=['name', 'qty', 'width', 'length', 'height', 'weight', 'itemsPerCase', 'canStack'])
    
    prods = load_products()
    if 'color_map' not in st.session_state:
        st.session_state.color_map = {p['name']: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, p in enumerate(prods)}

    with st.sidebar:
        st.header("1. Wybór Auta")
        v_name = st.selectbox("Pojazd:", list(VEHICLES.keys()))
        veh = VEHICLES[v_name]
        
        st.divider()
        st.header("2. Dodaj do listy")
        selected_p = st.selectbox("Produkt:", [p['name'] for p in prods], index=None, placeholder="Wybierz sprzęt...")
        add_qty = st.number_input("Sztuk:", min_value=1, value=1)
        
        if st.button("➕ Dodaj do zamówienia", use_container_width=True) and selected_p:
            p_data = next(p for p in prods if p['name'] == selected_p)
            new_row = {
                'name': p_data['name'],
                'qty': add_qty,
                'width': p_data['width'],
                'length': p_data['length'],
                'height': p_data['height'],
                'weight': p_data['weight'],
                'itemsPerCase': p_data.get('itemsPerCase', 1),
                'canStack': p_data.get('canStack', True)
            }
            st.session_state.cargo_df = pd.concat([st.session_state.cargo_df, pd.DataFrame([new_row])], ignore_index=True)
            st.rerun()

        if st.button("🗑️ Wyczyść wszystko", use_container_width=True):
            st.session_state.cargo_df = pd.DataFrame(columns=['name', 'qty', 'width', 'length', 'height', 'weight', 'itemsPerCase', 'canStack'])
            st.rerun()

    # --- EDYCJA I WIZUALIZACJA ---
    if not st.session_state.cargo_df.empty:
        st.subheader("📝 Aktywne zamówienie (możesz edytować ilości bezpośrednio w tabeli)")
        # Edytowalna tabela
        edited_df = st.data_editor(
            st.session_state.cargo_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "qty": st.column_config.NumberColumn("Sztuk", min_value=1, step=1),
                "name": "Nazwa produktu",
                "width": "Szer (cm)", "length": "Dł (cm)", "height": "Wys (cm)", "weight": "Waga (kg/case)"
            },
            key="main_editor"
        )
        st.session_state.cargo_df = edited_df

        # Przetworzenie DataFrame na listę skrzyń do algorytmu
        cargo_to_pack = []
        for _, row in edited_df.iterrows():
            ipc = row['itemsPerCase']
            num_cases = math.ceil(row['qty'] / ipc)
            for i in range(num_cases):
                case_item = row.to_dict()
                if i == num_cases - 1 and row['qty'] % ipc != 0:
                    case_item['actual_items'] = row['qty'] % ipc
                else:
                    case_item['actual_items'] = ipc
                cargo_to_pack.append(case_item)

        # Algorytm pakowania
        rem = sorted(cargo_to_pack, key=lambda x: x['width']*x['length'], reverse=True)
        fleet = []
        while rem:
            s, w, n = pack_one_vehicle(rem, veh)
            if not s: break
            fleet.append({"stacks": s, "weight": w})
            rem = n

        # Wyświetlanie pojazdów
        for i, res in enumerate(fleet):
            with st.expander(f"🚚 POJAZD #{i+1} - {v_name}", expanded=True):
                c1, c2 = st.columns([3, 2])
                all_items = [item for s in res['stacks'] for item in s['items']]
                df_res = pd.DataFrame(all_items)

                with c1:
                    st.plotly_chart(draw_3d(res['stacks'], veh, st.session_state.color_map), use_container_width=True, key=f"plot_{i}")
                
                with c2:
                    st.subheader("📊 Wykorzystanie")
                    floor_cm2 = sum(s['width']*s['length'] for s in res['stacks'])
                    vol_cm3 = sum(item['width']*item['length']*item['height'] for item in all_items)
                    
                    m1, m2 = st.columns(2)
                    m1.metric("Powierzchnia", f"{floor_cm2/10000:.1f} m²", f"{int((floor_cm2/(veh['L']*veh['W']))*100)}%")
                    m2.metric("Waga", f"{res['weight']} kg", f"{int((res['weight']/veh['maxWeight'])*100)}%")
                    
                    st.progress(min(res['weight'] / veh['maxWeight'], 1.0))
                    
                    st.subheader("📋 Specyfikacja załadunku")
                    summ = df_res.groupby('name').agg({'actual_items':'sum', 'name':'count', 'weight':'sum'}).rename(
                        columns={'actual_items':'Sztuk sprzętu', 'name':'Liczba skrzyń', 'weight':'Waga (kg)'})
                    st.dataframe(summ, use_container_width=True)
    else:
        st.info("Wybierz produkty z panelu po lewej stronie, aby rozpocząć planowanie.")
