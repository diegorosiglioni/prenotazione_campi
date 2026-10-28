# Piano 3 – Campi e prenotazione

28/10/2026 · approvato (tutte le scelte della sezione 3 accettate così come proposte)

Terzo dei 7 pezzi di `specifiche-tecniche.md` (sezione 7). Alla fine di questo pezzo il sito ha i 5 campi con i loro prezzi, il calendario e la prenotazione: il tesserato prenota per sé entro le regole, l'admin prenota a nome di un tesserato e blocca i campi. Le regole su sovrapposizioni e limite di 3 reggono anche con richieste nello stesso istante.

Non ci sono ancora cancellazioni a mano (pezzo 4), esiti, pagamenti e strike (pezzo 5), notifiche (pezzo 6).

## 1. Prerequisiti

- Branch `feature/campi-prenotazione`, creato da `develop` dopo il merge della PR #7 (`8fdbe23`).
- Database di sviluppo avviato (`docker compose up -d db`).
- Nessuna nuova dipendenza Python. Si aggiungono:
  - `django.contrib.postgres` tra le app: fa già parte di Django, serve per i vincoli di esclusione;
  - l'estensione PostgreSQL `btree_gist`, attivata con una migrazione (è inclusa in PostgreSQL);
  - il file `static/htmx.min.js` versione 2.0.11 (già deciso), scaricato dalla fonte indicata nella documentazione ufficiale di HTMX e controllato con il suo codice di verifica (hash).

**Vincolo di esclusione**, in parole semplici: una regola scritta nel database che dice "nella tabella non possono esistere due righe con lo stesso campo e orari che si sovrappongono". Il database la controlla a ogni inserimento, anche se due richieste arrivano nello stesso istante. `btree_gist` è l'estensione che permette di mettere nella stessa regola un confronto "uguale" (stesso campo) e uno "si sovrappone" (orari).

## 2. Requisiti coperti

| Requisito | Cosa si realizza qui | Cosa resta ai pezzi successivi |
| --- | --- | --- |
| RF-03, RF-06 | 4 tipi di campo, 5 campi (tennis 1 e 2 distinti), durata fissa | – |
| RF-04, RF-47 | Inizio a passi di 15 minuti, dalle 8:00, fine entro le 23:00, anche per l'admin | – |
| RF-05 | Prezzo per tipo, copiato sulla prenotazione; pagina dell'admin per cambiarlo (scelta 2) | – |
| RF-07, RF-44 | Nessuna sovrapposizione sullo stesso campo né per la stessa persona, garantita dal database | – |
| RF-08 | Slot futuro, entro 14 giorni di calendario | – |
| RF-09 | Massimo 3 prenotazioni attive per il tesserato; l'admin può superarlo | – |
| RF-10, RF-34 | Account attivo e non bloccato, tessera valida, slot non dopo la scadenza | – |
| RF-11, RF-02 | Calendario: il tesserato vede libero/occupato senza nomi, l'admin vede nome e stato | – |
| RF-12 | "Le mie prenotazioni", in sola lettura (scelta 4) | Pulsante "Cancella": pezzo 4 |
| RF-14 | Blocco dei campi: creazione, rimozione, annullamento delle prenotazioni non ancora iniziate | Notifica al tesserato: pezzo 6. Rimborso: pezzo 5 |
| RF-23 | Prenotazione offerta creata dall'admin | Segnare come offerta una prenotazione esistente: pezzo 5 |
| RF-31 | L'admin non può essere intestatario di una prenotazione | – |
| RF-40, RF-41 | L'admin non prenota per un account disattivato; la disattivazione annulla le prenotazioni non ancora iniziate | Rimborso: pezzo 5 |
| RF-42, RF-43 | Riepilogo prima della conferma; messaggio con la regola violata | – |
| RNF-03 | Orari in Europe/Rome, prove nei giorni del cambio dell'ora | – |
| RNF-04 | Prove con richieste vere in parallelo | – |
| RNF-07 | Registro azioni per prenotazioni dell'admin, blocchi, prezzi, annullamenti causati dall'admin | – |

## 3. Scelte da confermare

Già concordate (passaggio di consegne): `DomainError` nasce qui; `django.contrib.postgres` e `btree_gist`; HTMX 2.0.11; la pagina iniziale diventa il calendario per tutti; la disattivazione annulla le prenotazioni.

Ogni punto ha una proposta, che si può accettare con "ok". Le risposte vanno registrate in `decisioni.md`.

