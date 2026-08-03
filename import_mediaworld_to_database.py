import csv
import os
from collections import defaultdict

# Configuration
MEDIAWORLD_OUTPUT = "mediaworld_products.csv"
DATABASE_DIR = "databases"

# Database file mappings based on product type
DATABASE_FILES = {
    "Smartphone": os.path.join(DATABASE_DIR, "database_smartphone.csv"),
    "Tablet": os.path.join(DATABASE_DIR, "database_tablet.csv"),
    "Smartwatch": os.path.join(DATABASE_DIR, "database_smartwatch.csv"),
    "Notebook": os.path.join(DATABASE_DIR, "database_notebook.csv")  # Will create if needed
}

# Column mappings for each database type
# Maps scraper columns to database columns
COLUMN_MAPPINGS = {
    "Smartphone": {
        "Marca": "Marca",
        "Tipo": "Tipo",
        "Modello": "Modello",
        "Memoria": "Memoria",
        "Colore": "Colore",
        "Codice_PIM": "Codice_PIM"
    },
    "Tablet": {
        "Marca": "Marca",
        "Tipo": "Tipo",
        "Modello": "Modello",
        "Memoria": "Memoria",
        "Codice_PIM": "Codice_PIM"
    },
    "Smartwatch": {
        "Marca": "Marca",
        "Tipo": "Tipo",
        "Modello": "Modello",
        "mm": "mm",
        "Colore": "Colore",
        "Codice_PIM": "Codice_PIM"
    },
    "Notebook": {
        "Marca": "Marca",
        "Tipo": "Tipo",
        "Modello": "Modello",
        "Memoria": "Memoria",
        "pollici": "pollici",
        "Codice_PIM": "Codice_PIM"
    }
}

def read_existing_pims(database_file):
    """Read existing PIM codes from a database file to avoid duplicates"""
    existing_pims = set()
    if not os.path.exists(database_file):
        return existing_pims
    
    try:
        with open(database_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'Codice_PIM' in row and row['Codice_PIM']:
                    existing_pims.add(row['Codice_PIM'])
    except Exception as e:
        print(f"Warning: Could not read existing PIMs from {database_file}: {e}")
    
    return existing_pims

def map_product_to_database(product, product_type):
    """Map product fields to database-specific columns"""
    mapping = COLUMN_MAPPINGS.get(product_type, {})
    mapped_product = {}
    
    for scraper_col, db_col in mapping.items():
        if scraper_col in product:
            mapped_product[db_col] = product[scraper_col]
    
    return mapped_product

def import_products():
    """Import products from mediaworld output to appropriate databases"""
    # Check if output file exists
    if not os.path.exists(MEDIAWORLD_OUTPUT):
        print(f"Error: {MEDIAWORLD_OUTPUT} not found. Run mediaworld_scraper.py first.")
        return
    
    # Read all products from scraper output
    products_by_type = defaultdict(list)
    
    with open(MEDIAWORLD_OUTPUT, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            product_type = row.get('Tipo', 'Smartphone')
            products_by_type[product_type].append(row)
    
    print(f"Found {sum(len(products) for products in products_by_type.values())} products to import")
    
    # Import each product type to its database
    total_imported = 0
    total_skipped = 0
    
    for product_type, products in products_by_type.items():
        if product_type not in DATABASE_FILES:
            print(f"Warning: No database mapping for product type '{product_type}'. Skipping {len(products)} products.")
            continue
        
        database_file = DATABASE_FILES[product_type]
        print(f"\nProcessing {product_type}: {len(products)} products")
        
        # Read existing PIMs to avoid duplicates
        existing_pims = read_existing_pims(database_file)
        print(f"  Existing PIMs in database: {len(existing_pims)}")
        
        # Prepare new products to add
        products_to_add = []
        skipped_count = 0
        
        for product in products:
            pim = product.get('Codice_PIM', '')
            
            # Skip if PIM already exists or is empty
            if not pim or pim in existing_pims:
                skipped_count += 1
                continue
            
            # Map product fields to database structure
            mapped_product = map_product_to_database(product, product_type)
            products_to_add.append(mapped_product)
            existing_pims.add(pim)  # Mark as seen to avoid duplicates within this batch
        
        print(f"  New products to add: {len(products_to_add)}")
        print(f"  Skipped (duplicates/empty): {skipped_count}")
        
        if not products_to_add:
            continue
        
        # Get the correct column order for this database type
        column_mapping = COLUMN_MAPPINGS[product_type]
        fieldnames = list(column_mapping.values())
        
        # Check if database file exists
        file_exists = os.path.exists(database_file)
        
        # Append products to database
        try:
            with open(database_file, 'a', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # Write header if file is new or empty
                if not file_exists or os.path.getsize(database_file) == 0:
                    writer.writeheader()
                
                # Write products
                for product in products_to_add:
                    writer.writerow(product)
            
            print(f"  ✓ Successfully imported {len(products_to_add)} products to {database_file}")
            total_imported += len(products_to_add)
            total_skipped += skipped_count
            
        except Exception as e:
            print(f"  Error writing to {database_file}: {e}")
    
    print(f"\n{'='*50}")
    print(f"Import complete!")
    print(f"Total imported: {total_imported}")
    print(f"Total skipped: {total_skipped}")
    print(f"{'='*50}")

if __name__ == "__main__":
    import_products()
