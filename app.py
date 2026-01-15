import streamlit as st
import json
import plotly.graph_objects as go
import math

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
    except FileNotFoundError:
        st.error("Nie znaleziono pliku products.json!")
        return []

# --- LOGIKA PAKOWANIA JEDNEGO POJAZDU (Shelf-Packing z Twojego HTML) ---
def pack_one_vehicle(remaining_cases, vehicle):
    placed_stacks = []
    not_placed = []
    current_weight = 0
    current_x = 0
    current_y = 0
    max_width_in_row = 0

    for case in remaining_cases:
        # Sprawdzenie limitu wagi auta
        if current_weight + case['weight'] > vehicle['maxWeight']:
            not_placed.append(case)
            continue

        added_to_stack = False
        # Próba stackowania (na podstawie wymiarów podstawy i wysokości)
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
        
        # Jeśli nie dodano do stosu -> Nowe miejsce na podłodze
        if not added_to_stack:
            # Sprawdzenie czy mieści się w szerokości (logika półek)
            if current_y + case['length'] > vehicle['W']:
                current_y = 0
                current_x += max_width_in_row
                max_width_in_row = 0
            
            # Sprawdzenie czy mieści się w długości auta
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
        xaxis_title="Długość", yaxis_title="Szerokość", zaxis_title="Wysokość",
        aspectmode='manual', aspectratio=dict(x=vehicle['L']/vehicle['W'], y=1, z=vehicle['H']/vehicle['W'])
    ))
    return fig

# --- INTERFEJS STREAMLIT ---
st.set_page_config(page_title="SQM Fleet Planner", layout="wide")
st.title("🚛 SQM Multimedia - Planowanie Załadunku")

if 'cargo_cases' not in st.session_state: st.session_state.cargo_cases = []
products = load_products()

with st.sidebar:
    st.header("1. Wybierz Typ Auta")
    v_type = st.selectbox("Domyślny pojazd:", list(VEHICLES.keys()))
    veh = VEHICLES[v_type]
    
    st.divider()
    st.header("2. Dodaj Sprzęt")
    p_name = st.selectbox("Produkt:", [p['name'] for p in products])
    total_qty = st.number_input("Ilość sztuk produktu:", min_value=1, value=1)
    
    if st.button("Dodaj do listy"):
        p_data = next(p for p in products if p['name'] == p_name)
        
        # LOGIKA TWOJEGO HTML: Przeliczanie sztuk na skrzynie
        ipc = p_data.get('itemsPerCase', 1)
        needed_cases = math.ceil(total_qty / ipc)
        
        for i in range(needed_cases):
            case = p_data.copy()
            case['unique_id'] = f"{p_name}_{len(st.session_state.cargo_cases)}_{i}"
            st.session_state.cargo_cases.append(case)
        
        st.success(f"Dodano {total_qty} szt. = {needed_cases} skrzyń transportowych.")

    if st.button("Wyczyść plan"):
        st.session_state.cargo_cases = []
        st.rerun()

# --- PROCES OBLICZEŃ FLOTY ---
if st.session_state.cargo_cases:
    # Sortowanie skrzyń (największe na początku - identycznie jak w JS)
    remaining = sorted([dict(c) for c in st.session_state.cargo_cases], 
                       key=lambda x: x['width'] * x['length'], reverse=True)
    
    fleet_results = []
    while len(remaining) > 0:
        stacks, weight, not_packed = pack_one_vehicle(remaining, veh)
        
        # Zabezpieczenie przed błędem, jeśli skrzynia jest za duża dla typu auta
        if not stacks and remaining:
            st.error(f"⚠️ Skrzynia '{remaining[0]['name']}' ({remaining[0]['width']}x{remaining[0]['length']}cm) nie mieści się w wybranym aucie ({veh['L']}x{veh['W']}cm)!")
            break
            
        fleet_results.append({"stacks": stacks, "weight": weight})
        remaining = not_packed

    st.header(f"📊 Wynik: Potrzebujesz {len(fleet_results)} pojazdów typu {v_type}")

    # Wyświetlanie wyników dla każdego auta
    for i, res in enumerate(fleet_results):
        with st.expander(f"🚛 Pojazd #{i+1} - Załadunek", expanded=(i==0)):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.plotly_chart(draw_3d(res['stacks'], veh, f"Plan auta #{i+1}"), use_container_width=True)
            with c2:
                st.metric("Waga", f"{res['weight']} kg", f"limit {veh['maxWeight']} kg")
                total_area = sum(s['width'] * s['length'] for s in res['stacks'])
                st.metric("Miejsca paletowe", f"{total_area/(120*80):.2f}", f"limit {veh['maxPallets']}")
                
                st.write("**Lista stosów w tym aucie:**")
                for idx, s in enumerate(res['stacks']):
                    st.write(f"Stos {idx+1}: {len(s['items'])} skrzyń ({s['width']}x{s['length']} cm)")
else:
    st.info("Lista ładunkowa jest pusta. Dodaj sprzęt w panelu bocznym.")
