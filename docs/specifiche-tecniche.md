# Specifiche tecniche – Prenotazione campi sportivi

20/10/2026 · prima versione

Questo documento dice **come** si costruisce il sito. **Cosa** deve fare è scritto in `requisiti-prenotazione-campi.md`, che resta la fonte di verità: se i due documenti non sono d'accordo, valgono i requisiti e questo file va corretto. Le decisioni sono registrate in `decisioni.md`.

I nomi di codice (moduli, tabelle, campi, funzioni) sono in inglese; il testo è in italiano.

## 1. Architettura

Un'unica applicazione Django con template lato server. Ogni regola dei requisiti vive in una **funzione di servizio**; le view leggono l'input, chiamano il servizio e mostrano il risultato. Nessuna regola nelle view, nei form o nei template.

Il pannello admin incluso in Django non viene esposto: permetterebbe di modificare i dati saltando le regole (RF-45) e il registro azioni (RNF-07). L'admin del sito usa pagine costruite apposta. Chi gestisce il server usa i comandi di Django (ad esempio `changepassword` per RF-33).

### Moduli

| Modulo | Contenuto |
| --- | --- |
| `config` | Impostazioni, URL principali, avvio WSGI |
| `common` | Funzioni condivise: `now()` per l'ora corrente, errori di dominio |
| `accounts` | Utente, login con codice tessera, tentativi falliti, cambio password, lingua, gestione utenti dell'admin |
| `courts` | Tipi di campo, campi, blocchi dei campi, prezzi |
| `bookings` | Prenotazioni, cancellazioni, esiti, strike, movimenti di denaro, calendario |
| `notifications` | Notifiche interne e comando giornaliero `send_card_reminders` |
| `audit` | Registro azioni e funzione `log_action()` usata dai servizi |

In `bookings` i servizi sono divisi per argomento: `services/booking.py`, `services/cancellation.py`, `services/outcomes.py`, `services/payments.py`, `services/sanctions.py`. Strike e movimenti stanno nello stesso modulo delle prenotazioni perché cambiano nella stessa transazione.

### Struttura delle cartelle

```
config/            impostazioni e URL
common/            now(), errori di dominio
accounts/  courts/  bookings/  notifications/  audit/
templates/         template condivisi (base, menu)
static/            CSS e htmx.min.js
locale/en/         traduzione inglese
docker/            Dockerfile, Caddyfile
compose.yaml       sviluppo: solo PostgreSQL
compose.prod.yaml  produzione: db, web, caddy, scheduler
.github/workflows/ test sulla CI
```

## 2. Modello dati

Tutti gli istanti sono `DateTimeField` con fuso: PostgreSQL li salva in UTC, il sito li mostra in Europe/Rome (RNF-03). Gli importi sono `DecimalField` in euro con due decimali. Gli intervalli di tempo sono "inizio incluso, fine esclusa": 18:00–19:00 e 19:00–20:00 non si sovrappongono.

Niente si cancella fisicamente, tranne i blocchi dei campi rimossi dall'admin (la rimozione resta nel registro azioni). Movimenti e strike annullati vengono segnati, non eliminati.

### `accounts.User`

Modello utente personalizzato, definito prima della prima migrazione.

| Campo | Tipo | Note |
| --- | --- | --- |
| `card_code` | testo, max 20 | Campo di login. Univoco, salvato in maiuscolo. Per l'admin è il codice riservato: l'unicità impedisce che una tessera lo usi (RF-31) |
| `first_name`, `last_name` | testo | Obbligatori |
| `card_expiry` | data, facoltativa | Obbligatoria per i tesserati, vuota per l'admin |
| `role` | `member` o `admin` | |
| `language` | `it` o `en` | Predefinita `it` |
| `is_active` | sì/no | Falso = account disattivato (RF-40) |
| `is_blocked` | sì/no | Vero dal secondo strike fino allo sblocco manuale (RF-28, RF-29) |
| `must_change_password` | sì/no | Vero dopo ogni password temporanea (RF-32) |
| `email`, `phone` | testo, facoltativi | |

