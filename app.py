import streamlit as st
import json
import plotly.graph_objects as go
import math
import pandas as pd

# --- KONFIGURACJA POJAZDÓW ---
VEHICLES = {
    "BUS": {"maxWeight": 1100, "L": 450, "W": 150, "H": 245},
    "6m": {"maxWeight": 3500, "L": 600, "W": 245, "H": 245},
    "7m": {"maxWeight": 3500, "L": 700, "W": 245, "H": 245},
    "FTL": {"maxWeight": 12000, "L": 1360, "W": 245, "H": 265}
}

def load_products():
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        st.error("Błąd: Nie znaleziono pliku products.json.")
        return []

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

def draw_3d(placed_stacks, vehicle, title):
    fig = go.Figure()
    for s in placed_stacks:
        for item in s['items']:
            x0, y0, z0 = s['x'], s['y'], item['z_pos']
            dx, dy, dz = s['width'], s['length'], item['height']
            color = "#4682B4" if item.get('canStack') else "#A52A2A"
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

# --- STREAMLIT ---
st.set_page_config(page_title="SQM Logistyka", layout="wide")
st.title("🚛 SQM Multimedia Solutions - Planer Transportu")

if 'cargo_cases' not in st.session_state: st.session_state.cargo_cases = []
products = load_products()

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
            
            # Rejestrujemy konkretną liczbę sztuk produktu przypadającą na te skrzynie
            for i in range(needed_cases):
                case = p_data.copy()
                # Ostatnia skrzynia może mieć mniej sztuk jeśli qty nie jest podzielne przez ipc
                if i == needed_cases - 1 and qty % ipc != 0:
                    case['actual_items'] = qty % ipc
                else:
                    case['actual_items'] = ipc
                st.session_state.cargo_cases.append(case)
            st.success(f"Dodano {qty} szt. ({needed_cases} skrzyń).")

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

    st.header(f"📊 Planowanie: {len(fleet)}x {v_type}")

    for i, res in enumerate(fleet):
        with st.expander(f"🚚 POJAZD #{i+1}", expanded=True):
            col1, col2 = st.columns([3, 2])
            
            items_in_car = [item for s in res['stacks'] for item in s['items']]
            df = pd.DataFrame(items_in_car)
            
            # --- OBLICZENIA LOGISTYCZNE DLA AUTA ---
            # Miejsca paletowe: (szer * dł) / (80 * 120)
            df['ep'] = (df['width'] * df['length']) / 9600 
            # Objętość m3: (szer * dł * wys) / 1 000 000
            df['m3'] = (df['width'] * df['length'] * df['height']) / 1000000
            # Powierzchnia m2: (szer * dł) / 10 000
            df['m2'] = (df['width'] * df['length']) / 10000

            with col1:
                st.plotly_chart(draw_3d(res['stacks'], veh, f"Wizualizacja #{i+1}"), use_container_width=True)
            
            with col2:
                st.subheader("📋 Lista załadunkowa")
                summary = df.groupby('name').agg({
                    'actual_items': 'sum',
                    'name': 'count',
                    'ep': 'sum',
                    'weight': 'sum'
                }).rename(columns={
                    'actual_items': 'Szt. produktu',
                    'name': 'Liczba skrzyń',
                    'ep': 'Miejsca EP',
                    'weight': 'Waga (kg)'
                })
                summary['Miejsca EP'] = summary['Miejsca EP'].round(2)
                st.table(summary)
                
                # --- STATYSTYKI WYKORZYSTANIA ---
                total_ep = df['ep'].sum()
                total_m2 = df['m2'].sum()
                total_m3 = df['m3'].sum()
                
                veh_m2 = (veh['L'] * veh['W']) / 10000
                veh_m3 = (veh['L'] * veh['W'] * veh['H']) / 1000000
                
                st.subheader("📈 Wykorzystanie przestrzeni")
                m_col1, m_col2, m_col3 = st.columns(3)
                m_col1.metric("Miejsca EP", f"{total_ep:.2f}")
                m_col2.metric("Powierzchnia", f"{total_m2:.2f} m²", f"{int((total_m2/veh_m2)*100)}%")
                m_col3.metric("Objętość", f"{total_m3:.2f} m³", f"{int((total_m3/veh_m3)*100)}%")
                
                # Pasek postępu dla wagi
                w_perc = min(res['weight'] / veh['maxWeight'], 1.0)
                st.write(f"**Waga:** {res['weight']} / {veh['maxWeight']} kg")
                st.progress(w_perc)
                
                st.caption(f"Wolne miejsce: {100 - int((total_m2/veh_m2)*100)}% powierzchni podłogi.")

else:
    st.info("Dodaj sprzęt, aby wygenerować listę i statystyki.")
