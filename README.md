# Prenotazione campi sportivi

[![Test](https://github.com/diegorosiglioni/prenotazione_campi/actions/workflows/tests.yml/badge.svg?branch=develop)](https://github.com/diegorosiglioni/prenotazione_campi/actions/workflows/tests.yml)

> 🚧 **Progetto in lavorazione.** Le funzionalità vengono sviluppate a pezzi; lo stato aggiornato è nella sezione [Stato del progetto](#stato-del-progetto).

Web app per gestire le prenotazioni di **5 campi sportivi** (calcio, 2 campi da tennis, pallacanestro, bocce).
Sostituisce le prenotazioni a voce, al bar e per telefono con un'unica agenda online e impedisce che due persone prenotino lo stesso campo nello stesso orario.

Progetto scolastico realizzato con **Django** e **PostgreSQL**, partendo da requisiti scritti e numerati (`RF-xx`, `RNF-xx`) e procedendo un pezzo alla volta, ognuno con il suo piano, i suoi test e una Pull Request.

## Funzionalità

*Le voci con 🔄 fanno parte del pezzo 3, in revisione.*

**Tesserato**
- accesso con codice tessera e password, cambio password e lingua (italiano / inglese);
- 🔄 calendario dei campi, prenotazione e storico delle proprie prenotazioni;
- 🔄 regole applicate dal sistema: nessuna sovrapposizione, massimo 3 prenotazioni attive, slot a passi di 15 minuti negli orari di apertura.

**Admin** (un unico account, usato dal gestore o dal bar)
- gestione dei tesserati: creazione, modifica, disattivazione;
- 🔄 prezzi per tipo di campo e blocchi dei campi;
- registro di tutte le azioni dell'admin.

## Punti tecnici

- 🔄 **Nessuna doppia prenotazione, anche con richieste simultanee:** il controllo è fatto nel database con un vincolo di esclusione PostgreSQL (`btree_gist`) e con le transazioni, non solo nelle view. Ci sono test di concorrenza dedicati.
- **Orari corretti con l'ora legale:** date timezone-aware su `Europe/Rome`; l'ora corrente passa da un unico punto (`common.now()`), così i test possono fissarla.
- **Sicurezza del login:** limite ai tentativi falliti, validazione delle password, utente personalizzato con codice tessera.
- **Registro azioni:** ogni azione dell'admin viene salvata nella stessa transazione dell'operazione.
- **Interfaccia bilingue:** tutti i testi passano da gettext (italiano predefinito, inglese).
- **Test automatici e CI:** oltre 100 test; GitHub Actions esegue controlli, migrazioni e test su PostgreSQL a ogni push e Pull Request.
- **Documentazione:** requisiti, specifiche tecniche, decisioni e piano di ogni pezzo sono nella cartella [`docs/`](docs/).

## Tecnologie

Python 3.13 · Django 5.2 · PostgreSQL 18 · Docker Compose · HTMX · GitHub Actions

## Stato del progetto

| Pezzo | Stato |
| --- | --- |
| 1. Base del progetto (Django, PostgreSQL in Docker, traduzioni, CI) | ✅ Completato |
| 2. Account e login | ✅ Completato |
| 3. Campi e prenotazione (calendario, vincoli, concorrenza) | 🔄 In revisione sul branch `feature/campi-prenotazione` |
| 4. Cancellazioni | ⏳ Da fare |
| 5. Esiti, pagamenti, debiti e strike | ⏳ Da fare |
| 6. Notifiche e job giornaliero | ⏳ Da fare |
| 7. Pannello admin e deploy | ⏳ Da fare |

## Avvio in locale (Windows)

Servono Python 3.13, Docker Desktop e gettext.

```powershell
# 1. Ambiente Python e dipendenze
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2. Configurazione: copia il modello e compila DJANGO_SECRET_KEY e POSTGRES_PASSWORD
Copy-Item .env.example .env

# 3. Database PostgreSQL in Docker
docker compose up -d db

# 4. Migrazioni, traduzioni e account admin
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py compilemessages --ignore=.venv
.\.venv\Scripts\python.exe manage.py create_admin

# 5. Avvio
.\.venv\Scripts\python.exe manage.py runserver
```

Test:

```powershell
.\.venv\Scripts\python.exe manage.py test --noinput
```

## Struttura

```
accounts/        utente personalizzato, login, password, gestione tesserati
audit/           registro delle azioni dell'admin
bookings/        prenotazioni
courts/          campi, tipi di campo, prezzi e blocchi
notifications/   notifiche interne (in arrivo)
common/          orologio centralizzato e parti condivise
config/          impostazioni Django, formati e lettura del file .env
docs/            requisiti, specifiche tecniche, decisioni e piani
```

## Licenza

[MIT](LICENSE) © 2026 Diego Rosiglioni