Vincoli nel database:
- `card_code` univoco e uguale alla sua versione maiuscola.
- **Un solo admin** (RF-01): univocità parziale su `role` dove `role = 'admin'`.
- `card_expiry` non vuota se `role = 'member'`.

### `accounts.LoginAttempt`

Un record per ogni login fallito: `card_code`, `created_at`. Serve a RNF-05 (sezione 5). Al login riuscito i tentativi di quel codice si eliminano.

### `courts.CourtType` e `courts.Court`

| Tabella | Campi | Note |
| --- | --- | --- |
| `CourtType` | `code` (`football`, `tennis`, `basketball`, `bocce`), `slot_minutes`, `price` | Durata e prezzo maggiori di zero. Il prezzo è per tipo (RF-05) |
| `Court` | `code` (`football`, `tennis_1`, `tennis_2`, `basketball`, `bocce`), `court_type`, `is_active` | I 5 record si creano con una migrazione di dati |

I nomi mostrati all'utente si generano dal `code` con gettext: non ci sono testi da tradurre nel database.

### `courts.CourtBlock`

`court`, `start`, `end`. Vincolo: `end > start`. Si crea solo con `start` nel futuro (RF-14, controllo nel servizio).

### `bookings.Booking`

| Campo | Note |
| --- | --- |
| `member` | Il tesserato intestatario (RF-41) |
| `court`, `start`, `end` | `end` = `start` + durata del tipo di campo |
| `price` | Prezzo copiato alla creazione (RF-05) |
| `status` | Uno degli stati della sezione 3 |
| `created_by`, `created_at` | Tesserato o admin |
| `outcome_by`, `outcome_at` | Chi ha impostato l'ultimo esito e quando |
| `cancelled_by`, `cancelled_at` | `cancelled_by` vuoto = cancellazione del sistema |
| `system_reason` | `account_blocked`, `account_deactivated` o `court_blocked` (RF-18) |
| `admin_reason` | Testo libero facoltativo dell'admin, non tradotto |

Addebito e strike non hanno colonne proprie: si ricavano da `Movement` e `Strike`, così non possono andare fuori sincrono.

Vincoli nel database:
- **RF-07.** Vincolo di esclusione su (`court` uguale, intervallo `[start, end)` sovrapposto).
- **RF-44.** Vincolo di esclusione su (`member` uguale, intervallo `[start, end)` sovrapposto).
- Entrambi valgono solo per gli stati che occupano il campo: `booked`, `paid`, `offered`, `no_show`, `unpaid`.
- `end > start`, `price >= 0`.
- Richiedono l'estensione PostgreSQL `btree_gist`, attivata con una migrazione.

### `bookings.Strike`

`member`, `booking`, `kind` (`no_show`, `unpaid`, `late_cancellation`), `created_at`, `removed_at`, `removal_cause` (`settlement`, `manual`, `correction`, `unblock`).

Uno strike è **attivo** se `removed_at` è vuoto. Vincolo: al massimo uno strike attivo per prenotazione.

### `bookings.Movement`

`member`, `booking`, `kind` (`payment`, `charge`, `settlement`, `refund`), `amount` (maggiore di zero), `created_at`, `created_by`, `voided_at`.

Un movimento è **valido** se `voided_at` è vuoto. Vincolo: al massimo un movimento valido per (`booking`, `kind`): niente doppi incassi, doppi addebiti o doppi rimborsi.

Calcoli, solo sui movimenti validi:
- Debito di una prenotazione = `charge` − `settlement`. Debito del tesserato = somma sulle sue prenotazioni (RF-26).
- Incassi del giorno = `payment` + `settlement` − `refund` con `created_at` in quel giorno, ora italiana (RF-56).
- Rimborso da restituire: prenotazione cancellata o annullata con un `payment` valido, senza `charge` valido e senza `refund` (RF-48).

### `notifications.Notification`

