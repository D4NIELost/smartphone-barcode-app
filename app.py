import streamlit as st
import pandas as pd
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from PIL import Image
import os
import hashlib
import secrets
import time
import subprocess

# Configuration
# Generate a secure password hash using: python -c "import hashlib, secrets; salt = secrets.token_hex(16); print(f'SALT={salt}'); print(f'PASSWORD_HASH={hashlib.sha256((\"your_password\" + salt).encode()).hexdigest()}')"
# Replace the values below with your generated salt and hash
SALT = "104400c1965d483e027b4780011d2563"
PASSWORD_HASH = "6a9fd0d08b82c52634eb8d27a80908d5ea9715a8f81edef175057ee991d31fd4"
ADMIN_PASSWORD_ENABLED = True  # Set to True to enable admin password

# Git configuration for manual sync (optional)
# If you want automatic sync, generate a Personal Access Token at: https://github.com/settings/tokens
# Select 'repo' scope and configure the values below
GIT_USERNAME = ""  # Your GitHub username (leave empty for manual sync only)
GIT_TOKEN = ""  # Your GitHub Personal Access Token (leave empty for manual sync only)
AUTO_GIT_SYNC = False  # Set to True to enable automatic git sync (requires credentials above)
SMARTPHONE_CSV_FILE = "databases/database_smartphone.csv"
SMARTWATCH_CSV_FILE = "databases/database_smartwatch.csv"
TABLET_CSV_FILE = "databases/database_tablet.csv"
NOTEBOOK_CSV_FILE = "databases/database_notebook.csv"
SERVICES_CSV_FILE = "databases/database_servizi.csv"
APP_VERSION = "2.2"  # Version to verify deployment

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = True  # Always auto-authenticate for normal app access
if 'admin_authenticated' not in st.session_state:
    st.session_state.admin_authenticated = False
if 'show_admin_login' not in st.session_state:
    st.session_state.show_admin_login = False
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

def verify_password(password):
    """Verify password against hash"""
    if not ADMIN_PASSWORD_ENABLED:
        return True
    if SALT == "YOUR_SALT_HERE" or PASSWORD_HASH == "YOUR_PASSWORD_HASH_HERE":
        st.error("⚠️ Password admin non configurata. Configura SALT e PASSWORD_HASH nel codice.")
        return False
    password_hash = hashlib.sha256((password + SALT).encode()).hexdigest()
    return password_hash == PASSWORD_HASH

