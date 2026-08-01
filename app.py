import streamlit as st
import pandas as pd
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from PIL import Image
import os

# Configuration
# PASSWORD = "negozio2026"  # Change this to your desired password (disabled for now)
PASSWORD = None  # Set to None to disable password authentication
SMARTPHONE_CSV_FILE = "databases/database_smartphone.csv"
SMARTWATCH_CSV_FILE = "databases/database_smartwatch.csv"
TABLET_CSV_FILE = "databases/database_tablet.csv"
NOTEBOOK_CSV_FILE = "databases/database_notebook.csv"
SERVICES_CSV_FILE = "databases/database_servizi.csv"
APP_VERSION = "2.0"  # Version to verify deployment

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = PASSWORD is None  # Auto-authenticate if password is disabled
if 'current_section' not in st.session_state:
    st.session_state.current_section = 'phones'  # 'phones' or 'services'
if 'selected_brand' not in st.session_state:
    st.session_state.selected_brand = None
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = None
if 'selected_variant' not in st.session_state:
    st.session_state.selected_variant = None
if 'selected_memory' not in st.session_state:
    st.session_state.selected_memory = None
if 'model_has_single_memory' not in st.session_state:
    st.session_state.model_has_single_memory = False
if 'skipped_color_selection' not in st.session_state:
    st.session_state.skipped_color_selection = False
# Services section state
if 'services_category' not in st.session_state:
    st.session_state.services_category = None
if 'services_subcategory' not in st.session_state:
    st.session_state.services_subcategory = None
if 'selected_service' not in st.session_state:
    st.session_state.selected_service = None

def load_database(category=None):
    """Load phone database from appropriate CSV file based on category"""
    try:
        if category is None:
            # Load all databases and combine them
            dfs = []
            for csv_file, cat_name in [(SMARTPHONE_CSV_FILE, 'Smartphone'), 
                                        (SMARTWATCH_CSV_FILE, 'Smartwatch'),
                                        (TABLET_CSV_FILE, 'Tablet'),
                                        (NOTEBOOK_CSV_FILE, 'Notebook')]:
                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file, dtype={'Codice_PIM': str})
                    dfs.append(df)
            if dfs:
                return pd.concat(dfs, ignore_index=True)
            else:
                st.error("Nessun database trovato")
                return None
        else:
            # Load specific database based on category
            csv_file = None
            if category == 'Smartphone':
                csv_file = SMARTPHONE_CSV_FILE
                required_columns = ['Marca', 'Tipo', 'Modello', 'Memoria', 'Colore', 'Codice_PIM']
            elif category == 'Smartwatch':
                csv_file = SMARTWATCH_CSV_FILE
                required_columns = ['Marca', 'Tipo', 'Modello', 'mm', 'Colore', 'Codice_PIM']
            elif category == 'Tablet':
                csv_file = TABLET_CSV_FILE
                required_columns = ['Marca', 'Tipo', 'Modello', 'Memoria', 'Codice_PIM']
            elif category == 'Notebook':
                csv_file = NOTEBOOK_CSV_FILE
                required_columns = ['Marca', 'Tipo', 'Modello', 'Memoria', 'pollici', 'Codice_PIM']
            else:
                st.error(f"Categoria non valida: {category}")
                return None
            
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file, dtype={'Codice_PIM': str})
                # Ensure required columns exist
                for col in required_columns:
                    if col not in df.columns:
                        st.error(f"Colonna mancante nel CSV {csv_file}: {col}")
                        return None
                return df
            else:
                st.error(f"File {csv_file} non trovato")
                return None
    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return None

def load_services_database():
    """Load services database from CSV file"""
    try:
        if os.path.exists(SERVICES_CSV_FILE):
            df = pd.read_csv(SERVICES_CSV_FILE, dtype={'Codice': str})
            required_columns = ['Categoria', 'Sottocategoria', 'Servizio', 'Codice', 'Costo']
            for col in required_columns:
                if col not in df.columns:
                    st.error(f"Colonna mancante nel CSV servizi: {col}")
                    return None
            return df
        else:
            st.error(f"File {SERVICES_CSV_FILE} non trovato")
            return None
    except Exception as e:
        st.error(f"Errore nel caricamento del database servizi: {e}")
        return None

