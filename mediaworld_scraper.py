import requests
from bs4 import BeautifulSoup
import csv
import time
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Configuration
BASE_URL = "https://www.mediaworld.it"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Brands and their MediaWorld URL paths
BRANDS = {
    "Samsung": "it/brand/samsung",
    "Google": "it/brand/google",
    "Xiaomi": "it/brand/xiaomi",
    "OPPO": "it/brand/oppo",
    "Honor": "it/brand/honor",
    "ZTE": "it/brand/zte",
    "Motorola": "it/brand/motorola"
}

# Categories to scrape for each brand
# Use None for brands that need filter-based scraping (no specific category URL)
CATEGORIES = {
    "Samsung": ["smartphone", "smartwatch", "tablet", "notebook"],
    "Google": None,  # Will use filter-based scraping
    "Xiaomi": ["smartphone"],
    "OPPO": ["smartphone"],
    "Honor": ["smartphone", "wearables", "tablet"],
    "ZTE": ["blade", "nubia"],
    "Motorola": None  # Will use filter-based scraping
}

def is_mediaworld_product(soup):
    """Check if product is sold by MediaWorld (not third-party)"""
    # Check for MediaWorld seller indicators
    seller_text = soup.get_text()
    
    # Look for MediaWorld-specific indicators
    if "Venduto e spedito da MediaWorld" in seller_text:
        return True
    
    # Check for third-party seller warnings
    if "Venduto e spedito da" in seller_text and "MediaWorld" not in seller_text:
        return False
    
    # Default to True if no clear third-party indicator
    return True

def extract_pim_code(soup):
    """Extract 6-digit PIM code from product page"""
    # Try to find Art.-No. field
    art_no = soup.find(string=re.compile(r"Art\.-No\.|Codice articolo|Cod\. Art\."))
    if art_no:
        pim_text = art_no.find_next().get_text(strip=True)
        # Extract 6-digit number
        pim_match = re.search(r'\b\d{6}\b', pim_text)
        if pim_match:
            return pim_match.group()
    
    # Alternative: look for PIM in product data
    # Check for data attributes or meta tags
    for meta in soup.find_all('meta'):
        if 'pim' in meta.get('name', '').lower() or 'pim' in meta.get('property', '').lower():
            pim_match = re.search(r'\b\d{6}\b', meta.get('content', ''))
            if pim_match:
                return pim_match.group()
    
    return None

def extract_color(soup, url=""):
    """Extract color from product page"""
    # Non-color terms to exclude
    exclude_terms = [
        'magnetic case', 'case inclusa', 'cover', 'caricabatteria', 
        'power adapter', 'inclusi', 'bundle', 'box', 'case', 'adapter'
    ]
    
    # Try to extract color from URL first (most reliable for MediaWorld)
    # URL pattern: .../product/_model-color-pim.html
    url_color_match = re.search(r'/product/_[^-]+-([^-]+)-\d+\.html', url)
    if url_color_match:
        url_color = url_color_match.group(1)
        # Clean up URL color (replace hyphens with spaces, capitalize)
        url_color = url_color.replace('-', ' ').strip()
        url_color = ' '.join(word.capitalize() for word in url_color.split())
        # Check if it's a valid color (not a bundle term)
        if url_color and len(url_color) < 30 and not any(term.lower() in url_color.lower() for term in exclude_terms):
            return url_color
    
    # Try multiple selectors for color from page
    selectors = [
        soup.find('span', string=re.compile(r"Colore|Color", re.I)),
        soup.find('div', string=re.compile(r"Colore|Color", re.I)),
        soup.find('label', string=re.compile(r"Colore|Color", re.I)),
        soup.find('dt', string=re.compile(r"Colore|Color", re.I)),
    ]
    
    for selector in selectors:
        if selector:
            # Try to get the next sibling or parent's next child
            next_elem = selector.find_next_sibling()
            if next_elem:
                color_text = next_elem.get_text(strip=True)
                # Clean up - remove common non-color text
                if color_text and len(color_text) < 50:  # Reasonable color name length
                    # Check if text contains excluded bundle terms
                    if not any(term.lower() in color_text.lower() for term in exclude_terms):
                        return color_text
    
    # Alternative: look for color in product title or specs
    title = soup.find('h1')
    if title:
        title_text = title.get_text()
        # Try to extract color from title (common pattern: "Model Name, Color")
        color_match = re.search(r',\s*([A-Za-z\s]+)$', title_text)
        if color_match:
            potential_color = color_match.group(1).strip()
            if len(potential_color) < 30 and not any(term.lower() in potential_color.lower() for term in exclude_terms):
                return potential_color
    
    return ""

def extract_color_from_model(model):
    """Extract color from model name as fallback"""
    # Color patterns including OPPO specific colors
    color_patterns = [
        r'(Black|White|Blue|Green|Red|Yellow|Orange|Purple|Pink|Gray|Grey|Silver|Gold|Brown|Beige|Cream|Ivory|Lavender|Rose|Navy|Cobalt|Titanium|Obsidian|Charcoal|Natural|Deep|Icy|Flowy|Cook|Asteroid|Graphite|Mint|Shadow|Jetblack|Icyblue)$',
        r'(Light\s+\w+|Dark\s+\w+|Awesome\s+\w+|Stellar\s+\w+|Lunar\s+\w+|Sky\s+\w+|Titanium\s+\w+|Violet\s+\w+)$',
        r'(Cobalt\s+Violet|Jet\s+Black|Light\s+Green|Awesome\s+Navy|Silver\s+Blue|White\s+Silver|Titanium\s+Gray|Titanium\s+Silverblue|Titanium\s+Whitesilver)$',
        r'(Canyon\s+Orange|Tundra\s+Umber|Aurora\s+White|Aurora\s+Blue|Twilight\s+Black|Dusk\s+Black|Titanium\s+Charcoal)$',
        r'(Silver\s+Shadow|Black/Blue|Black/White|Blue/Black|White/Black)$'
    ]
    
    for pattern in color_patterns:
        match = re.search(pattern, model, re.I)
        if match:
            return match.group(1).strip()
    
    return ""

def extract_memory(soup, model=""):
    """Extract memory from product page or model name (for smartwatches)"""
    # Try multiple selectors for memory/storage
    selectors = [
        soup.find('span', string=re.compile(r"Memoria|Storage|Capacità", re.I)),
        soup.find('div', string=re.compile(r"Memoria|Storage|Capacità", re.I)),
        soup.find('label', string=re.compile(r"Memoria|Storage|Capacità", re.I)),
        soup.find('dt', string=re.compile(r"Memoria|Storage|Capacità", re.I)),
    ]
    
    for selector in selectors:
        if selector:
            next_elem = selector.find_next_sibling()
            if next_elem:
                memory_text = next_elem.get_text(strip=True)
                # Clean up - extract memory pattern (e.g., "256 GB", "128 GB")
                memory_match = re.search(r'\d+\s*(GB|TB|MB)', memory_text, re.I)
                if memory_match:
                    return memory_match.group(0)
    
    # Alternative: look for memory in product title
    title = soup.find('h1')
    if title:
        title_text = title.get_text()
        # Try to extract memory from title (common pattern: "Model 256GB" or "Model 8+256GB")
        memory_match = re.search(r'(\d+\+\d+|\d+)\s*(GB|TB)', title_text, re.I)
        if memory_match:
            return memory_match.group(0) + " GB" if "GB" not in memory_match.group(0).upper() else memory_match.group(0)
    
    # For smartwatches, extract mm from model name as fallback
    if model:
        mm_match = re.search(r'(\d+)\s*mm', model, re.I)
        if mm_match:
            return mm_match.group(1) + " mm"
    
    return "n/n"

