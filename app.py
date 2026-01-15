import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Konfiguracja strony
st.set_page_config(page_title="SQM Multimedia Solutions - Planer Załadunku", layout="wide")

# --- KOMPLETNA BAZA PRODUKTÓW Z TWOJEGO PLIKU HTML ---
PRODUCTS_DATA = {
    "17-23\" - plastic case": {"l": 80, "w": 60, "h": 20, "weight": 20, "items_per_case": 1, "stackable": True},
    "24-32\" - plastic case": {"l": 60, "w": 40, "h": 20, "weight": 15, "items_per_case": 1, "stackable": True},
    "32\" - triple - STANDARD": {"l": 90, "w": 50, "h": 70, "weight": 50, "items_per_case": 3, "stackable": True},
    "43\" - triple - STANDARD": {"l": 112, "w": 42, "h": 80, "weight": 90, "items_per_case": 3, "stackable": True},
    "45\"-55\" - double - STANDARD": {"l": 140, "w": 42, "h": 100, "weight": 150, "items_per_case": 2, "stackable": True},
    "60-65\" - double - STANDARD": {"l": 160, "w": 40, "h": 230, "weight": 200, "items_per_case": 2, "stackable": True},
    "75-86\" - double - STANDARD": {"l": 210, "w": 40, "h": 230, "weight": 230, "items_per_case": 2, "stackable": True},
    "98\" - double - STANDARD": {"l": 250, "w": 70, "h": 230, "weight": 400, "items_per_case": 1, "stackable": True},
    "NEC E326 - STANDARD": {"l": 70, "w": 50, "h": 70, "weight": 90, "items_per_case": 3, "stackable": True},
    "NEC C431 - STANDARD": {"l": 80, "w": 50, "h": 80, "weight": 120, "items_per_case": 3, "stackable": True},
    "NEC C501 - STANDARD": {"l": 100, "w": 50, "h": 100, "weight": 140, "items_per_case": 2, "stackable": True},
    "NEC C551 - STANDARD": {"l": 100, "w": 50, "h": 100, "weight": 140, "items_per_case": 2, "stackable": True},
    "SAMSUNG series 7 - STANDARD": {"l": 110, "w": 50, "h": 60, "weight": 160, "items_per_case": 2, "stackable": True},
    "NEC C861 86\" - STANDARD": {"l": 140, "w": 40, "h": 230, "weight": 210, "items_per_case": 1, "stackable": True},
    "NEC C981 98\" - STANDARD": {"l": 170, "w": 70, "h": 230, "weight": 250, "items_per_case": 1, "stackable": True},
    "NEC X981 98\" TOUCHSCREEN - STANDARD": {"l": 170, "w": 70, "h": 230, "weight": 250, "items_per_case": 1, "stackable": True},
    "iiYama 46\" - TOUCHSCREEN - STANDARD": {"l": 100, "w": 50, "h": 100, "weight": 140, "items_per_case": 2, "stackable": True},
    "P1.9 UNILUMIN UPAD IV / S-FLEX": {"l": 117, "w": 57, "h": 79, "weight": 115, "items_per_case": 8, "stackable": True},
    "P2.06 frameLED (STANDARD / CORNERS)": {"l": 86, "w": 62, "h": 100, "weight": 118, "items_per_case": 10, "stackable": True},
    "P2.06 frameLED (CURVE)": {"l": 115, "w": 62, "h": 100, "weight": 138, "items_per_case": 10, "stackable": True},
    "P2.6 INFILED": {"l": 120, "w": 60, "h": 80, "weight": 125, "items_per_case": 8, "stackable": True},
    "MULTIMEDIA TOTEM 55\"": {"l": 100, "w": 60, "h": 210, "weight": 210, "items_per_case": 1, "stackable": False},
    "KOLUMNA GŁOŚNIKOWA D&B V8/V12": {"l": 120, "w": 60, "h": 80, "weight": 160, "items_per_case": 4, "stackable": True},
    "GŁOŚNIK D&B V-SUB": {"l": 120, "w": 60, "h": 80, "weight": 140, "items_per_case": 2, "stackable": True},
    "GŁOŚNIK D&B J-INFRA": {"l": 120, "w": 120, "h": 100, "weight": 110, "items_per_case": 1, "stackable": True},
    "GŁOŚNIK D&B Q1": {"l": 120, "w": 60, "h": 80, "weight": 130, "items_per_case": 6, "stackable": True},
    "GŁOŚNIK D&B Q7": {"l": 80, "w": 60, "h": 60, "weight": 60, "items_per_case": 2, "stackable": True},
    "GŁOŚNIK D&B Q-SUB": {"l": 80, "w": 60, "h": 80, "weight": 110, "items_per_case": 2, "stackable": True},
    "GŁOŚNIK D&B M4": {"l": 120, "w": 60, "h": 60, "weight": 65, "items_per_case": 2, "stackable": True},
    "GŁOŚNIK D&B M6": {"l": 120, "w": 60, "h": 60, "weight": 55, "items_per_case": 2, "stackable": True},
    "GŁOŚNIK D&B E8": {"l": 80, "w": 60, "h": 60, "weight": 55, "items_per_case": 4, "stackable": True},
    "GŁOŚNIK D&B E5/E6": {"l": 80, "w": 60, "h": 40, "weight": 40, "items_per_case": 6, "stackable": True},
    "KOŃCÓWKA MOCY D&B D80": {"l": 80, "w": 60, "h": 80, "weight": 140, "items_per_case": 3, "stackable": True},
    "KOŃCÓWKA MOCY D&B D20/D12": {"l": 80, "w": 60, "h": 80, "weight": 110, "items_per_case": 3, "stackable": True},
    "KOŃCÓWKA MOCY D&B P1200": {"l": 60, "w": 60, "h": 80, "weight": 90, "items_per_case": 2, "stackable": True},
    "PROCESOR D&B DS10 / DS100": {"l": 60, "w": 60, "h": 40, "weight": 35, "items_per_case": 4, "stackable": True},
    "MIKSER AUDIO YAMAHA RIVAGE PM7": {"l": 160, "w": 60, "h": 120, "weight": 210, "items_per_case": 1, "stackable": False},
    "MIKSER AUDIO YAMAHA CL5": {"l": 120, "w": 60, "h": 110, "weight": 130, "items_per_case": 1, "stackable": False},
    "MIKSER AUDIO YAMAHA CL3": {"l": 100, "w": 60, "h": 110, "weight": 110, "items_per_case": 1, "stackable": False},
    "MIKSER AUDIO YAMAHA QL5": {"l": 100, "w": 60, "h": 100, "weight": 100, "items_per_case": 1, "stackable": False},
    "MIKSER AUDIO YAMAHA QL1": {"l": 60, "w": 60, "h": 100, "weight": 65, "items_per_case": 1, "stackable": False},
    "MIKSER AUDIO YAMAHA LS9-32": {"l": 120, "w": 60, "h": 100, "weight": 110, "items_per_case": 1, "stackable": False},
    "MIKSER AUDIO YAMAHA LS9-16": {"l": 80, "w": 60, "h": 100, "weight": 70, "items_per_case": 1, "stackable": False},
    "STAGEBOX YAMAHA RIO3224-D2": {"l": 60, "w": 60, "h": 80, "weight": 75, "items_per_case": 1, "stackable": True},
    "STAGEBOX YAMAHA RIO1608-D2": {"l": 60, "w": 60, "h": 60, "weight": 55, "items_per_case": 1, "stackable": True},
    "ROBEYE 1 / 2": {"l": 60, "w": 60, "h": 40, "weight": 35, "items_per_case": 1, "stackable": True},
    "ROBE BMFL BLADE / SPOT": {"l": 120, "w": 60, "h": 100, "weight": 120, "items_per_case": 2, "stackable": True},
    "ROBE ROBIN MEGAPOINTE": {"l": 80, "w": 60, "h": 80, "weight": 85, "items_per_case": 2, "stackable": True},
    "ROBE ROBIN POINTE": {"l": 80, "w": 60, "h": 80, "weight": 75, "items_per_case": 2, "stackable": True},
    "ROBE ROBIN SPIIDER": {"l": 80, "w": 60, "h": 80, "weight": 75, "items_per_case": 2, "stackable": True},
    "ROBE ROBIN LEDBEAM 150": {"l": 120, "w": 60, "h": 60, "weight": 95, "items_per_case": 8, "stackable": True},
    "ROBE ROBIN LEDBEAM 100": {"l": 120, "w": 60, "h": 60, "weight": 85, "items_per_case": 12, "stackable": True},
    "SGM Q-7 / XC-5": {"l": 120, "w": 60, "h": 60, "weight": 90, "items_per_case": 6, "stackable": True},
    "SGM P-5 / P-2": {"l": 120, "w": 60, "h": 60, "weight": 85, "items_per_case": 6, "stackable": True},
    "CLAY PAKY SHARPY": {"l": 80, "w": 60, "h": 80, "weight": 75, "items_per_case": 2, "stackable": True},
    "CLAY PAKY B-EYE K20": {"l": 120, "w": 60, "h": 100, "weight": 110, "items_per_case": 2, "stackable": True},
    "CLAY PAKY B-EYE K10": {"l": 80, "w": 60, "h": 80, "weight": 80, "items_per_case": 2, "stackable": True},
    "MARTIN ATOMIC 3000": {"l": 120, "w": 60, "h": 60, "weight": 75, "items_per_case": 4, "stackable": True},
    "MARTIN ATOMIC LED": {"l": 120, "w": 60, "h": 60, "weight": 85, "items_per_case": 4, "stackable": True},
    "MARTIN MAC VIPER PERFORMANCE": {"l": 120, "w": 60, "h": 100, "weight": 130, "items_per_case": 2, "stackable": True},
    "MARTIN MAC QUANTUM WASH": {"l": 120, "w": 60, "h": 100, "weight": 115, "items_per_case": 2, "stackable": True},
    "MARTIN MAC AURA / AURA XB": {"l": 120, "w": 60, "h": 60, "weight": 105, "items_per_case": 6, "stackable": True},
    "CHAUVET WELL FIT": {"l": 120, "w": 60, "h": 60, "weight": 85, "items_per_case": 6, "stackable": True},
    "ASTERA TITAN TUBE": {"l": 120, "w": 60, "h": 40, "weight": 45, "items_per_case": 8, "stackable": True},
    "ASTERA HELIOS TUBE": {"l": 80, "w": 60, "h": 40, "weight": 35, "items_per_case": 8, "stackable": True},
    "CONSOLES MA LIGHTING GRANDMA3 FULL SIZE": {"l": 140, "w": 60, "h": 120, "weight": 150, "items_per_case": 1, "stackable": False},
    "CONSOLES MA LIGHTING GRANDMA3 LIGHT": {"l": 120, "w": 60, "h": 120, "weight": 120, "items_per_case": 1, "stackable": False},
    "CONSOLES MA LIGHTING GRANDMA2 FULL SIZE": {"l": 140, "w": 60, "h": 120, "weight": 140, "items_per_case": 1, "stackable": False},
    "CONSOLES MA LIGHTING GRANDMA2 LIGHT": {"l": 120, "w": 60, "h": 120, "weight": 110, "items_per_case": 1, "stackable": False},
    "MA LIGHTING NPU / PROCESSING UNIT": {"l": 60, "w": 60, "h": 40, "weight": 45, "items_per_case": 1, "stackable": True},
    "DIMMER MA LIGHTING 12x2.3kW": {"l": 60, "w": 60, "h": 80, "weight": 95, "items_per_case": 1, "stackable": True},
    "POWER DISTRIBUTION 63A / 125A": {"l": 60, "w": 60, "h": 60, "weight": 55, "items_per_case": 1, "stackable": True},
    "PODEST ALUDECK LIGHT 2 x 1M": {"l": 200, "w": 100, "h": 20, "weight": 45, "items_per_case": 1, "stackable": True},
    "PODEST ALUDECK LIGHT 1 x 1M": {"l": 100, "w": 100, "h": 20, "weight": 25, "items_per_case": 1, "stackable": True},
    "PODEST ALUDECK LIGHT 2 x 0.5M": {"l": 200, "w": 50, "h": 20, "weight": 25, "items_per_case": 1, "stackable": True},
    "PODEST ALUDECK LIGHT 1 x 0.5M": {"l": 100, "w": 50, "h": 20, "weight": 15, "items_per_case": 1, "stackable": True},
    "ALUSTAGE / AL34 / QUADRO-290 TRUSS FD / 3M": {"l": 300, "w": 30, "h": 30, "weight": 16, "items_per_case": 1, "stackable": True},
    "ALUSTAGE / AL34 / QUADRO-290 TRUSS FD / 2.5M": {"l": 250, "w": 30, "h": 30, "weight": 14, "items_per_case": 1, "stackable": True},
    "ALUSTAGE / AL34 / QUADRO-290 TRUSS FD / 2M": {"l": 200, "w": 30, "h": 30, "weight": 11, "items_per_case": 1, "stackable": True},
    "ALUSTAGE / AL34 / QUADRO-290 TRUSS FD / 1.5M": {"l": 150, "w": 30, "h": 30, "weight": 9, "items_per_case": 1, "stackable": True},
    "ALUSTAGE / AL34 / QUADRO-290 TRUSS FD / 1M": {"l": 100, "w": 30, "h": 30, "weight": 6, "items_per_case": 1, "stackable": True},
    "ALUSTAGE / AL34 / QUADRO-290 TRUSS FD / 0.5M": {"l": 50, "w": 30, "h": 30, "weight": 4, "items_per_case": 1, "stackable": True},
    "TRUSS x CORNER 2-WAY": {"l": 60, "w": 60, "h": 30, "weight": 8, "items_per_case": 1, "stackable": True},
    "TRUSS x CORNER 3-WAY": {"l": 60, "w": 60, "h": 60, "weight": 10, "items_per_case": 1, "stackable": True},
    "TRUSS x CORNER 4-WAY": {"l": 60, "w": 60, "h": 60, "weight": 12, "items_per_case": 1, "stackable": True},
    "TRUSS x CORNER 5-WAY": {"l": 60, "w": 60, "h": 60, "weight": 14, "items_per_case": 1, "stackable": True},
    "TRUSS x CORNER 6-WAY": {"l": 60, "w": 60, "h": 60, "weight": 16, "items_per_case": 1, "stackable": True},
    "TRUSS x HANGED CIRCLE Ø2m": {"l": 200, "w": 200, "h": 30, "weight": 45, "items_per_case": 1, "stackable": False},
    "TRUSS x HANGED CIRCLE Ø3m": {"l": 300, "w": 150, "h": 30, "weight": 65, "items_per_case": 1, "stackable": False},
    "TRUSS x HANGED CIRCLE Ø4m": {"l": 200, "w": 150, "h": 30, "weight": 85, "items_per_case": 1, "stackable": False},
    "TRUSS x HANGED CIRCLE Ø5m": {"l": 250, "w": 150, "h": 30, "weight": 105, "items_per_case": 1, "stackable": False},
    "TRUSS x HANGED CIRCLE Ø6m": {"l": 300, "w": 150, "h": 30, "weight": 125, "items_per_case": 1, "stackable": False},
    "TRUSS x HANGED CIRCLE Ø8m": {"l": 320, "w": 100, "h": 60, "weight": 165, "items_per_case": 1, "stackable": False},
    "TRUSS x HANGED CIRCLE Ø10m": {"l": 320, "w": 100, "h": 80, "weight": 215, "items_per_case": 1, "stackable": False},
    "TRUSS x HANGED CIRCLE Ø12m": {"l": 320, "w": 100, "h": 100, "weight": 265, "items_per_case": 1, "stackable": False},
    "TRUSS x HANGED CIRCLE Ø15m": {"l": 320, "w": 120, "h": 150, "weight": 315, "items_per_case": 1, "stackable": False},
    "TRUSS x HANGED CIRCLE Ø19m": {"l": 320, "w": 150, "h": 200, "weight": 415, "items_per_case": 1, "stackable": False},
    "MOTOR HOIST CM LODESTAR 1T": {"l": 120, "w": 60, "h": 60, "weight": 140, "items_per_case": 2, "stackable": True},
    "MOTOR HOIST CM LODESTAR 0.5T": {"l": 120, "w": 60, "h": 60, "weight": 110, "items_per_case": 2, "stackable": True},
    "MOTOR HOIST CM LODESTAR 0.25T": {"l": 80, "w": 60, "h": 60, "weight": 80, "items_per_case": 2, "stackable": True},
    "MOTOR CONTROLLER 4-WAY / 8-WAY": {"l": 60, "w": 60, "h": 60, "weight": 45, "items_per_case": 1, "stackable": True},
    "Własny ładunek": {"l": 100, "w": 100, "h": 100, "weight": 100, "items_per_case": 1, "stackable": True}
}