def generate_barcode(pim_code, text=None):
    """Generate ITF-25 barcode image with 6-digit PIM code"""
    try:
        # Remove decimal point and convert to string
        pim_code = str(pim_code).replace('.', '').replace(',', '')
        
        # Create ITF (Interleaved 2 of 5) barcode
        itf = barcode.get_barcode_class('itf')
        barcode_obj = itf(pim_code, writer=ImageWriter())
        
        # Generate barcode with custom options for better readability
        options = {
            'module_width': 0.4,  # Width of each bar
            'module_height': 15.0,  # Height of bars
            'font_size': 14,  # Font size for text below barcode
            'text_distance': 5.0,  # Distance between barcode and text
            'quiet_zone': 6.5,  # White space around barcode
        }
        
        # Save to BytesIO
        buffer = BytesIO()
        barcode_obj.write(buffer, options=options)
        buffer.seek(0)
        
        # Open with PIL and convert to RGB
        img = Image.open(buffer)
        img = img.convert('RGB')
        
        return img
    except Exception as e:
        st.error(f"Errore nella generazione del codice a barre: {e}")
        return None

def login_page():
    """Display login page"""
    st.title("🔐 Accesso Negozio")
    st.markdown("---")
    
    password = st.text_input("Inserisci la password:", type="password", key="password_input")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Accedi", width='stretch'):
            if password == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Password errata! Riprova.")

def main_app():
    """Display main application"""
    # Section selector
    st.title("📱 Catalogo Dispositivi")
    st.caption(f"Versione: {APP_VERSION}")
    st.markdown("---")
    
    # CSS for active button highlighting
    if st.session_state.current_section == 'phones':
        st.markdown("""
            <style>
            div[data-testid="stButton"] > button[kind="primary"] {
                background-color: #1f77b4 !important;
            }
            </style>
        """, unsafe_allow_html=True)
    elif st.session_state.current_section == 'services':
        st.markdown("""
            <style>
            div[data-testid="stButton"] > button[kind="primary"] {
                background-color: #1f77b4 !important;
            }
            </style>
        """, unsafe_allow_html=True)
    
    # Search bar
    if 'search_counter' not in st.session_state:
        st.session_state.search_counter = 0
    
    col_search, col_clear = st.columns([9, 1])
    with col_search:
        search_query = st.text_input("🔍 Cerca prodotto (modello, marca o codice PIM):", key=f"search_bar_{st.session_state.search_counter}")
    with col_clear:
        st.markdown("""
            <style>
            div[data-testid="stVerticalBlock"] > div > div > div[data-testid="stButton"] {
                margin-top: 1.6rem;
            }
            </style>
        """, unsafe_allow_html=True)
        if st.button("✖️", key="clear_search", help="Cancella ricerca", use_container_width=True):
            st.session_state.search_counter += 1
            st.rerun()
    
    if search_query:
        show_search_results(search_query)
        st.markdown("---")
    
    # Navigation buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.session_state.current_section == 'phones':
            if st.button("📱 Dispositivi", key="nav_phones", type="primary", width='stretch', use_container_width=True):
                st.session_state.current_section = 'phones'
                st.rerun()
        else:
            if st.button("📱 Dispositivi", key="nav_phones", width='stretch', use_container_width=True):
                st.session_state.current_section = 'phones'
                st.rerun()
    with col2:
        if st.session_state.current_section == 'services':
            if st.button("🔧 Servizi e Software", key="nav_services", type="primary", width='stretch', use_container_width=True):
                st.session_state.current_section = 'services'
                st.rerun()
        else:
            if st.button("🔧 Servizi e Software", key="nav_services", width='stretch', use_container_width=True):
                st.session_state.current_section = 'services'
                st.rerun()
    
    # Route to appropriate section
    if st.session_state.current_section == 'services':
        services_app()
    else:
        phones_app()
    
    st.markdown("---")
    
    # Back button, Home and Logout
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("⬅️ Indietro", width='stretch'):
            if st.session_state.current_section == 'services':
                go_back_services()
            else:
                go_back()
    with col2:
        if st.button("🏠 Home", width='stretch'):
            reset_all_state()
            st.rerun()
    with col3:
        if st.button("🚪 Logout", width='stretch'):
            st.session_state.authenticated = False
            reset_all_state()
            st.rerun()

def reset_all_state():
    """Reset all session state variables"""
    st.session_state.current_section = 'phones'
    st.session_state.selected_brand = None
    st.session_state.selected_category = None
    st.session_state.selected_model = None
    st.session_state.selected_memory = None
    st.session_state.selected_variant = None
    st.session_state.model_has_single_memory = False
    st.session_state.skipped_color_selection = False
    st.session_state.services_category = None
    st.session_state.services_subcategory = None
    st.session_state.selected_service = None

