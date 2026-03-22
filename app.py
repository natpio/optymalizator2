import streamlit as st
import json
import plotly.graph_objects as go
import math
import pandas as pd

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Logistics Dept - Professional Planer", layout="wide")

# --- 2. ZABEZPIECZENIA ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔐 Logistics Department")
        try:
            master_password = str(st.secrets["password"])
        except:
            st.error("🔒 Brak konfiguracji hasła w Secrets.")
            return False
        pwd = st.text_input("Hasło dostępu:", type="password")
        if st.button("Zaloguj"):
            if pwd == master_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Nieprawidłowe hasło.")
        return False
    return True

# --- 3. KONFIGURACJA POJAZDÓW (TWOJE LIMITY) ---
VEHICLES = {
    "BUS": {"maxWeight": 1100, "L": 450, "W": 150, "H": 245},
    "6m": {"maxWeight": 3500, "L": 600, "W": 245, "H": 245},
    "7m": {"maxWeight": 7000, "L": 700, "W": 245, "H": 245},
    "FTL": {"maxWeight": 12000, "L": 1360, "W": 245, "H": 265}
}

COLOR_PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]

def load_products():
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            return sorted(json.load(f), key=lambda x: x.get('name', ''))
    except: return []

# --- 4. LOGIKA PAKOWANIA ---
def pack_one_vehicle(remaining_items, vehicle):
    placed_stacks = []
    not_placed = []
    current_weight = 0
    curr_x, curr_y, max_w_row = 0, 0, 0
    max_reached_l = 0

    sorted_items = sorted(remaining_items, key=lambda x: (x['weight'], x['width']*x['length']), reverse=True)

    for item in sorted_items:
        if current_weight + item['weight'] > vehicle['maxWeight']:
            not_placed.append(item)
            continue

        added = False
        if item.get('canStack', True):
            for s in placed_stacks:
                if (s['canStackBase'] and item['width'] == s['width'] and 
                    item['length'] == s['length'] and (s['currentH'] + item['height']) <= vehicle['H']):
                    it_copy = item.copy()
                    it_copy['z_pos'] = s['currentH']
                    s['items'].append(it_copy)
                    s['currentH'] += item['height']
                    current_weight += item['weight']
                    added = True
                    break
        
        if not added:
            if curr_y + item['length'] > vehicle['W']:
                curr_y = 0
                curr_x += max_w_row
                max_w_row = 0
            
            if curr_x + item['width'] <= vehicle['L']:
                it_copy = item.copy()
                it_copy['z_pos'] = 0
                placed_stacks.append({
                    'x': curr_x, 'y': curr_y, 'width': item['width'], 'length': item['length'],
                    'currentH': item['height'], 'canStackBase': item.get('canStack', True),
                    'items': [it_copy]
                })
                curr_y += item['length']
                max_w_row = max(max_w_row, item['width'])
                current_weight += item['weight']
                max_reached_l = max(max_reached_l, curr_x + item['width'])
                added = True
            else:
                not_placed.append(item)
                
    return placed_stacks, current_weight, not_placed, max_reached_l

# --- 5. RYSOWANIE 3D ---
def draw_3d(placed_stacks, vehicle, color_map):
    fig = go.Figure()
    for s in placed_stacks:
        for it in s['items']:
            x0, y0, z0 = s['x'], s['y'], it['z_pos']
            dx, dy, dz = it['width'], it['length'], it['height']
            fig.add_trace(go.Mesh3d(
                x=[x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0],
                y=[y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy],
                z=[z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz],
                i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
                opacity=0.8, color=color_map.get(it['name'], "#808080"), name=it['name']
            ))
    fig.update_layout(scene=dict(
        xaxis=dict(range=[0, vehicle['L']], title="Dł"),
        yaxis=dict(range=[0, vehicle['W']], title="Szer"),
        zaxis=dict(range=[0, vehicle['H']], title="Wys"),
        aspectmode='manual', aspectratio=dict(x=vehicle['L']/vehicle['W'], y=1, z=vehicle['H']/vehicle['W'])
    ), margin=dict(l=0, r=0, b=0, t=0))
    return fig

