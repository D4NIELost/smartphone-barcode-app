# 📱 App Barcode Dispositivi

Web app ottimizzata per smartphone per la ricerca e generazione di codici a barre di dispositivi elettronici. Realizzata con Streamlit, permette ai dipendenti di un negozio di elettronica di cercare rapidamente smartphone, smartwatch, tablet, notebook e servizi, generando codici a barre ITF-25 scansionabili con tablet aziendali.

## 🔒 Sicurezza

L'app può essere protetta da password. Attualmente l'autenticazione è disabilitata (modificabile nel file `app.py`).

## ✨ Funzionalità

- **Protezione con password** (opzionale): Accesso riservato ai dipendenti autorizzati
- **Catalogo completo**: Smartphone, Smartwatch, Tablet, Notebook e Servizi
- **Ricerca rapida**: Barra di ricerca reattiva per trovare prodotti per marca, modello o codice PIM
- **Generazione codici a barre**: Creazione automatica di codici a barre ITF-25 ottimizzati per la scansione
- **Interfaccia mobile-first**: Design ottimizzato per smartphone e tablet
- **Database CSV**: Dati caricati da file CSV nella cartella `databases/` (facilmente espandibile)
- **Navigazione gerarchica**: Marchio → Categoria → Modello → Specifiche → Colore → Barcode

## 📋 Requisiti

- Python 3.8 o superiore
- pip (gestore pacchetti Python)

## 🚀 Installazione

1. **Clona o scarica il progetto** nella directory desiderata

2. **Installa le dipendenze**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura la password** (opzionale):
   - Apri il file `app.py`
   - Modifica la variabile `PASSWORD` alla riga 11:
   ```python
   PASSWORD = "tua_password_sicura"  # Imposta la password desiderata
   # PASSWORD = None  # Disabilita l'autenticazione
   ```

4. **Prepara i database**:
   - I file CSV sono nella cartella `databases/`
   - `database_smartphone.csv`: Database smartphone (colonne: Marca, Tipo, Modello, Memoria, Colore, Codice_PIM)
   - `database_smartwatch.csv`: Database smartwatch (colonne: Marca, Tipo, Modello, mm, Colore, Codice_PIM)
   - `database_tablet.csv`: Database tablet (colonne: Marca, Tipo, Modello, Memoria, Codice_PIM)
   - `database_notebook.csv`: Database notebook (colonne: Marca, Tipo, Modello, Memoria, pollici, Codice_PIM)
   - `database_servizi.csv`: Database servizi (colonne: Categoria, Sottocategoria, Servizio, Codice, Costo)

## 🎯 Utilizzo

1. **Avvia l'app**:
   ```bash
   streamlit run app.py
   ```

2. **Apri il browser**:
   - L'app sarà disponibile all'indirizzo: `http://localhost:8501`

3. **Accedi all'app** (se password abilitata):
   - Inserisci la password configurata
   - Clicca su "Accedi"

4. **Naviga nel catalogo**:
   - **Dispositivi**: Seleziona Marchio → Categoria (Smartphone/Smartwatch/Tablet/Notebook) → Modello → Specifiche → Colore
   - **Servizi**: Seleziona Categoria → Sottocategoria → Servizio

5. **Ricerca rapida**:
   - Usa la barra di ricerca per trovare prodotti per marca, modello o codice PIM
   - I risultati appariranno in tempo reale

6. **Genera codice a barre**:
   - Seleziona un prodotto/servizio
   - Il codice a barre ITF-25 verrà generato automaticamente con il codice PIM

## 📁 Struttura del Progetto

```
smartphone-barcode-app/
├── app.py                      # File principale dell'applicazione Streamlit
├── databases/                  # Cartella con i database CSV
│   ├── database_smartphone.csv
│   ├── database_smartwatch.csv
│   ├── database_tablet.csv
│   ├── database_notebook.csv
│   └── database_servizi.csv
├── images/                     # Cartella per le immagini (loghi marchi, colori, modelli)
│   ├── brands/
│   ├── colors/
│   └── models/
├── requirements.txt            # Dipendenze Python
├── mediaworld_scraper.py       # Script per scraping prodotti Mediaworld
├── mediaworld_products.csv     # Output dello scraper
└── README.md                   # Questo file
```