VEHICLES_DATA = {
    "BUS": {"l": 450, "w": 150, "h": 245, "weight": 1100, "pallets": 8},
    "Solówka 6m": {"l": 600, "w": 245, "h": 245, "weight": 3500, "pallets": 14},
    "Solówka 7m": {"l": 700, "w": 245, "h": 245, "weight": 3500, "pallets": 16},
    "FTL (TIR)": {"l": 1360, "w": 245, "h": 265, "weight": 12000, "pallets": 31}
}

EURO_PALLET_AREA = 120 * 80

def draw_3d_box(fig, x, y, z, l, w, h, name, color, opacity=0.6):
    # Punkty wierzchołkowe prostopadłościanu
    fig.add_trace(go.Mesh3d(
        x=[x, x, x+w, x+w, x, x, x+w, x+w],
        y=[y, y+l, y+l, y, y, y+l, y+l, y],
        z=[z, z, z, z, z+h, z+h, z+h, z+h],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
        j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
        k=[0, 7, 2, 3, 6, 7, 1, 6, 5, 5, 7, 6],
        opacity=opacity, color=color, name=name, showlegend=False,
        hoverinfo='name+text', text=f"Wymiary: {w}x{l}x{h} cm"
    ))

st.title("📦 SQM Multimedia Solutions - Planer Załadunku v2")

