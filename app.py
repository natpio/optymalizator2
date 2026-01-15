import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

st.set_page_config(page_title="SQM Multimedia Solutions - Planer Załadunku", layout="wide")

# --- DANE PRODUKTÓW ---
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
    "P1.9 UNILUMIN UPAD IV / S-FLEX": {"l": 117, "w": 57, "h": 79, "weight": 115, "items_per_case": 8, "stackable": True},
    "P2.06 frameLED (STANDARD / CORNERS)": {"l": 86, "w": 62, "h": 100, "weight": 118, "items_per_case": 10, "stackable": True},
    "MULTIMEDIA TOTEM 55\"": {"l": 100, "w": 60, "h": 210, "weight": 210, "items_per_case": 1, "stackable": False},
    "PODEST ALUDECK LIGHT 2 x 1M": {"l": 200, "w": 100, "h": 20, "weight": 45, "items_per_case": 1, "stackable": True},
    "ALUSTAGE QUADRO-290 2M": {"l": 200, "w": 30, "h": 30, "weight": 11, "items_per_case": 1, "stackable": True},
    "Własny ładunek": {"l": 0, "w": 0, "h": 0, "weight": 0, "items_per_case": 1, "stackable": True}
}

VEHICLES_DATA = {
    "BUS": {"max_pallets": 8, "max_weight": 1100, "l": 450, "w": 150, "h": 245},
    "Solówka 6m": {"max_pallets": 14, "max_weight": 3500, "l": 600, "w": 245, "h": 245},
    "Solówka 7m": {"max_pallets": 16, "max_weight": 3500, "l": 700, "w": 245, "h": 245},
    "FTL (TIR)": {"max_pallets": 31, "max_weight": 12000, "l": 1360, "w": 245, "h": 265}
}

EURO_PALLET_AREA = 120 * 80

def draw_3d_box(fig, x, y, z, l, w, h, name, color):
    # Punkty narożne boxa
    fig.add_trace(go.Mesh3d(
        x=[x, x, x+w, x+w, x, x, x+w, x+w],
        y=[y, y+l, y+l, y, y, y+l, y+l, y],
        z=[z, z, z, z, z+h, z+h, z+h, z+h],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
        j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
        k=[0, 7, 2, 3, 6, 7, 1, 6, 5, 5, 7, 6],
        opacity=0.6,
        color=color,
        name=name,
        showlegend=False
    ))

# --- UI ---
st.title("📦 SQM Multimedia Solutions - Planer Załadunku")
st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Konfiguracja")
    v_type = st.selectbox("Wybierz pojazd:", list(VEHICLES_DATA.keys()))
    vehicle = VEHICLES_DATA[v_type]
    
    st.subheader("Ładunki")
    if 'rows' not in st.session_state:
        st.session_state.rows = 1

    cargo_to_pack = []
    for i in range(st.session_state.rows):
        with st.expander(f"Ładunek #{i+1}", expanded=True):
            p_name = st.selectbox(f"Produkt", list(PRODUCTS_DATA.keys()), key=f"p_{i}")
            p_base = PRODUCTS_DATA[p_name]
            
            l = st.number_input("Długość (cm)", value=p_base['l'], key=f"l_{i}")
            w = st.number_input("Szerokość (cm)", value=p_base['w'], key=f"w_{i}")
            h = st.number_input("Wysokość (cm)", value=p_base['h'], key=f"h_{i}")
            wt = st.number_input("Waga (kg)", value=float(p_base['weight']), key=f"wt_{i}")
            qty = st.number_input("Ilość sztuk", min_value=1, value=1, key=f"qty_{i}")
            stack = st.checkbox("Można stackować", value=p_base['stackable'], key=f"s_{i}")
            
            num_cases = int(np.ceil(qty / p_base['items_per_case']))
            st.info(f"Potrzeba skrzyń: {num_cases}")
            
            for _ in range(num_cases):
                cargo_to_pack.append({
                    "name": p_name, "l": l, "w": w, "h": h, "weight": wt, "stackable": stack,
                    "area": l * w, "volume": l * w * h
                })

    if st.button("➕ Dodaj kolejny ładunek"):
        st.session_state.rows += 1
        st.rerun()