1. **Notifiche.** Le specifiche chiedono una notifica quando l'admin prenota a nome di un tesserato e quando il sistema annulla una prenotazione. Le notifiche però sono il pezzo 6. Proposta: in questo pezzo nessuna notifica; il pezzo 6 le aggiunge nei servizi già scritti, con i test.
2. **Prezzi.** Nessun altro pezzo prevede la pagina dei prezzi (RF-05). Proposta: farla qui, nella pagina "Prezzi e blocchi" dell'admin, con riga nel registro azioni. Il prezzo deve essere maggiore di zero.
3. **Prezzo di una prenotazione offerta.** Proposta: anche la prenotazione offerta copia il prezzo del tipo di campo, come tutte le altre. Che sia gratuita lo dice lo stato "Offerta", mostrato accanto al prezzo. Così è coerente con il pezzo 5, quando una prenotazione già creata potrà diventare offerta senza cambiare prezzo.
4. **Le mie prenotazioni (RF-12).** Proposta: farla qui, in sola lettura (campo, data, orario, prezzo, stato, motivo dell'annullamento se c'è), perché dopo aver prenotato il tesserato deve poter ritrovare la prenotazione. Il pulsante "Cancella" arriva con il pezzo 4.
5. **Forma del calendario.** Proposta:
   - un giorno alla volta; i 5 campi in colonne; righe da 15 minuti dalle 8:00 alle 22:45;
   - ogni casella è libera, occupata, bloccata o passata; il tesserato vede solo questo (RF-11), l'admin anche nome e stato (RF-02);
   - una casella libera da cui uno slot intero ci sta (fino alle 23:00 e senza incroci) è un link "Prenota" che apre il riepilogo;
   - frecce "giorno prima / dopo" e scelta della data; HTMX aggiorna solo la griglia, senza ricaricare la pagina; senza JavaScript i link funzionano lo stesso;
   - il tesserato vede da oggi a 14 giorni (la finestra di RF-08); l'admin qualsiasi giorno, anche passato.
6. **Campo "attivo".** Le specifiche danno al campo un `is_active`, ma nessun requisito dice chi lo cambia né cosa succede. Proposta: tenerlo, tutti i campi attivi, nessuna pagina per cambiarlo. Un campo non attivo non compare nel calendario e il servizio lo rifiuta con lo stesso messaggio di "campo bloccato". Alternativa: toglierlo finché non serve.
7. **Admin come intestatario (RF-31).** La tabella "Errori" delle specifiche non ha un codice per questo caso. Proposta: nuovo codice `not_a_member`, "La prenotazione deve essere intestata a un tesserato", aggiunto alla tabella delle specifiche.
8. **Blocchi dei campi.** Proposta: inizio e fine con data e ora, anche su più giorni (es. manutenzione dal lunedì al mercoledì), senza obbligo dei 15 minuti; l'inizio deve essere nel futuro (RF-14). La pagina mostra i blocchi non ancora finiti; ognuno si può rimuovere. Nel calendario una casella è bloccata se il blocco la tocca anche solo in parte.
9. **Registro azioni per gli annullamenti.** Quando l'admin blocca un campo o disattiva un account, il sistema annulla delle prenotazioni. Proposta: oltre alla riga dell'azione (`court_blocked`, `user_deactivated`), una riga `booking_system_cancelled` per ogni prenotazione annullata, così il registro di ogni prenotazione è completo.
10. **Prenotare a nome di un tesserato.** Proposta: dal calendario dell'admin, il link "Prenota" apre lo stesso riepilogo, con in più l'elenco dei tesserati attivi (in ordine di cognome) e la casella "Offerta".

## 4. Modello dati

### `courts.CourtType` e `courts.Court`

Come nelle specifiche (sezione 2). Una migrazione di dati crea:

| Tipo | Durata | Prezzo | Campi |
| --- | --- | --- | --- |
| `football` | 90 min | €60 | `football` |
| `tennis` | 60 min | €18 | `tennis_1`, `tennis_2` |
| `basketball` | 60 min | €25 | `basketball` |
| `bocce` | 60 min | €10 | `bocce` |

Vincoli nel database: `slot_minutes > 0`, `price > 0`, `code` univoci. I nomi mostrati ("Calcio", "Tennis 1"…) si generano dal codice con gettext.

### `courts.CourtBlock`

`court`, `start`, `end`. Vincolo `end > start`. Si cancella davvero alla rimozione (eccezione prevista dalle specifiche), dopo averlo scritto nel registro.