`user`, `kind`, `params` (JSON), `created_at`, `read_at`, `dedup_key` (facoltativo).

Il testo si genera dal `kind` e dai `params` nella lingua corrente dell'utente. Vincolo: (`user`, `dedup_key`) univoco quando `dedup_key` è presente; serve al comando giornaliero per non creare due volte lo stesso avviso (ad esempio `card_expiring:2026-11-30`).

### `audit.ActionLog`

`actor`, `action`, `object_type`, `object_id`, `before` (JSON), `after` (JSON), `created_at`. Lo scrivono i servizi, nella stessa transazione dell'azione, ogni volta che agisce l'admin (RNF-07).

## 3. Servizi, concorrenza e stati

### Regole generali

- Ogni servizio lavora in una transazione (`transaction.atomic`): o salva tutto, o niente.
- L'ora corrente si legge solo da `common.now()`; i test la sostituiscono con un'ora fissa.
- Le righe da proteggere si bloccano con `select_for_update`, **sempre nell'ordine utente → campo → prenotazione**, per evitare stalli tra transazioni (deadlock).
- Una regola violata solleva `DomainError` con un codice (tabella "Errori"). La view lo trasforma nel messaggio tradotto.

### Creare una prenotazione

`create_booking(actor, member, court, start, offered=False)`

1. Blocca la riga di `member`: due richieste dello stesso tesserato vengono eseguite una dopo l'altra, quindi il conteggio di RF-09 è sempre esatto.
2. Blocca la riga di `court`: una prenotazione e un blocco del campo non possono incrociarsi (RF-14, RNF-04).
3. Controlla, in quest'ordine:
   - inizio a passi di 15 minuti, dalle 8:00, fine entro le 23:00 ora italiana (RF-04, RF-47);
   - inizio dopo `now()` (RF-08);
   - se `actor` è il tesserato: data entro 14 giorni di calendario (RF-08), account attivo e non bloccato, tessera valida e slot non oltre la scadenza (RF-10, RF-34), meno di 3 prenotazioni attive (RF-09);
   - se `actor` è l'admin: `member` è un tesserato con account attivo (RF-40, RF-41); `offered` è permesso solo all'admin (RF-23);
   - nessun blocco del campo sovrapposto (RF-14).
4. Inserisce la prenotazione con stato `booked` o `offered`. Se un'altra transazione ha appena occupato il campo o il tesserato, il vincolo di esclusione fa fallire l'inserimento: il servizio lo traduce in `slot_taken` (RF-07) o `member_overlap` (RF-44).
5. Se `actor` è l'admin: notifica al tesserato e riga nel registro azioni.

### Altre operazioni

| Servizio | Blocchi | Effetti |
| --- | --- | --- |
| `cancel_booking` (tesserato) | utente, prenotazione | Solo da 2 ore o più prima dell'inizio (RF-15, RF-16). Stato `cancelled`. Se era pagata, il rimborso diventa da restituire |
| `cancel_booking` (admin) | utente, prenotazione | Prima delle ultime 2 ore: `cancelled`. Dalle ultime 2 ore alla fine dello slot: `admin_cancelled`, con addebito e strike a scelta (RF-17, RF-19). Motivo facoltativo |
| `block_court` | campo, poi prenotazioni | Crea il blocco; annulla con `system_cancelled` / `court_blocked` le prenotazioni non ancora iniziate che si sovrappongono; notifiche (RF-14) |
| `set_outcome` | utente, prenotazione | `paid`, `offered`, `no_show`, `unpaid` secondo RF-49; crea movimenti e strike collegati; controlla il secondo strike |
| `correct_outcome` | utente, prenotazione | Storna movimenti e strike dell'esito precedente e applica quelli del nuovo (RF-50) |
| `register_settlement` | utente, prenotazione | Saldo per intero (RF-54); rimuove lo strike collegato con causa `settlement`; non sblocca (RF-39) |
| `register_refund` | utente, prenotazione | Solo per un rimborso da restituire (RF-48) |
| `remove_strike` | utente | Causa `manual`; non sblocca (RF-52) |
| `unblock_member` | utente | `is_blocked` falso; rimuove tutti gli strike attivi con causa `unblock`; il debito resta (RF-29) |
| `deactivate_member` | utente, poi prenotazioni | `is_active` falso; annulla le prenotazioni non ancora iniziate con `account_deactivated` (RF-40) |

