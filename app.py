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
CSV_FILE = "database_telefoni.csv"
APP_VERSION = "1.1"  # Version to verify deployment

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = PASSWORD is None  # Auto-authenticate if password is disabled
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

def load_database():
    """Load phone database from CSV file"""
    try:
        if os.path.exists(CSV_FILE):
            # Specify dtype to prevent automatic conversion to float
            df = pd.read_csv(CSV_FILE, dtype={'Codice_PIM': str})
            # Ensure required columns exist
            required_columns = ['Marca', 'Tipo', 'Modello', 'Memoria', 'Colore', 'Codice_PIM']
            for col in required_columns:
                if col not in df.columns:
                    st.error(f"Colonna mancante nel CSV: {col}")
                    return None
            return df
        else:
            st.error(f"File {CSV_FILE} non trovato")
            return None
    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return None

def resize_and_crop(img, target_width, target_height):
    """Resize and crop image to target dimensions maintaining aspect ratio"""
    # Get current dimensions
    current_width, current_height = img.size
    
    # Calculate aspect ratios
    target_ratio = target_width / target_height
    current_ratio = current_width / current_height
    
    if current_ratio > target_ratio:
        # Image is wider than target - crop width
        new_height = current_height
        new_width = int(new_height * target_ratio)
        left = (current_width - new_width) // 2
        top = 0
        right = left + new_width
        bottom = current_height
    else:
        # Image is taller than target - crop height
        new_width = current_width
        new_height = int(new_width / target_ratio)
        left = 0
        top = (current_height - new_height) // 2
        right = current_width
        bottom = top + new_height
    
    # Crop and resize
    img = img.crop((left, top, right, bottom))
    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    return img

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
    st.title("📱 Catalogo Dispositivi")
    st.caption(f"Versione: {APP_VERSION}")
    st.markdown("---")
    
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
    
    st.markdown("---")
    
    # Back button, Home and Logout
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("⬅️ Indietro", width='stretch'):
            go_back()
    with col2:
        if st.button("🏠 Home", width='stretch'):
            st.session_state.selected_brand = None
            st.session_state.selected_category = None
            st.session_state.selected_model = None
            st.session_state.selected_memory = None
            st.session_state.selected_variant = None
            st.session_state.model_has_single_memory = False
            st.session_state.skipped_color_selection = False
            st.rerun()
    with col3:
        if st.button("🚪 Logout", width='stretch'):
            st.session_state.authenticated = False
            st.session_state.selected_brand = None
            st.session_state.selected_category = None
            st.session_state.selected_model = None
            st.session_state.selected_memory = None
            st.session_state.selected_variant = None
            st.session_state.model_has_single_memory = False
            st.session_state.skipped_color_selection = False
            st.rerun()

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

def show_brands_view(df):
    """Display all brands as buttons with logos"""
    st.subheader("Seleziona Marchio")
    
    brands = df['Marca'].unique()
    
    # Create grid of brand buttons
    cols = st.columns(min(3, len(brands)))
    for idx, brand in enumerate(brands):
        col_idx = idx % len(cols)
        with cols[col_idx]:
            # Try to load brand logo
            logo_path = f"images/brands/{brand.lower().replace(' ', '_')}.png"
            if os.path.exists(logo_path):
                # Load image and add white background if transparent
                img = Image.open(logo_path)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    if img.mode in ('RGBA', 'LA'):
                        background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                        img = background
                    else:
                        img = img.convert('RGB')
                # Resize and crop to 720x390
                img = resize_and_crop(img, 720, 390)
                st.image(img, width='stretch')
            
            if st.button(brand, key=f"brand_{brand}", width='stretch'):
                st.session_state.selected_brand = brand
                st.rerun()

def show_categories_view(df):
    """Display categories for selected brand"""
    brand = st.session_state.selected_brand
    st.subheader(f"{brand} - Seleziona Categoria")
    
    # Filter by brand
    brand_df = df[df['Marca'] == brand]
    
    # Get categories from Tipo column
    categories = brand_df['Tipo'].unique()
    categories = [c for c in categories if pd.notna(c) and c != '']
    
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
    
    # Display category buttons
    cols = st.columns(min(2, len(categories)))
    for idx, category in enumerate(sorted(categories)):
        col_idx = idx % len(cols)
        with cols[col_idx]:
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
    
    # Filter by brand and category using Tipo column
    category_df = df[(df['Marca'] == brand) & (df['Tipo'] == category)]
    
    models = category_df['Modello'].drop_duplicates()
    
    # Category emojis for model buttons
    category_emojis = {
        'Smartphone': '📲',
        'Smartwatch': '⌚'
    }
    model_emoji = category_emojis.get(category, '📲')
    
    # Use simple sequential rendering to ensure consistent order across devices
    for idx, model in enumerate(models):
        # Try to load model image
        model_filename = model.lower().replace(' ', '_').replace('/', '_')
        model_path = f"images/models/{model_filename}.png"
        if os.path.exists(model_path):
            # Load image and add white background if transparent
            img = Image.open(model_path)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode in ('RGBA', 'LA'):
                    background.paste(img, mask=img.split()[-1])
                    img = background
                else:
                    img = img.convert('RGB')
            # Resize and crop to 720x390
            img = resize_and_crop(img, 720, 390)
            st.image(img, width='stretch')
        
        if st.button(f"{model_emoji} {model}", key=f"model_{idx}", width='stretch'):
            st.session_state.selected_model = model
            # Check if model has single memory (filter out empty/NaN and "n/n")
            model_df = df[df['Modello'] == model]
            memories = model_df['Memoria'].dropna().unique()
            memories = [m for m in memories if m and str(m).strip() != '' and str(m).strip().lower() != 'n/n']
            st.session_state.model_has_single_memory = (len(memories) <= 1)
            st.rerun()