### `bookings.Booking`

Solo i campi che servono in questo pezzo: `member`, `court`, `start`, `end`, `price`, `status`, `created_by`, `created_at` (`default=common.clock.now`), `cancelled_by`, `cancelled_at`, `system_reason`. Gli stati sono già tutti e 8, perché il vincolo di esclusione dipende da quali stati occupano il campo. `admin_reason` arriva con il pezzo 4, `outcome_by` e `outcome_at` con il pezzo 5.

Vincoli nel database:

| Vincolo | Requisito |
| --- | --- |
| Esclusione: stesso `court`, intervallo `[start, end)` sovrapposto, solo stati che occupano il campo | RF-07 |
| Esclusione: stesso `member`, intervallo sovrapposto, stessi stati | RF-44 |
| `end > start`, `price >= 0` | – |

"Stati che occupano il campo": `booked`, `paid`, `offered`, `no_show`, `unpaid`. `[start, end)` vuol dire inizio incluso e fine esclusa: 18:00–19:00 e 19:00–20:00 non si toccano.

### `common.DomainError`

`DomainError(code)` in `common/errors.py`, con i codici della tabella "Errori" delle specifiche più `not_a_member` (scelta 7). Ogni codice ha il suo messaggio con gettext; le view mostrano il messaggio nella lingua dell'utente.

## 5. Servizi e pagine

### Servizi

| Servizio | Dove | Effetto |
| --- | --- | --- |
| `create_booking(actor, member, court, start, offered=False)` | `bookings/services/booking.py` | Come nelle specifiche (sezione 3): blocca utente e campo, controlla le regole in ordine, inserisce; l'errore del vincolo diventa `slot_taken` o `member_overlap`. Se agisce l'admin: registro azioni `booking_created` |
| `cancel_by_system(bookings, reason, actor)` | `bookings/services/booking.py` | Stato `system_cancelled` con motivo; per le prenotazioni non ancora iniziate. Usato da blocco campo e disattivazione (scelta 9) |
| `set_price(actor, court_type, price)` | `courts/services.py` | Nuovo prezzo, registro `price_changed` (scelta 2) |
| `block_court(actor, court, start, end)` | `courts/services.py` | Blocca il campo, poi annulla le prenotazioni non ancora iniziate che si sovrappongono (`court_blocked`); registro |
| `remove_block(actor, block)` | `courts/services.py` | Rimuove il blocco; le prenotazioni annullate non tornano; registro |
| `deactivate_member` | `accounts/services.py` (esiste) | In più annulla le prenotazioni non ancora iniziate con `account_deactivated` |

Ordine dei blocchi delle righe (per evitare che due transazioni si aspettino a vicenda): utente → campo → prenotazione, come nelle specifiche.

Il controllo "campo bloccato" non può essere un vincolo del database, perché blocchi e prenotazioni sono in due tabelle diverse: lo garantisce il blocco della riga del campo, preso sia da `create_booking` sia da `block_court`. La prova di concorrenza lo verifica.

### Pagine

| Indirizzo | Chi | Contenuto |
| --- | --- | --- |
| `/` | tutti | Rimanda al calendario |
| `/calendar/?date=…` | tutti | Calendario del giorno (scelta 5); con HTMX restituisce solo la griglia |
| `/book/?court=…&date=…&time=…` | tutti | Riepilogo (RF-42): campo, data, inizio, fine, prezzo, "Conferma"; per l'admin anche tesserato e "Offerta" (scelta 10). Gli errori mostrano la regola violata (RF-43) |
| `/bookings/` | tesserato | Le mie prenotazioni (scelta 4) |
| `/staff/courts/` | admin | Prezzi e blocchi (scelte 2 e 8) |

Nel menu: "Calendario" per tutti, "Le mie prenotazioni" per il tesserato, "Prezzi e blocchi" per l'admin. Data e ora nell'indirizzo sono in ora italiana: il sito le trasforma in un istante con fuso.

## 6. Passi e comandi (PowerShell)

**Passo 1 – Campi.** Prima i test di modello e migrazione dei dati, visti fallire; poi `django.contrib.postgres`, modelli, migrazioni, `DomainError`.
```powershell
.\.venv\Scripts\python.exe manage.py makemigrations courts
.\.venv\Scripts\python.exe manage.py test --noinput
```

**Passo 2 – Prenotazione e vincoli del database.** Prima i test di inserimento diretto, poi modello, migrazione con `btree_gist` e vincoli di esclusione.