**Secondo strike.** Dopo ogni nuovo strike, se il tesserato ha almeno 2 strike attivi e non è già bloccato: `is_blocked` vero, prenotazioni non ancora iniziate annullate con `account_blocked`, notifica al tesserato e all'admin (RF-28). Se è già bloccato, lo strike si registra senza nuova notifica di blocco.

**Addebito alla cancellazione dell'admin (RF-17).** Si crea un `charge` solo se la prenotazione è `booked`. Se è `paid`, il pagamento copre l'importo: nessun addebito e nessun rimborso. Se è `offered`, non c'è un importo da addebitare.

### Stati e passaggi ammessi

| Codice | Stato (RF-21) |
| --- | --- |
| `booked` | Prenotata |
| `paid` | Pagata |
| `offered` | Offerta |
| `cancelled` | Cancellata |
| `admin_cancelled` | Cancellata dall'admin |
| `system_cancelled` | Annullata dal sistema |
| `no_show` | No-show |
| `unpaid` | Non pagata |

| Da | A | Chi | Condizione |
| --- | --- | --- | --- |
| `booked` | `paid`, `offered` | admin | In qualsiasi momento (RF-49) |
| `booked` | `no_show`, `unpaid` | admin | Dopo l'inizio dello slot (RF-49) |
| `booked`, `paid`, `offered` | `cancelled` | tesserato o admin | 2 ore o più prima dell'inizio |
| `booked`, `paid`, `offered` | `admin_cancelled` | admin | Dalle ultime 2 ore alla fine dello slot |
| `booked`, `paid`, `offered` | `system_cancelled` | sistema | Prenotazione non ancora iniziata |
| `paid`, `offered`, `no_show`, `unpaid` | un altro di questi quattro | admin | Correzione (RF-50), rispettando RF-49 |

Ogni altro passaggio viene rifiutato con `invalid_transition`. Gli stati di cancellazione sono finali. Una prenotazione `booked` finita resta `booked` e compare nella lista "da chiudere".

Da dettagliare nel piano del pezzo 5: la correzione di un esito su cui è già stato registrato un saldo.

### Errori

| Codice | Quando | Requisito |
| --- | --- | --- |
| `out_of_hours` | Fuori dalle 8:00–23:00 o non a passi di 15 minuti | RF-04, RF-47 |
| `slot_in_past` | Lo slot, o il blocco del campo, inizia prima di adesso | RF-08, RF-14 |
| `out_of_window` | Oltre i 14 giorni | RF-08 |
| `slot_taken` | Campo già occupato | RF-07 |
| `member_overlap` | Il tesserato ha già una prenotazione in quell'orario | RF-44 |
| `court_blocked` | Campo bloccato in quell'intervallo | RF-14 |
| `limit_reached` | Già 3 prenotazioni attive | RF-09 |
| `card_expired` | Tessera scaduta | RF-34 |
| `card_expires_before_slot` | Lo slot è dopo la scadenza della tessera | RF-34 |
| `account_blocked` | Account bloccato | RF-10 |
| `account_inactive` | Account disattivato | RF-40 |
| `not_a_member` | L'intestatario non è un tesserato (per esempio l'admin) | RF-31 |
| `too_late_to_cancel` | Il tesserato cancella nelle ultime 2 ore | RF-16 |
| `outcome_too_early` | No-show o non pagata prima dell'inizio | RF-49 |
| `invalid_transition` | Passaggio di stato non ammesso | RF-21 |

Gli errori non previsti mostrano un messaggio generico e finiscono nel log del server.

## 4. Pagine e traduzioni

