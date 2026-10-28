# Piano 1 – Base del progetto

20/10/2026 · approvato (tutte le scelte della sezione 3 accettate così come proposte)

Primo dei 7 pezzi di `specifiche-tecniche.md` (sezione 7). Alla fine di questo pezzo il progetto ha uno scheletro Django vuoto ma funzionante: impostazioni lette dall'ambiente, PostgreSQL in Docker, fuso orario e traduzioni configurati, la funzione `common.now()` e i test che girano sul PC e su GitHub.

Nessuna regola dei requisiti viene ancora implementata: questo pezzo prepara il terreno per tutti gli altri.

## 1. Prerequisiti

### Git

Stato verificato il 20/10/2026 (`git fetch` e `git branch -av`):

| Branch | Ultimo commit | Note |
| --- | --- | --- |
| `main`, `develop` (locali e su GitHub) | `12f9332` | Non contengono né i requisiti corretti né le specifiche |
| `feature/revisione-requisiti` | `265b28e` | Su GitHub, PR verso `develop` non ancora unita |
| `feature/specifiche-tecniche` | `f18f721` | **Solo locale**: non è su GitHub. Parte da `265b28e` |

Prima di creare `feature/base-progetto` servono, in quest'ordine:
1. Unire la PR `feature/revisione-requisiti` → `develop` (la fa l'utente).
2. Pubblicare `feature/specifiche-tecniche` su GitHub e aprire la PR verso `develop`; dopo il punto 1 la PR mostrerà solo `f18f721`. Unirla.
3. Aggiornare `develop` in locale e creare `feature/base-progetto` da lì.

Questo piano è per ora un file non tracciato: segue il cambio di branch e diventa il primo commit di `feature/base-progetto`.

Nota: `gh` (il comando di GitHub) non è installato sul PC, quindi le PR si aprono dal sito di GitHub.

### Strumenti sul PC

| Strumento | Stato verificato | Cosa serve |
| --- | --- | --- |
| Python | 3.13 e 3.10 installati (`py --list`) | Si usa 3.13 |
| Docker | 29.3.0, Compose 5.1.0 | Docker Desktop era spento: va avviato prima del passo 3 |
| PostgreSQL locale | Già in ascolto sulla porta 5432 (processo `postgres`) | Il container usa un'altra porta (scelta 6) |
| gettext | Non installato (`msgfmt` assente) | Serve a Django per creare e compilare le traduzioni (scelta 7) |

## 2. Versioni verificate

Controllate il 20/10/2026 sulle fonti ufficiali.

| Componente | Versione | Fonte | Note |
| --- | --- | --- | --- |
| Django | 5.2.18 (LTS) | djangoproject.com/download | Supporto fino ad aprile 2028. Python 3.10–3.14, PostgreSQL 14 o successivo, psycopg 3.1.8 o successivo |
| psycopg | 3.3.6 | pypi.org/project/psycopg | Python 3.10 o successivo |
| gunicorn | 26.2.0 | pypi.org/project/gunicorn | Python 3.10 o successivo. Non gira su Windows: si usa solo nel deploy (pezzo 7) |
| python-dotenv | 1.2.4 | pypi.org/project/python-dotenv | Python 3.10 o successivo |
| HTMX | 2.0.11 | htmx.org/docs | File JavaScript, non pacchetto Python (scelta 5) |
| PostgreSQL | 18.6 | postgresql.org/support/versioning | Supporto fino a novembre 2030 |
| Immagine Docker | `postgres:18.6` | hub.docker.com/_/postgres | Dalla 18 il volume va montato su `/var/lib/postgresql`, non più su `.../data` |
| GitHub Actions | `actions/checkout@v7`, `actions/setup-python@v7` | Pagine delle release su GitHub | Da ricontrollare al momento di scrivere il file |

`requirements.txt` previsto:

```
Django==5.2.18
psycopg[binary]==3.3.6
gunicorn==26.2.0
python-dotenv==1.2.4
```

## 3. Scelte da confermare

Ogni punto ha una proposta. Le risposte vanno registrate in `decisioni.md`.

1. **Versione di Django.** Proposta: 5.2.18, la versione LTS (supporto lungo, fino ad aprile 2028). L'alternativa 6.1.2 è più recente ma è supportata solo fino a dicembre 2027 e non porta nulla che ci serva.
2. **Python.** Proposta: 3.13, già installato, uguale sul PC e nella CI.
3. **psycopg con `[binary]`.** Proposta: sì. Installa anche il pacchetto `psycopg-binary`, che contiene le librerie di PostgreSQL già compilate: su Windows evita di dover installare un compilatore C. Per il server di produzione si rivaluta nel pezzo 7.
4. **Dipendenze indirette.** Proposta: `requirements.txt` fissa solo le 4 dipendenze dirette concordate. Pip installa da solo quelle che servono a loro (per esempio `asgiref`, `sqlparse`, `tzdata` su Windows, `psycopg-binary`); non sono dipendenze nuove scelte da noi. Alternativa: fissare anche queste con `pip freeze`, più ripetibile ma più lungo da aggiornare.
5. **HTMX.** Proposta: la versione 2.0.11 è annotata qui, ma il file `static/htmx.min.js` si scarica nel pezzo 3, quando nasce il calendario che lo usa. Non va in `requirements.txt`, che contiene solo pacchetti Python.
6. **PostgreSQL in Docker.** Proposta: `postgres:18.6`, uguale sul PC e nella CI. Sul PC il container usa la porta **5433**, perché la 5432 è già occupata dal PostgreSQL installato sul computer. La porta resta configurabile in `.env`.
7. **gettext su Windows.** Proposta: installarlo con `winget install --id mlocati.GetText` (è il pacchetto indicato dalla documentazione di Django). È uno strumento del sistema, non una dipendenza Python. I file compilati delle traduzioni (`.mo`) non vanno in Git: si generano con `compilemessages` sul PC e nella CI.
8. **Lingua dei testi nel codice.** Le specifiche dicono che la traduzione sta in `locale/en/`: quindi i testi dell'interfaccia si scrivono in italiano nel codice (`_("Prenotazione campi")`) e il file inglese li traduce. Nomi, variabili e commenti restano in inglese come da CLAUDE.md. Proposta: confermare.
9. **Formato delle date.** Django in italiano mostra di serie le date come "20 ottobre 2026" e in inglese come "Oct. 20, 2026". Proposta: un modulo di formati per **entrambe** le lingue (`config/formats/it` e `config/formats/en`) con date `gg/mm/aaaa`, orari `HH:MM` e date inserite nei moduli lette come `gg/mm/aaaa` (RNF-10).
10. **`common.now()` nei test.** Proposta: `now()` restituisce l'ora attuale con fuso (in UTC, come `django.utils.timezone.now()`); un "context manager" (un blocco `with`) `fixed_now(istante)` la blocca su un'ora fissa per la durata del blocco. Così funziona anche se un modulo scrive `from common import now`. L'alternativa (`unittest.mock.patch`) obbligherebbe tutti i moduli a scrivere `common.now()` e basta un import sbagliato per rompere i test senza accorgersene.
11. **Template di base.** Per provare davvero una traduzione serve almeno un testo. Proposta: `templates/base.html` minimale, con il solo titolo del sito tradotto ("Prenotazione campi" / "Court booking"). Nessuna view e nessuna pagina.
12. **Admin di Django e prima migrazione.** Proposta: togliere `django.contrib.admin` (le specifiche dicono che non va esposto) e **non** eseguire `migrate` sul database di sviluppo fino al pezzo 2. Il motivo: l'utente personalizzato va definito prima della prima migrazione; se le tabelle dell'utente standard di Django esistessero già, cambiarlo dopo è complicato. I test non ne risentono, perché usano un database temporaneo ricreato a ogni esecuzione.
13. **Test senza requisito.** I test sulla lettura delle variabili d'ambiente non verificano un RF o RNF. Proposta: chiamarli `test_env_...`; tutti gli altri citano l'ID come da CLAUDE.md.
14. **Quando gira la CI.** Proposta: su ogni Pull Request (come dicono le specifiche) e anche a ogni push su `develop` e `main`, così si vede subito se un merge ha rotto qualcosa.
15. **Punti aperti dei pezzi successivi.** Proposta: aggiungerli alle "Ipotesi aperte" di `decisioni.md` (vedi sezione 9), che è l'unico elenco delle ipotesi aperte.

## 4. File da creare o modificare

| File | Contenuto |
| --- | --- |
| `requirements.txt` | Le 4 dipendenze della sezione 2 |
| `manage.py` | Generato da `startproject` |
| `config/__init__.py`, `urls.py`, `wsgi.py` | Generati da `startproject`; `urls.py` senza la rotta dell'admin. `asgi.py` si elimina: gunicorn usa WSGI |
| `config/settings.py` | Riscritto: legge l'ambiente, PostgreSQL, fuso, lingue, formati, template, statici |
| `config/env.py` | Tre funzioni per leggere le variabili: testo obbligatorio, sì/no, lista separata da virgole |
| `config/formats/it/formats.py`, `config/formats/en/formats.py` | Formati di data e ora (scelta 9) |
| `common/__init__.py`, `common/clock.py` | `now()` e `fixed_now()`; `common/__init__.py` espone `now` così che `common.now()` funzioni |
| `accounts/`, `courts/`, `bookings/`, `notifications/`, `audit/` | Generati da `startapp`, vuoti. Si elimina `admin.py` |
| `templates/base.html` | Scheletro HTML con titolo tradotto (scelta 11) |
| `static/.gitkeep` | Cartella dei file statici, vuota per ora |
| `locale/en/LC_MESSAGES/django.po` | Traduzione inglese, generata da `makemessages` |
| `.env.example` | Variabili con valori d'esempio, senza segreti |
| `.gitignore` | Aggiunge `*.mo` |
| `compose.yaml` | Servizio `db` con PostgreSQL |
| `.github/workflows/tests.yml` | Test sulla CI |
| `config/tests/`, `common/tests/` | Test della sezione 6 |
| `CLAUDE.md` | Aggiorna "Stato attuale" e "Comandi" con i comandi eseguiti davvero |
| `docs/decisioni.md` | Registra le scelte approvate e i punti aperti |

### Variabili d'ambiente

| Variabile | Obbligatoria | Valore predefinito | Note |
| --- | --- | --- | --- |
| `DJANGO_SECRET_KEY` | sì | – | Chiave segreta di Django. Senza, il sito non parte |
| `DJANGO_DEBUG` | no | `false` | `true` solo in sviluppo |
| `DJANGO_ALLOWED_HOSTS` | no | vuoto | Nomi del sito separati da virgole |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | sì | – | Le leggono sia Django sia il container |
| `POSTGRES_HOST` | no | `localhost` | |
| `POSTGRES_PORT` | no | `5432` | In `.env.example` vale `5433` (scelta 6) |

`settings.py` carica `.env` con python-dotenv solo se il file esiste e senza sovrascrivere le variabili già impostate: nella CI le variabili arrivano dal workflow. Una variabile obbligatoria mancante ferma l'avvio con un messaggio chiaro (`ImproperlyConfigured`).

Docker Compose legge da solo il file `.env` della cartella del progetto, quindi nome, utente e password del database si scrivono una volta sola.

### `compose.yaml`

Un servizio `db`: immagine `postgres:18.6`, porta `127.0.0.1:${POSTGRES_PORT}:5432` (raggiungibile solo dal PC stesso), volume con nome montato su `/var/lib/postgresql`, controllo di salute con `pg_isready`.

### Workflow della CI

Su Ubuntu: servizio `postgres:18.6` con controllo di salute; Python 3.13; installazione di gettext con `apt-get`; `pip install -r requirements.txt`; poi `compilemessages`, `check`, `makemigrations --check --dry-run` e `test`. Le variabili sono scritte nel workflow: la chiave segreta della CI non protegge nulla, quindi non serve un segreto di GitHub.

## 5. Passi e comandi (PowerShell)

Si lavora nella cartella del progetto, su `feature/base-progetto`. Ogni passo si chiude solo se il suo comando dà il risultato atteso.

**Passo 1 – Strumenti.**
```powershell
winget install --id mlocati.GetText
msgfmt --version          # in un terminale nuovo, dopo l'installazione
```

**Passo 2 – Ambiente Python e dipendenze.**
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

**Passo 3 – Scheletro del progetto e database.**
```powershell
.\.venv\Scripts\python.exe -m django startproject config .
foreach ($app in "common", "accounts", "courts", "bookings", "notifications", "audit") { .\.venv\Scripts\python.exe manage.py startapp $app }
Copy-Item .env.example .env   # poi si inseriscono chiave e password generate così:
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(50))"
docker compose up -d db
docker compose ps             # atteso: db "healthy"
```
Poi si scrivono `config/env.py` e la parte di `settings.py` che legge ambiente e database, senza ancora fuso, lingue e formati: servono perché i test possano partire.

**Passo 4 – Test prima del codice.** Si scrivono i test della sezione 6 e si eseguono:
```powershell
.\.venv\Scripts\python.exe manage.py test
```
Atteso: falliscono i test su fuso, lingue, formati, traduzione, `now()` e admin, perché le impostazioni generate da Django sono ancora quelle predefinite (`UTC`, `en-us`) e `common.now()` non esiste. Si annota quali falliscono e perché: un test che passa subito non sta provando nulla e va rivisto.

**Passo 5 – Codice.** Impostazioni di fuso, lingue e formati; `common/clock.py`; `templates/base.html`; rimozione dell'admin.

**Passo 6 – Traduzioni.**
```powershell
.\.venv\Scripts\python.exe manage.py makemessages -l en --ignore=.venv
# si traduce a mano locale/en/LC_MESSAGES/django.po
.\.venv\Scripts\python.exe manage.py compilemessages --ignore=.venv
```

**Passo 7 – Test verdi e controlli.**
```powershell
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

**Passo 8 – CI.** Si scrive `.github/workflows/tests.yml`. Si può provare solo dopo il push, che si fa su richiesta.

**Passo 9 – Documenti.** Si aggiornano `CLAUDE.md` ("Stato attuale" e "Comandi", solo con i comandi eseguiti davvero) e `decisioni.md`.

## 6. Test da scrivere prima del codice

| File | Test | Cosa verifica |
| --- | --- | --- |
| `config/tests/test_env.py` | `test_env_missing_required_variable_raises` | Variabile obbligatoria assente: errore chiaro |
| | `test_env_bool_accepts_true_false` | `true`/`false`, `1`/`0`, maiuscole e minuscole; un valore diverso dà errore |
| | `test_env_list_splits_on_commas` | `"a, b,,c"` diventa `["a", "b", "c"]`; vuoto diventa lista vuota |
| `config/tests/test_settings.py` | `test_rnf03_time_zone_is_europe_rome` | `TIME_ZONE = "Europe/Rome"` e `USE_TZ = True` |
| | `test_rnf02_italian_default_and_english_available` | `LANGUAGE_CODE = "it"`, lingue `it` ed `en` |
| | `test_rnf04_tests_run_on_postgresql` | Il database è PostgreSQL: i vincoli di RNF-04 non esistono su SQLite |
| | `test_rf45_django_admin_not_installed` | `django.contrib.admin` assente: niente modifiche che saltano le regole |
| `config/tests/test_locale.py` | `test_rnf10_date_format_it`, `test_rnf10_date_format_en` | 9 marzo 2026 si mostra `09/03/2026` in entrambe le lingue, sia con il filtro `date` sia con la visualizzazione predefinita |
| | `test_rnf10_time_24_hours_it`, `test_rnf10_time_24_hours_en` | 20:30 si mostra `20:30`, non `8:30 p.m.` |
| | `test_rnf10_date_input_dd_mm_yyyy_en` | In inglese un modulo legge `09/03/2026` come 9 marzo, non 3 settembre |
| | `test_rnf02_base_template_translated` | Il titolo è "Prenotazione campi" in italiano e "Court booking" in inglese |
| | `test_rnf03_display_in_rome_time_across_dst` | Lo stesso orario UTC si mostra con l'ora italiana giusta: 28/03/2026 07:00 UTC → 08:00; 29/03/2026 06:00 UTC → 08:00 (ora legale); 25/10/2026 07:00 UTC → 08:00 (ora solare) |
| `common/tests/test_clock.py` | `test_rnf03_now_is_timezone_aware` | `now()` ha il fuso ed è vicina all'ora reale |
| | `test_rnf03_fixed_now_returns_given_instant` | Dentro `fixed_now(x)`, `common.now()` restituisce `x`; fuori torna all'ora reale |
| | `test_rnf03_fixed_now_works_with_direct_import` | Funziona anche con `from common import now` |
| | `test_rnf03_fixed_now_rejects_naive_datetime` | Un orario senza fuso viene rifiutato, così un test non può usare per sbaglio un'ora ambigua |

Le date del cambio d'ora 2026 sono verificate sul calendario: domenica 29 marzo e domenica 25 ottobre.

## 7. Verifiche da eseguire davvero

Si annotano come **eseguita** (con il risultato) o **da fare**, senza simulare risultati.

| Verifica | Comando | Risultato atteso |
| --- | --- | --- |
| Dipendenze coerenti | `pip check` | "No broken requirements found." |
| Database avviato | `docker compose ps` | `db` in stato "healthy" |
| Test rossi prima del codice | `manage.py test` (passo 4) | Falliscono i test elencati al passo 4 |
| Test verdi | `manage.py test` (passo 7) | Tutti superati, con il numero dei test |
| Configurazione | `manage.py check` | "System check identified no issues" |
| Nessuna migrazione dimenticata | `makemigrations --check --dry-run` | "No changes detected" |
| Traduzioni compilate | `compilemessages` | Crea `locale/en/LC_MESSAGES/django.mo` senza errori |
| Avvio senza chiave | `manage.py check` con `DJANGO_SECRET_KEY` tolta | Si ferma con `ImproperlyConfigured` |
| Segreti fuori da Git | `git status` | `.env`, `.venv/` e `*.mo` non compaiono |
| CI | Esito del workflow su GitHub | Verde. **Da fare dopo il push**, su richiesta |

## 8. Fuori da questo pezzo

- Utente personalizzato, login, selettore della lingua e `LocaleMiddleware`: pezzo 2, dove c'è una pagina su cui provarli.
- `django.contrib.postgres`, estensione `btree_gist`, `DomainError`: pezzo 3, con il primo servizio e i primi vincoli.
- File `htmx.min.js`: pezzo 3 (scelta 5).
- Dockerfile, `compose.prod.yaml`, Caddy, configurazione di gunicorn: pezzo 7.

Nota per i pezzi successivi: i campi `created_at` useranno `default=common.now`, non `auto_now_add`, che leggerebbe l'ora direttamente da Django e non si potrebbe fissare nei test.

## 9. Punti aperti dei pezzi successivi

Non bloccano questo pezzo. Da registrare in `decisioni.md` (scelta 15):

- **Pezzo 5:** cosa succede se l'admin corregge un esito su cui è già stato registrato un saldo.
- **Sezione 3 delle specifiche:** una prenotazione offerta cancellata dall'admin nelle ultime 2 ore non genera addebito. È una deduzione, va confermata.

## 10. Commit proposti

Solo su richiesta, uno per ogni risultato verificato:

1. `docs(piani): aggiunge il piano della base del progetto`
2. `chore(base): crea il progetto Django con PostgreSQL in Docker`
3. `feat(common): aggiunge now() con ora fissabile nei test`
4. `feat(i18n): configura fuso orario, lingue e formati delle date`
5. `chore(ci): esegue i test su PostgreSQL con GitHub Actions`
6. `docs: aggiorna CLAUDE.md e decisioni del pezzo 1`

## 11. Note dall'esecuzione

- **Chiave segreta senza `$`.** La chiave di `get_random_secret_key()` può contenere `$`; Docker Compose legge anche `.env` e scambia `$...` per una variabile da sostituire (avviso "The "ba" variable is not set"). Si genera con `secrets.token_urlsafe(50)`, che usa solo lettere, cifre, `-` e `_`.
- **Host `127.0.0.1`, non `localhost`.** Con `localhost` la creazione del database di test restava bloccata: su Windows `localhost` prova prima l'indirizzo IPv6 `::1`, dove la connessione resta appesa (prova diretta: `127.0.0.1` risponde in 0,01 s, `localhost` solo allo scadere di un timeout di 10 s). L'host predefinito è `127.0.0.1` e `DATABASES` ha `connect_timeout` di 10 secondi, così un database irraggiungibile dà un errore invece di bloccare tutto.
- **`--noinput` nei test.** Interrompere i test lascia il database `test_prenotazioni`; all'esecuzione successiva Django chiede se eliminarlo. `--noinput` lo elimina senza chiedere.
- **Test che passano prima del codice.** I 9 `test_env_...` (scritti e visti fallire prima di `config/env.py`), `test_rnf04_tests_run_on_postgresql` (il database va configurato prima di poter eseguire i test) e la lettura di `09/03/2026` in italiano (già prevista da Django; in inglese falliva).
- **Formati di input.** Oltre a `gg/mm/aaaa`, le date nei moduli accettano anche `aaaa-mm-gg`, il formato che invia il campo data dei browser.
- **Commit raggruppati.** I commit 2, 3 e 4 della sezione 10 sono diventati uno solo: `config/settings.py` contiene sia la base sia fuso, lingue e formati, e i test di `common` richiedono le impostazioni. Separarli avrebbe creato versioni intermedie mai provate. Commit eseguiti: piano, progetto (codice e test), CI, documenti.

## 12. Verifiche eseguite

20/10/2026, sul PC.

| Verifica | Esito |
| --- | --- |
| `pip check` | Eseguita: "No broken requirements found." |
| `docker compose ps` | Eseguita: `db` "healthy" su `127.0.0.1:5433` |
| Test rossi prima del codice | Eseguita: 21 test, 16 falliti e 3 errori, per i motivi attesi (fuso `UTC`, lingua `en-us`, formati americani, admin presente, `base.html` e `common.now` mancanti) |
| Test verdi | Eseguita: 25 test superati |
| `manage.py check` | Eseguita: "System check identified no issues (0 silenced)." |
| `makemigrations --check --dry-run` | Eseguita: "No changes detected" |
| `compilemessages` | Eseguita: creato `locale/en/LC_MESSAGES/django.mo` |
| Avvio senza chiave | Eseguita: `ImproperlyConfigured: Missing required environment variable DJANGO_SECRET_KEY.` |
| Segreti fuori da Git | Eseguita: `.env`, `.venv/` e `django.mo` ignorati (`git check-ignore`) |
| CI su GitHub | Eseguita il 28/10/2026 sulla PR #6: 25 test superati, `check` e `makemigrations --check` senza problemi |