**Passo 3 – `create_booking`.** Prima i test delle regole e del cambio dell'ora, poi il servizio.

**Passo 4 – Concorrenza.** Test con richieste in parallelo (thread, cioè più richieste eseguite nello stesso momento, ognuna con la sua connessione al database). Usano `TransactionTestCase` con `serialized_rollback = True`, altrimenti i campi creati dalla migrazione di dati sparirebbero per i test successivi.

**Passo 5 – Blocchi, prezzi, disattivazione.** Prima i test, poi i servizi.

**Passo 6 – Pagine.** Prima i test delle pagine, poi HTMX, view, template, menu, pagina iniziale.

**Passo 7 – Traduzioni.**
```powershell
.\.venv\Scripts\python.exe manage.py makemessages -l en --ignore=.venv
# si traduce a mano locale/en/LC_MESSAGES/django.po
.\.venv\Scripts\python.exe manage.py compilemessages --ignore=.venv
```

**Passo 8 – Test verdi, controlli e prova a mano.**
```powershell
.\.venv\Scripts\python.exe manage.py test --noinput
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```
Giro nel browser: il tesserato prenota e vede la prenotazione; un secondo tesserato vede lo slot occupato senza nome; l'admin prenota a nome di un tesserato, crea un'offerta, cambia un prezzo, blocca un campo e vede la prenotazione annullata.

**Passo 9 – Documenti.** `CLAUDE.md`, `decisioni.md`, tabella "Errori" delle specifiche (scelta 7), `handoff.md`.

## 7. Test da scrivere prima del codice

| File | Test | Cosa verifica |
| --- | --- | --- |
| `courts/tests/test_models.py` | `test_rf03_courts_created_by_migration` | 5 campi, 4 tipi, durate e prezzi della tabella |
| | `test_rf05_price_positive_in_db` | Prezzo 0 rifiutato dal database |
| | `test_rf14_block_end_after_start_in_db` | Blocco con fine prima dell'inizio rifiutato |
| `bookings/tests/test_constraints.py` | `test_rf07_same_court_overlap_rejected_in_db` | Sovrapposizione parziale sullo stesso campo rifiutata |
| | `test_rf07_adjacent_slots_allowed_in_db` | 18:00–19:00 e 19:00–20:00 accettate |
| | `test_rf07_cancelled_booking_frees_slot_in_db` | Una prenotazione annullata non occupa il campo |
| | `test_rf44_same_member_other_court_rejected_in_db` | Stesso tesserato, due campi, stesso orario: rifiutato |
| `bookings/tests/test_create_booking.py` | `test_rf04_start_on_15_minute_steps` | 18:10 rifiutato con `out_of_hours` |
| | `test_rf04_opening_hours` | 7:45 rifiutato; 8:00 accettato |
| | `test_rf04_last_start_per_court_type` | Calcio 21:30 sì e 21:45 no; tennis 22:00 sì e 22:15 no |
| | `test_rf47_admin_respects_hours` | Stesse regole per l'admin |
| | `test_rf08_rejects_slot_in_past` | `slot_in_past` |
| | `test_rf08_window_last_day_included` | Il 20/10 si prenota il 03/11 alle 22:00, non il 04/11 alle 8:00 |
| | `test_rf08_admin_not_limited_by_window` | L'admin prenota oltre i 14 giorni |
| | `test_rf09_fourth_active_booking_rejected` | `limit_reached` |
| | `test_rf09_finished_and_cancelled_do_not_count` | Prenotazioni finite o annullate non contano |
| | `test_rf09_admin_bookings_count_and_admin_can_exceed` | Quelle dell'admin contano; l'admin supera il limite |
| | `test_rf10_blocked_account_rejected` | `account_blocked` per il tesserato; l'admin invece prenota |
| | `test_rf34_expired_card_rejected` | `card_expired` |
| | `test_rf34_slot_after_card_expiry_rejected` | `card_expires_before_slot`; il giorno della scadenza è accettato |
| | `test_rf40_admin_cannot_book_for_inactive_member` | `account_inactive` |
| | `test_rf31_admin_cannot_be_holder` | `not_a_member` (scelta 7) |
| | `test_rf23_only_admin_creates_offered` | Stato `offered` solo se agisce l'admin |
| | `test_rf05_price_copied_at_creation` | Cambiare il prezzo non cambia le prenotazioni esistenti |
| | `test_rf14_blocked_court_rejected` | `court_blocked` |
| | `test_rf07_service_reports_slot_taken` | Messaggio giusto dal servizio |
| | `test_rf44_service_reports_member_overlap` | Messaggio giusto dal servizio |
| | `test_rnf07_admin_booking_logged` | Riga `booking_created`; nessuna riga quando prenota il tesserato |
| `bookings/tests/test_dst.py` | `test_rnf03_8am_slot_on_dst_change_days` | Ultima domenica di marzo e di ottobre: lo slot delle 8:00 è alle 8:00 italiane |
| | `test_rnf03_window_across_dst_change` | La finestra di 14 giorni a cavallo del cambio dell'ora |
| `bookings/tests/test_concurrency.py` | `test_rnf04_same_slot_two_members_one_wins` | Stesso slot da due tesserati insieme: ne passa 1 |
| | `test_rnf04_same_member_four_requests_max_three` | 4 richieste insieme dello stesso tesserato: al massimo 3 |
| | `test_rnf04_block_and_booking_together` | Blocco e prenotazione insieme: mai una prenotazione attiva dentro un blocco |
| `courts/tests/test_services.py` | `test_rf05_admin_changes_price` | Nuovo prezzo e riga nel registro |
| | `test_rf14_block_must_start_in_future` | Blocco nel passato rifiutato |
| | `test_rf14_block_cancels_overlapping_not_started` | Annullate anche le sovrapposizioni parziali, motivo `court_blocked` |
| | `test_rf14_block_leaves_started_booking` | La prenotazione in corso resta |
| | `test_rf14_remove_block_does_not_restore` | Le prenotazioni annullate restano annullate |
| | `test_rnf07_block_actions_logged` | Righe per blocco, rimozione e prenotazioni annullate (scelta 9) |
| `accounts/tests/test_admin_users.py` | `test_rf40_deactivation_cancels_future_bookings` | Annullate con `account_deactivated`; quelle iniziate o passate restano |
| `bookings/tests/test_pages.py` | `test_rf11_member_calendar_has_no_names` | Il tesserato vede "occupato" senza nomi |
| | `test_rf02_admin_calendar_shows_names_and_status` | L'admin vede nome e stato |
| | `test_rf11_htmx_request_returns_grid_only` | Con l'intestazione HTMX torna solo la griglia |
| | `test_rf08_member_calendar_limited_to_window` | Il tesserato non apre giorni oltre i 14 |
| | `test_rf42_confirmation_shows_summary` | Campo, data, inizio, fine, prezzo |
| | `test_rf43_error_message_shown_it_and_en` | La regola violata, nelle due lingue |
| | `test_rf12_my_bookings_shows_only_own` | Solo le proprie, con stato e prezzo |
| | `test_rf01_member_gets_403_on_courts_admin_page` | Accesso negato a "Prezzi e blocchi" |
| | `test_home_redirects_to_calendar` | Tesserato e admin arrivano al calendario |