## 🔧 Personalizzazione

### Modificare la password

Modifica la variabile `PASSWORD` nel file `app.py` (riga 11):

```python
PASSWORD = "nuova_password"  # Abilita autenticazione
# PASSWORD = None  # Disabilita autenticazione
```

### Aggiungere/Modificare dati

Modifica i file CSV nella cartella `databases/` aggiungendo o modificando righe:

**Smartphone** (`database_smartphone.csv`):
- Colonne: Marca, Tipo, Modello, Memoria, Colore, Codice_PIM
- Esempio: Samsung,Smartphone,Galaxy S24 Ultra,256GB,Black,411110

**Smartwatch** (`database_smartwatch.csv`):
- Colonne: Marca, Tipo, Modello, mm, Colore, Codice_PIM
- Esempio: Apple,Smartwatch,Watch Series 9,45mm,Black,411118

**Tablet** (`database_tablet.csv`):
- Colonne: Marca, Tipo, Modello, Memoria, Codice_PIM
- Esempio: Apple,Tablet,iPad Air 128GB,128GB,411112

**Notebook** (`database_notebook.csv`):
- Colonne: Marca, Tipo, Modello, Memoria, pollici, Codice_PIM
- Esempio: Apple,Notebook,MacBook Air 13,256GB,13.6,431292

**Servizi** (`database_servizi.csv`):
- Colonne: Categoria, Sottocategoria, Servizio, Codice, Costo
- Esempio: Servizi Generali,Computer,PRIMO AVVIO COMPUTER,433214,19.99

### Configurazione codice a barre

Puoi modificare le impostazioni del codice a barre ITF-25 nella funzione `generate_barcode()` nel file `app.py` (righe 127-133):

```python
options = {
    'module_width': 0.4,      # Larghezza di ogni barra
    'module_height': 15.0,    # Altezza delle barre
    'font_size': 14,          # Dimensione del testo sotto il codice
    'text_distance': 5.0,    # Distanza tra codice e testo
    'quiet_zone': 6.5,        # Spazio bianco attorno al codice
}
```

## 🌐 Accesso Remoto

Per rendere l'app accessibile da altri dispositivi nella rete locale:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Poi accedi dall'indirizzo IP del computer che ospita l'app.

## 📱 Note sull'Interfaccia

L'app è ottimizzata per:
- **Smartphone**: Input touch-friendly, font leggibili, navigazione a pulsanti
- **Tablet**: Codici a barre grandi e ad alto contrasto per facile scansione
- **Desktop**: Interfaccia pulita e intuitiva

## 🔒 Note sulla Sicurezza

- La password è configurabile nel file `app.py`. Per ambienti di produzione, considera l'uso di variabili d'ambiente o un sistema di autenticazione più robusto.
- L'app non cripta i dati in transito. Per uso in produzione, considera l'uso di HTTPS.

## 🐛 Risoluzione Problemi

### Il database non viene caricato
- Verifica che i file CSV siano nella cartella `databases/`
- Controlla che i CSV abbiano le colonne corrette per ogni categoria
- Assicurati che i file siano in formato UTF-8

### Il codice a barre non viene generato
- Verifica che il `Codice_PIM` sia un valore numerico valido per ITF-25
- Il codice PIM viene convertito rimuovendo punti e virgole prima della generazione
- Controlla i log di errore nell'interfaccia per dettagli specifici

### L'app è lenta
- Riduci il numero di righe nei CSV se contengono migliaia di prodotti
- Considera l'uso di un database più performante per grandi volumi di dati

### I colori non vengono visualizzati correttamente
- I colori sono mappati nel file `app.py` (funzione `show_colors_view`)
- Per aggiungere nuovi colori, modifica il dizionario `color_map` nel codice

## 📄 Licenza

Questo progetto è fornito così com'è per uso interno aziendale.

## 🤝 Supporto

Per problemi o domande, contatta l'amministratore di sistema o il team IT.