col_input, col_viz = st.columns([1, 2])

with col_input:
    st.header("1. Konfiguracja")
    v_type = st.selectbox("Wybierz pojazd:", list(VEHICLES_DATA.keys()))
    veh = VEHICLES_DATA[v_type]

    if 'cargo_rows' not in st.session_state:
        st.session_state.cargo_rows = 1

    to_pack = []
    # Dynamiczna lista produktów
    for i in range(st.session_state.cargo_rows):
        with st.expander(f"Ładunek #{i+1}", expanded=True):
            p_key = st.selectbox("Produkt", sorted(list(PRODUCTS_DATA.keys())), key=f"p_{i}")
            p_def = PRODUCTS_DATA[p_key]
            
            # Formularz z domyślnymi wartościami z bazy
            l = st.number_input("Długość (cm)", value=int(p_def['l']), key=f"l_{i}")
            w = st.number_input("Szerokość (cm)", value=int(p_def['w']), key=f"w_{i}")
            h = st.number_input("Wysokość (cm)", value=int(p_def['h']), key=f"h_{i}")
            wt = st.number_input("Waga/case (kg)", value=float(p_def['weight']), key=f"wt_{i}")
            qty = st.number_input("Ilość produktów", min_value=1, value=1, key=f"qty_{i}")
            stack_check = st.checkbox("Można stawiać jeden na drugim?", value=p_def['stackable'], key=f"st_{i}")
            
            num_cases = int(np.ceil(qty / p_def['items_per_case']))
            st.info(f"Skrzyń do planowania: {num_cases}")
            
            for _ in range(num_cases):
                to_pack.append({
                    "name": p_key, "l": l, "w": w, "h": h, "weight": wt, 
                    "stackable": stack_check, "area": l * w
                })

    if st.button("➕ Dodaj kolejną pozycję"):
        st.session_state.cargo_rows += 1
        st.rerun()

