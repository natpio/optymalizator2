# --- 5. INTERFEJS ---
if check_password():
    if 'setup' not in st.session_state:
        st.set_page_config(page_title="Logistics Dept", layout="wide")
        st.session_state.setup = True

    st.title("🚛 Logistics Department: Planer Transportu")
    if 'cargo' not in st.session_state: st.session_state.cargo = []
    
    prods = load_products()
    if 'color_map' not in st.session_state:
        st.session_state.color_map = {p['name']: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, p in enumerate(prods)}

    with st.sidebar:
        st.header("1. Pojazd")
        v_name = st.selectbox("Wybierz auto:", list(VEHICLES.keys()))
        veh = VEHICLES[v_name]
        st.divider()
        st.header("2. Sprzęt")
        selected_p = st.selectbox("Produkt:", [p['name'] for p in prods], index=None, placeholder="Szukaj...")
        qty = st.number_input("Sztuk:", min_value=1, value=1)
        
        if st.button("Dodaj do planu", use_container_width=True) and selected_p:
            p_data = next(p for p in prods if p['name'] == selected_p)
            ipc = p_data.get('itemsPerCase', 1)
            # Dodajemy skrzynie dla wybranej ilości
            for i in range(math.ceil(qty/ipc)):
                c = p_data.copy()
                c['actual_items'] = qty % ipc if (i == math.ceil(qty/ipc)-1 and qty % ipc != 0) else ipc
                st.session_state.cargo.append(c)
            st.success(f"Dodano: {selected_p}")
        
        if st.button("Wyczyść wszystko", use_container_width=True):
            st.session_state.cargo = []
            st.rerun()

    # --- EDYCJA LISTY ŁADUNKOWEJ ---
    if st.session_state.cargo:
        st.header("📋 Lista ładunkowa (Edytuj ilości)")
        
        # Przygotowanie danych do edytora (agregacja po nazwie)
        temp_df = pd.DataFrame(st.session_state.cargo)
        cargo_summary = temp_df.groupby('name').agg({'actual_items': 'sum'}).reset_index()
        
        # Interaktywny edytor
        edited_df = st.data_editor(
            cargo_summary,
            column_config={
                "name": "Produkt",
                "actual_items": st.column_config.NumberColumn("Suma sztuk", min_value=0, step=1)
            },
            disabled=["name"],
            hide_index=True,
            use_container_width=True,
            key="cargo_editor"
        )

        # Logika aktualizacji: jeśli wartości w edytorze się zmieniły
        if not edited_df.equals(cargo_summary):
            new_cargo = []
            for _, row in edited_df.iterrows():
                if row['actual_items'] > 0:
                    p_data = next(p for p in prods if p['name'] == row['name'])
                    ipc = p_data.get('itemsPerCase', 1)
                    q = row['actual_items']
                    for i in range(math.ceil(q/ipc)):
                        c = p_data.copy()
                        c['actual_items'] = q % ipc if (i == math.ceil(q/ipc)-1 and q % ipc != 0) else ipc
                        new_cargo.append(c)
            st.session_state.cargo = new_cargo
            st.rerun()

        st.divider()

    # --- WIZUALIZACJA I STATYSTYKI ---
    if st.session_state.cargo:
        rem = sorted([dict(c) for c in st.session_state.cargo], key=lambda x: x['width']*x['length'], reverse=True)
        # ... (reszta kodu bez zmian: pakowanie, rysowanie 3D i statystyki)