def git_commit_and_push(message):
    """Execute git add, commit and push for database changes"""
    try:
        # Check if auto git sync is enabled
        if not AUTO_GIT_SYNC:
            return False, "Sincronizzazione automatica disabilitata. Usa il pulsante 'Sincronizza GitHub' manualmente."
        
        # Check if git credentials are configured
        if not GIT_USERNAME or not GIT_TOKEN:
            return False, "Credenziali Git non configurate. Imposta GIT_USERNAME e GIT_TOKEN in app.py o usa sincronizzazione manuale."
        
        # Get the repository root directory
        repo_root = os.path.dirname(os.path.abspath(__file__))
        
        # Configure git user identity if not set (required for commit)
        subprocess.run(['git', 'config', 'user.email', 'admin@smartphone-barcode-app'], cwd=repo_root, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Admin App'], cwd=repo_root, check=True, capture_output=True)
        
        # Configure git credentials for push
        git_url_with_auth = f"https://{GIT_USERNAME}:{GIT_TOKEN}@github.com/D4NIELost/smartphone-barcode-app.git"
        subprocess.run(['git', 'remote', 'set-url', 'origin', git_url_with_auth], cwd=repo_root, check=True, capture_output=True)
        
        # Add databases folder
        subprocess.run(['git', 'add', 'databases/'], cwd=repo_root, check=True, capture_output=True)
        
        # Commit with message
        subprocess.run(['git', 'commit', '-m', message], cwd=repo_root, check=True, capture_output=True)
        
        # Push to remote
        subprocess.run(['git', 'push'], cwd=repo_root, check=True, capture_output=True)
        
        return True, None
    except subprocess.CalledProcessError as e:
        error_msg = f"Errore git: {e.stderr.decode() if e.stderr else str(e)}"
        return False, error_msg
    except Exception as e:
        return False, f"Errore durante sincronizzazione git: {str(e)}"

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
            if verify_password(password):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Password errata! Riprova.")

def main_app():
    """Display main application"""
    # Section selector
    st.title("📱 Catalogo MW")
    st.caption(f"Versione: {APP_VERSION}")
    
    # Admin icon (small and discreet)
    col_admin = st.columns([10, 1])
    with col_admin[1]:
        if st.button("⚙️", key="admin_icon", help="Accesso Admin"):
            if not st.session_state.admin_authenticated:
                st.session_state.show_admin_login = True
            else:
                st.session_state.current_section = 'admin'
                st.rerun()
    
    st.markdown("---")
    
    # Admin login popup
    if st.session_state.get('show_admin_login', False):
        with st.expander("🔐 Accesso Admin", expanded=True):
            admin_password = st.text_input("Password Admin:", type="password", key="admin_password_input")
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Accedi", key="admin_login_btn"):
                    if verify_password(admin_password):
                        st.session_state.admin_authenticated = True
                        st.session_state.show_admin_login = False
                        st.success("✅ Accesso admin effettuato!")
                        st.rerun()
                    else:
                        st.error("❌ Password errata!")
            with col2:
                if st.button("Annulla", key="admin_cancel_btn"):
                    st.session_state.show_admin_login = False
                    st.rerun()
    
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
    if st.session_state.current_section == 'admin':
        if st.session_state.admin_authenticated:
            admin_app()
        else:
            st.error("⚠️ Accesso non autorizzato")
            st.session_state.current_section = 'phones'
            st.rerun()
    elif st.session_state.current_section == 'services':
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
        # Show logout button only when in admin mode
        if st.session_state.admin_authenticated and st.session_state.current_section == 'admin':
            if st.button("🚪 Esci Admin", width='stretch'):
                st.session_state.admin_authenticated = False
                st.session_state.current_section = 'phones'
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
        'green': '#008000',
        'forest green': '#3A4D39',
        'dark grey': '#4F4F4F',
        # Xiaomi specific colors
        'glacier blue': '#87CEEB',
        'titanio': '#A9A9A9',
        'starlit green': '#4A6B5C',  # Dark teal/green with starlit effect
        'blu': '#0000FF',
        'viola': '#EE82EE',
        'violet': '#8B7B8B',  # 17T Pro violet - muted purple/plum
        # Honor specific colors
        'cyan': '#00FFFF',
        'midnight black': '#1A1A1A',
        'nero': '#000000',
        'grey': '#808080',
        'orange': '#FFA500',
        'red': '#FF0000',
        'pink': '#FFC0CB',
        'purple': '#800080',
        'silver': '#C0C0C0',
        'brown': '#A52A2A',
        # Smartwatch specific colors
        'matte silver': '#C0C0C0',
        'light gold': '#faf7f0',
        'obsidian black': '#0B0B0B',
        'silver gray': '#A9A9A9',
        'juniper green': '#2E8B57',
        'mint green': '#98FF98',
        'sunset gold': '#FFD700',
        # Smartwatch colors with strap info
        'black (fluororubber strap)': '#000000',
        'mint green (fluororubber strap)': '#98FF98',
        'white (leather strap)': '#FFFFFF',
        'sunset gold (milanese strap)': '#FFD700',
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
    
    # Create fuzzy matching patterns (remove vowels for abbreviation matching)
    query_no_vowels = ''.join(c for c in query_lower if c not in 'aeiou')
    
    # Synonym dictionary for common search terms
    synonyms = {
        'opaca': ['matt', 'matte'],
        'opaco': ['matt', 'matte'],
        'privacy': ['antispy'],
        'privato': ['antispy'],
    }
    
    # Get all search terms including synonyms
    search_terms = [query_lower]
    for key, values in synonyms.items():
        if key in query_lower:
            search_terms.extend(values)
    
    def fuzzy_match(text):
        """Check if text matches query - ALL query words must be present"""
        text_lower = str(text).lower()
        text_no_vowels = ''.join(c for c in text_lower if c not in 'aeiou')
        
        # Split query into words
        query_words = query_lower.split()
        if not query_words:
            return False
        
        # ALL words must be present in the text (AND logic)
        for word in query_words:
            word_found = False
            
            # Check direct match
            if word in text_lower:
                word_found = True
            else:
                # Check abbreviation match
                word_no_vowels = ''.join(c for c in word if c not in 'aeiou')
                if word_no_vowels and word_no_vowels in text_no_vowels:
                    word_found = True
            
            # If word not found, check synonyms
            if not word_found:
                for key, values in synonyms.items():
                    if key in word:
                        for synonym in values:
                            if synonym in text_lower:
                                word_found = True
                                break
                if not word_found:
                    return False
        
        return True
    
    # Search in all phone databases
    phone_results = []
    for csv_file, cat_name in [(SMARTPHONE_CSV_FILE, 'Smartphone'), 
                                (SMARTWATCH_CSV_FILE, 'Smartwatch'),
                                (TABLET_CSV_FILE, 'Tablet'),
                                (NOTEBOOK_CSV_FILE, 'Notebook')]:
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file, dtype={'Codice_PIM': str})
                # Combine relevant columns into a single text for each row
                # This allows words to match across different columns (e.g., "honor" in Marca, "400" in Modello)
                def combine_columns(row):
                    parts = []
                    if 'Marca' in row:
                        parts.append(str(row['Marca']))
                    if 'Modello' in row:
                        parts.append(str(row['Modello']))
                    if 'Codice_PIM' in row:
                        parts.append(str(row['Codice_PIM']))
                    return ' '.join(parts)
                
                df['combined_text'] = df.apply(combine_columns, axis=1)
                mask = df['combined_text'].apply(fuzzy_match)
                cat_results = df[mask]
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
        mask = (
            df_services['Servizio'].apply(fuzzy_match) |
            df_services['Categoria'].apply(fuzzy_match) |
            df_services['Sottocategoria'].apply(fuzzy_match) |
            df_services['Codice'].astype(str).apply(fuzzy_match)
        )
        service_results = df_services[mask]
    
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