with col_viz:
    st.header("2. Wizualizacja 3D i Raport")
    
    # LOGIKA FIRST-FIT (Identyczna z JS)
    to_pack.sort(key=lambda x: x['area'], reverse=True)
    
    placed_stacks = []
    unloaded = []
    total_weight = 0
    total_area_floor = 0
    
    # Przestrzeń podłogowa paki
    available_spaces = [{"x": 0, "y": 0, "w": veh['w'], "l": veh['l']}]

    for item in to_pack:
        placed = False
        
        # 1. Próba stackowania na istniejących stosach
        if item['stackable']:
            for stack in placed_stacks:
                if stack['can_stack'] and item['l'] <= stack['l'] and item['w'] <= stack['w'] \
                   and (stack['curr_h'] + item['h']) <= veh['h'] \
                   and (total_weight + item['weight']) <= veh['weight']:
                    
                    stack['items'].append({"z": stack['curr_h'], "h": item['h'], "name": item['name']})
                    stack['curr_h'] += item['h']
                    total_weight += item['weight']
                    placed = True
                    break
        
        # 2. Próba postawienia na nowym miejscu na podłodze
        if not placed:
            # Sortowanie wolnych przestrzeni (zgodnie z logiką JS)
            available_spaces.sort(key=lambda s: (s['l'] * s['w']))
            
            for idx, space in enumerate(available_spaces):
                # Sprawdzamy oba obroty (0 i 90 stopni)
                if (item['l'] <= space['l'] and item['w'] <= space['w']) or (item['w'] <= space['l'] and item['l'] <= space['w']):
                    
                    # Jeśli trzeba obrócić
                    if not (item['l'] <= space['l'] and item['w'] <= space['w']):
                        item['l'], item['w'] = item['w'], item['l']

                    if (total_weight + item['weight']) <= veh['weight']:
                        new_stack = {
                            "x": space['x'], "y": space['y'], "w": item['w'], "l": item['l'],
                            "curr_h": item['h'], "can_stack": item['stackable'],
                            "items": [{"z": 0, "h": item['h'], "name": item['name']}]
                        }
                        placed_stacks.append(new_stack)
                        total_weight += item['weight']
                        total_area_floor += (item['l'] * item['w'])
                        
                        # Podział przestrzeni ( Guillotine Split)
                        available_spaces.pop(idx)
                        if space['w'] - item['w'] > 0:
                            available_spaces.append({"x": space['x'] + item['w'], "y": space['y'], "w": space['w'] - item['w'], "l": item['l']})
                        if space['l'] - item['l'] > 0:
                            available_spaces.append({"x": space['x'], "y": space['y'] + item['l'], "w": space['w'], "l": space['l'] - item['l']})
                        
                        placed = True
                        break
            
            if not placed:
                unloaded.append(item)

    # Rysowanie w Plotly
    fig = go.Figure()
    
    # Obrys pojazdu
    draw_3d_box(fig, 0, 0, 0, veh['l'], veh['w'], veh['h'], "Pojazd", "rgba(100,100,100,0.05)", 0.1)
    
    # Kolory dla różnych typów skrzyń
    palette = ["#A52A2A", "#4682B4", "#5F9EA0", "#B8860B", "#8B4513", "#2E8B57", "#6A5ACD"]
    
    for i, stack in enumerate(placed_stacks):
        color = palette[i % len(palette)]
        for sub in stack['items']:
            draw_3d_box(fig, stack['x'], stack['y'], sub['z'], stack['l'], stack['w'], sub['h'], sub['name'], color)

    fig.update_layout(
        scene=dict(
            xaxis_title="Szerokość (cm)",
            yaxis_title="Długość (cm)",
            zaxis_title="Wysokość (cm)",
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        height=700
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- PODSUMOWANIE ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Waga całkowita", f"{int(total_weight)} / {veh['weight']} kg")
    c2.metric("Miejsca paletowe", f"{round(total_area_floor/EURO_PALLET_AREA, 2)} / {veh['pallets']}")
    c3.metric("Załadowano", f"{len(to_pack)-len(unloaded)} / {len(to_pack)} skrzyń")

    if unloaded:
        st.error(f"⚠️ Nie zmieściło się: {len(unloaded)} sztuk")
        with st.expander("Lista brakujących elementów"):
            for u in unloaded:
                st.write(f"- {u['name']} ({u['l']}x{u['w']}x{u['h']})")