## 8. Verifiche da eseguire davvero

| Verifica | Comando | Risultato atteso |
| --- | --- | --- |
| Test rossi prima del codice | `manage.py test --noinput` (a ogni passo) | Falliscono i test nuovi, per i motivi attesi |
| Test verdi | `manage.py test --noinput` | Tutti superati, con il numero dei test |
| Configurazione | `manage.py check` | "System check identified no issues" |
| Migrazioni | `makemigrations --check --dry-run` | "No changes detected" |
| Migrazioni sul database di sviluppo | `manage.py migrate` | 5 campi creati, estensione `btree_gist` attiva |
| HTMX | Codice di verifica del file scaricato | Uguale a quello pubblicato da HTMX |
| Traduzioni | `compilemessages` | Nessun errore; nessun testo nuovo senza traduzione |
| Prova nel browser | Passo 8 | Annotata come eseguita o da fare |
| CI | Esito sulla PR | Verde, dopo il push su richiesta |

## 9. Fuori da questo pezzo

- Cancellazione del tesserato e dell'admin, motivo dell'admin (RF-15–RF-19): pezzo 4.
- Esiti, pagamenti, rimborsi, debiti, strike, blocco al secondo strike: pezzo 5.
- Notifiche (scelta 1): pezzo 6.
- Dettaglio della prenotazione per l'admin e lista "da chiudere": pezzi 4, 5 e 7.

## 10. Commit proposti

Solo su richiesta, uno per ogni risultato verificato:

