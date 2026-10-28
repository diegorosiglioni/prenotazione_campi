# Passaggio di consegne

28/10/2026 · da aggiornare alla fine di ogni sessione

Punto di partenza per chi riprende il lavoro (una persona o una nuova sessione di Claude Code). Le regole di lavoro sono in `CLAUDE.md`; requisiti, specifiche e decisioni sono in `docs/`.

## Dove siamo

| Pezzo (specifiche, sezione 7) | Stato | Piano |
| --- | --- | --- |
| 1. Base del progetto | Unito in `develop` (PR #6), CI verde | `piani/01-base-progetto.md` |
| 2. Account e login | Fatto; PR #7 `feature/account-login` → `develop` aperta, CI verde, **da unire** | `piani/02-account-login.md` |
| 3. Campi e prenotazione | Da pianificare | – |
| 4. Cancellazioni | – | – |
| 5. Esiti, pagamenti, debiti e strike | – | – |
| 6. Notifiche e job giornaliero | – | – |
| 7. Pannello admin e deploy | – | – |

Ultimi commit del pezzo 2: `f011d87` (piano), `3180fcf` (codice e test), `b59886d` (documenti).

Verifiche del pezzo 2, eseguite il 28/10/2026: 104 test superati sul PC e nella CI della PR #7, `check` e `makemigrations --check` senza problemi, prova nel browser fatta dall'utente.

## Prossimi passi

1. L'utente unisce la PR #7: https://github.com/diegorosiglioni/prenotazione_campi/pull/7
2. Aggiornare `develop` sul PC e creare `feature/campi-prenotazione`.
3. Pezzo 3: Ask → Plan (`piani/03-campi-prenotazione.md`, con scelte numerate e una proposta per ciascuna) → approvazione → Execute → Verifica e commit.

## Cose da ricordare per il pezzo 3

Lasciate in sospeso dal pezzo 2 (`piani/02-account-login.md`, sezione 9):

- **RF-40.** `accounts.services.deactivate_member()` per ora blocca solo l'accesso: deve anche annullare le prenotazioni non ancora iniziate, con motivo "account disattivato" (e rimborso da restituire se erano pagate, RF-48).
- **RF-31.** L'admin non può essere intestatario di una prenotazione.
- **RF-40, RF-41.** L'admin non prenota per un account disattivato.
- **`DomainError`** in `common`, con i codici della tabella "Errori" delle specifiche: nasce nel pezzo 3.
- **Database.** `django.contrib.postgres` tra le app ed estensione `btree_gist` con una migrazione, per i vincoli di esclusione di RF-07 e RF-44.
- **HTMX 2.0.11.** Il file `static/htmx.min.js` si scarica nel pezzo 3, con il calendario.
- **Pagina iniziale.** `accounts.views.home` oggi manda il tesserato su "Il mio account" e l'admin sull'elenco utenti: dal pezzo 3 entrambi vanno al calendario.
- **Ora corrente.** Solo da `common.now()`; nei test `common.clock.fixed_now()`. I campi `created_at` usano `default=common.clock.now`, mai `auto_now_add`.
- **Registro azioni.** Ogni azione dell'admin chiama `audit.services.log_action()` nella stessa transazione.

## Punti aperti

Elenco completo e aggiornato: `decisioni.md`, sezione "Ipotesi aperte".

- **Prima del pezzo 4:** una prenotazione offerta, cancellata dall'admin nelle ultime 2 ore, genera addebito? Le specifiche deducono di no: va confermato.
- **Nel piano del pezzo 5:** cosa succede se l'admin corregge un esito su cui è già stato registrato un saldo.
- **Prima della produzione:** per quanto tempo si conservano i dati (RNF-06).
- **Grafica.** L'aspetto attuale (`static/css/site.css`) è provvisorio: l'utente vuole rifarlo in futuro. Finché non c'è un piano dedicato, le pagine nuove usano lo stesso stile semplice.
- **Lezioni del corso.** In cartella c'è solo `LLM_Lez_3.pdf`. Quando arriva la lezione 4 (Docker e Superpowers), leggerla e proporre gli aggiornamenti a `CLAUDE.md`.

## Ambiente: cose che hanno fatto perdere tempo

- **Docker Desktop spento:** i test si fermano con "connection timeout expired". Avviare Docker Desktop, poi `docker compose up -d db`.
- **Host del database:** `127.0.0.1`, non `localhost` (su Windows `localhost` prova prima IPv6 e resta appeso).
- **Chiave segreta senza `$`:** Docker Compose legge anche `.env`.
- **gettext e `gh`:** in un terminale aperto prima dell'installazione non sono nel PATH.
- **Push dei workflow:** `gh` ora ha il permesso `workflow`; senza, GitHub rifiuta il push di `.github/workflows/`.
- **Test lenti:** 104 test in circa 70 secondi, quasi tutti spesi nell'hash delle password. Si può accorciare con un hash veloce solo per i test, se diventa scomodo.
- **`create_admin`:** chiede la password in modo interattivo, quindi va lanciato da un terminale dell'utente. Per una nuova password dell'admin: `changepassword ADMIN`, con il codice in maiuscolo.

## Comandi principali

Elenco completo in `CLAUDE.md`, sezione "Comandi".

```powershell
docker compose up -d db
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py test --noinput
.\.venv\Scripts\python.exe manage.py runserver
```
