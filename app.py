import streamlit as st
import json
import plotly.graph_objects as go
import math
import pandas as pd

# --- 1. KONFIGURACJA STRONY (Musi być na samym początku) ---
st.set_page_config(page_title="Logistics Dept - Planer", layout="wide")

# --- 2. ZABEZPIECZENIA ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 Logistics Department")
        st.subheader("Planer Transportu - Logowanie")

        try:
            # Hasło pobierane z pliku .streamlit/secrets.toml
            master_password = str(st.secrets["password"])
        except Exception:
            st.error("🔒 Brak konfiguracji hasła w Secrets. Dodaj 'password = \"twoje_haslo\"'.")
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

# --- 3. TWOJE PIERWOTNE LIMITY POJAZDÓW ---
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
            return sorted(json.load(f), key=lambda x: x.get('name', 'Nienazwany'))
    except:
        return []

# --- 4. NAPRAWIONA LOGIKA PAKOWANIA ---
def pack_one_vehicle(remaining_items, vehicle):
    """
    Pakuje przedmioty do JEDNEGO auta, pilnując wagi i wymiarów.
    Zwraca: (postawione_stosy, waga_auta, towary_ktore_zostaly)
    """
    placed_stacks = []
    not_placed = []
    current_weight = 0
    curr_x, curr_y, max_w_row = 0, 0, 0

    # Sortowanie: najcięższe i największe najpierw (stabilność logistyczna)
    sorted_items = sorted(remaining_items, key=lambda x: (x['weight'], x['width']*x['length']), reverse=True)

    for item in sorted_items:
        # Sprawdzenie limitu wagi auta (DMC)
        if current_weight + item['weight'] > vehicle['maxWeight']:
            not_placed.append(item)
            continue

        added = False
        # Próba sztaplowania (stacking)
        if item.get('canStack', True):
            for s in placed_stacks:
                if (s['canStackBase'] and item['width'] == s['width'] and 
                    item['length'] == s['length'] and (s['currentH'] + item['height']) <= vehicle['H']):
                    
                    item_copy = item.copy()
                    item_copy['z_pos'] = s['currentH']
                    s['items'].append(item_copy)
                    s['currentH'] += item['height']
                    current_weight += item['weight']
                    added = True
                    break
        
        # Próba postawienia na podłodze (Floor space)
        if not added:
            if curr_y + item['length'] > vehicle['W']:
                curr_y = 0
                curr_x += max_w_row
                max_w_row = 0
            
            if curr_x + item['width'] <= vehicle['L']:
                item_copy = item.copy()
                item_copy['z_pos'] = 0
                placed_stacks.append({
                    'x': curr_x, 'y': curr_y, 'width': item['width'], 'length': item['length'],
                    'currentH': item['height'], 'canStackBase': item.get('canStack', True),
                    'items': [item_copy]
                })
                curr_y += item['length']
                max_w_row = max(max_w_row, item['width'])
                current_weight += item['weight']
                added = True
            else:
                not_placed.append(item)
                
    return placed_stacks, current_weight, not_placed

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
                opacity=0.85, color=color_map.get(it['name'], "#808080"), name=it['name']
            ))
    fig.update_layout(scene=dict(
        xaxis=dict(range=[0, vehicle['L']], title="Dł (cm)"),
        yaxis=dict(range=[0, vehicle['W']], title="Szer (cm)"),
        zaxis=dict(range=[0, vehicle['H']], title="Wys (cm)"),
        aspectmode='manual', aspectratio=dict(x=vehicle['L']/vehicle['W'], y=1, z=vehicle['H']/vehicle['W'])
    ), margin=dict(l=0, r=0, b=0, t=0))
    return fig

# --- 6. GŁÓWNY INTERFEJS ---
if check_password():
    if 'cargo' not in st.session_state: st.session_state.cargo = []
    prods = load_products()
    
    if 'color_map' not in st.session_state:
        st.session_state.color_map = {p['name']: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, p in enumerate(prods)}

    with st.sidebar:
        st.header("1. Wybierz Auto")
        v_name = st.selectbox("Typ pojazdu:", list(VEHICLES.keys()))
        veh = VEHICLES[v_name]
        
        st.divider()
        st.header("2. Dodaj Produkty")
        selected_p_name = st.selectbox("Szukaj produktu:", [p['name'] for p in prods], index=None)
        qty = st.number_input("Ilość sztuk:", min_value=1, value=1)
        
        if st.button("Dodaj do planu", use_container_width=True) and selected_p_name:
            p_data = next(p for p in prods if p['name'] == selected_p_name)
            ipc = p_data.get('itemsPerCase', 1)
            num_cases = math.ceil(qty / ipc)
            for i in range(num_cases):
                c = p_data.copy()
                c['actual_items'] = qty % ipc if (i == num_cases - 1 and qty % ipc != 0) else ipc
                st.session_state.cargo.append(c)
            st.rerun()
            
        if st.button("Wyczyść wszystko", use_container_width=True, type="secondary"):
            st.session_state.cargo = []
            st.rerun()

    # WYŚWIETLANIE WYNIKÓW
    if st.session_state.cargo:
        st.header("📋 Wynik planowania floty")
        
        # Logika rozdziału na wiele aut
        items_to_ship = [dict(c) for c in st.session_state.cargo]
        fleet = []
        
        # Sprawdzenie czy pojedynczy towar nie jest cięższy niż całe auto
        too_heavy = [i['name'] for i in items_to_ship if i['weight'] > veh['maxWeight']]
        if too_heavy:
            st.error(f"❌ Towary {list(set(too_heavy))} przekraczają DMC auta ({veh['maxWeight']} kg)!")
        else:
            while len(items_to_ship) > 0:
                stacks, weight, items_to_ship_remaining = pack_one_vehicle(items_to_ship, veh)
                
                # Zabezpieczenie przed pętlą jeśli gabaryt nie pasuje
                if len(items_to_ship_remaining) == len(items_to_ship) and weight == 0:
                    st.warning("⚠️ Pozostałe towary nie mieszczą się gabarytowo w tym typie auta.")
                    break
                    
                fleet.append({"stacks": stacks, "weight": weight})
                items_to_ship = items_to_ship_remaining

            # Generowanie widoków dla każdego auta
            for idx, truck in enumerate(fleet):
                with st.expander(f"🚚 POJAZD #{idx+1} | Ładunek: {truck['weight']} / {veh['maxWeight']} kg", expanded=True):
                    col1, col2 = st.columns([3, 2])
                    
                    with col1:
                        st.plotly_chart(draw_3d(truck['stacks'], veh, st.session_state.color_map), 
                                      use_container_width=True, key=f"truck_{idx}")
                    
                    with col2:
                        # Tabela ładunkowa dla konkretnego auta
                        all_items = [it for s in truck['stacks'] for it in s['items']]
                        df_truck = pd.DataFrame(all_items)
                        summary = df_truck.groupby('name').agg({'actual_items':'sum', 'weight':'sum'}).reset_index()
                        summary.columns = ['Produkt', 'Sztuk', 'Waga (kg)']
                        st.table(summary)
                        
                        st.metric("Wykorzystanie DMC", f"{int((truck['weight']/veh['maxWeight'])*100)}%")
                        st.progress(truck['weight'] / veh['maxWeight'])
    else:
        st.info("Dodaj produkty z lewego panelu, aby rozpocząć symulację.")