1. `docs(piani): aggiunge il piano di campi e prenotazione`
2. `feat(courts): aggiunge tipi di campo, campi e blocchi`
3. `feat(prenotazioni): aggiunge la prenotazione con i vincoli del database`
4. `test(prenotazioni): aggiunge le prove di concorrenza`
5. `feat(courts): aggiunge prezzi e blocchi dei campi per l'admin`
6. `feat(prenotazioni): aggiunge calendario, riepilogo e le mie prenotazioni`
7. `docs: aggiorna CLAUDE.md, decisioni e specifiche del pezzo 3`

## 11. Note dall'esecuzione

- **Prova di concorrenza dei 4 tentativi.** Nella prima versione le 4 richieste erano tutte sul campo tennis 1: le metteva in fila già il blocco della riga del campo, e il test passava anche togliendo il blocco del tesserato. Ora le richieste sono su 4 campi diversi. Controprova: togliendo per un momento il blocco del tesserato, il test fallisce (4 prenotazioni invece di 3) in 2 esecuzioni su 3; con il blocco passa 3 volte su 3.
- **Prova di blocco e prenotazione insieme.** Controprova analoga: togliendo il blocco della riga del campo in `block_court`, il test fallisce in 3 esecuzioni su 5; con il blocco passa 5 volte su 5.
- **Tesserato che prenota per un altro, o crea un'offerta.** Non è una regola che l'utente può violare dalle pagine (non ci sono pulsanti per farlo): il servizio rifiuta con "accesso negato" (`PermissionDenied`), non con un `DomainError`.
- **Blocco nel passato.** Usa il codice `slot_in_past` ("Questo orario è già passato."), aggiunto alla tabella "Errori" delle specifiche insieme a `not_a_member`.
- **"La tua prenotazione" nel calendario.** Aggiunta non prevista dal piano: il tesserato vede le proprie prenotazioni con questa scritta invece di "Occupato". Non mostra nomi di altri, quindi RF-02 resta rispettato.
- **"Le mie prenotazioni" per l'admin.** L'admin non può avere prenotazioni (RF-31): la pagina gli risponde "accesso negato" e non compare nel suo menu.
- **Prezzo con la virgola.** Il modulo dei prezzi accetta il formato italiano (`20,50`) e mostra i prezzi con la virgola in italiano e il punto in inglese.
- **Pagina di arrivo.** Due test del pezzo 2 controllavano la vecchia pagina di arrivo dopo il login (elenco utenti e "Il mio account"): aggiornati al calendario, come concordato.
- **Traduzioni "fuzzy".** `makemessages` ha proposto per 14 testi nuovi traduzioni prese da testi simili, ma sbagliate (es. "Campo bloccato." → "blocked"): sono state riscritte tutte.
- **Durata dei test.** La suite completa è diventata molto più lenta (vedi sezione 12), quasi tutta per l'hash delle password degli utenti creati nei test.

## 12. Verifiche eseguite

28/10/2026, sul PC.

| Verifica | Esito |
| --- | --- |
| Test rossi prima del codice | Eseguita a ogni passo: passo 1 `ImportError` (`Court` mancante); passo 2 `ImportError` (`Booking` mancante); passo 3 `ModuleNotFoundError` (`bookings.services`); passo 5 servizi dei campi mancanti e prenotazioni non annullate alla disattivazione; passo 6 `NoReverseMatch` (pagine mancanti), poi solo il messaggio in inglese, fino alle traduzioni |
| Prove di concorrenza significative | Eseguita: vedi sezione 11 (controprove togliendo i blocchi delle righe) |
| Test verdi | Eseguita: 194 test superati, in circa 6 minuti (346 secondi) |
| `manage.py check` | Eseguita: "System check identified no issues (0 silenced)." |
| `makemigrations --check --dry-run` | Eseguita: "No changes detected" |
| Migrazioni sul database di sviluppo | Eseguita: `courts.0001`, `courts.0002`, `bookings.0001` applicate; estensione `btree_gist` presente; 5 campi con prezzi 60, 18, 18, 25, 10 |
| HTMX | Eseguita: `static/htmx.min.js` 2.0.11 scaricato da jsDelivr; codice sha384 uguale a quello pubblicato su htmx.org |
| Traduzioni | Eseguita: 78 testi nuovi tradotti, nessuna voce vuota né "fuzzy"; `compilemessages` senza errori |
| Server vero | Eseguita con `runserver`: `/login/` 200, `/static/htmx.min.js` 200, `/calendar/` e `/staff/courts/` rimandano al login |
| Prova nel browser | Da fare (utente): passo 8 |
| CI | Da fare: dopo push e PR, su richiesta |