def phones_app():
    """Display phones section"""
    # Load database
    df = load_database()
    
    if df is None:
        st.warning("Impossibile caricare il database. Assicurati che il file CSV esista.")
        return
    
    # Navigation logic
    if st.session_state.selected_variant:
        # Show final view with barcode
        show_variant_view(df)
    elif st.session_state.selected_memory:
        # Show colors for selected memory
        show_colors_view(df)
    elif st.session_state.selected_model:
        # Show memories for selected model (or colors if only one memory)
        show_memories_view(df)
    elif st.session_state.selected_category:
        # Show models for selected category
        show_models_view(df)
    elif st.session_state.selected_brand:
        # Show categories for selected brand
        show_categories_view(df)
    else:
        # Show brands
        show_brands_view(df)

def services_app():
    """Display services section"""
    # Load services database
    df = load_services_database()
    
    if df is None:
        st.warning("Impossibile caricare il database servizi. Assicurati che il file CSV esista.")
        return
    
    # Navigation logic
    if st.session_state.selected_service:
        # Show final view with barcode
        show_service_view(df)
    elif st.session_state.services_subcategory:
        # Show services for selected subcategory
        show_services_view(df)
    elif st.session_state.services_category:
        # Show subcategories for selected category
        show_subcategories_view(df)
    else:
        # Show categories
        show_services_categories_view(df)

def go_back():
    """Navigate back in the hierarchy"""
    if st.session_state.selected_variant:
        st.session_state.selected_variant = None
        # If color selection was skipped, also reset memory to go back to model view
        if st.session_state.skipped_color_selection:
            st.session_state.skipped_color_selection = False
            if st.session_state.model_has_single_memory:
                st.session_state.selected_memory = None
                st.session_state.selected_model = None
            else:
                st.session_state.selected_memory = None
    elif st.session_state.selected_memory:
        # If model has single memory, skip memory view and go directly to model
        if st.session_state.model_has_single_memory:
            st.session_state.selected_memory = None
            st.session_state.selected_model = None
        else:
            st.session_state.selected_memory = None
    elif st.session_state.selected_model:
        st.session_state.selected_model = None
        st.session_state.model_has_single_memory = False
    elif st.session_state.selected_category:
        st.session_state.selected_category = None
        st.session_state.model_has_single_memory = False
    elif st.session_state.selected_brand:
        st.session_state.selected_brand = None
        st.session_state.model_has_single_memory = False
    st.rerun()

def go_back_services():
    """Navigate back in the services hierarchy"""
    if st.session_state.selected_service:
        st.session_state.selected_service = None
    elif st.session_state.services_subcategory:
        # Check if the category has only one subcategory (like Software)
        # If so, skip subcategory view and go directly to category selection
        df = load_services_database()
        if df is not None and st.session_state.services_category:
            category_df = df[df['Categoria'] == st.session_state.services_category]
            subcategories = category_df['Sottocategoria'].drop_duplicates()
            subcategories = [s for s in subcategories if pd.notna(s) and s != '']
            if len(subcategories) == 1:
                # Only one subcategory, skip to category selection
                st.session_state.services_subcategory = None
                st.session_state.services_category = None
            else:
                # Multiple subcategories, go back to subcategory view
                st.session_state.services_subcategory = None
        else:
            st.session_state.services_subcategory = None
    elif st.session_state.services_category:
        st.session_state.services_category = None
    st.rerun()

def show_brands_view(df):
    """Display all brands as buttons"""
    st.subheader("Seleziona Marchio")
    
    brands = df['Marca'].unique()
    
    # Linear view for mobile
    for idx, brand in enumerate(brands):
        if st.button(brand, key=f"brand_{brand}", width='stretch'):
            st.session_state.selected_brand = brand
            st.rerun()