### Pagine del tesserato

| Pagina | Contenuto | Requisiti |
| --- | --- | --- |
| Login | Codice tessera, password, selettore della lingua | RF-31 |
| Cambio password | Obbligatoria al primo accesso, poi sempre disponibile | RF-32 |
| Calendario | Giorno e campo; slot liberi, occupati e bloccati, senza nomi. HTMX aggiorna la griglia | RF-11, RF-14 |
| Conferma prenotazione | Campo, data, inizio, fine, prezzo, pulsante "Conferma" | RF-42 |
| Le mie prenotazioni | Future e passate, con stato e prezzo; pulsante "Cancella", disattivato con spiegazione nelle ultime 2 ore | RF-12, RF-16 |
| Area personale | Debito con dettaglio, strike attivi, scadenza della tessera, lingua | RF-46, RF-55 |
| Notifiche | Elenco, segna come letta; contatore dei non letti nel menu | RF-38 |

### Pagine dell'admin

| Pagina | Contenuto | Requisiti |
| --- | --- | --- |
| Calendario completo | Tutti i campi con nome e stato; da qui si prenota a nome di un tesserato | Funzioni admin 1, 2 |
| Dettaglio prenotazione | Esito, correzione, cancellazione con scelte su addebito e strike, debito del tesserato in evidenza | RF-17, RF-49, RF-50, RF-53 |
| Da chiudere | Prenotazioni finite senza esito; contatore nel menu | Funzioni admin 4 |
| Utenti | Elenco, crea, modifica, disattiva, password temporanea, strike, sblocco | RF-29, RF-30, RF-40, RF-52 |
| Debiti e rimborsi | Debiti aperti, rimborsi da restituire, registrazione di saldi e rimborsi | RF-26, RF-48, RF-54 |
| Prezzi e blocchi | Prezzo per tipo di campo; creazione e rimozione dei blocchi | RF-05, RF-14 |
| Incassi del giorno | Pagamenti, saldi, rimborsi e totale di un giorno | RF-56 |

Il registro azioni non ha una pagina di consultazione: nessun requisito la chiede.

Ogni view dell'admin è protetta da un controllo di ruolo; ogni view del tesserato mostra solo i dati dell'utente collegato.

### Traduzioni e formati

- `LANGUAGE_CODE = "it"`, `LANGUAGES` = italiano e inglese; ogni testo passa da gettext; traduzione in `locale/en/`.
- Dopo il login la lingua attiva è `User.language`; prima del login la sceglie il selettore della pagina di accesso.
- Nomi dei campi, stati, motivi di sistema e notifiche sono codici: il testo si traduce al momento della visualizzazione (RNF-02).
- Date `gg/mm/aaaa` e orari a 24 ore in entrambe le lingue: per l'inglese un modulo di formati personalizzato (`FORMAT_MODULE_PATH`), perché quello predefinito di Django è americano (RNF-10).
- `TIME_ZONE = "Europe/Rome"`, `USE_TZ = True`. Le date di calendario (14 giorni, scadenza della tessera, incassi del giorno) si calcolano sulla data italiana, non su quella UTC (RNF-03).

## 5. Sicurezza, job, ambienti e dipendenze

### Sicurezza (RNF-05)

- Password con l'hash predefinito di Django; validatore di lunghezza minima 8.
- Un middleware rimanda al cambio password ogni utente con `must_change_password` vero (RF-32).
- Login: se ci sono 5 `LoginAttempt` per quel codice negli ultimi 15 minuti, il login viene rifiutato. Il messaggio è sempre lo stesso, anche per codici inesistenti. Scritto nel progetto, senza librerie esterne.
- Sessione: scade dopo 30 minuti di inattività (`SESSION_COOKIE_AGE = 1800`, `SESSION_SAVE_EVERY_REQUEST = True`).
- Produzione: Caddy gestisce il certificato HTTPS; Django usa cookie sicuri, redirect a HTTPS e HSTS. Protezione CSRF attiva anche per le richieste HTMX.

