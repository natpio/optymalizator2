import streamlit as st
import json
import plotly.graph_objects as go

# --- DANE POJAZDÓW 1:1 Z TWOJEGO PLIKU HTML ---
VEHICLES = {
    "BUS": {"maxPallets": 8, "maxWeight": 1100, "L": 450, "W": 150, "H": 245},
    "6m": {"maxPallets": 14, "maxWeight": 3500, "L": 600, "W": 245, "H": 245},
    "7m": {"maxPallets": 16, "maxWeight": 3500, "L": 700, "W": 245, "H": 245},
    "FTL": {"maxPallets": 31, "maxWeight": 12000, "L": 1360, "W": 245, "H": 265}
}

def load_products():
    with open('products.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# --- LOGIKA PAKOWANIA JEDNEGO AUTA ---
def pack_one_vehicle(remaining_items, vehicle):
    placed_stacks = []
    not_placed = []
    current_weight = 0
    current_x = 0
    current_y = 0
    max_width_in_row = 0

    for item in remaining_items:
        # Sprawdzenie wagi
        if current_weight + item['weight'] > vehicle['maxWeight']:
            not_placed.append(item)
            continue

        added_to_stack = False
        if item.get('canStack', True):
            for s in placed_stacks:
                if (s['canStackBase'] and item['width'] == s['width'] and 
                    item['length'] == s['length'] and (s['currentHeight'] + item['height']) <= vehicle['H']):
                    
                    item_copy = item.copy()
                    item_copy['z_pos'] = s['currentHeight']
                    s['items'].append(item_copy)
                    s['currentHeight'] += item['height']
                    current_weight += item['weight']
                    added_to_stack = True
                    break
        
        if not added_to_stack:
            # Logika "półek" (Shelf Packing)
            if current_y + item['length'] > vehicle['W']:
                current_y = 0
                current_x += max_width_in_row
                max_width_in_row = 0
            
            if current_x + item['width'] <= vehicle['L']:
                item_copy = item.copy()
                item_copy['z_pos'] = 0
                new_stack = {
                    'x': current_x, 'y': current_y,
                    'width': item['width'], 'length': item['length'],
                    'currentHeight': item['height'],
                    'canStackBase': item.get('canStack', True),
                    'items': [item_copy]
                }
                placed_stacks.append(new_stack)
                current_y += item['length']
                max_width_in_row = max(max_width_in_row, item['width'])
                current_weight += item['weight']
            else:
                not_placed.append(item)

    return placed_stacks, current_weight, not_placed

# --- WIZUALIZACJA 3D ---
def draw_3d(placed_stacks, vehicle, title):
    fig = go.Figure()
    for s in placed_stacks:
        for item in s['items']:
            x0, y0, z0 = s['x'], s['y'], item['z_pos']
            dx, dy, dz = s['width'], s['length'], item['height']
            fig.add_trace(go.Mesh3d(
                x=[x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0],
                y=[y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy],
                z=[z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz],
                i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
                opacity=0.8, color="#4682B4" if item.get('canStack') else "#A52A2A", name=item['name']
            ))
    fig.update_layout(title=title, scene=dict(
        aspectmode='manual', aspectratio=dict(x=vehicle['L']/vehicle['W'], y=1, z=vehicle['H']/vehicle['W'])
    ))
    return fig

# --- INTERFEJS ---
st.set_page_config(page_title="SQM Fleet Planner", layout="wide")
st.title("🚛 SQM - Planowanie floty (Wiele pojazdów)")

if 'cargo' not in st.session_state: st.session_state.cargo = []
products = load_products()

with st.sidebar:
    st.header("Konfiguracja")
    v_type = st.selectbox("Typ preferowanego auta:", list(VEHICLES.keys()))
    veh = VEHICLES[v_type]
    
    st.divider()
    p_name = st.selectbox("Produkt:", [p['name'] for p in products])
    qty = st.number_input("Sztuk:", min_value=1, value=1)
    if st.button("Dodaj do listy"):
        p_data = next(p for p in products if p['name'] == p_name)
        for _ in range(qty): st.session_state.cargo.append(p_data.copy())
    if st.button("Wyczyść wszystko"):
        st.session_state.cargo = []
        st.rerun()

if st.session_state.cargo:
    # GŁÓWNA PĘTLA FLOTY
    remaining = sorted([dict(i) for i in st.session_state.cargo], key=lambda x: x['width'] * x['length'], reverse=True)
    fleet_results = []
    
    while len(remaining) > 0:
        stacks, weight, not_packed = pack_one_vehicle(remaining, veh)
        if not stacks: # Zabezpieczenie przed nieskończoną pętlą (jeśli element jest większy niż auto)
            fleet_results.append({"error": remaining[0]})
            break
        fleet_results.append({"stacks": stacks, "weight": weight})
        remaining = not_packed

    st.success(f"Potrzebujesz **{len(fleet_results)}** pojazdów typu {v_type}")

    # Wyświetlanie każdego auta
    for i, res in enumerate(fleet_results):
        if "error" in res:
            st.error(f"Element '{res['error']['name']}' jest zbyt duży dla wybranego auta!")
            break
            
        with st.expander(f"Pojazd #{i+1} - Szczegóły załadunku", expanded=(i==0)):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.plotly_chart(draw_3d(res['stacks'], veh, f"Auto #{i+1}"), use_container_width=True)
            with c2:
                st.write(f"**Waga:** {res['weight']} / {veh['maxWeight']} kg")
                area_cm2 = sum(s['width'] * s['length'] for s in res['stacks'])
                st.write(f"**Zajętość:** {area_cm2/(120*80):.2f} palet")
                st.write("**Lista stosów:**")
                for j, s in enumerate(res['stacks']):
                    st.write(f"Stos {j+1}: {len(s['items'])} szt.")
else:
    st.info("Dodaj sprzęt, aby wyliczyć potrzebną liczbę aut.")