def show_categories_view(df):
    """Display categories for selected brand"""
    brand = st.session_state.selected_brand
    st.subheader(f"{brand} - Seleziona Categoria")
    
    # Load all databases to get available categories for this brand
    all_categories = set()
    for csv_file, cat_name in [(SMARTPHONE_CSV_FILE, 'Smartphone'), 
                                (SMARTWATCH_CSV_FILE, 'Smartwatch'),
                                (TABLET_CSV_FILE, 'Tablet'),
                                (NOTEBOOK_CSV_FILE, 'Notebook')]:
        if os.path.exists(csv_file):
            cat_df = pd.read_csv(csv_file, dtype={'Codice_PIM': str})
            brand_cat_df = cat_df[cat_df['Marca'] == brand]
            if not brand_cat_df.empty:
                all_categories.add(cat_name)
    
    # Define desired order
    desired_order = ['Smartphone', 'Smartwatch', 'Tablet', 'Notebook']
    categories = [cat for cat in desired_order if cat in all_categories]
    
    # If only one category, skip to models
    if len(categories) == 1:
        st.session_state.selected_category = categories[0]
        st.rerun()
        return
    
    # Category emojis
    category_emojis = {
        'Smartphone': '📱',
        'Smartwatch': '⌚',
        'Tablet': '📱',
        'Notebook': '💻'
    }
    
    # Linear view for mobile
    for idx, category in enumerate(categories):
        emoji = category_emojis.get(category, '📱')
        category_name = f"{emoji} {category.capitalize()}"
        if st.button(category_name, key=f"cat_{category}", width='stretch'):
            st.session_state.selected_category = category
            st.rerun()

def show_models_view(df):
    """Display models for selected brand and category"""
    brand = st.session_state.selected_brand
    category = st.session_state.selected_category
    st.subheader(f"{brand} - {category.capitalize()}")
    
    # Load specific database for this category
    category_df = load_database(category)
    if category_df is None:
        st.warning(f"Impossibile caricare il database per {category}")
        return
    
    # Filter by brand
    category_df = category_df[category_df['Marca'] == brand]
    
    models = category_df['Modello'].drop_duplicates()
    
    # Category emojis for model buttons
    category_emojis = {
        'Smartphone': '📲',
        'Smartwatch': '⌚',
        'Tablet': '📱',
        'Notebook': '💻'
    }
    model_emoji = category_emojis.get(category, '📲')
    
    # Use simple sequential rendering to ensure consistent order across devices
    for idx, model in enumerate(models):
        if st.button(f"{model_emoji} {model}", key=f"model_{idx}", width='stretch'):
            st.session_state.selected_model = model
            # Check if model has single spec based on category
            model_df = category_df[category_df['Modello'] == model]
            if category == 'Smartwatch':
                spec_column = 'mm'
            elif category == 'Notebook':
                spec_column = 'pollici'
            else:
                spec_column = 'Memoria'
            
            specs = model_df[spec_column].dropna().unique()
            specs = [s for s in specs if s and str(s).strip() != '' and str(s).strip().lower() != 'n/n']
            st.session_state.model_has_single_memory = (len(specs) <= 1)
            st.rerun()

def show_memories_view(df):
    """Display memory options for selected model (or mm for smartwatch, pollici for notebook)"""
    category = st.session_state.selected_category
    
    # Load specific database for this category
    category_df = load_database(category)
    if category_df is None:
        st.warning(f"Impossibile caricare il database per {category}")
        return
    
    brand_model_df = category_df[
        (category_df['Marca'] == st.session_state.selected_brand) & 
        (category_df['Modello'] == st.session_state.selected_model)
    ]
    
    # Determine which column to use based on category
    if category == 'Smartwatch':
        spec_column = 'mm'
        spec_label = 'Dimensioni'
        spec_emoji = '⌚'
    elif category == 'Notebook':
        spec_column = 'pollici'
        spec_label = 'Dimensioni'
        spec_emoji = '💻'
    else:
        spec_column = 'Memoria'
        spec_label = 'Memoria'
        spec_emoji = '💾'
    
    # Filter out empty/NaN memories and "n/n" (not applicable)
    memories = brand_model_df[spec_column].dropna().unique()
    memories = [m for m in memories if m and str(m).strip() != '' and str(m).strip().lower() != 'n/n']
    
    # If no valid memories or only one, skip directly to colors (or next step)
    if len(memories) <= 1:
        # Use empty string for memory if no valid memories (product has only "n/n")
        st.session_state.selected_memory = memories[0] if len(memories) == 1 else 'n/n'
        st.rerun()
    
    # Show memory options
    st.subheader(f"Modello: {st.session_state.selected_model}")
    
    # Linear view for mobile
    for idx, memory in enumerate(memories):
        if st.button(f"{spec_emoji} {memory}", key=f"memory_{idx}", width='stretch'):
            st.session_state.selected_memory = memory
            st.rerun()