def determine_product_type(model, category):
    """Determine product type based on model name and category"""
    model_lower = model.lower()
    if 'smartwatch' in model_lower or 'smartband' in model_lower or 'anello' in model_lower or 'ring' in model_lower:
        return 'Smartwatch'
    elif category == 'smartwatch' or category == 'wearables':
        return 'Smartwatch'
    elif category == 'tablet':
        return 'Tablet'
    elif category == 'notebook':
        return 'Notebook'
    else:
        return 'Smartphone'

def scrape_category_products(brand, category):
    """Scrape all products for a brand and category with 'Show more' button support"""
    base_url = f"{BASE_URL}/{BRANDS[brand]}/{category}"
    products = []
    seen_urls = set()
    
    # First try with category - just check if URL works
    try:
        print(f"Checking {brand} - {category}: {base_url}")
        response = requests.get(base_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Check if this page actually has products (not a 404 or empty page)
        test_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/it/product' in href:
                test_links.append(href)
        
        print(f"Debug: Found {len(test_links)} product links on first page")
        
        if not test_links:
            print(f"No products found for {brand} - {category}, trying brand-only URL")
            # Fall back to brand-only URL
            return scrape_brand_only(brand)
        
    except Exception as e:
        print(f"Error accessing {brand} - {category}: {e}, trying brand-only URL")
        # Fall back to brand-only URL
        return scrape_brand_only(brand)
    
    # Use Selenium to handle "Show more" button
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # FORCE DESKTOP VERSION AND ADD USER AGENT
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(f"user-agent={HEADERS['User-Agent']}")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(base_url)
        
        # Add WebDriverWait for dynamic elements
        wait = WebDriverWait(driver, 10)
        
        # 1. COOKIE BANNER HANDLING (Critical for unblocking subsequent clicks)
        try:
            cookie_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accetta tutti')]",
                "//button[@id='pwa-consent-layer-accept-all-button']",
                "//button[contains(@class, 'cookie')]"
            ]
            for selector in cookie_selectors:
                try:
                    cookie_btn = driver.find_element(By.XPATH, selector)
                    if cookie_btn.is_displayed():
                        driver.execute_script("arguments[0].click();", cookie_btn)
                        print("✓ Banner cookie accettato.")
                        time.sleep(2)
                        break
                except:
                    continue
        except Exception:
            print("Nessun banner cookie intercettato.")

        # Apply MediaWorld-only filter to exclude marketplace
        try:
            print("Applying MediaWorld-only filter...")
            # Navigate to URL with marketplace parameter instead of clicking
            current_url = driver.current_url
            if 'marketplace' not in current_url:
                separator = '&' if '?' in current_url else '?'
                filtered_url = f"{current_url}{separator}marketplace=MediaWorld"
                driver.get(filtered_url)
                print(f"✓ Navigated to filtered URL")
                time.sleep(5)
            else:
                print("✓ Marketplace filter already in URL")
        except Exception as e:
            print(f"Could not apply MediaWorld filter: {e}")
        # Click "Show more" button until no more products
        max_clicks = 40
        click_count = 0
        
        while click_count < max_clicks:
            try:
                # Scroll to bottom to force rendering
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                show_more_button = None
                
                # List of targeted selectors based on MediaWorld's actual structure
                selectors = [
                    (By.XPATH, "//button[@data-test='mms-search-srp-loadmore']"),
                    (By.XPATH, "//button[contains(@class, 'load-more')]"),
                    (By.XPATH, "//span[contains(text(), 'Mostra')]/parent::button"),
                    (By.XPATH, "//button[contains(., 'Mostra altri')]"),
                    (By.XPATH, "//button[contains(., 'Carica')]")
                ]
                
                for by_type, selector in selectors:
                    try:
                        # Simple find with retry - avoid strict clickable check
                        show_more_button = driver.find_element(by_type, selector)
                        if show_more_button and show_more_button.is_displayed():
                            print(f"Debug: Found button with selector: {selector}")
                            break
                    except:
                        continue
                
                if not show_more_button:
                    print("Nessun pulsante 'Mostra altri' trovato (fine catalogo raggiunta).")
                    break
                
                print(f"Clicco 'Mostra altri' (click {click_count + 1})")
                
                # Center button and execute click via JavaScript
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", show_more_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", show_more_button)
                
                click_count += 1
                time.sleep(4)  # Wait for new products DOM to load
                
            except Exception as e:
                print("Nessun altro pulsante intercettato o fine catalogo raggiunta.")
                break
        
        # Get all product links after clicking "Show more"
        soup = BeautifulSoup(driver.page_source, "html.parser")
        all_product_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/it/product' in href:
                full_url = href if href.startswith('http') else BASE_URL + href
                if full_url not in seen_urls:
                    all_product_links.append(full_url)
                    seen_urls.add(full_url)
        
        print(f"Total product links found after clicking 'Show more': {len(all_product_links)}")
        driver.quit()
        
    except Exception as e:
        print(f"Error with Selenium: {e}")
        # Fallback to regular requests if Selenium fails
        print("Falling back to regular requests (may not get all products)")
        try:
            response = requests.get(base_url, headers=HEADERS, timeout=30)
            soup = BeautifulSoup(response.text, "html.parser")
            all_product_links = []
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/it/product' in href:
                    full_url = href if href.startswith('http') else BASE_URL + href
                    if full_url not in seen_urls:
                        all_product_links.append(full_url)
                        seen_urls.add(full_url)
        except Exception as e2:
            print(f"Error with fallback: {e2}")
            return products
    
    # Scrape each product page
    for idx, prod_url in enumerate(all_product_links):
        print(f"  [{idx+1}/{len(all_product_links)}] Scraping: {prod_url}")
        
        try:
            time.sleep(1)  # Be respectful to the server
            prod_response = requests.get(prod_url, headers=HEADERS, timeout=30)
            prod_response.raise_for_status()
            prod_soup = BeautifulSoup(prod_response.text, "html.parser")
            
            # Check if it's a MediaWorld product
            if not is_mediaworld_product(prod_soup):
                print(f"    Skipping: Third-party seller")
                continue
            
            # Extract PIM code
            pim = extract_pim_code(prod_soup)
            if not pim:
                print(f"    Skipping: No PIM code found")
                continue
            
            # Verify it's a 6-digit code
            if not re.match(r'^\d{6}$', pim):
                print(f"    Skipping: PIM {pim} is not 6 digits")
                continue
            
            # Extract product details
            title = prod_soup.find('h1')
            model = title.get_text(strip=True) if title else "Unknown"
            
            # Verify product is actually from the correct brand (check title contains brand name)
            if brand.lower() not in model.lower():
                print(f"    Skipping: Product '{model}' does not match brand '{brand}'")
                continue
            
            # Clean model name - remove brand prefix if present
            model = re.sub(r'^' + re.escape(brand) + r'\s*', '', model, flags=re.I)
            # Also remove brand name if it appears after type (e.g., "SMARTBAND SAMSUNG Galaxy FIT3")
            model = re.sub(r'\s+' + re.escape(brand) + r'\s+', ' ', model, flags=re.I)
            model = model.strip()
            
            # Remove "Tablet" prefix from model name
            model = re.sub(r'^Tablet\s+', '', model, flags=re.I)
            model = re.sub(r',\s*Tablet\s+', ', ', model, flags=re.I)
            
            # Remove display dimensions (e.g., "8,7 """, "11 """, "10.1""")
            model = re.sub(r'\s*\d+[,.]?\d*\s*["\']+\s*', '', model, flags=re.I)
            model = re.sub(r'\s*\d+[,.]?\d*\s*["\']+\s*,\s*', ', ', model, flags=re.I)
            
            # Remove memory from model name (patterns like "4/128GB", "256GB", "8+256GB")
            # More precise patterns to avoid leaving extra commas
            model = re.sub(r'\s*\d+/\d+\s*(GB|TB|MB)\s*', '', model, flags=re.I)
            model = re.sub(r'\s*\d+\+\d+\s*(GB|TB|MB)\s*', '', model, flags=re.I)
            model = re.sub(r'\s*\d+\s*(GB|TB|MB)\s*', '', model, flags=re.I)
            model = re.sub(r',\s*\d+\s*(GB|TB|MB)', '', model, flags=re.I)
            
            # Remove mm from model name (for smartwatches) - will be extracted as memory separately
            model = re.sub(r'\s*\d+\s*mm\s*', '', model, flags=re.I)
            model = re.sub(r',\s*\d+\s*mm\s*', '', model, flags=re.I)
            
            model = re.sub(r',\s*,\s*', ', ', model)  # Fix double commas
            model = re.sub(r'\s*,\s*$', '', model)  # Remove trailing comma
            model = re.sub(r'^\s*,\s*', '', model)  # Remove leading comma
            model = model.strip()
            
            # Remove bundle text from model name FIRST (before color extraction)
            bundle_patterns = [
                r',\s*cover e caricabatteria \d+W inclusi\s*$',
                r',\s*Magnetic Case \+ SUPERVOOC \d+W Power Adapter inclusi\s*$',
                r',\s*Magnetic Case inclusa\s*$',
                r',\s*Box\s*$',
                r',\s*cover e caric\s*$',
                r',\s*cover e carica\s*$',
            ]
            for pattern in bundle_patterns:
                model = re.sub(pattern, '', model, flags=re.I)
            model = re.sub(r'\s*,\s*$', '', model)  # Remove trailing comma after bundle removal
            model = model.strip()
            
            # Extract color from model name as fallback before removing it
            color_from_model = extract_color_from_model(model)
            
            # Remove color from model name (color should be in separate field only)
            # Common color names to remove from end of model name (English and Italian)
            color_patterns = [
                r',\s*(Black|White|Blue|Green|Red|Yellow|Orange|Purple|Pink|Gray|Grey|Silver|Gold|Brown|Beige|Cream|Ivory|Lavender|Rose|Navy|Cobalt|Titanium|Obsidian|Charcoal|Natural|Deep|Icy|Flowy|Cook|Asteroid|Graphite|Mint|Shadow|Jetblack|Icyblue)\s*$',
                r',\s*(Light\s+\w+|Dark\s+\w+|Awesome\s+\w+|Stellar\s+\w+|Lunar\s+\w+|Sky\s+\w+|Titanium\s+\w+|Violet\s+\w+)\s*$',
                r',\s*(Cobalt\s+Violet|Jet\s+Black|Light\s+Green|Awesome\s+Navy|Silver\s+Blue|White\s+Silver|Titanium\s+Gray|Titanium\s+Silverblue|Titanium\s+Whitesilver)\s*$',
                r',\s*(Canyon\s+Orange|Tundra\s+Umber|Aurora\s+White|Aurora\s+Blue|Twilight\s+Black|Dusk\s+Black|Titanium\s+Charcoal)\s*$',
                r',\s*(Silver\s+Shadow|Black/Blue|Black/White|Blue/Black|White/Black)\s*$',
                # Italian color patterns
                r',\s*(Nero|Bianco|Blu|Verde|Rosso|Giallo|Arancione|Viola|Rosa|Grigio|Argento|Oro|Marrone|Beige|Crema|Avorio|Lavanda|Navy|Cobalto|Titanio|Ossidiana|Carbone|Naturale|Profondo|Ghiaccio|Graphite|Menta)\s*$',
                r',\s*(Nero\s+ossidiana|Viola\s+lavanda|Bianco\s+argento|Nero\s+jet|Verde\s+chiaro|Blu\s+cobalto|Grigio\s+titanio)\s*$'
            ]
            
            # Also remove colors from middle of model name (for cases like "Galaxy S25, Icyblue")
            middle_color_patterns = [
                r',\s*(Jetblack|Icyblue|Silver\s+Shadow|Black/Blue)\s*,',
                r',\s*(Jetblack|Icyblue|Silver\s+Shadow|Black/Blue)\s*$'
            ]
            
            for pattern in color_patterns:
                model = re.sub(pattern, '', model, flags=re.I)
            
            # Apply middle color patterns
            for pattern in middle_color_patterns:
                model = re.sub(pattern, ',', model, flags=re.I)
            
            model = re.sub(r'\s*,\s*$', '', model)  # Remove trailing comma after color removal
            model = re.sub(r',\s*,\s*', ', ', model)  # Fix double commas
            model = model.strip()
            
            color = extract_color(prod_soup, prod_url)
            # Use color from model as fallback if page extraction fails
            if not color and color_from_model:
                color = color_from_model
            # Replace empty color with "n/n"
            if not color or color.strip() == '':
                color = 'n/n'
            
            memory = extract_memory(prod_soup, model)
            
            # Determine product type
            product_type = determine_product_type(model, category)
            
            # Special handling for notebooks
            if product_type == 'Notebook':
                # Extract display size for color field
                # Try to extract from URL first (more reliable)
                # Find all numbers in URL and pick the one that looks like display size
                all_numbers = re.findall(r'-(\d+)(?:\.?(\d+))?', prod_url)
                display_str = 'n/n'
                for whole, decimal in all_numbers:
                    num_str = f"{whole}.{decimal}" if decimal else whole
                    display_size = float(num_str)
                    # Convert 3-digit numbers like 156 to 15.6, 140 to 14.0
                    if display_size > 100:
                        display_size = display_size / 10
                        num_str = str(display_size)
                    # Only use if it's a reasonable display size (10-20 inches)
                    if 10 <= display_size <= 20:
                        display_str = num_str.replace(',', '.') + '"'
                        break
                
                color = display_str
                
                # Extract SSD storage from page (look for storage/capacità with larger values)
                storage_selectors = [
                    prod_soup.find('span', string=re.compile(r"Memoria|Storage|Capacità|SSD", re.I)),
                    prod_soup.find('div', string=re.compile(r"Memoria|Storage|Capacità|SSD", re.I)),
                    prod_soup.find('label', string=re.compile(r"Memoria|Storage|Capacità|SSD", re.I)),
                    prod_soup.find('dt', string=re.compile(r"Memoria|Storage|Capacità|SSD", re.I)),
                ]
                
                ssd_found = False
                for selector in storage_selectors:
                    if selector:
                        next_elem = selector.find_next_sibling()
                        if next_elem:
                            storage_text = next_elem.get_text(strip=True)
                            # Look for larger storage values (typically 256GB, 512GB, 1TB for SSD)
                            # Skip RAM values (usually 8GB, 16GB, 32GB)
                            for match in re.finditer(r'(\d+)\s*(GB|TB)', storage_text, re.I):
                                value = int(match.group(1))
                                unit = match.group(2).upper()
                                # If it's TB or large GB value (>64), it's likely SSD
                                if unit == 'TB' or value > 64:
                                    memory = f"{value * 1000 if unit == 'TB' else value} GB"
                                    ssd_found = True
                                    break
                            if ssd_found:
                                break
                
                # Fallback: try to extract SSD from title
                if not ssd_found:
                    title_text = title.get_text() if title else ""
                    ssd_match = re.search(r'(\d+)\s*(GB|TB)\s*SSD', title_text, re.I)
                    if ssd_match:
                        value = int(ssd_match.group(1))
                        unit = ssd_match.group(2).upper()
                        memory = f"{value * 1000 if unit == 'TB' else value} GB"
                    else:
                        # Try to find any large storage value in title
                        for match in re.finditer(r'(\d+)\s*(GB|TB)', title_text, re.I):
                            value = int(match.group(1))
                            unit = match.group(2).upper()
                            if unit == 'TB' or value > 64:
                                memory = f"{value * 1000 if unit == 'TB' else value} GB"
                                break
                
                # Clean model name for notebooks - remove NOTEBOOK, CHROMEBOOK, processore and processor codes
                model = re.sub(r'\s+NOTEBOOK\s*', ' ', model, flags=re.I)
                model = re.sub(r'\s+CHROMEBOOK\s*', ' ', model, flags=re.I)
                model = re.sub(r'\s+CONVERTIBILE\s*', ' ', model, flags=re.I)
                model = re.sub(r'\s*,\s*processore.*$', '', model, flags=re.I)
                model = re.sub(r'\s+processore.*$', '', model, flags=re.I)
                # Remove display size numbers from model name (like "14" in "GALAXY GO 14")
                # Only remove 1-2 digit numbers (display sizes), not 3-digit numbers like 360 (model name part)
                # Also protect known model name parts like 360
                if '360' not in model:
                    model = re.sub(r'\s+\d{1,2}\.?\d*\s*$', '', model, flags=re.I)
                # Remove specific processor codes (like N4500, X1-26-100, 226V, 255U, 355, 356H)
                # Be careful not to remove model name parts like "Book6"
                model = re.sub(r'\s+N\d+[A-Z]*$', '', model, flags=re.I)  # Intel Celeron N4500
                model = re.sub(r'\s+X\d+-\d+-\d+$', '', model, flags=re.I)  # Snapdragon X1-26-100
                model = re.sub(r'\s+\d{3}[A-Z]$', '', model, flags=re.I)  # Intel Core 226V, 255U, 355, 356H
                model = model.strip()
            
            
            # Debug: print extracted values
            print(f"    Extracted - Model: {model[:50]}, Memory: {memory}, Color: {color}, Type: {product_type}")
            
            products.append({
                "Marca": brand,
                "Tipo": product_type,
                "Modello": model,
                "Memoria": memory,
                "Colore": color,
                "Codice_PIM": pim
            })
            
            print(f"    ✓ Added: {model} - PIM: {pim}")
            
        except Exception as e:
            print(f"    Error scraping {prod_url}: {e}")
            continue
    
    return products