# --- LOGIKA PAKOWANIA (Zgodna z HTML) ---
with col2:
    st.header("Wizualizacja 3D i Wyniki")
    
    if cargo_to_pack:
        # Sortowanie od największej powierzchni (zgodnie z JS)
        cargo_to_pack.sort(key=lambda x: x['area'], reverse=True)
        
        placed_stacks = []
        unloaded = []
        total_weight = 0
        total_area_cm2 = 0
        
        available_spaces = [{"x": 0, "y": 0, "w": vehicle['w'], "l": vehicle['l']}]
        
        for item in cargo_to_pack:
            # Walidacja wymiarów
            if item['h'] > vehicle['h'] or (item['l'] > vehicle['l'] and item['w'] > vehicle['l']):
                unloaded.append(item)
                continue
            
            placed = False
            
            # Próba stackowania
            if item['stackable']:
                for stack in placed_stacks:
                    if stack['can_stack'] and item['l'] <= stack['l'] and item['w'] <= stack['w'] \
                       and (stack['curr_h'] + item['h']) <= vehicle['h'] \
                       and (total_weight + item['weight']) <= vehicle['max_weight']:
                        
                        stack['items'].append({
                            "z": stack['curr_h'], "h": item['h'], "name": item['name']
                        })
                        stack['curr_h'] += item['h']
                        total_weight += item['weight']
                        placed = True
                        break
            
            # Próba postawienia na podłodze
            if not placed:
                for idx, space in enumerate(available_spaces):
                    if item['l'] <= space['l'] and item['w'] <= space['w'] \
                       and (total_weight + item['weight']) <= vehicle['max_weight']:
                        
                        new_stack = {
                            "x": space['x'], "y": space['y'], "w": item['w'], "l": item['l'],
                            "curr_h": item['h'], "can_stack": item['stackable'],
                            "items": [{"z": 0, "h": item['h'], "name": item['name']}]
                        }
                        placed_stacks.append(new_stack)
                        total_weight += item['weight']
                        total_area_cm2 += item['area']
                        
                        # Podział wolnej przestrzeni (zgodnie z JS)
                        available_spaces.pop(idx)
                        if space['w'] - item['w'] > 0:
                            available_spaces.append({"x": space['x'] + item['w'], "y": space['y'], "w": space['w'] - item['w'], "l": item['l']})
                        if space['l'] - item['l'] > 0:
                            available_spaces.append({"x": space['x'], "y": space['y'] + item['l'], "w": space['w'], "l": space['l'] - item['l']})
                        
                        available_spaces.sort(key=lambda s: s['w'] * s['l'])
                        placed = True
                        break
                
                if not placed:
                    unloaded.append(item)

        # --- WIDOK 3D ---
        fig = go.Figure()
        
        # Rysowanie paki pojazdu
        draw_3d_box(fig, 0, 0, 0, vehicle['l'], vehicle['w'], vehicle['h'], "Pojazd", "lightgrey")
        
        # Rysowanie skrzyń
        colors = ["#A52A2A", "#4682B4", "#5F9EA0", "#B8860B", "#8B4513"]
        for i, stack in enumerate(placed_stacks):
            color = colors[i % len(colors)]
            for sub_item in stack['items']:
                draw_3d_box(fig, stack['x'], stack['y'], sub_item['z'], stack['l'], stack['w'], sub_item['h'], sub_item['name'], color)

        fig.update_layout(
            scene=dict(
                xaxis_title='Szerokość (cm)',
                yaxis_title='Długość (cm)',
                zaxis_title='Wysokość (cm)',
                aspectmode='data'
            ),
            margin=dict(l=0, r=0, b=0, t=0),
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- STATYSTYKI ---
        m1, m2, m3 = st.columns(3)
        m1.metric("Waga", f"{total_weight} / {vehicle['max_weight']} kg")
        m2.metric("Miejsca Paletowe", f"{round(total_area_cm2/EURO_PALLET_AREA, 2)} / {vehicle['max_pallets']}")
        m3.metric("Załadowano skrzyń", f"{len(cargo_to_pack) - len(unloaded)} / {len(cargo_to_pack)}")

        if unloaded:
            st.error(f"⚠️ Nie zmieściło się {len(unloaded)} elementów!")
            for u in unloaded:
                st.write(f"- {u['name']}")