# --- 6. INTERFEJS GŁÓWNY ---
if check_password():
    if 'cargo' not in st.session_state: st.session_state.cargo = []
    prods = load_products()
    if 'color_map' not in st.session_state:
        st.session_state.color_map = {p['name']: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, p in enumerate(prods)}

    with st.sidebar:
        st.header("🚚 Flota")
        v_name = st.selectbox("Typ pojazdu:", list(VEHICLES.keys()))
        veh = VEHICLES[v_name]
        st.divider()
        st.header("📦 Dodaj Towar")
        sel_p = st.selectbox("Produkt:", [p['name'] for p in prods], index=None)
        qty = st.number_input("Ilość:", min_value=1, value=1)
        if st.button("Dodaj do planu", use_container_width=True) and sel_p:
            p_data = next(p for p in prods if p['name'] == sel_p)
            ipc = p_data.get('itemsPerCase', 1)
            for i in range(math.ceil(qty/ipc)):
                c = p_data.copy()
                c['actual_items'] = qty % ipc if (i == math.ceil(qty/ipc)-1 and qty % ipc != 0) else ipc
                st.session_state.cargo.append(c)
            st.rerun()
        if st.button("Wyczyść wszystko", use_container_width=True, type="secondary"):
            st.session_state.cargo = []
            st.rerun()

    if st.session_state.cargo:
        # --- MODUŁ EDYCJI LISTY ---
        st.header("📝 Lista i edycja")
        df_cargo = pd.DataFrame(st.session_state.cargo)
        summary = df_cargo.groupby('name').agg({'actual_items': 'sum'}).reset_index()
        
        edited_summary = st.data_editor(
            summary,
            column_config={
                "name": "Produkt",
                "actual_items": st.column_config.NumberColumn("Łączna liczba sztuk (wpisz 0 aby usunąć)", min_value=0)
            },
            disabled=["name"],
            hide_index=True,
            use_container_width=True,
            key="cargo_editor"
        )

        # Sprawdzenie czy użytkownik zmienił ilości
        if not edited_summary.equals(summary):
            new_cargo = []
            for _, row in edited_summary.iterrows():
                if row['actual_items'] > 0:
                    orig_p = next(p for p in prods if p['name'] == row['name'])
                    ipc = orig_p.get('itemsPerCase', 1)
                    num_c = math.ceil(row['actual_items'] / ipc)
                    for i in range(num_c):
                        new_c = orig_p.copy()
                        new_c['actual_items'] = row['actual_items'] % ipc if (i == num_c - 1 and row['actual_items'] % ipc != 0) else ipc
                        new_cargo.append(new_c)
            st.session_state.cargo = new_cargo
            st.rerun()

        # --- LOGIKA PODZIAŁU NA AUTA ---
        items_left = [dict(c) for c in st.session_state.cargo]
        fleet = []
        too_heavy = [i['name'] for i in items_left if i['weight'] > veh['maxWeight']]
        
        if too_heavy:
            st.error(f"❌ Towar {list(set(too_heavy))} jest cięższy niż DMC auta!")
        else:
            while items_left:
                stacks, weight, left, m_l = pack_one_vehicle(items_left, veh)
                if not stacks: break
                fleet.append({"stacks": stacks, "weight": weight, "ldm": m_l/100})
                items_left = left

            st.header(f"📊 Plan Załadunku ({len(fleet)} auta)")
            for idx, res in enumerate(fleet):
                with st.expander(f"🚚 Pojazd #{idx+1} | Waga: {res['weight']} / {veh['maxWeight']} kg", expanded=True):
                    c1, c2 = st.columns([3, 2])
                    floor_f = sum(s['width']*s['length'] for s in res['stacks'])
                    vol_f = sum(it['width']*it['length']*it['height'] for s in res['stacks'] for it in s['items'])
                    
                    with c1:
                        st.plotly_chart(draw_3d(res['stacks'], veh, st.session_state.color_map), use_container_width=True, key=f"v_{idx}")
                    with c2:
                        st.write("### 📏 Metryki")
                        m1, m2, m3 = st.columns(3)
                        m1.metric("LDM", f"{res['ldm']:.2f}")
                        m2.metric("Miejsca EP", f"{floor_f/9600:.1f}")
                        m3.metric("Waga", f"{res['weight']} kg")
                        
                        st.write(f"Powierzchnia: {int(floor_f/(veh['L']*veh['W'])*100)}%")
                        st.progress(min(floor_f/(veh['L']*veh['W']), 1.0))
                        st.write(f"Objętość: {int(vol_f/(veh['L']*veh['W']*veh['H'])*100)}%")
                        st.progress(min(vol_f/(veh['L']*veh['W']*veh['H']), 1.0))
                        st.write(f"DMC: {int(res['weight']/veh['maxWeight']*100)}%")
                        st.progress(min(res['weight']/veh['maxWeight'], 1.0))
                        
                        in_t = [it for s in res['stacks'] for it in s['items']]
                        st.table(pd.DataFrame(in_t).groupby('name').agg({'actual_items':'sum', 'weight':'sum'}).rename(columns={'actual_items':'Sztuk','weight':'Waga (kg)'}))
    else:
        st.info("Brak towarów na liście.")
