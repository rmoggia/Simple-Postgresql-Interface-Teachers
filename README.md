# PG Admin Lite

Interfaccia web leggera per PostgreSQL costruita con Flask e psycopg2.

## Requisiti

- Python 3.8+
- PostgreSQL accessibile in rete

## Installazione

```bash
# 1. Entra nella cartella del progetto
cd pg_admin_lite

# 2. Crea un ambiente virtuale (consigliato)
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Installa le dipendenze
pip install -r requirements.txt

# 4. Avvia l'applicazione
python app.py
```

Apri il browser su: **http://localhost:5000**

## Funzionalità

| Sezione | Descrizione |
|---------|-------------|
| **Login** | Connessione con host, porta, database, utente e password |
| **Dashboard** | Lista degli schemi e delle tabelle |
| **Dati tabella** | Visualizzazione paginata con ordinamento colonne |
| **Inserisci riga** | Form per aggiungere nuovi record |
| **Modifica riga** | Editing inline di un record esistente |
| **Elimina riga** | Rimozione con conferma |
| **Query SQL** | Editor SQL libero con Ctrl+Enter per eseguire |
| **Struttura** | Dettaglio colonne, tipi, PK + editor DDL |

## Note di sicurezza

- Le credenziali del DB sono salvate solo nella sessione Flask (in memoria), non su disco
- Cambia `SECRET_KEY` in `config.py` in ambienti di produzione
- Non esporre questa applicazione su internet senza autenticazione aggiuntiva

## Struttura progetto

```
pg_admin_lite/
├── app.py          # Applicazione Flask, routes
├── db.py           # Gestione connessione e query PostgreSQL
├── config.py       # Configurazione
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── table_view.html
│   ├── row_form.html
│   ├── query.html
│   └── structure.html
└── static/
    └── style.css
```
