#!/usr/bin/env python3
"""
Script per generare hash password sicuro per l'app barcode.
Esegui questo script per generare SALT e PASSWORD_HASH da inserire in app.py
"""

import hashlib
import secrets

def generate_password_hash(password: str) -> tuple[str, str]:
    """
    Genera un salt e un hash SHA-256 per la password fornita.
    
    Args:
        password: La password in chiaro
        
    Returns:
        Tuple (salt, password_hash) da inserire in app.py
    """
    # Generate a random 16-byte salt (32 hex characters)
    salt = secrets.token_hex(16)
    
    # Generate SHA-256 hash of password + salt
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    
    return salt, password_hash

if __name__ == "__main__":
    print("=== Generatore Hash Password Admin ===\n")
    
    while True:
        password = input("Inserisci la password admin (o 'q' per uscire): ").strip()
        
        if password.lower() == 'q':
            print("\nUscita...")
            break
        
        if not password:
            print("❌ Password non può essere vuota!\n")
            continue
        
        if len(password) < 6:
            print("⚠️  Avviso: La password dovrebbe avere almeno 6 caratteri per sicurezza.\n")
        
        salt, password_hash = generate_password_hash(password)
        
        print("\n✅ Hash generato con successo!")
        print("\nCopia queste righe in app.py:")
        print("-" * 50)
        print(f"SALT = \"{salt}\"")
        print(f"PASSWORD_HASH = \"{password_hash}\"")
        print("ADMIN_PASSWORD_ENABLED = True")
        print("-" * 50)
        print("\n⚠️  IMPORTANTE:")
        print("- Non condividere questi valori con nessuno")
        print("- Non caricare la password in chiaro su GitHub")
        print("- Conserva questi valori in un luogo sicuro")
        print()