def show_colors_view(df):
    """Display color options for selected memory with color swatches (or pollici for notebook)"""
    st.subheader(f"Modello: {st.session_state.selected_model}")
    
    category = st.session_state.selected_category
    
    # Load specific database for this category
    category_df = load_database(category)
    if category_df is None:
        st.warning(f"Impossibile caricare il database per {category}")
        return
    
    # Show memory/pollici/mm only if it's not empty
    if st.session_state.selected_memory and str(st.session_state.selected_memory).strip():
        if category == 'Smartwatch':
            st.write(f"**Dimensioni:** {st.session_state.selected_memory}")
        elif category == 'Notebook':
            st.write(f"**Dimensioni:** {st.session_state.selected_memory}")
        else:
            st.write(f"**Memoria:** {st.session_state.selected_memory}")
    
    # For notebook, skip color selection and go directly to barcode
    if category == 'Notebook':
        brand_model_df = category_df[
            (category_df['Marca'] == st.session_state.selected_brand) & 
            (category_df['Modello'] == st.session_state.selected_model)
        ]
        # Filter by pollici if selected
        if st.session_state.selected_memory and str(st.session_state.selected_memory).strip() and str(st.session_state.selected_memory).strip().lower() != 'n/n':
            brand_model_df = brand_model_df[brand_model_df['pollici'] == st.session_state.selected_memory]
        
        if not brand_model_df.empty:
            st.session_state.selected_variant = brand_model_df.iloc[0].to_dict()
            st.session_state.skipped_color_selection = True
            st.rerun()
            return
    
    # Filter by brand and model
    brand_model_df = category_df[
        (category_df['Marca'] == st.session_state.selected_brand) & 
        (category_df['Modello'] == st.session_state.selected_model)
    ]
    
    # Determine which column to use for filtering based on category
    if category == 'Smartwatch':
        filter_column = 'mm'
    elif category == 'Notebook':
        filter_column = 'pollici'
    else:
        filter_column = 'Memoria'
    
    # Check if product has only "n/n" in the filter column (no valid values)
    if filter_column in brand_model_df.columns:
        valid_memories = brand_model_df[filter_column].apply(lambda x: str(x).strip().lower() != 'n/n')
        has_only_n_n = not valid_memories.any()
    else:
        has_only_n_n = False
    
    # If filter value is selected and not empty (and not "n/n"), filter by it
    memory = str(st.session_state.selected_memory).strip() if st.session_state.selected_memory else ''
    if memory and memory.lower() != 'n/n' and filter_column in brand_model_df.columns:
        brand_model_memory_df = brand_model_df[brand_model_df[filter_column] == memory]
    elif has_only_n_n:
        # If product has only "n/n" values, show all of them (don't filter out)
        brand_model_memory_df = brand_model_df
    else:
        # If no filter value selected but product has valid values, filter out "n/n"
        if filter_column in brand_model_df.columns:
            brand_model_memory_df = brand_model_df[valid_memories]
        else:
            brand_model_memory_df = brand_model_df
    
    # Safety check: if no results, show all variants
    if brand_model_memory_df.empty:
        brand_model_memory_df = brand_model_df
    
    # If still empty after safety check, show error message
    if brand_model_memory_df.empty:
        st.warning("Nessuna variante disponibile per questo prodotto.")
        return
    
    # Check if all colors are "n/n" - if so, skip directly to barcode
    # Only check colors if the column exists (tablets and notebooks don't have colors)
    if 'Colore' in brand_model_memory_df.columns:
        colors = brand_model_memory_df['Colore'].unique()
        all_n_n = all(str(c).strip().lower() == 'n/n' for c in colors)
        if all_n_n and len(colors) == 1:
            # Automatically select the variant and skip to barcode
            st.session_state.selected_variant = brand_model_memory_df.iloc[0].to_dict()
            st.session_state.skipped_color_selection = True
            st.rerun()
            return
    else:
        # No color column, skip directly to barcode
        st.session_state.selected_variant = brand_model_memory_df.iloc[0].to_dict()
        st.session_state.skipped_color_selection = True
        st.rerun()
        return
    
    # Color mapping for common colors
    color_map = {
        'black': '#000000',
        'white': '#FFFFFF',
        'red': '#FF0000',
        'blue': '#0000FF',
        'green': '#00FF00',
        'yellow': '#FFFF00',
        'orange': '#FFA500',
        'purple': '#800080',
        'pink': '#FFC0CB',
        'gray': '#808080',
        'grey': '#808080',
        'silver': '#C0C0C0',
        'gold': '#FFD700',
        'brown': '#A52A2A',
        'beige': '#F5F5DC',
        'cream': '#FFFDD0',
        'ivory': '#FFFFF0',
        'lavender': '#E6E6FA',
        'rose': '#FF007F',
        'obsidian': '#0B0B0B',
        'charcoal': '#36454F',
        'titanium black': '#1A1A1A',
        'titanium gray': '#4A4A4A',
        'natural titanium': '#B8B8B8',
        'blue titanium': '#4169E1',
        'deep purple': '#4B0082',
        'icy blue': '#87CEEB',
        'flowy emerald': '#50C878',
        'cool gray': '#8C92AC',
        'asteroid black': '#1C1C1C',
        'titanium charcoal': '#2C2C2C',
        'tundra umber': '#5C4033',
        'canyon orange': '#E86A17',
        'aurora white': '#F0F8FF',
        'twilight black': '#1A1A2E',
        'aurora blue': '#87CEFA',
        'dusk black': '#2F2F2F',
        'navy': '#000080',
        'mint': '#98FF98',
        'jetblack': '#1A1A1A',
        'icyblue': '#87CEEB',
        'silver shadow': '#C0C0C0',
        'black blue': '#1A2A3A',
        'cobalt violet': '#6B2E9E',
        'sky blue': '#87CEEB',
        'titanium silverblue': '#708090',
        'titanium gray': '#4A4A4A',
        'titanium whitesilver': '#E8E8E8',
        'light green': '#90EE90',
        'awesome charcoal': '#36454F',
        'awesome lavender': '#E6E6FA',
        'awesome white': '#FFFFFF',
        'awesome graygreen': '#8FBC8F',
        'awesome navy': '#000080',
        'awesome lilac': '#C8A2C8',
        'awesome icyblue': '#87CEEB',
        'awesome gray': '#808080',
        'violet shadow': '#7B68EE',
        'graphite': '#383838',
        'pink gold': '#E6C8C8',
        'titanium silver': '#C0C0C0',
        # OPPO specific colors
        'crystal blue': '#E0FFFF',
        'crystal black': '#1A1A1A',
        'black purple': '#4B0082',
        'ice blue': '#87CEEB',
        'aurora gold': '#fdd4be',
        # Motorola specific colors
        'denim blue': '#1560BD',
        'forest green': '#228B22',
        'arabesque': '#8B4513',
        'viola': '#EE82EE',
        'oro': '#FFD700',
        'bronze green': '#5C7A68',
        'lily pad': '#4A7C59',
        'scarab': '#1A4D2E',
        'pantone corsair': '#006994',
        'pantone regatta': '#005F7F',
        'pantone black oyster': '#1C1C1C',
        'pantone gray mist': '#A9A9A9',
        'pantone carbon': '#36454F',
        'pantone martini olive': '#556B2F',
        'pantone hematite': '#2F2F2F',
        'pantone sporting green': '#2E8B57',
        'pantone mountain view': '#4A5D23',
        'pantone blackened blue': '#1A237E',
        'pantone lily white': '#F8F8FF',
        # Italian color variants
        'blu': '#0000FF',
        'lavanda': '#E6E6FA',
        # Google Pixel specific colors
        'nero ossidiana': '#0B0B0B',
        'viola glicine': '#CCCCFF',
        'blu indaco': '#6495ED',
        'verde cedro': '#ADFF2F',
        'viola lavanda': '#9370DB',
        'grigio nebbia': '#E0E6E9',
        'green': '#C1E1C1',
        'forest green': '#3A4D39',
        'dark grey': '#4F4F4F',
    }
    
    # Linear view for mobile
    for idx, row in brand_model_memory_df.iterrows():
        color_name = row['Colore'].lower()
        
        # Try to get color from mapping, otherwise use default gray
        hex_color = color_map.get(color_name, '#CCCCCC')
        st.markdown(f"""
            <div style="background-color: {hex_color}; width: 100px; height: 100px; border-radius: 10px; margin: 0 auto; border: 2px solid #ddd;"></div>
        """, unsafe_allow_html=True)
        
        if st.button(f"🎨 {row['Colore']}", key=f"color_{idx}", width='stretch'):
            st.session_state.selected_variant = row.to_dict()
            st.rerun()

