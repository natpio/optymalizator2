import streamlit as st
import json
import plotly.graph_objects as go
import math
import pandas as pd

# --- 0. KONFIGURACJA STRONY (Musi być pierwszą komendą Streamlit) ---
st.set_page_config(page_title="Logistics Dept - Planer", layout="wide")

# --- 1. ZABEZPIECZENIA ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 Logistics Department")
        st.subheader("Planer Transportu - Logowanie")

        try:
            # Pobieranie hasła ze Streamlit Secrets
            master_password = str(st.secrets["password"])
        except Exception:
            st.error("🔒 Brak konfiguracji hasła głównego w Streamlit Secrets (wymagany wpis 'password').")
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

# --- 2. KONFIGURACJA POJAZDÓW I POMOCNICZE ---
VEHICLES = {
    "BUS": {"maxWeight": 1100, "L": 450, "W": 150, "H": 245},
    "6m": {"maxWeight": 3500, "L": 600, "W": 245, "H": 245},
    "7m": {"maxWeight": 7000, "L": 700, "W": 245, "H": 245},
    "FTL": {"maxWeight": 24000, "L": 1360, "W": 245, "H": 265}
}

COLOR_PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]

def load_products():
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return sorted(data, key=lambda x: x.get('name', 'Nienazwany'))
    except FileNotFoundError:
        st.warning("Nie znaleziono pliku products.json. Używam pustej listy.")
        return []
    except Exception as e:
        st.error(f"Błąd ładowania produktów: {e}")
        return []

# --- 3. LOGIKA PAKOWANIA ---
def pack_one_vehicle(remaining_cases, vehicle):
    placed_stacks = []
    not_placed = []
    current_weight = 0
    current_x = 0
    current_y = 0
    max_w_row = 0

    # Sortowanie po powierzchni dla lepszego upakowania
    remaining_cases = sorted(remaining_cases, key=lambda x: x['width'] * x['length'], reverse=True)

    for case in remaining_cases:
        if current_weight + case['weight'] > vehicle['maxWeight']:
            not_placed.append(case)
            continue

        added = False
        # Próba sztaplowania (stacking)
        if case.get('canStack', True):
            for s in placed_stacks:
                if (s['canStackBase'] and 
                    case['width'] == s['width'] and 
                    case['length'] == s['length'] and 
                    (s['currentH'] + case['height']) <= vehicle['H']):
                    
                    item_copy = case.copy()
                    item_copy['z_pos'] = s['currentH']
                    s['items'].append(item_copy)
                    s['currentH'] += case['height']
                    current_weight += case['weight']
                    added = True
                    break
        
        if not added:
            # Sprawdzenie czy wejdzie w nowym rzędzie (oś Y)
            if current_y + case['length'] > vehicle['W']:
                current_y = 0
                current_x += max_w_row
                max_w_row = 0
            
            # Sprawdzenie czy wejdzie w osi X
            if current_x + case['width'] <= vehicle['L']:
                item_copy = case.copy()
                item_copy['z_pos'] = 0
                placed_stacks.append({
                    'x': current_x, 
                    'y': current_y, 
                    'width': case['width'], 
                    'length': case['length'],
                    'currentH': case['height'], 
                    'canStackBase': case.get('canStack', True),
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
            dx, dy, dz = item['width'], item['length'], item['height']
            
            # Definicja prostopadłościanu
            fig.add_trace(go.Mesh3d(
                x=[x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0],
                y=[y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy],
                z=[z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz],
                i=[7,0,0,0,4,4,6,6,4,0,3,2], 
                j=[3,4,1,2,5,6,5,2,0,1,6,3], 
                k=[0,7,2,3,6,7,1,1,5,5,7,6],
                opacity=0.8, 
                color=color_map.get(item['name'], "#808080"), 
                name=item['name'], 
                showlegend=True
            ))
            
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[0, vehicle['L']], title="Długość (cm)"),
            yaxis=dict(range=[0, vehicle['W']], title="Szerokość (cm)"),
            zaxis=dict(range=[0, vehicle['H']], title="Wysokość (cm)"),
            aspectmode='manual',
            aspectratio=dict(x=vehicle['L']/vehicle['W'], y=1, z=vehicle['H']/vehicle['W'])
        ),
        margin=dict(l=0, r=0, b=0, t=30),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    return fig