def show_memories_view(df):
    """Display memory options for selected model"""
    brand_model_df = df[
        (df['Marca'] == st.session_state.selected_brand) & 
        (df['Modello'] == st.session_state.selected_model)
    ]
    
    # Filter out empty/NaN memories and "n/n" (not applicable)
    memories = brand_model_df['Memoria'].dropna().unique()
    memories = [m for m in memories if m and str(m).strip() != '' and str(m).strip().lower() != 'n/n']
    
    # If no valid memories or only one, skip directly to colors
    if len(memories) <= 1:
        # Use empty string for memory if no valid memories (product has only "n/n")
        st.session_state.selected_memory = memories[0] if len(memories) == 1 else 'n/n'
        st.rerun()
    
    # Show memory options
    st.subheader(f"Modello: {st.session_state.selected_model}")
    
    cols = st.columns(min(2, len(memories)))
    for idx, memory in enumerate(memories):
        col_idx = idx % len(cols)
        with cols[col_idx]:
            if st.button(f"💾 {memory}", key=f"memory_{idx}", width='stretch'):
                st.session_state.selected_memory = memory
                st.rerun()

def show_colors_view(df):
    """Display color options for selected memory with color swatches"""
    st.subheader(f"Modello: {st.session_state.selected_model}")
    
    # Show memory only if it's not empty
    if st.session_state.selected_memory and str(st.session_state.selected_memory).strip():
        st.write(f"**Memoria:** {st.session_state.selected_memory}")
    
    # Filter by brand and model
    brand_model_df = df[
        (df['Marca'] == st.session_state.selected_brand) & 
        (df['Modello'] == st.session_state.selected_model)
    ]
    
    # Check if product has only "n/n" memories (no valid memories)
    valid_memories = brand_model_df['Memoria'].apply(lambda x: str(x).strip().lower() != 'n/n')
    has_only_n_n = not valid_memories.any()
    
    # If memory is selected and not empty (and not "n/n"), filter by memory too
    memory = str(st.session_state.selected_memory).strip() if st.session_state.selected_memory else ''
    if memory and memory.lower() != 'n/n':
        brand_model_memory_df = brand_model_df[brand_model_df['Memoria'] == memory]
    elif has_only_n_n:
        # If product has only "n/n" memories, show all of them (don't filter out)
        brand_model_memory_df = brand_model_df
    else:
        # If no memory selected but product has valid memories, filter out "n/n"
        brand_model_memory_df = brand_model_df[valid_memories]
    
    # Safety check: if no results, show all variants
    if brand_model_memory_df.empty:
        brand_model_memory_df = brand_model_df
    
    # If still empty after safety check, show error message
    if brand_model_memory_df.empty:
        st.warning("Nessuna variante disponibile per questo prodotto.")
        return
    
    # Check if all colors are "n/n" - if so, skip directly to barcode
    colors = brand_model_memory_df['Colore'].unique()
    all_n_n = all(str(c).strip().lower() == 'n/n' for c in colors)
    if all_n_n and len(colors) == 1:
        # Automatically select the variant and skip to barcode
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
        'magnetic case inclusa': '#CCCCCC',  # Fallback for non-color descriptions
        # Samsung specific colors
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
    }
    
    cols = st.columns(max(1, min(2, len(brand_model_memory_df))))
    for idx, row in brand_model_memory_df.iterrows():
        col_idx = idx % len(cols)
        with cols[col_idx]:
            color_name = row['Colore'].lower()
            
            # Try to get color from mapping or load image
            if color_name in color_map:
                hex_color = color_map[color_name]
                st.markdown(f"""
                    <div style="background-color: {hex_color}; width: 100px; height: 100px; border-radius: 10px; margin: 0 auto; border: 2px solid #ddd;"></div>
                """, unsafe_allow_html=True)
            else:
                # Try to load color image
                color_filename = color_name.replace(' ', '_').replace('/', '_')
                color_path = f"images/colors/{color_filename}.png"
                if os.path.exists(color_path):
                    # Load image and add white background if transparent
                    img = Image.open(color_path)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        if img.mode in ('RGBA', 'LA'):
                            background.paste(img, mask=img.split()[-1])
                            img = background
                        else:
                            img = img.convert('RGB')
                    # Resize and crop to 720x390
                    img = resize_and_crop(img, 720, 390)
                    st.image(img, width='stretch')
                else:
                    # Fallback to colored square with default gray
                    st.markdown("""
                        <div style="background-color: #CCCCCC; width: 100px; height: 100px; border-radius: 10px; margin: 0 auto; border: 2px solid #ddd;"></div>
                    """, unsafe_allow_html=True)
            
            if st.button(f"🎨 {row['Colore']}", key=f"color_{idx}", width='stretch'):
                st.session_state.selected_variant = row.to_dict()
                st.rerun()

def show_variant_view(df):
    """Display final view with PIM code and barcode"""
    variant = st.session_state.selected_variant
    
    st.subheader(f"{variant['Marca']} - {variant['Modello']}")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.write(f"**Memoria:** {variant['Memoria']}")
        st.write(f"**Colore:** {variant['Colore']}")
        st.write(f"**Codice PIM:** {variant['Codice_PIM']}")
    
    with col2:
        # Generate and display barcode
        barcode_img = generate_barcode(str(variant['Codice_PIM']))
        
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
    """, unsafe_allow_html=True)
    
    # Route based on authentication
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()