def admin_app():
    """Display admin interface for database management"""
    st.title("⚙️ Gestione Database")
    st.markdown("---")
    
    # Database selection
    database_options = {
        'Servizi': SERVICES_CSV_FILE,
        'Smartphone': SMARTPHONE_CSV_FILE,
        'Smartwatch': SMARTWATCH_CSV_FILE,
        'Tablet': TABLET_CSV_FILE,
        'Notebook': NOTEBOOK_CSV_FILE
    }
    
    selected_db_name = st.selectbox("📁 Seleziona Database:", list(database_options.keys()))
    selected_db_file = database_options[selected_db_name]
    
    st.info(f"📂 File: `{selected_db_file}`")
    st.markdown("---")
    
    # Load selected database
    try:
        if os.path.exists(selected_db_file):
            df = pd.read_csv(selected_db_file, dtype={'Codice_PIM': str, 'Codice': str})
        else:
            st.error(f"File {selected_db_file} non trovato")
            return
    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return
    
    # Display current database
    st.subheader(f"📋 Database {selected_db_name} Attuale")
    st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    
    # Action selection
    action = st.radio("Seleziona azione:", ["➕ Aggiungi Riga", "✏️ Modifica Riga", "🗑️ Rimuovi Riga"])
    
    columns = df.columns.tolist()
    
    if action == "➕ Aggiungi Riga":
        st.subheader("➕ Aggiungi Nuova Riga")
        
        # Create input fields for each column
        new_row_data = {}
        cols_per_row = 2
        col_groups = [columns[i:i + cols_per_row] for i in range(0, len(columns), cols_per_row)]
        
        for group in col_groups:
            cols = st.columns(len(group))
            for idx, col in enumerate(group):
                with cols[idx]:
                    new_row_data[col] = st.text_input(f"{col}*", placeholder=f"Inserisci {col}", key=f"add_{col}")
        
        if st.button("💾 Salva Nuova Riga"):
            if not all(new_row_data.values()):
                st.error("❌ Tutti i campi sono obbligatori!")
            else:
                try:
                    # Add new row
                    new_row = pd.DataFrame([new_row_data])
                    df = pd.concat([df, new_row], ignore_index=True)
                    df.to_csv(selected_db_file, index=False)
                    
                    # Show success message with visual feedback
                    st.success("✅ Riga aggiunta con successo!")
                    st.balloons()
                    st.toast("Salvataggio completato!", icon="✅")
                    
                    # Try to sync with git if enabled
                    if AUTO_GIT_SYNC:
                        with st.spinner("🔄 Sincronizzazione con GitHub..."):
                            git_success, git_error = git_commit_and_push(f"Aggiunta riga in {selected_db_name}")
                            if git_success:
                                st.success("🚀 Sincronizzazione GitHub completata!")
                            else:
                                st.warning(f"⚠️ Salvataggio locale OK, ma sincronizzazione GitHub fallita: {git_error}")
                    else:
                        st.info("💡 Modifiche salvate localmente. Usa 'Sincronizza GitHub' per inviare a GitHub.")
                    
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Errore durante il salvataggio: {e}")
    
    elif action == "✏️ Modifica Riga":
        st.subheader("✏️ Modifica Riga Esistente")
        
        # Add filter for Marca if available
        filtered_df = df.copy()
        
        if 'Marca' in columns:
            unique_brands = ['Tutte'] + sorted(df['Marca'].unique().tolist())
            selected_brand = st.selectbox("🏷️ Filtra per Marca:", unique_brands, key="edit_filter_brand")
            if selected_brand != 'Tutte':
                filtered_df = filtered_df[filtered_df['Marca'] == selected_brand]
        
        # Select row to edit from filtered results
        if filtered_df.empty:
            st.warning("Nessuna riga trovata con i filtri selezionati")
        else:
            # Map filtered indices back to original dataframe
            filtered_indices = filtered_df.index.tolist()
            row_options = filtered_df.apply(lambda row: " | ".join([f"{col}: {val}" for col, val in row.items()]), axis=1).tolist()
            
            selected_filtered_idx = st.selectbox(
                "Seleziona riga da modificare:", 
                range(len(row_options)), 
                format_func=lambda x: row_options[x][:100] + "..." if len(row_options[x]) > 100 else row_options[x],
                key="edit_row_selector"
            )
            
            if selected_filtered_idx is not None:
                original_idx = filtered_indices[selected_filtered_idx]
                selected_row = df.iloc[original_idx]
                
                # Create input fields for each column with current values
                updated_row_data = {}
                cols_per_row = 2
                col_groups = [columns[i:i + cols_per_row] for i in range(0, len(columns), cols_per_row)]
                
                for group in col_groups:
                    cols = st.columns(len(group))
                    for idx, col in enumerate(group):
                        with cols[idx]:
                            # Use unique key with original index to force refresh
                            updated_row_data[col] = st.text_input(
                                f"{col}", 
                                value=str(selected_row[col]), 
                                key=f"edit_field_{col}_{original_idx}"
                            )
                
                if st.button("💾 Salva Modifiche", key="save_edit_btn"):
                    try:
                        # Update row
                        for col in columns:
                            df.at[original_idx, col] = updated_row_data[col]
                        
                        df.to_csv(selected_db_file, index=False)
                        
                        # Show success message with visual feedback
                        st.success("✅ Riga modificata con successo!")
                        st.balloons()
                        st.toast("Modifiche salvate!", icon="✏️")
                        
                        # Try to sync with git if enabled
                        if AUTO_GIT_SYNC:
                            with st.spinner("🔄 Sincronizzazione con GitHub..."):
                                git_success, git_error = git_commit_and_push(f"Modifica riga in {selected_db_name}")
                                if git_success:
                                    st.success("🚀 Sincronizzazione GitHub completata!")
                                else:
                                    st.warning(f"⚠️ Salvataggio locale OK, ma sincronizzazione GitHub fallita: {git_error}")
                        else:
                            st.info("💡 Modifiche salvate localmente. Usa 'Sincronizza GitHub' per inviare a GitHub.")
                        
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Errore durante il salvataggio: {e}")
    
    elif action == "🗑️ Rimuovi Riga":
        st.subheader("🗑️ Rimuovi Riga")
        
        # Add filter for Marca if available
        filtered_df = df.copy()
        
        if 'Marca' in columns:
            unique_brands = ['Tutte'] + sorted(df['Marca'].unique().tolist())
            selected_brand = st.selectbox("🏷️ Filtra per Marca:", unique_brands, key="remove_filter_brand")
            if selected_brand != 'Tutte':
                filtered_df = filtered_df[filtered_df['Marca'] == selected_brand]
        
        # Select row to remove from filtered results
        if filtered_df.empty:
            st.warning("Nessuna riga trovata con i filtri selezionati")
        else:
            # Map filtered indices back to original dataframe
            filtered_indices = filtered_df.index.tolist()
            row_options = filtered_df.apply(lambda row: " | ".join([f"{col}: {val}" for col, val in row.items()]), axis=1).tolist()
            
            selected_filtered_idx = st.selectbox(
                "Seleziona riga da rimuovere:", 
                range(len(row_options)), 
                format_func=lambda x: row_options[x][:100] + "..." if len(row_options[x]) > 100 else row_options[x],
                key="remove_row_selector"
            )
            
            if selected_filtered_idx is not None:
                original_idx = filtered_indices[selected_filtered_idx]
                selected_row = df.iloc[original_idx]
                row_preview = " | ".join([f"{col}: {val}" for col, val in selected_row.items()])
                st.warning(f"Sei sicuro di voler rimuovere questa riga?\n\n{row_preview[:200]}...")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🗑️ Conferma Rimozione", type="primary", key="confirm_remove_btn"):
                        try:
                            df = df.drop(original_idx).reset_index(drop=True)
                            df.to_csv(selected_db_file, index=False)
                            
                            # Show success message with visual feedback
                            st.success("✅ Riga rimossa con successo!")
                            st.balloons()
                            st.toast("Riga eliminata!", icon="🗑️")
                            
                            # Try to sync with git if enabled
                            if AUTO_GIT_SYNC:
                                with st.spinner("🔄 Sincronizzazione con GitHub..."):
                                    git_success, git_error = git_commit_and_push(f"Rimozione riga in {selected_db_name}")
                                    if git_success:
                                        st.success("🚀 Sincronizzazione GitHub completata!")
                                    else:
                                        st.warning(f"⚠️ Salvataggio locale OK, ma sincronizzazione GitHub fallita: {git_error}")
                            else:
                                st.info("💡 Modifiche salvate localmente. Usa 'Sincronizza GitHub' per inviare a GitHub.")
                            
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Errore durante la rimozione: {e}")
                with col2:
                    if st.button("❌ Annulla", key="cancel_remove_btn"):
                        st.rerun()
    
    st.markdown("---")
    st.info("💡 Le modifiche vengono salvate direttamente nei file CSV del progetto nella cartella `databases/`")
    
    # Manual sync button
    if not AUTO_GIT_SYNC:
        st.markdown("---")
        st.subheader("🔄 Sincronizzazione Manuale")
        st.info("Sincronizza le modifiche locali con GitHub quando sei pronto.")
        
        if st.button("🚀 Sincronizza GitHub", type="primary"):
            with st.spinner("🔄 Sincronizzazione con GitHub in corso..."):
                git_success, git_error = git_commit_and_push("Sincronizzazione manuale database")
                if git_success:
                    st.success("🚀 Sincronizzazione GitHub completata con successo!")
                    st.balloons()
                else:
                    st.error(f"❌ Sincronizzazione fallita: {git_error}")
    
    if st.button("🏠 Torna alla Home"):
        st.session_state.current_section = 'phones'
        st.rerun()

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