def scrape_with_filters(brand):
    """Scrape products for brands that need filter-based scraping (no specific category URL)"""
    base_url = f"{BASE_URL}/{BRANDS[brand]}"
    products = []
    seen_urls = set()
    
    # Use Selenium to handle filters and "Show more" button
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(f"user-agent={HEADERS['User-Agent']}")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(base_url)
        
        wait = WebDriverWait(driver, 10)
        
        # 1. COOKIE BANNER HANDLING
        try:
            cookie_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accetta tutti')]",
                "//button[@id='pwa-consent-layer-accept-all-button']",
                "//button[contains(@class, 'cookie')]"
            ]
            for selector in cookie_selectors:
                try:
                    cookie_btn = driver.find_element(By.XPATH, selector)
                    if cookie_btn.is_displayed():
                        driver.execute_script("arguments[0].click();", cookie_btn)
                        print("✓ Banner cookie accettato.")
                        time.sleep(2)
                        break
                except:
                    continue
        except Exception:
            print("Nessun banner cookie intercettato.")

        # 2. APPLY CATEGORY FILTER (Smartphone/Cellulari)
        try:
            print(f"Applying category filter for {brand}...")
            # Try to find and click on smartphone/cellulari filter
            category_selectors = [
                "//span[contains(text(), 'Smartphone')]/parent::label",
                "//span[contains(text(), 'Cellulari')]/parent::label",
                "//span[contains(text(), 'smartphone')]/parent::label",
                "//span[contains(text(), 'cellulari')]/parent::label",
            ]
            for selector in category_selectors:
                try:
                    category_filter = driver.find_element(By.XPATH, selector)
                    if category_filter.is_displayed():
                        driver.execute_script("arguments[0].click();", category_filter)
                        print(f"✓ Category filter applied")
                        time.sleep(3)
                        break
                except:
                    continue
        except Exception as e:
            print(f"Could not apply category filter: {e}")

        # 3. APPLY BRAND FILTER (if not already filtered)
        try:
            print(f"Applying brand filter for {brand}...")
            brand_selectors = [
                f"//span[contains(text(), '{brand}')]/parent::label",
                f"//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{brand.lower()}')]/parent::label",
            ]
            for selector in brand_selectors:
                try:
                    brand_filter = driver.find_element(By.XPATH, selector)
                    if brand_filter.is_displayed():
                        # Check if already selected
                        input_elem = brand_filter.find_element(By.TAG_NAME, "input")
                        if not input_elem.is_selected():
                            driver.execute_script("arguments[0].click();", brand_filter)
                            print(f"✓ Brand filter applied")
                            time.sleep(3)
                        break
                except:
                    continue
        except Exception as e:
            print(f"Could not apply brand filter: {e}")

        # 4. APPLY MEDIAWORLD-ONLY FILTER
        try:
            print("Applying MediaWorld-only filter...")
            # Navigate to URL with marketplace parameter instead of clicking
            current_url = driver.current_url
            if 'marketplace' not in current_url:
                separator = '&' if '?' in current_url else '?'
                filtered_url = f"{current_url}{separator}marketplace=MediaWorld"
                driver.get(filtered_url)
                print(f"✓ Navigated to filtered URL")
                time.sleep(5)
            else:
                print("✓ Marketplace filter already in URL")
        except Exception as e:
            print(f"Could not apply MediaWorld filter: {e}")
        # 5. CLICK "Show more" BUTTON
        max_clicks = 40
        click_count = 0
        
        while click_count < max_clicks:
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                show_more_button = None
                selectors = [
                    (By.XPATH, "//button[@data-test='mms-search-srp-loadmore']"),
                    (By.XPATH, "//button[contains(@class, 'load-more')]"),
                    (By.XPATH, "//span[contains(text(), 'Mostra')]/parent::button"),
                    (By.XPATH, "//button[contains(., 'Mostra altri')]"),
                    (By.XPATH, "//button[contains(., 'Carica')]")
                ]
                
                for by_type, selector in selectors:
                    try:
                        show_more_button = driver.find_element(by_type, selector)
                        if show_more_button and show_more_button.is_displayed():
                            print(f"Debug: Found button with selector: {selector}")
                            break
                    except:
                        continue
                
                if not show_more_button:
                    print("Nessun pulsante 'Mostra altri' trovato (fine catalogo raggiunta).")
                    break
                
                print(f"Clicco 'Mostra altri' (click {click_count + 1})")
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", show_more_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", show_more_button)
                
                click_count += 1
                time.sleep(4)
                
            except Exception as e:
                print("Nessun altro pulsante intercettato o fine catalogo raggiunta.")
                break
        
        # Get all product links
        soup = BeautifulSoup(driver.page_source, "html.parser")
        all_product_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/it/product' in href:
                full_url = href if href.startswith('http') else BASE_URL + href
                if full_url not in seen_urls:
                    all_product_links.append(full_url)
                    seen_urls.add(full_url)
        
        print(f"Total product links found: {len(all_product_links)}")
        driver.quit()
        
    except Exception as e:
        print(f"Error with Selenium: {e}")
        return products
    
    # Scrape each product page (reuse existing logic)
    for idx, prod_url in enumerate(all_product_links):
        print(f"  [{idx+1}/{len(all_product_links)}] Scraping: {prod_url}")
        
        try:
            time.sleep(1)
            prod_response = requests.get(prod_url, headers=HEADERS, timeout=30)
            prod_response.raise_for_status()
            prod_soup = BeautifulSoup(prod_response.text, "html.parser")
            
            if not is_mediaworld_product(prod_soup):
                print(f"    Skipping: Third-party seller")
                continue
            
            pim = extract_pim_code(prod_soup)
            if not pim:
                print(f"    Skipping: No PIM code found")
                continue
            
            if not re.match(r'^\d{6}$', pim):
                print(f"    Skipping: PIM {pim} is not 6 digits")
                continue
            
            title = prod_soup.find('h1')
            model = title.get_text(strip=True) if title else "Unknown"
            
            if brand.lower() not in model.lower():
                print(f"    Skipping: Product '{model}' does not match brand '{brand}'")
                continue
            
            model = re.sub(r'^' + re.escape(brand) + r'\s*', '', model, flags=re.I)
            model = model.strip()
            
            model = re.sub(r'\s*\d+/\d+\s*(GB|TB|MB)\s*', '', model, flags=re.I)
            model = re.sub(r'\s*\d+\+\d+\s*(GB|TB|MB)\s*', '', model, flags=re.I)
            model = re.sub(r'\s*\d+\s*(GB|TB|MB)\s*', '', model, flags=re.I)
            model = re.sub(r',\s*\d+\s*(GB|TB|MB)', '', model, flags=re.I)
            model = re.sub(r',\s*,\s*', ', ', model)
            model = re.sub(r'\s*,\s*$', '', model)
            model = re.sub(r'^\s*,\s*', '', model)
            model = model.strip()
            
            bundle_patterns = [
                r',\s*cover e caricabatteria \d+W inclusi\s*$',
                r',\s*Magnetic Case \+ SUPERVOOC \d+W Power Adapter inclusi\s*$',
                r',\s*Magnetic Case inclusa\s*$',
                r',\s*Box\s*$',
                r',\s*cover e caric\s*$',
                r',\s*cover e carica\s*$',
            ]
            for pattern in bundle_patterns:
                model = re.sub(pattern, '', model, flags=re.I)
            model = re.sub(r'\s*,\s*$', '', model)
            model = model.strip()
            
            color_from_model = extract_color_from_model(model)
            
            color_patterns = [
                r',\s*(Black|White|Blue|Green|Red|Yellow|Orange|Purple|Pink|Gray|Grey|Silver|Gold|Brown|Beige|Cream|Ivory|Lavender|Rose|Navy|Cobalt|Titanium|Obsidian|Charcoal|Natural|Deep|Icy|Flowy|Cook|Asteroid|Graphite|Mint|Shadow)\s*$',
                r',\s*(Light\s+\w+|Dark\s+\w+|Awesome\s+\w+|Stellar\s+\w+|Lunar\s+\w+|Sky\s+\w+|Titanium\s+\w+|Violet\s+\w+)\s*$',
                r',\s*(Cobalt\s+Violet|Jet\s+Black|Light\s+Green|Awesome\s+Navy|Silver\s+Blue|White\s+Silver|Titanium\s+Gray|Titanium\s+Silverblue|Titanium\s+Whitesilver)\s*$',
                r',\s*(Canyon\s+Orange|Tundra\s+Umber|Aurora\s+White|Aurora\s+Blue|Twilight\s+Black|Dusk\s+Black|Titanium\s+Charcoal)\s*$',
                r',\s*(Nero|Bianco|Blu|Verde|Rosso|Giallo|Arancione|Viola|Rosa|Grigio|Argento|Oro|Marrone|Beige|Crema|Avorio|Lavanda|Navy|Cobalto|Titanio|Ossidiana|Carbone|Naturale|Profondo|Ghiaccio|Graphite|Menta)\s*$',
                r',\s*(Nero\s+ossidiana|Viola\s+lavanda|Bianco\s+argento|Nero\s+jet|Verde\s+chiaro|Blu\s+cobalto|Grigio\s+titanio)\s*$'
            ]
            
            for pattern in color_patterns:
                model = re.sub(pattern, '', model, flags=re.I)
            model = re.sub(r'\s*,\s*$', '', model)
            model = model.strip()
            
            color = extract_color(prod_soup, prod_url)
            if not color and color_from_model:
                color = color_from_model
            
            memory = extract_memory(prod_soup, model)
            
            # Determine product type
            product_type = determine_product_type(model, category)
            
            # Special handling for notebooks
            if product_type == 'Notebook':
                # Extract display size for color field
                # Try to extract from URL first (more reliable)
                # Find all numbers in URL and pick the one that looks like display size
                all_numbers = re.findall(r'-(\d+)(?:\.?(\d+))?', prod_url)
                display_str = 'n/n'
                for whole, decimal in all_numbers:
                    num_str = f"{whole}.{decimal}" if decimal else whole
                    display_size = float(num_str)
                    # Convert 3-digit numbers like 156 to 15.6, 140 to 14.0
                    if display_size > 100:
                        display_size = display_size / 10
                        num_str = str(display_size)
                    # Only use if it's a reasonable display size (10-20 inches)
                    if 10 <= display_size <= 20:
                        display_str = num_str.replace(',', '.') + '"'
                        break
                
                color = display_str
                
                # Extract SSD storage from page (look for storage/capacità with larger values)
                storage_selectors = [
                    prod_soup.find('span', string=re.compile(r"Memoria|Storage|Capacità|SSD", re.I)),
                    prod_soup.find('div', string=re.compile(r"Memoria|Storage|Capacità|SSD", re.I)),
                    prod_soup.find('label', string=re.compile(r"Memoria|Storage|Capacità|SSD", re.I)),
                    prod_soup.find('dt', string=re.compile(r"Memoria|Storage|Capacità|SSD", re.I)),
                ]
                
                ssd_found = False
                for selector in storage_selectors:
                    if selector:
                        next_elem = selector.find_next_sibling()
                        if next_elem:
                            storage_text = next_elem.get_text(strip=True)
                            # Look for larger storage values (typically 256GB, 512GB, 1TB for SSD)
                            # Skip RAM values (usually 8GB, 16GB, 32GB)
                            for match in re.finditer(r'(\d+)\s*(GB|TB)', storage_text, re.I):
                                value = int(match.group(1))
                                unit = match.group(2).upper()
                                # If it's TB or large GB value (>64), it's likely SSD
                                if unit == 'TB' or value > 64:
                                    memory = f"{value * 1000 if unit == 'TB' else value} GB"
                                    ssd_found = True
                                    break
                            if ssd_found:
                                break
                
                # Fallback: try to extract SSD from title
                if not ssd_found:
                    title_text = title.get_text() if title else ""
                    ssd_match = re.search(r'(\d+)\s*(GB|TB)\s*SSD', title_text, re.I)
                    if ssd_match:
                        value = int(ssd_match.group(1))
                        unit = ssd_match.group(2).upper()
                        memory = f"{value * 1000 if unit == 'TB' else value} GB"
                    else:
                        # Try to find any large storage value in title
                        for match in re.finditer(r'(\d+)\s*(GB|TB)', title_text, re.I):
                            value = int(match.group(1))
                            unit = match.group(2).upper()
                            if unit == 'TB' or value > 64:
                                memory = f"{value * 1000 if unit == 'TB' else value} GB"
                                break
                
                # Clean model name for notebooks - remove NOTEBOOK, CHROMEBOOK, processore and processor codes
                model = re.sub(r'\s+NOTEBOOK\s*', ' ', model, flags=re.I)
                model = re.sub(r'\s+CHROMEBOOK\s*', ' ', model, flags=re.I)
                model = re.sub(r'\s+CONVERTIBILE\s*', ' ', model, flags=re.I)
                model = re.sub(r'\s*,\s*processore.*$', '', model, flags=re.I)
                model = re.sub(r'\s+processore.*$', '', model, flags=re.I)
                # Remove display size numbers from model name (like "14" in "GALAXY GO 14")
                # Only remove 1-2 digit numbers (display sizes), not 3-digit numbers like 360 (model name part)
                # Also protect known model name parts like 360
                if '360' not in model:
                    model = re.sub(r'\s+\d{1,2}\.?\d*\s*$', '', model, flags=re.I)
                # Remove specific processor codes (like N4500, X1-26-100, 226V, 255U, 355, 356H)
                # Be careful not to remove model name parts like "Book6"
                model = re.sub(r'\s+N\d+[A-Z]*$', '', model, flags=re.I)  # Intel Celeron N4500
                model = re.sub(r'\s+X\d+-\d+-\d+$', '', model, flags=re.I)  # Snapdragon X1-26-100
                model = re.sub(r'\s+\d{3}[A-Z]$', '', model, flags=re.I)  # Intel Core 226V, 255U, 355, 356H
                model = model.strip()
            
            
            print(f"    Extracted - Model: {model[:50]}, Memory: {memory}, Color: {color}, Type: {product_type}")
            
            products.append({
                "Marca": brand,
                "Tipo": product_type,
                "Modello": model,
                "Memoria": memory,
                "Colore": color,
                "Codice_PIM": pim
            })
            
            print(f"    ✓ Added: {model} - PIM: {pim}")
            
        except Exception as e:
            print(f"    Error scraping {prod_url}: {e}")
            continue
    
    return products