### Job giornaliero

Il comando `send_card_reminders` crea gli avvisi "Tessera in scadenza" (10 giorni prima) e "La tessera scade oggi" (RF-36), usando `dedup_key` per non duplicarli. Nel deploy gira nel servizio `scheduler`, che lo esegue ogni ora: se un'esecuzione salta, la successiva recupera.

### Ambienti

- **Sviluppo:** `compose.yaml` avvia solo PostgreSQL; Django gira dal PC con `.\.venv\Scripts\python.exe` e legge `.env`.
- **Produzione:** `compose.prod.yaml` su un VPS con quattro servizi: `db` (PostgreSQL), `web` (Django con gunicorn), `caddy` (HTTPS e file statici), `scheduler` (job).
- **CI:** una GitHub Action esegue i test con un servizio PostgreSQL su ogni Pull Request.
- Configurazione da variabili d'ambiente; `.env.example` elenca le variabili, senza segreti.

### Dipendenze Python

Le versioni si fissano in `requirements.txt` quando si crea il progetto, verificandole sulla documentazione ufficiale.

| Pacchetto | Motivo |
| --- | --- |
| Django | Framework scelto (`decisioni.md`) |
| psycopg | Driver PostgreSQL |
| gunicorn | Server di produzione |
| python-dotenv | Lettura di `.env` quando Django gira dal PC |

HTMX è un solo file JavaScript salvato in `static/`, senza CDN. I test usano il runner incluso in Django. Ogni nuova dipendenza va motivata e concordata.

## 6. Test

Tutti i test girano su PostgreSQL, sul PC (quello di `compose.yaml`) e nella CI. SQLite non si usa: non supporta i vincoli di esclusione. Il nome di ogni test cita l'ID del requisito (`test_rf08_rejects_slot_after_14_days`).

| Tipo | Cosa verifica | Strumento |
| --- | --- | --- |
| Regole | Ogni servizio, un test per ogni caso di un requisito | `TestCase` |
| Vincoli del database | Inserimenti diretti, senza servizi, rifiutati dal database (RF-01, RF-07, RF-44, unicità di strike e movimenti) | `TestCase` |
| Concorrenza (RNF-04) | Richieste vere in thread paralleli: stesso slot da due tesserati (ne passa 1); 4 richieste dello stesso tesserato (al massimo 3); blocco del campo e prenotazione insieme | `TransactionTestCase` |
| Ora legale (RNF-03) | Ultima domenica di marzo e di ottobre: slot delle 8:00 corretto, finestra di 14 giorni e limite delle 2 ore a cavallo del cambio | `TestCase` con `now()` fisso |
| Pagine | Permessi, messaggi d'errore in italiano e inglese, cambio password obbligatorio, pulsante di cancellazione disattivato | `Client` di Django |

**Prove manuali** prima di ogni rilascio: giro sulle pagine principali con Chrome, Firefox, Edge e Safari (RNF-01). Si annotano come eseguite o da fare, senza simulare risultati.

## 7. Ordine di realizzazione

Ogni pezzo ha il suo piano e si chiude con i test verdi prima di passare al successivo.

1. **Base del progetto:** Django, PostgreSQL in Docker, impostazioni, traduzioni, `now()`, CI.
2. **Account e login:** utente personalizzato, login, tentativi falliti, cambio password, gestione utenti.
3. **Campi e prenotazione:** tipi di campo, campi, blocchi, `create_booking` con vincoli e test di concorrenza, calendario.
4. **Cancellazioni.**
5. **Esiti, pagamenti, debiti e strike.**
6. **Notifiche e job giornaliero.**
7. **Pannello admin:** da chiudere, debiti e rimborsi, incassi del giorno, deploy di produzione.

## 8. Fuori da questa specifica

- **Conservazione dei dati (RNF-06):** ancora aperta in `decisioni.md`; va decisa prima della messa in produzione.
- **Backup del database:** escluso per scelta, per ora (`decisioni.md`).
