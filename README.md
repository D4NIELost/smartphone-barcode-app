# 📱 App Barcode Smartphone

Web app ottimizzata per smartphone per la ricerca e generazione di codici a barre di telefoni cellulari. Realizzata con Streamlit, permette ai dipendenti di un negozio di elettronica di cercare rapidamente i modelli di smartphone e generare codici a barre scansionabili con tablet aziendali.

## 🔒 Sicurezza

L'app è protetta da password. All'apertura viene richiesto di inserire una password condivisa per accedere alle funzionalità principali.

## ✨ Funzionalità

- **Protezione con password**: Accesso riservato ai dipendenti autorizzati
- **Ricerca rapida**: Barra di ricerca reattiva per trovare smartphone per marca, modello o codice articolo
- **Generazione codici a barre**: Creazione automatica di codici a barre Code128 ottimizzati per la scansione
- **Interfaccia mobile-first**: Design ottimizzato per smartphone e tablet
- **Database CSV**: Dati caricati da file CSV locale (facilmente espandibile)

## 📋 Requisiti

- Python 3.8 o superiore
- pip (gestore pacchetti Python)

## 🚀 Installazione

1. **Clona o scarica il progetto** nella directory desiderata

2. **Installa le dipendenze**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura la password**:
   - Apri il file `app.py`
   - Modifica la variabile `PASSWORD` alla riga 8 con la tua password desiderata:
   ```python
   PASSWORD = "tua_password_sicura"
   ```

4. **Prepara il database**:
   - Il file `database_telefoni.csv` contiene dati di esempio
   - Puoi modificarlo aggiungendo i tuoi dati seguendo il formato:
   ```csv
   Marca,Modello,Codice_Articolo
   Samsung,Galaxy S24 Ultra,8806094751234
   Apple,iPhone 15 Pro,1942537890123
   ```

## 🎯 Utilizzo

1. **Avvia l'app**:
   ```bash
   streamlit run app.py
   ```

2. **Apri il browser**:
   - L'app sarà disponibile all'indirizzo: `http://localhost:8501`

3. **Accedi all'app**:
   - Inserisci la password configurata
   - Clicca su "Accedi"

4. **Cerca smartphone**:
   - Digita il nome del telefono nella barra di ricerca (es. "S24 Ultra", "iPhone 15 Pro")
   - I risultati appariranno in tempo reale

5. **Genera codice a barre**:
   - Seleziona un telefono dai risultati
   - Clicca su "Genera Codice a Barre"
   - Il codice a barre apparirà grande e nitido per facilitare la scansione

## 📁 Struttura del Progetto

```
smartphone-barcode-app/
├── app.py                      # File principale dell'applicazione Streamlit
├── database_telefoni.csv       # Database CSV con i dati degli smartphone
├── requirements.txt            # Dipendenze Python
└── README.md                   # Questo file
```

## 🔧 Personalizzazione

### Modificare la password

Modifica la variabile `PASSWORD` nel file `app.py` (riga 8):

```python
PASSWORD = "nuova_password"
```

### Aggiungere/Modificare dati

Modifica il file `database_telefoni.csv` aggiungendo o modificando righe. Assicurati di mantenere le colonne:
- `Marca`: Es. Samsung, Apple, Google
- `Modello`: Es. Galaxy S24 Ultra, iPhone 15 Pro
- `Codice_Articolo`: Codice EAN o codice interno (deve essere compatibile con Code128)

### Configurazione codice a barre

Puoi modificare le impostazioni del codice a barre nella funzione `generate_barcode()` nel file `app.py` (righe 30-38):

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
- **Smartphone**: Input touch-friendly, font leggibili
- **Tablet**: Codici a barre grandi e ad alto contrasto per facile scansione
- **Desktop**: Interfaccia pulita e intuitiva

## 🔒 Note sulla Sicurezza

- La password è hardcoded nel file `app.py`. Per ambienti di produzione, considera l'uso di variabili d'ambiente o un sistema di autenticazione più robusto.
- L'app non cripta i dati in transito. Per uso in produzione, considera l'uso di HTTPS.

## 🐛 Risoluzione Problemi

### Il database non viene caricato
- Verifica che il file `database_telefoni.csv` sia nella stessa directory di `app.py`
- Controlla che il CSV abbia le colonne corrette: `Marca`, `Modello`, `Codice_Articolo`

### Il codice a barre non viene generato
- Verifica che il `Codice_Articolo` sia compatibile con il formato Code128 (caratteri alfanumerici standard)
- Controlla i log di errore nell'interfaccia per dettagli specifici

### L'app è lenta
- Riduci il numero di righe nel CSV se contiene migliaia di prodotti
- Considera l'uso di un database più performante per grandi volumi di dati

## 📄 Licenza

Questo progetto è fornito così com'è per uso interno aziendale.

## 🤝 Supporto

Per problemi o domande, contatta l'amministratore di sistema o il team IT.