def scrape_brand_only(brand):
    """Scrape all products for a brand without category (fallback) using Selenium"""
    base_url = f"{BASE_URL}/{BRANDS[brand]}"
    products = []
    seen_urls = set()
    
    # Use Selenium to handle "Show more" button
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # FORCE DESKTOP VERSION AND ADD USER AGENT
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(f"user-agent={HEADERS['User-Agent']}")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(base_url)
        
        # Add WebDriverWait for dynamic elements
        wait = WebDriverWait(driver, 10)
        
        # 1. COOKIE BANNER HANDLING (Critical for unblocking subsequent clicks)
        try:
            cookie_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accetta tutti')]",
                "//button[@id='pwa-consent-layer-accept-all-button']",
                "//button[contains(@class, 'cookie')]"
            ]
            for selector in cookie_selectors:
                try:
                    cookie_btn = driver.find_element(By.XPATH, selector)
                    if cookie_btn.is_displayed():
                        driver.execute_script("arguments[0].click();", cookie_btn)
                        print("✓ Banner cookie accettato.")
                        time.sleep(2)
                        break
                except:
                    continue
        except Exception:
            print("Nessun banner cookie intercettato.")

        # Apply MediaWorld-only filter to exclude marketplace
        try:
            print("Applying MediaWorld-only filter...")
            # Click the label instead of the hidden input
            mw_label = driver.find_element(By.XPATH, "//label[contains(., 'MediaWorld') and not(contains(., 'CONSIGLIA'))]")
            if mw_label:
                input_elem = mw_label.find_element(By.TAG_NAME, "input")
                if not input_elem.is_selected():
                    driver.execute_script("arguments[0].click();", mw_label)
                    print("✓ MediaWorld filter applied")
                    time.sleep(3)  # Wait for filter to apply
                else:
                    print("✓ MediaWorld filter already selected")
        except Exception as e:
            print(f"Could not apply MediaWorld filter: {e}")

        # Click "Show more" button until no more products
        max_clicks = 40
        click_count = 0
        
        while click_count < max_clicks:
            try:
                # Scroll to bottom to force rendering
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                show_more_button = None
                
                # List of targeted selectors based on MediaWorld's actual structure
                selectors = [
                    (By.XPATH, "//button[@data-test='mms-search-srp-loadmore']"),
                    (By.XPATH, "//button[contains(@class, 'load-more')]"),
                    (By.XPATH, "//span[contains(text(), 'Mostra')]/parent::button"),
                    (By.XPATH, "//button[contains(., 'Mostra altri')]"),
                    (By.XPATH, "//button[contains(., 'Carica')]")
                ]
                
                for by_type, selector in selectors:
                    try:
                        # Simple find with retry - avoid strict clickable check
                        show_more_button = driver.find_element(by_type, selector)
                        if show_more_button and show_more_button.is_displayed():
                            print(f"Debug: Found button with selector: {selector}")
                            break
                    except:
                        continue
                
                if not show_more_button:
                    print("Nessun pulsante 'Mostra altri' trovato (fine catalogo raggiunta).")
                    break
                
                print(f"Clicco 'Mostra altri' (click {click_count + 1})")
                
                # Center button and execute click via JavaScript
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", show_more_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", show_more_button)
                
                click_count += 1
                time.sleep(4)  # Wait for new products DOM to load
                
            except Exception as e:
                print("Nessun altro pulsante intercettato o fine catalogo raggiunta.")
                break
        
        # Get all product links after clicking "Show more"
        soup = BeautifulSoup(driver.page_source, "html.parser")
        all_product_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/it/product' in href:
                full_url = href if href.startswith('http') else BASE_URL + href
                if full_url not in seen_urls:
                    all_product_links.append(full_url)
                    seen_urls.add(full_url)
        
        print(f"Total product links found after clicking 'Show more': {len(all_product_links)}")
        driver.quit()
        
    except Exception as e:
        print(f"Error with Selenium: {e}")
        # Fallback to regular requests if Selenium fails
        print("Falling back to regular requests (may not get all products)")
        try:
            response = requests.get(base_url, headers=HEADERS, timeout=30)
            soup = BeautifulSoup(response.text, "html.parser")
            all_product_links = []
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/it/product' in href:
                    full_url = href if href.startswith('http') else BASE_URL + href
                    if full_url not in seen_urls:
                        all_product_links.append(full_url)
                        seen_urls.add(full_url)
        except Exception as e2:
            print(f"Error with fallback: {e2}")
            return products
    
    # Scrape each product page
    for idx, prod_url in enumerate(all_product_links):
        print(f"  [{idx+1}/{len(all_product_links)}] Scraping: {prod_url}")
        
        try:
            time.sleep(1)
            prod_response = requests.get(prod_url, headers=HEADERS, timeout=30)
            prod_response.raise_for_status()
            prod_soup = BeautifulSoup(prod_response.text, "html.parser")
            
            if not is_mediaworld_product(prod_soup):
                print(f"    Skipping: Third-party seller")
                continue
            
            pim = extract_pim_code(prod_soup)
            if not pim:
                print(f"    Skipping: No PIM code found")
                continue
            
            if not re.match(r'^\d{6}$', pim):
                print(f"    Skipping: PIM {pim} is not 6 digits")
                continue
            
            title = prod_soup.find('h1')
            model = title.get_text(strip=True) if title else "Unknown"
            
            # Verify product is actually from the correct brand (check title contains brand name)
            if brand.lower() not in model.lower():
                print(f"    Skipping: Product '{model}' does not match brand '{brand}'")
                continue
            
            # Clean model name - remove brand prefix if present
            model = re.sub(r'^' + re.escape(brand) + r'\s*', '', model, flags=re.I)
            # Also remove brand name if it appears after type (e.g., "SMARTBAND SAMSUNG Galaxy FIT3")
            model = re.sub(r'\s+' + re.escape(brand) + r'\s+', ' ', model, flags=re.I)
            model = model.strip()
            
            # Remove "Tablet" prefix from model name
            model = re.sub(r'^Tablet\s+', '', model, flags=re.I)
            model = re.sub(r',\s*Tablet\s+', ', ', model, flags=re.I)
            
            # Remove display dimensions (e.g., "8,7 """, "11 """, "10.1""")
            model = re.sub(r'\s*\d+[,.]?\d*\s*["\']+\s*', '', model, flags=re.I)
            model = re.sub(r'\s*\d+[,.]?\d*\s*["\']+\s*,\s*', ', ', model, flags=re.I)
            
            # Remove memory from model name (patterns like "4/128GB", "256GB", "8+256GB")
            # More precise patterns to avoid leaving extra commas
            model = re.sub(r'\s*\d+/\d+\s*(GB|TB|MB)\s*', '', model, flags=re.I)
            model = re.sub(r'\s*\d+\+\d+\s*(GB|TB|MB)\s*', '', model, flags=re.I)
            model = re.sub(r'\s*\d+\s*(GB|TB|MB)\s*', '', model, flags=re.I)
            model = re.sub(r',\s*\d+\s*(GB|TB|MB)', '', model, flags=re.I)
            
            # Remove mm from model name (for smartwatches) - will be extracted as memory separately
            model = re.sub(r'\s*\d+\s*mm\s*', '', model, flags=re.I)
            model = re.sub(r',\s*\d+\s*mm\s*', '', model, flags=re.I)
            
            model = re.sub(r',\s*,\s*', ', ', model)  # Fix double commas
            model = re.sub(r'\s*,\s*$', '', model)  # Remove trailing comma
            model = re.sub(r'^\s*,\s*', '', model)  # Remove leading comma
            model = model.strip()
            
            # Remove bundle text from model name FIRST (before color extraction)
            bundle_patterns = [
                r',\s*cover e caricabatteria \d+W inclusi\s*$',
                r',\s*Magnetic Case \+ SUPERVOOC \d+W Power Adapter inclusi\s*$',
                r',\s*Magnetic Case inclusa\s*$',
                r',\s*Box\s*$',
                r',\s*cover e caric\s*$',
                r',\s*cover e carica\s*$',
            ]
            for pattern in bundle_patterns:
                model = re.sub(pattern, '', model, flags=re.I)
            model = re.sub(r'\s*,\s*$', '', model)  # Remove trailing comma after bundle removal
            model = model.strip()
            
            # Extract color from model name as fallback before removing it
            color_from_model = extract_color_from_model(model)
            
            # Remove color from model name (color should be in separate field only)
            # Common color names to remove from end of model name (English and Italian)
            color_patterns = [
                r',\s*(Black|White|Blue|Green|Red|Yellow|Orange|Purple|Pink|Gray|Grey|Silver|Gold|Brown|Beige|Cream|Ivory|Lavender|Rose|Navy|Cobalt|Titanium|Obsidian|Charcoal|Natural|Deep|Icy|Flowy|Cook|Asteroid|Graphite|Mint|Shadow|Jetblack|Icyblue)\s*$',
                r',\s*(Light\s+\w+|Dark\s+\w+|Awesome\s+\w+|Stellar\s+\w+|Lunar\s+\w+|Sky\s+\w+|Titanium\s+\w+|Violet\s+\w+)\s*$',
                r',\s*(Cobalt\s+Violet|Jet\s+Black|Light\s+Green|Awesome\s+Navy|Silver\s+Blue|White\s+Silver|Titanium\s+Gray|Titanium\s+Silverblue|Titanium\s+Whitesilver)\s*$',
                r',\s*(Canyon\s+Orange|Tundra\s+Umber|Aurora\s+White|Aurora\s+Blue|Twilight\s+Black|Dusk\s+Black|Titanium\s+Charcoal)\s*$',
                r',\s*(Silver\s+Shadow|Black/Blue|Black/White|Blue/Black|White/Black)\s*$',
                # Italian color patterns
                r',\s*(Nero|Bianco|Blu|Verde|Rosso|Giallo|Arancione|Viola|Rosa|Grigio|Argento|Oro|Marrone|Beige|Crema|Avorio|Lavanda|Navy|Cobalto|Titanio|Ossidiana|Carbone|Naturale|Profondo|Ghiaccio|Graphite|Menta)\s*$',
                r',\s*(Nero\s+ossidiana|Viola\s+lavanda|Bianco\s+argento|Nero\s+jet|Verde\s+chiaro|Blu\s+cobalto|Grigio\s+titanio)\s*$'
            ]
            
            # Also remove colors from middle of model name (for cases like "Galaxy S25, Icyblue")
            middle_color_patterns = [
                r',\s*(Jetblack|Icyblue|Silver\s+Shadow|Black/Blue)\s*,',
                r',\s*(Jetblack|Icyblue|Silver\s+Shadow|Black/Blue)\s*$'
            ]
            
            for pattern in color_patterns:
                model = re.sub(pattern, '', model, flags=re.I)
            
            # Apply middle color patterns
            for pattern in middle_color_patterns:
                model = re.sub(pattern, ',', model, flags=re.I)
            
            model = re.sub(r'\s*,\s*$', '', model)  # Remove trailing comma after color removal
            model = re.sub(r',\s*,\s*', ', ', model)  # Fix double commas
            model = model.strip()
            
            color = extract_color(prod_soup, prod_url)
            # Use color from model as fallback if page extraction fails
            if not color and color_from_model:
                color = color_from_model
            # Replace empty color with "n/n"
            if not color or color.strip() == '':
                color = 'n/n'
            
            memory = extract_memory(prod_soup, model)
            
            # Determine product type
            product_type = determine_product_type(model, category)
            
            # Special handling for notebooks
            if product_type == 'Notebook':
                # Extract display size for color field
                # Try to extract from URL first (more reliable)
                # Find all numbers in URL and pick the one that looks like display size
                all_numbers = re.findall(r'-(\d+)(?:\.?(\d+))?', prod_url)
                display_str = 'n/n'
                for whole, decimal in all_numbers:
                    num_str = f"{whole}.{decimal}" if decimal else whole
                    display_size = float(num_str)
                    # Convert 3-digit numbers like 156 to 15.6, 140 to 14.0
                    if display_size > 100:
                        display_size = display_size / 10
                        num_str = str(display_size)
                    # Only use if it's a reasonable display size (10-20 inches)
                    if 10 <= display_size <= 20:
                        display_str = num_str.replace(',', '.') + '"'
                        break
                
                color = display_str
                
                # Extract SSD storage from page (look for storage/capacità with larger values)
                storage_selectors = [
                    prod_soup.find('span', string=re.compile(r"Memoria|Storage|Capacità|SSD", re.I)),
                    prod_soup.find('div', string=re.compile(r"Memoria|Storage|Capacità|SSD", re.I)),
                    prod_soup.find('label', string=re.compile(r"Memoria|Storage|Capacità|SSD", re.I)),
                    prod_soup.find('dt', string=re.compile(r"Memoria|Storage|Capacità|SSD", re.I)),
                ]
                
                ssd_found = False
                for selector in storage_selectors:
                    if selector:
                        next_elem = selector.find_next_sibling()
                        if next_elem:
                            storage_text = next_elem.get_text(strip=True)
                            # Look for larger storage values (typically 256GB, 512GB, 1TB for SSD)
                            # Skip RAM values (usually 8GB, 16GB, 32GB)
                            for match in re.finditer(r'(\d+)\s*(GB|TB)', storage_text, re.I):
                                value = int(match.group(1))
                                unit = match.group(2).upper()
                                # If it's TB or large GB value (>64), it's likely SSD
                                if unit == 'TB' or value > 64:
                                    memory = f"{value * 1000 if unit == 'TB' else value} GB"
                                    ssd_found = True
                                    break
                            if ssd_found:
                                break
                
                # Fallback: try to extract SSD from title
                if not ssd_found:
                    title_text = title.get_text() if title else ""
                    ssd_match = re.search(r'(\d+)\s*(GB|TB)\s*SSD', title_text, re.I)
                    if ssd_match:
                        value = int(ssd_match.group(1))
                        unit = ssd_match.group(2).upper()
                        memory = f"{value * 1000 if unit == 'TB' else value} GB"
                    else:
                        # Try to find any large storage value in title
                        for match in re.finditer(r'(\d+)\s*(GB|TB)', title_text, re.I):
                            value = int(match.group(1))
                            unit = match.group(2).upper()
                            if unit == 'TB' or value > 64:
                                memory = f"{value * 1000 if unit == 'TB' else value} GB"
                                break
                
                # Clean model name for notebooks - remove NOTEBOOK, CHROMEBOOK, processore and processor codes
                model = re.sub(r'\s+NOTEBOOK\s*', ' ', model, flags=re.I)
                model = re.sub(r'\s+CHROMEBOOK\s*', ' ', model, flags=re.I)
                model = re.sub(r'\s+CONVERTIBILE\s*', ' ', model, flags=re.I)
                model = re.sub(r'\s*,\s*processore.*$', '', model, flags=re.I)
                model = re.sub(r'\s+processore.*$', '', model, flags=re.I)
                # Remove display size numbers from model name (like "14" in "GALAXY GO 14")
                # Only remove 1-2 digit numbers (display sizes), not 3-digit numbers like 360 (model name part)
                # Also protect known model name parts like 360
                if '360' not in model:
                    model = re.sub(r'\s+\d{1,2}\.?\d*\s*$', '', model, flags=re.I)
                # Remove specific processor codes (like N4500, X1-26-100, 226V, 255U, 355, 356H)
                # Be careful not to remove model name parts like "Book6"
                model = re.sub(r'\s+N\d+[A-Z]*$', '', model, flags=re.I)  # Intel Celeron N4500
                model = re.sub(r'\s+X\d+-\d+-\d+$', '', model, flags=re.I)  # Snapdragon X1-26-100
                model = re.sub(r'\s+\d{3}[A-Z]$', '', model, flags=re.I)  # Intel Core 226V, 255U, 355, 356H
                model = model.strip()
            
            
            # Debug: print extracted values
            print(f"    Extracted - Model: {model[:50]}, Memory: {memory}, Color: {color}, Type: {product_type}")
            
            products.append({
                "Marca": brand,
                "Tipo": product_type,
                "Modello": model,
                "Memoria": memory,
                "Colore": color,
                "Codice_PIM": pim
            })
            
            print(f"    ✓ Added: {model} - PIM: {pim}")
            
        except Exception as e:
            print(f"    Error scraping {prod_url}: {e}")
            continue
    
    return products

