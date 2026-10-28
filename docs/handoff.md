# Passaggio di consegne

28/10/2026 · da aggiornare alla fine di ogni sessione

Punto di partenza per chi riprende il lavoro (una persona o una nuova sessione di Claude Code). Le regole di lavoro sono in `CLAUDE.md`; requisiti, specifiche e decisioni sono in `docs/`.

## Dove siamo

| Pezzo (specifiche, sezione 7) | Stato | Piano |
| --- | --- | --- |
| 1. Base del progetto | Unito in `develop` (PR #6), CI verde | `piani/01-base-progetto.md` |
| 2. Account e login | Unito in `develop` (PR #7), CI verde | `piani/02-account-login.md` |
| 3. Campi e prenotazione | Fatto; branch `feature/campi-prenotazione` con push fatto, **PR verso `develop` da aprire** (su richiesta) | `piani/03-campi-prenotazione.md` |
| 4. Cancellazioni | – | – |
| 5. Esiti, pagamenti, debiti e strike | – | – |
| 6. Notifiche e job giornaliero | – | – |
| 7. Pannello admin e deploy | – | – |

Verifiche del pezzo 3: vedi `piani/03-campi-prenotazione.md`, sezione 12.

## Prossimi passi

1. PR `feature/campi-prenotazione` → `develop`, solo su richiesta; poi controllare la CI.
2. Prova nel browser del pezzo 3 da parte dell'utente (passo 8 del piano).
3. Decidere se accorciare i test con un hash veloce delle password solo per i test (vedi "Ambiente").
4. Pezzo 4 (cancellazioni): prima confermare l'ipotesi aperta sull'offerta cancellata dall'admin nelle ultime 2 ore.

## Cose da ricordare per i prossimi pezzi

- **Notifiche (pezzo 6).** Vanno aggiunte nei servizi già scritti: `create_booking` quando agisce l'admin, `cancel_by_system` (blocco del campo, disattivazione, e dal pezzo 5 blocco dell'account).
- **Rimborsi (pezzo 5).** `cancel_by_system` non crea movimenti: il rimborso da restituire si ricava dai movimenti, come dicono le specifiche.
- **Pezzo 4.** `Booking.admin_reason` non esiste ancora; `outcome_by` e `outcome_at` arrivano con il pezzo 5. Il pulsante "Cancella" va in "Le mie prenotazioni" (`bookings/templates/bookings/_booking_table.html`).
- **Errori.** Nuovi codici in `common/errors.py` (`MESSAGES`), con traduzione; i codici del pezzo 4 e 5 (`too_late_to_cancel`, `outcome_too_early`, `invalid_transition`) non ci sono ancora.
- **Ora corrente.** Solo da `common.now()`; nei test `common.clock.fixed_now()`. I campi `created_at` usano `default=common.clock.now`, mai `auto_now_add`.
- **Registro azioni.** Ogni azione dell'admin chiama `audit.services.log_action()` nella stessa transazione.
- **Ordine dei blocchi delle righe.** Utente → campo → prenotazione, in ogni nuovo servizio.

## Punti aperti

Elenco completo e aggiornato: `decisioni.md`, sezione "Ipotesi aperte".

- **Prima del pezzo 4:** una prenotazione offerta, cancellata dall'admin nelle ultime 2 ore, genera addebito? Le specifiche deducono di no: va confermato.
- **Nel piano del pezzo 5:** cosa succede se l'admin corregge un esito su cui è già stato registrato un saldo.
- **Prima della produzione:** per quanto tempo si conservano i dati (RNF-06).
- **Grafica.** L'aspetto attuale (`static/css/site.css`) è provvisorio: l'utente vuole rifarlo più avanti ("abbellimento del sito"), con un piano dedicato. Finché non c'è un piano dedicato, le pagine nuove usano lo stesso stile semplice.
- **Lezioni del corso.** In cartella c'è solo `LLM_Lez_3.pdf`. Quando arriva la lezione 4 (Docker e Superpowers), leggerla e proporre gli aggiornamenti a `CLAUDE.md`.

## Ambiente: cose che hanno fatto perdere tempo

- **Docker Desktop spento:** i test si fermano con "connection timeout expired". Avviare Docker Desktop, poi `docker compose up -d db`.
- **Host del database:** `127.0.0.1`, non `localhost` (su Windows `localhost` prova prima IPv6 e resta appeso).
- **Chiave segreta senza `$`:** Docker Compose legge anche `.env`.
- **gettext e `gh`:** in un terminale aperto prima dell'installazione non sono nel PATH.
- **Push dei workflow:** `gh` ora ha il permesso `workflow`; senza, GitHub rifiuta il push di `.github/workflows/`.
- **Test lenti:** dal pezzo 3 la suite completa dura diversi minuti (vedi piano 3, sezione 12), quasi tutti spesi nell'hash delle password degli utenti creati nei test. Si può accorciare con un hash veloce solo per i test.
- **`create_admin`:** chiede la password in modo interattivo, quindi va lanciato da un terminale dell'utente. Per una nuova password dell'admin: `changepassword ADMIN`, con il codice in maiuscolo.

## Comandi principali

Elenco completo in `CLAUDE.md`, sezione "Comandi".

```powershell
docker compose up -d db
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py test --noinput
.\.venv\Scripts\python.exe manage.py runserver
```