def show_variant_view(df):
    """Display final view with PIM code and barcode"""
    variant = st.session_state.selected_variant
    category = st.session_state.selected_category
    
    st.subheader(f"{variant['Marca']} - {variant['Modello']}")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if category == 'Smartwatch':
            st.write(f"**Dimensioni:** {variant.get('mm', 'N/A')}")
            st.write(f"**Colore:** {variant.get('Colore', 'N/A')}")
        elif category == 'Notebook':
            st.write(f"**Memoria:** {variant.get('Memoria', 'N/A')}")
            st.write(f"**Dimensioni:** {variant.get('pollici', 'N/A')}")
        elif category == 'Tablet':
            st.write(f"**Memoria:** {variant.get('Memoria', 'N/A')}")
        else:  # Smartphone
            st.write(f"**Memoria:** {variant.get('Memoria', 'N/A')}")
            st.write(f"**Colore:** {variant.get('Colore', 'N/A')}")
        st.write(f"**Codice PIM:** {variant['Codice_PIM']}")
    
    with col2:
        # Generate and display barcode
        barcode_img = generate_barcode(str(variant['Codice_PIM']))
        
        if barcode_img is not None:
            st.image(barcode_img, width=400)
            st.success("Codice a barre generato con successo!")

def show_search_results(query):
    """Display search results for products and services matching the query"""
    query_lower = query.lower()
    
    # Search in all phone databases
    phone_results = []
    for csv_file, cat_name in [(SMARTPHONE_CSV_FILE, 'Smartphone'), 
                                (SMARTWATCH_CSV_FILE, 'Smartwatch'),
                                (TABLET_CSV_FILE, 'Tablet'),
                                (NOTEBOOK_CSV_FILE, 'Notebook')]:
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file, dtype={'Codice_PIM': str})
                cat_results = df[
                    df['Modello'].str.lower().str.contains(query_lower, na=False) |
                    df['Marca'].str.lower().str.contains(query_lower, na=False) |
                    df['Codice_PIM'].astype(str).str.contains(query_lower, na=False)
                ]
                if not cat_results.empty:
                    phone_results.append(cat_results)
            except Exception as e:
                st.error(f"Errore nella ricerca in {csv_file}: {e}")
    
    # Combine all phone results
    if phone_results:
        phone_results = pd.concat(phone_results, ignore_index=True)
    else:
        phone_results = None
    
    # Search in services database
    df_services = load_services_database()
    
    service_results = None
    if df_services is not None:
        service_results = df_services[
            df_services['Servizio'].str.lower().str.contains(query_lower, na=False) |
            df_services['Categoria'].str.lower().str.contains(query_lower, na=False) |
            df_services['Sottocategoria'].str.lower().str.contains(query_lower, na=False) |
            df_services['Codice'].astype(str).str.contains(query_lower, na=False)
        ]
    
    # Check if any results found
    has_phone_results = phone_results is not None and not phone_results.empty
    has_service_results = service_results is not None and not service_results.empty
    
    if not has_phone_results and not has_service_results:
        st.info("Nessun prodotto o servizio trovato per la ricerca.")
        return
    
    # Display phone results
    if has_phone_results:
        st.subheader(f"📱 Dispositivi ({len(phone_results)} trovati)")
        for idx, row in phone_results.iterrows():
            with st.expander(f"{row['Marca']} - {row['Modello']} ({row.get('Memoria', '')}, {row.get('Colore', '')})"):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.write(f"**Marca:** {row['Marca']}")
                    st.write(f"**Modello:** {row['Modello']}")
                    st.write(f"**Tipo:** {row['Tipo']}")
                    if 'Memoria' in row:
                        st.write(f"**Memoria:** {row['Memoria']}")
                    if 'mm' in row:
                        st.write(f"**Dimensioni:** {row['mm']}")
                    if 'pollici' in row:
                        st.write(f"**Dimensioni:** {row['pollici']}")
                    if 'Colore' in row:
                        st.write(f"**Colore:** {row['Colore']}")
                    st.write(f"**Codice PIM:** {row['Codice_PIM']}")
                
                with col2:
                    barcode_img = generate_barcode(str(row['Codice_PIM']))
                    if barcode_img is not None:
                        st.image(barcode_img, width=300)
                        st.success("Codice a barre generato!")
    
    # Display service results
    if has_service_results:
        st.subheader(f"🔧 Servizi ({len(service_results)} trovati)")
        for idx, row in service_results.iterrows():
            with st.expander(f"{row['Categoria']} - {row['Servizio']} (€{row['Costo']})"):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.write(f"**Categoria:** {row['Categoria']}")
                    st.write(f"**Sottocategoria:** {row['Sottocategoria']}")
                    st.write(f"**Servizio:** {row['Servizio']}")
                    st.write(f"**Costo:** €{row['Costo']}")
                    st.write(f"**Codice:** {row['Codice']}")
                
                with col2:
                    barcode_img = generate_barcode(str(row['Codice']))
                    if barcode_img is not None:
                        st.image(barcode_img, width=300)
                        st.success("Codice a barre generato!")