def import_to_database(new_products):
    """Import scraped products into database_telefoni.csv"""
    database_file = "database_telefoni.csv"
    
    # Load existing database
    existing_products = []
    if os.path.exists(database_file):
        with open(database_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing_products = list(reader)
    
    # Create a set of existing PIM codes to avoid duplicates
    existing_pims = {p['Codice_PIM'] for p in existing_products if p.get('Codice_PIM')}
    
    # Add new products that don't already exist
    added_count = 0
    for product in new_products:
        if product['Codice_PIM'] not in existing_pims:
            existing_products.append(product)
            existing_pims.add(product['Codice_PIM'])
            added_count += 1
    
    # Save updated database
    with open(database_file, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Marca", "Tipo", "Modello", "Memoria", "Colore", "Codice_PIM"])
        writer.writeheader()
        for product in existing_products:
            writer.writerow(product)
    
    print(f"\nImported {added_count} new products to {database_file}")
    print(f"Total products in database: {len(existing_products)}")

def main():
    """Main scraping function"""
    import sys
    
    # Check if brand is specified as command line argument
    if len(sys.argv) > 1:
        selected_brand = sys.argv[1]
        if selected_brand not in BRANDS:
            print(f"Error: Brand '{selected_brand}' not found. Available brands: {', '.join(BRANDS.keys())}")
            sys.exit(1)
        brands_to_scrape = [selected_brand]
        # Check if category is specified as second argument
        if len(sys.argv) > 2:
            selected_category = sys.argv[2]
            # Override categories for this brand
            CATEGORIES[selected_brand] = [selected_category]
    else:
        # Interactive brand selection
        print("Available brands:")
        for idx, brand in enumerate(BRANDS.keys(), 1):
            print(f"  {idx}. {brand}")
        
        try:
            choice = input("\nSelect brand number (or 'all' for all brands): ").strip()
            if choice.lower() == 'all':
                brands_to_scrape = list(BRANDS.keys())
            else:
                brand_idx = int(choice) - 1
                if 0 <= brand_idx < len(BRANDS):
                    brands_to_scrape = [list(BRANDS.keys())[brand_idx]]
                else:
                    print("Invalid selection. Exiting.")
                    sys.exit(1)
        except (ValueError, KeyboardInterrupt):
            print("\nInvalid input or cancelled. Exiting.")
            sys.exit(1)
        
        # Ask for category selection if brand has multiple categories
        if len(brands_to_scrape) == 1:
            brand = brands_to_scrape[0]
            brand_categories = CATEGORIES.get(brand)
            if brand_categories and len(brand_categories) > 1:
                print(f"\nAvailable categories for {brand}:")
                for idx, cat in enumerate(brand_categories, 1):
                    print(f"  {idx}. {cat}")
                print(f"  {len(brand_categories) + 1}. All categories")
                
                try:
                    cat_choice = input(f"\nSelect category number (default: all): ").strip()
                    if cat_choice:
                        cat_idx = int(cat_choice) - 1
                        if 0 <= cat_idx < len(brand_categories):
                            CATEGORIES[brand] = [brand_categories[cat_idx]]
                        elif cat_idx == len(brand_categories):
                            # Keep all categories
                            pass
                        else:
                            print("Invalid selection. Using all categories.")
                    else:
                        # Default: all categories
                        pass
                except (ValueError, KeyboardInterrupt):
                    print("\nUsing all categories.")
    
    all_products = []
    
    # Scrape selected brands
    for brand in brands_to_scrape:
        print(f"\n{'='*60}")
        print(f"Scraping brand: {brand}")
        print(f"{'='*60}")
        
        brand_categories = CATEGORIES.get(brand)
        if brand_categories is None:
            # Use filter-based scraping for brands without specific categories
            products = scrape_with_filters(brand)
            all_products.extend(products)
        else:
            # Use category-based scraping for brands with specific categories
            for category in brand_categories:
                products = scrape_category_products(brand, category)
                all_products.extend(products)
    
    # Save to CSV
    if all_products:
        # Sort products by model name alphabetically
        all_products.sort(key=lambda x: x['Modello'])
        
        output_file = "mediaworld_products.csv"
        with open(output_file, "w", encoding="utf-8") as f:
            # Write header
            f.write("Marca,Tipo,Modello,Memoria,Colore,Codice_PIM\n")
            # Write each product manually to avoid CSV quoting
            for product in all_products:
                line = f"{product['Marca']},{product['Tipo']},{product['Modello']},{product['Memoria']},{product['Colore']},{product['Codice_PIM']}\n"
                f.write(line)
        
        print(f"\n{'='*60}")
        print(f"Scraping complete!")
        print(f"Total products found: {len(all_products)}")
        print(f"Saved to: {output_file}")
        print(f"{'='*60}")
        
        # Ask if user wants to import to database
        try:
            import_choice = input("\nDo you want to import these products to database_telefoni.csv? (y/n): ").strip().lower()
            if import_choice == 'y':
                import_to_database(all_products)
        except (EOFError, KeyboardInterrupt):
            print("\nSkipping import to database.")
    else:
        print("\nNo products found.")

if __name__ == "__main__":
    main()
