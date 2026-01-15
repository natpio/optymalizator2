import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go

# --- KONFIGURACJA POJAZDÓW (Zgodna z Twoim HTML) ---
VEHICLES = {
    "BUS": {"L": 450, "W": 170, "H": 200, "max_weight": 1100},
    "Solówka 6m": {"L": 600, "W": 245, "H": 250, "max_weight": 3500},
    "Solówka 7m": {"L": 700, "W": 245, "H": 250, "max_weight": 3500},
    "FTL (TIR)": {"L": 1360, "W": 245, "H": 270, "max_weight": 24000}
}

def load_products():
    with open('products.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# --- ALGORYTM LOGISTYCZNY SQM (Odzwierciedlenie JS) ---
def calculate_load_sqm(items_to_load, vehicle_dims):
    # 1. Tworzenie stosów (Stacking)
    stacks = []
    # Kopia, aby nie zmieniać stanu sesji
    remaining_items = [dict(i) for i in items_to_load]
    
    # Sortujemy przedmioty, aby ułatwić stackowanie (te same wymiary obok siebie)
    remaining_items.sort(key=lambda x: (x['width'], x['length']), reverse=True)
    
    for item in remaining_items:
        stacked = False
        if item.get('canStack', False):
            for s in stacks:
                # Warunek: te same wymiary podstawy + canStack + limit wysokości auta
                if (s['width'] == item['width'] and 
                    s['length'] == item['length'] and 
                    s['total_height'] + item['height'] <= vehicle_dims['H']):
                    
                    item_info = item.copy()
                    item_info['heightFromBottom'] = s['total_height']
                    s['items'].append(item_info)
                    s['total_height'] += item['height']
                    s['total_weight'] += item['weight']
                    stacked = True
                    break
        
        if not stacked:
            item_info = item.copy()
            item_info['heightFromBottom'] = 0
            stacks.append({
                'width': item['width'],
                'length': item['length'],
                'total_height': item['height'],
                'total_weight': item['weight'],
                'items': [item_info]
            })

    # 2. Sortowanie stosów po powierzchni (identycznie jak res.sort w JS)
    stacks.sort(key=lambda s: s['width'] * s['length'], reverse=True)

    # 3. Układanie rzędami (Shelf Packing)
    placed_stacks = []
    current_x = 0 # Pozycja wzdłuż długości naczepy
    current_y = 0 # Pozycja wzdłuż szerokości naczepy
    max_width_in_row = 0
    current_weight = 0

    for s in stacks:
        # Sprawdzenie DMC
        if current_weight + s['total_weight'] > vehicle_dims['max_weight']:
            continue
            
        # Jeśli nie mieści się w rzędzie (szerokość), przejdź do nowego rzędu
        if current_y + s['length'] > vehicle_dims['W']:
            current_y = 0
            current_x += max_width_in_row
            max_width_in_row = 0

        # Jeśli mieści się w naczepie (długość)
        if current_x + s['width'] <= vehicle_dims['L']:
            s['x'] = current_x
            s['y'] = current_y
            placed_stacks.append(s)
            
            current_y += s['length']
            max_width_in_row = max(max_width_in_row, s['width'])
            current_weight += s['total_weight']

    return placed_stacks

# --- WIZUALIZACJA 3D (PLOTLY) ---
def draw_3d_truck(placed_stacks, vehicle_dims):
    fig = go.Figure()

    # Rysowanie obrysu naczepy
    l, w, h = vehicle_dims['L'], vehicle_dims['W'], vehicle_dims['H']
    
    for s in placed_stacks:
        for item in s['items']:
            x0, y0, z0 = s['x'], s['y'], item['heightFromBottom']
            dx, dy, dz = s['width'], s['length'], item['height']

            fig.add_trace(go.Mesh3d(
                x=[x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0],
                y=[y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy],
                z=[z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz],
                i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
                j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
                k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
                opacity=0.85,
                flatshading=True,
                color="#4682B4" if item.get('canStack') else "#A52A2A",
                name=f"{item['name']}"
            ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[0, l], title="Długość"),
            yaxis=dict(range=[0, w], title="Szerokość"),
            zaxis=dict(range=[0, h], title="Wysokość"),
            aspectmode='manual',
            aspectratio=dict(x=l/w, y=1, z=h/w)
        ),
        margin=dict(l=0, r=0, b=0, t=30),
        showlegend=False
    )
    return fig

# --- INTERFEJS STREAMLIT ---
st.set_page_config(page_title="SQM Loader 3D", layout="wide")
st.title("🚛 SQM Multimedia Solutions - Planer Załadunku 3D")

if 'cargo_list' not in st.session_state:
    st.session_state.cargo_list = []

products = load_products()

# Sidebar: Wybór pojazdu i dodawanie
with st.sidebar:
    st.header("Konfiguracja")
    v_type = st.selectbox("Typ pojazdu", list(VEHICLES.keys()))
    selected_v = VEHICLES[v_type]
    
    st.divider()
    st.header("Dodaj sprzęt")
    prod_name = st.selectbox("Wybierz produkt", [p['name'] for p in products])
    count = st.number_input("Ilość", min_value=1, value=1)
    
    if st.button("Dodaj do listy"):
        p_data = next(i for i in products if i['name'] == prod_name)
        for _ in range(count):
            st.session_state.cargo_list.append(p_data)
        st.success("Dodano!")

    if st.button("Wyczyść wszystko"):
        st.session_state.cargo_list = []
        st.rerun()

# Główne okno: Wyniki i 3D
col_data, col_viz = st.columns([1, 2])

if st.session_state.cargo_list:
    results = calculate_load_sqm(st.session_state.cargo_list, selected_v)
    
    with col_data:
        st.subheader("Podsumowanie")
        total_items = sum(len(s['items']) for s in results)
        total_w = sum(s['total_weight'] for s in results)
        
        st.metric("Załadowane elementy", f"{total_items} / {len(st.session_state.cargo_list)}")
        st.metric("Waga całkowita", f"{total_w} kg / {selected_v['max_weight']} kg")
        
        # Wyświetlanie listy stosów (jak w raporcie HTML)
        for idx, s in enumerate(results):
            with st.expander(f"Stos {idx+1}: {s['width']}x{s['length']} cm"):
                for item in s['items']:
                    st.write(f"- {item['name']} (H: {item['height']}cm)")

    with col_viz:
        st.subheader("Wizualizacja 3D")
        fig = draw_3d_truck(results, selected_v)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Dodaj produkty w panelu bocznym, aby rozpocząć planowanie.")