def show_services_categories_view(df):
    """Display service categories"""
    st.subheader("Seleziona Categoria")
    
    categories = df['Categoria'].unique()
    
    # Category emojis
    category_emojis = {
        'Servizi Generali': '🔧',
        'Pellicole e protezioni': '🛡️',
        'Software': '💿'
    }
    
    # Linear view for mobile
    for idx, category in enumerate(categories):
        emoji = category_emojis.get(category, '📋')
        if st.button(f"{emoji} {category}", key=f"serv_cat_{idx}", width='stretch'):
            st.session_state.services_category = category
            st.rerun()

def show_subcategories_view(df):
    """Display subcategories for selected category"""
    category = st.session_state.services_category
    st.subheader(f"{category} - Seleziona Sottocategoria")
    
    # Filter by category
    category_df = df[df['Categoria'] == category]
    
    # Get subcategories preserving database order
    subcategories = category_df['Sottocategoria'].drop_duplicates()
    subcategories = [s for s in subcategories if pd.notna(s) and s != '']
    
    # If only one subcategory, skip to services
    if len(subcategories) == 1:
        st.session_state.services_subcategory = subcategories[0]
        st.rerun()
        return
    
    # Subcategory emojis
    subcategory_emojis = {
        'Computer': '💻',
        'Smartphone': '📱',
        'Smartwatch': '⌚',
        'Tablet': '📱',
        'Altro': '📦'
    }
    
    # Linear view for mobile
    for idx, subcategory in enumerate(subcategories):
        emoji = subcategory_emojis.get(subcategory, '📋')
        if st.button(f"{emoji} {subcategory}", key=f"subcat_{idx}", width='stretch'):
            st.session_state.services_subcategory = subcategory
            st.rerun()