# --- 5. INTERFEJS GŁÓWNY ---
if check_password():
    st.title("🚛 Logistics Dept: Planer Transportu")
    
    # Inicjalizacja stanów
    if 'cargo' not in st.session_state: 
        st.session_state.cargo = []
    
    prods = load_products()
    if 'color_map' not in st.session_state:
        st.session_state.color_map = {p['name']: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, p in enumerate(prods)}

    # --- PANEL BOCZNY ---
    with st.sidebar:
        st.header("1. Konfiguracja")
        v_name = st.selectbox("Wybierz pojazd:", list(VEHICLES.keys()))
        veh = VEHICLES[v_name]
        
        st.divider()
        st.header("2. Dodaj Sprzęt")
        selected_p_name = st.selectbox("Produkt:", [p['name'] for p in prods], index=None, placeholder="Wybierz produkt...")
        qty = st.number_input("Liczba sztuk:", min_value=1, value=1)
        
        if st.button("Dodaj do planu", use_container_width=True):
            if selected_p_name:
                p_data = next(p for p in prods if p['name'] == selected_p_name)
                ipc = p_data.get('itemsPerCase', 1)
                
                # Obliczanie liczby skrzyń
                num_cases = math.ceil(qty / ipc)
                new_items = []
                for i in range(num_cases):
                    c = p_data.copy()
                    # Ostatnia skrzynia może być niepełna
                    if i == num_cases - 1 and qty % ipc != 0:
                        c['actual_items'] = qty % ipc
                    else:
                        c['actual_items'] = ipc
                    new_items.append(c)
                
                st.session_state.cargo.extend(new_items)
                st.success(f"Dodano {qty} szt. produktu {selected_p_name}")
                st.rerun()
        
        if st.button("Wyczyść plan", use_container_width=True, type="secondary"):
            st.session_state.cargo = []
            st.rerun()

    # --- GŁÓWNY WIDOK ---
    if st.session_state.cargo:
        # 1. Edycja Listy
        with st.expander("📝 Edytuj listę ładunkową", expanded=False):
            df_cargo = pd.DataFrame(st.session_state.cargo)
            summary = df_cargo.groupby('name').agg({'actual_items': 'sum'}).reset_index()
            
            edited_summary = st.data_editor(
                summary,
                column_config={
                    "name": "Produkt",
                    "actual_items": st.column_config.NumberColumn("Łączna liczba sztuk", min_value=0)
                },
                disabled=["name"],
                hide_index=True,
                use_container_width=True,
                key="editor_v1"
            )

            if st.button("Zaktualizuj ilości"):
                updated_cargo = []
                for _, row in edited_summary.iterrows():
                    if row['actual_items'] > 0:
                        orig_p = next(p for p in prods if p['name'] == row['name'])
                        ipc = orig_p.get('itemsPerCase', 1)
                        num_c = math.ceil(row['actual_items'] / ipc)
                        for i in range(num_c):
                            new_c = orig_p.copy()
                            if i == num_c - 1 and row['actual_items'] % ipc != 0:
                                new_c['actual_items'] = row['actual_items'] % ipc
                            else:
                                new_c['actual_items'] = ipc
                            updated_cargo.append(new_c)
                st.session_state.cargo = updated_cargo
                st.rerun()

        # 2. Obliczenia Fleet Management (podział na auta)
        rem = [dict(c) for c in st.session_state.cargo]
        fleet = []
        while rem:
            stacks, weight, not_p = pack_one_vehicle(rem, veh)
            if not stacks and not_p: # Zabezpieczenie przed nieskończoną pętlą jeśli coś jest za duże
                st.error(f"⚠️ Produkt {not_p[0]['name']} jest za duży dla pojazdu {v_name}!")
                break
            fleet.append({"stacks": stacks, "weight": weight})
            rem = not_p

        # 3. Wyświetlanie Wyników
        st.header(f"📊 Wynik planowania: {len(fleet)} pojazd(ów)")
        
        for i, res in enumerate(fleet):
            with st.container(border=True):
                st.subheader(f"Pojazd #{i+1} ({v_name})")
                c1, c2 = st.columns([3, 2])
                
                with c1:
                    st.plotly_chart(draw_3d(res['stacks'], veh, st.session_state.color_map), 
                                  use_container_width=True, 
                                  key=f"plot_{i}")
                
                with c2:
                    # Statystyki pojazdu
                    total_items = sum(item['actual_items'] for s in res['stacks'] for item in s['items'])
                    floor_area = sum(s['width'] * s['length'] for s in res['stacks'])
                    veh_area = veh['L'] * veh['W']
                    
                    st.metric("Waga ładunku", f"{res['weight']} kg", f"{res['weight'] - veh['maxWeight']} kg" if res['weight'] > veh['maxWeight'] else "")
                    st.progress(min(res['weight'] / veh['maxWeight'], 1.0))
                    
                    st.write(f"**Wykorzystanie powierzchni:** {int((floor_area/veh_area)*100)}%")
                    st.write(f"**Liczba skrzyń:** {sum(len(s['items']) for s in res['stacks'])}")
                    st.write(f"**Łącznie sztuk sprzętu:** {total_items}")
                    
                    # Tabela detali
                    all_items_in_veh = [item for s in res['stacks'] for item in s['items']]
                    details_df = pd.DataFrame(all_items_in_veh).groupby('name').agg({'actual_items': 'sum', 'weight': 'sum'})
                    st.dataframe(details_df, use_container_width=True)

    else:
        st.info("Planer jest pusty. Dodaj produkty z panelu bocznego, aby rozpocząć symulację załadunku.")