def show_services_view(df):
    """Display services for selected subcategory"""
    category = st.session_state.services_category
    subcategory = st.session_state.services_subcategory
    st.subheader(f"{category} - {subcategory}")
    
    # Filter by category and subcategory
    filtered_df = df[(df['Categoria'] == category) & (df['Sottocategoria'] == subcategory)]
    
    # Linear view for mobile - preserves database order
    for idx, row in filtered_df.iterrows():
        service_name = row['Servizio']
        cost = row['Costo']
        if st.button(f"{service_name}\n€{cost}", key=f"service_{idx}", width='stretch'):
            st.session_state.selected_service = row.to_dict()
            st.rerun()

def show_service_view(df):
    """Display final view with service code and barcode"""
    service = st.session_state.selected_service
    
    st.subheader(f"{service['Categoria']} - {service['Servizio']}")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.write(f"**Sottocategoria:** {service['Sottocategoria']}")
        st.write(f"**Servizio:** {service['Servizio']}")
        st.write(f"**Costo:** €{service['Costo']}")
        st.write(f"**Codice:** {service['Codice']}")
    
    with col2:
        # Generate and display barcode
        barcode_img = generate_barcode(str(service['Codice']))
        
        if barcode_img is not None:
            st.image(barcode_img, width=400)
            st.success("Codice a barre generato con successo!")

def main():
    """Main application logic"""
    # Configure page
    st.set_page_config(
        page_title="Barcode Smartphone",
        page_icon="📱",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for mobile optimization
    st.markdown("""
        <style>
        .stApp {
            max-width: 100%;
        }
        .stTextInput > div > div > input {
            font-size: 18px;
            padding: 12px;
        }
        .stButton > button {
            font-size: 16px;
            padding: 12px 24px;
        }
        .stImage {
            display: flex;
            justify-content: center;
        }
        </style>
        <meta name="apple-mobile-web-app-title" content="Barcode Smartphone">
    """, unsafe_allow_html=True)
    
    # Route based on authentication
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()
