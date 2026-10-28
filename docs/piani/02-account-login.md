# Piano 2 – Account e login

28/10/2026 · approvato (tutte le scelte della sezione 3 accettate così come proposte)

Secondo dei 7 pezzi di `specifiche-tecniche.md` (sezione 7). Alla fine di questo pezzo il sito ha gli utenti: l'unico admin e i tesserati entrano con codice tessera e password, cambiano la password temporanea, scelgono la lingua, e l'admin crea, modifica e disattiva gli account. Ogni azione dell'admin sugli utenti finisce nel registro azioni.

Non ci sono ancora campi, prenotazioni, strike né notifiche.

## 1. Prerequisiti

- Branch `feature/account-login`, creato da `develop` dopo il merge della PR #6 (`8f4f8ec`).
- Database di sviluppo avviato (`docker compose up -d db`). Ancora senza migrazioni: la prima si esegue in questo pezzo, dopo aver definito l'utente personalizzato.
- Nessuna nuova dipendenza: tutto quello che serve è già in Django (login, hash delle password, sessioni, traduzioni).

## 2. Requisiti coperti

| Requisito | Cosa si realizza qui | Cosa resta ai pezzi successivi |
| --- | --- | --- |
| RF-01 | Due ruoli, un solo admin garantito dal database | – |
| RF-30 | Creazione account da parte dell'admin | – |
| RF-31 | Login con codice tessera, senza distinzione tra maiuscole e minuscole; codice riservato dell'admin | Admin non intestatario di prenotazioni: pezzo 3 |
| RF-32 | Password temporanea e cambio obbligatorio al primo accesso | – |
| RF-33 | L'admin assegna una nuova password temporanea; il gestore del server usa `changepassword` | – |
| RF-34 | Con la tessera scaduta si accede | Divieto di prenotare: pezzo 3 |
| RF-35 | L'admin aggiorna la scadenza della tessera | – |
| RF-40 | Un account disattivato non può accedere | Annullamento delle prenotazioni: pezzo 3 (già concordato) |
| RF-55 | Il tesserato cambia solo password e lingua | – |
| RF-28 | Con l'account bloccato si accede (il campo `is_blocked` esiste già) | Blocco e sblocco: pezzo 5 (già concordato) |
| RNF-02 | Lingua dell'utente dopo il login, selettore nella pagina di accesso | – |
| RNF-05 | Hash, password di almeno 8 caratteri, 5 tentativi falliti bloccano il codice per 15 minuti, sessione di 30 minuti | HTTPS: pezzo 7 |
| RNF-07 | Registro azioni (`ActionLog`, `log_action()`) per le azioni dell'admin sugli utenti (già concordato) | Azioni su prenotazioni, pagamenti e strike: pezzi 3–5 |
| RF-46 | Pagina "Il mio account" con la scadenza della tessera | Debito e strike: pezzo 5 |

## 3. Scelte da confermare

Già concordate il 28/10/2026: registro azioni in questo pezzo; disattivazione che per ora blocca solo l'accesso; strike e sblocco nel pezzo 5; admin creato con un comando di Django.

Ogni punto ha una proposta. Le risposte vanno registrate in `decisioni.md`.

1. **Formato del codice tessera.** RF-31 dice "lettere e numeri, da 1 a 20". Proposta: solo lettere `A`–`Z` senza accenti e cifre `0`–`9`, salvate in maiuscolo. Il codice dell'admin segue lo stesso formato (per esempio `ADMIN`). Nel database un solo vincolo controlla insieme formato e maiuscole, così un codice minuscolo non può entrare nemmeno per errore.
2. **Messaggi del login.** Proposta: due messaggi soli.
   - "Codice tessera o password non corretti": per password sbagliata, codice inesistente e account disattivato. Così chi prova non scopre quali codici esistono o sono disattivati.
   - "Troppi tentativi falliti: riprova tra 15 minuti": dopo 5 errori in 15 minuti su quel codice, anche se il codice non esiste.
   Durante il blocco anche la password giusta viene rifiutata, e i tentativi non si contano: il blocco finisce 15 minuti dopo il quinto errore. Se si contassero, chi continua a provare terrebbe il codice bloccato per sempre.
3. **Regole della password.** Django di serie ha 4 controlli: lunghezza minima 8, password troppo simile ai dati dell'utente, password troppo comune (`password123`), password fatta solo di numeri. I requisiti chiedono solo "almeno 8 caratteri". Proposta: tenere solo la lunghezza minima, per non aggiungere regole non scritte. Alternativa: tenerli tutti e 4, più sicuro, registrandolo come decisione.
4. **Password temporanea.** Proposta: la scrive l'admin nel modulo, alla creazione dell'account e ogni volta che ne assegna una nuova (RF-32, RF-33); vale la regola degli 8 caratteri. L'alternativa (password generata dal sito e mostrata una volta) obbliga l'admin a copiarla al momento.
5. **Riattivazione.** I requisiti dicono che un account si disattiva, ma non se si può riattivare. Senza riattivazione, un tesserato che torna non può più avere un account, perché il suo codice tessera resta occupato. Proposta: l'admin può riattivare un account; l'azione va nel registro, e le prenotazioni annullate alla disattivazione non tornano.
6. **Lingua.** Proposta: il selettore della pagina di accesso cambia solo le pagine prima del login. Dopo il login vale la lingua salvata sull'utente (specifiche, sezione 4), che il tesserato cambia da "Il mio account" (RF-55). L'admin sceglie la lingua alla creazione dell'account (predefinito italiano); dopo non la modifica, perché è una scelta del tesserato.
7. **Pagine di questo pezzo.** Proposta: dopo il login il tesserato arriva su "Il mio account" (dati, scadenza della tessera, lingua, link al cambio password) e l'admin sull'elenco utenti. Dal pezzo 3 entrambi arriveranno al calendario.
8. **Elenco utenti dell'admin.** Proposta: tutti i tesserati, attivi e disattivati, in ordine di cognome, con codice, nome, scadenza della tessera e stato. Per ora niente ricerca: con pochi tesserati non serve, si aggiunge se diventa scomoda. L'account admin non compare nell'elenco e non si modifica da lì: cambia la propria password come tutti.
9. **Aspetto delle pagine.** Proposta: un piccolo file `static/css/site.css` scritto a mano, senza librerie grafiche. Il layout è solo per desktop (RNF-01).

## 4. Modello dati

### `accounts.User`

Basato su `AbstractBaseUser` di Django, che fornisce password con hash e ultimo accesso. Non si usano gruppi e permessi di Django (`PermissionsMixin`): i ruoli sono solo due (RF-01). Campi come nelle specifiche (sezione 2): `card_code`, `first_name`, `last_name`, `card_expiry`, `role`, `language`, `is_active`, `is_blocked`, `must_change_password`, `email`, `phone`.

`AUTH_USER_MODEL = "accounts.User"`, `USERNAME_FIELD = "card_code"`. Il gestore (`UserManager`) cerca il codice sempre in maiuscolo, così il login non distingue tra maiuscole e minuscole.

Vincoli nel database:

| Vincolo | Requisito |
| --- | --- |
| `card_code` univoco | RF-31 |
| `card_code` fatto solo di `A`–`Z` e `0`–`9`, da 1 a 20 caratteri (quindi maiuscolo) | RF-31 (scelta 1) |
| Al massimo una riga con `role = 'admin'` | RF-01 |
| `card_expiry` presente se `role = 'member'`, vuota se `role = 'admin'` | RF-30, RF-31 |

### `accounts.LoginAttempt`

`card_code` (maiuscolo), `created_at` (`default=common.now`). Un record per ogni login fallito fuori dal blocco; al login riuscito si eliminano quelli del codice (specifiche, sezione 5).

### `audit.ActionLog`

`actor` (l'admin), `action`, `object_type`, `object_id`, `before` e `after` (JSON), `created_at` (`default=common.now`). Si scrive con `log_action()`, nella stessa transazione dell'azione. Le password, anche temporanee, non entrano mai nel registro: si registra solo che è stata assegnata.

Azioni di questo pezzo: `user_created`, `user_updated`, `user_deactivated`, `user_reactivated`, `temporary_password_set`.

## 5. Servizi, pagine e comandi

### Servizi (`accounts/services.py`)

Ognuno in una transazione, con la riga dell'utente bloccata (`select_for_update`) e una riga di `log_action()`:

| Servizio | Effetto |
| --- | --- |
| `create_member(actor, data, temporary_password)` | Crea il tesserato con `must_change_password` vero |
| `update_member(actor, member, data)` | Modifica nome, cognome, codice, scadenza, email, telefono |
| `set_temporary_password(actor, member, password)` | Nuova password, `must_change_password` vero; le sessioni aperte del tesserato scadono (Django lo fa da solo quando cambia la password) |
| `deactivate_member(actor, member)` | `is_active` falso |
| `reactivate_member(actor, member)` | `is_active` vero (scelta 5) |

Il login, il cambio della propria password e della lingua non sono azioni dell'admin sugli utenti: non vanno nel registro.

### Middleware

- `LocaleMiddleware` di Django: lingua prima del login (selettore, scelta 6).
- `UserLanguageMiddleware`: dopo il login attiva `User.language`.
- `PasswordChangeRequiredMiddleware`: con `must_change_password` vero, ogni pagina rimanda al cambio password, tranne il cambio stesso, il logout e il selettore della lingua (RF-32).

### Pagine

| Indirizzo | Chi | Contenuto |
| --- | --- | --- |
| `/login/` | tutti | Codice tessera, password, selettore della lingua |
| `/logout/` | utente collegato | Solo con pulsante (richiesta POST, come vuole Django 5) |
| `/password/` | utente collegato | Cambio password: vecchia, nuova, conferma |
| `/account/` | tesserato | "Il mio account": dati, scadenza tessera, modulo della lingua (scelta 7) |
| `/staff/users/` | admin | Elenco utenti (scelta 8) |
| `/staff/users/new/` | admin | Creazione con password temporanea |
| `/staff/users/<id>/` | admin | Modifica dati, nuova password temporanea, disattiva o riattiva |

Un tesserato che apre una pagina dell'admin riceve "accesso negato" (errore 403); chi non è collegato viene mandato al login. Gli indirizzi sono in inglese e non si traducono; i testi delle pagine sì.

### Impostazioni

`AUTH_USER_MODEL`, `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `SESSION_COOKIE_AGE = 1800`, `SESSION_SAVE_EVERY_REQUEST = True` (RNF-05), validatori della password secondo la scelta 3.

### Comandi

- `create_admin`: chiede codice, nome, cognome e password (due volte, senza mostrarla); rifiuta se l'admin esiste già (RF-01).
- `changepassword <codice>`: già incluso in Django, per l'admin che dimentica la password (RF-33). Da provare con l'utente personalizzato. Questo comando cerca il codice così com'è scritto, senza passare dal gestore: va scritto in maiuscolo (`changepassword ADMIN`).

## 6. Passi e comandi (PowerShell)

**Passo 1 – Test del modello prima del codice.** Si scrivono i test della sezione 7 sul modello e sui vincoli. Atteso: errori, perché `accounts.User` non esiste.

**Passo 2 – Modello e prima migrazione.** `User`, `UserManager`, `LoginAttempt`, `ActionLog`, `log_action()`, impostazioni.
```powershell
.\.venv\Scripts\python.exe manage.py makemigrations accounts audit
.\.venv\Scripts\python.exe manage.py test --noinput
.\.venv\Scripts\python.exe manage.py migrate        # primo migrate sul database di sviluppo
```

**Passo 3 – Login, tentativi falliti, cambio password, lingua.** Prima i test, visti fallire, poi form, view, middleware e template.

**Passo 4 – Gestione utenti e registro azioni.** Prima i test, poi servizi e pagine dell'admin.

**Passo 5 – Comando `create_admin`.** Prima i test, poi il comando.

**Passo 6 – Traduzioni.**
```powershell
.\.venv\Scripts\python.exe manage.py makemessages -l en --ignore=.venv
# si traduce a mano locale/en/LC_MESSAGES/django.po
.\.venv\Scripts\python.exe manage.py compilemessages --ignore=.venv
```

**Passo 7 – Test verdi, controlli e prova a mano.**
```powershell
.\.venv\Scripts\python.exe manage.py test --noinput
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py create_admin
.\.venv\Scripts\python.exe manage.py runserver
```
Giro nel browser: login dell'admin, creazione di un tesserato, primo accesso con cambio password, cambio lingua, disattivazione.

**Passo 8 – Documenti.** `CLAUDE.md` ("Stato attuale", "Comandi" con quelli eseguiti davvero) e `decisioni.md`.

## 7. Test da scrivere prima del codice

| File | Test | Cosa verifica |
| --- | --- | --- |
| `accounts/tests/test_models.py` | `test_rf31_card_code_unique` | Due utenti con lo stesso codice: rifiutato dal database |
| | `test_rf31_card_code_format_enforced_in_db` | `abc1`, `AB-1` e 21 caratteri rifiutati dal database |
| | `test_rf01_only_one_admin_in_db` | Un secondo admin rifiutato dal database |
| | `test_rf30_member_requires_card_expiry_in_db` | Tesserato senza scadenza rifiutato |
| | `test_rf31_admin_has_no_card_expiry_in_db` | Admin con scadenza rifiutato |
| | `test_rnf05_password_stored_hashed` | La password salvata non è quella in chiaro |
| `accounts/tests/test_login.py` | `test_rf31_login_any_case` | `abc1` entra nell'account `ABC1` |
| | `test_rf31_admin_uses_same_form` | L'admin entra dalla stessa pagina con il suo codice |
| | `test_rnf05_wrong_password_and_unknown_code_same_message` | Stesso messaggio nei due casi |
| | `test_rnf05_fifth_failure_locks_code` | Al sesto tentativo, anche con la password giusta: messaggio di blocco |
| | `test_rnf05_lock_ends_after_15_minutes` | Con `fixed_now()`: dopo 15 minuti si entra |
| | `test_rnf05_lock_applies_to_unknown_code` | Il blocco vale anche per codici inesistenti |
| | `test_rnf05_attempts_during_lock_not_counted` | Il blocco non si allunga provando di nuovo |
| | `test_rnf05_success_clears_attempts` | Dopo un login riuscito il conteggio riparte da zero |
| | `test_rnf05_session_lasts_30_minutes_of_inactivity` | `SESSION_COOKIE_AGE` 1800 e rinnovo a ogni richiesta |
| | `test_rf40_deactivated_cannot_log_in` | Messaggio generico, nessun accesso |
| | `test_rf40_deactivation_ends_open_session` | La pagina successiva rimanda al login |
| | `test_rf34_expired_card_can_log_in` | Si entra con la tessera scaduta |
| | `test_rf28_blocked_account_can_log_in` | Si entra con l'account bloccato |
| `accounts/tests/test_password.py` | `test_rf32_must_change_password_redirects` | Ogni pagina rimanda al cambio password |
| | `test_rf32_change_clears_flag` | Dopo il cambio si naviga normalmente |
| | `test_rf32_member_can_change_password_later` | Il cambio resta disponibile |
| | `test_rnf05_password_min_8_characters` | 7 caratteri rifiutati, 8 accettati |
| `accounts/tests/test_language.py` | `test_rnf02_login_page_language_selector` | Il selettore mostra la pagina di accesso in inglese |
| | `test_rnf02_user_language_after_login` | Dopo il login vale `User.language` |
| | `test_rf55_member_changes_language` | Il tesserato cambia la propria lingua |
| | `test_rf55_member_cannot_change_other_data` | Il modulo di "Il mio account" accetta solo la lingua |
| `accounts/tests/test_admin_users.py` | `test_rf30_admin_creates_member` | Dati obbligatori, email e telefono facoltativi |
| | `test_rf31_rejects_duplicate_code_any_case` | `abc1` rifiutato se esiste `ABC1` |
| | `test_rf31_rejects_invalid_code` | Simboli e più di 20 caratteri rifiutati con messaggio |
| | `test_rf31_member_cannot_take_admin_code` | Il codice dell'admin non si può assegnare a una tessera |
| | `test_rf32_new_member_must_change_password` | Il tesserato creato deve cambiare password |
| | `test_rf33_admin_sets_temporary_password` | Nuova password temporanea e cambio obbligatorio |
| | `test_rf35_admin_updates_card_expiry` | La scadenza si aggiorna |
| | `test_rf40_admin_deactivates_member` | L'account non entra più |
| | `test_rf40_admin_reactivates_member` | Secondo la scelta 5 |
| | `test_rf01_member_gets_403_on_admin_pages` | Accesso negato |
| | `test_rf01_anonymous_redirected_to_login` | Rimando al login |
| | `test_rnf07_admin_actions_logged` | Ogni azione scrive il registro con valori prima e dopo |
| | `test_rnf07_password_never_logged` | Nel registro non c'è la password né il suo hash |
| `accounts/tests/test_commands.py` | `test_rf01_create_admin_command` | Crea l'admin senza scadenza della tessera |
| | `test_rf01_create_admin_refuses_second_admin` | Rifiutato se l'admin esiste |
| | `test_rf33_changepassword_command_uses_card_code` | Il comando di Django trova l'utente dal codice |
| `audit/tests/test_log.py` | `test_rnf07_log_action_in_same_transaction` | Se l'azione fallisce, nel registro non resta nulla |

## 8. Verifiche da eseguire davvero

| Verifica | Comando | Risultato atteso |
| --- | --- | --- |
| Test rossi prima del codice | `manage.py test --noinput` (passi 1, 3, 4, 5) | Falliscono i test nuovi, per i motivi attesi |
| Test verdi | `manage.py test --noinput` | Tutti superati, con il numero dei test |
| Configurazione | `manage.py check` | "System check identified no issues" |
| Migrazioni | `makemigrations --check --dry-run` | "No changes detected" |
| Prima migrazione | `manage.py migrate` | Tabelle create sul database di sviluppo |
| Traduzioni | `compilemessages` | Nessun errore; nessun testo nuovo senza traduzione nel `.po` |
| Prova nel browser | Passo 7 | Annotata come eseguita o da fare |
| CI | Esito sulla PR | Verde, dopo il push su richiesta |

## 9. Fuori da questo pezzo

- Annullamento delle prenotazioni alla disattivazione (RF-40): pezzo 3, quando esistono le prenotazioni.
- Admin non intestatario di prenotazioni (RF-31): pezzo 3.
- Strike, blocco, sblocco, debito in "Il mio account": pezzo 5.
- Notifiche, anche per la scadenza della tessera: pezzo 6.
- `DomainError`: pezzo 3, con le prime regole di prenotazione. In questo pezzo gli errori dei dati si mostrano con la validazione dei moduli.
- HTTPS, cookie sicuri, HSTS: pezzo 7.

## 10. Commit proposti

Solo su richiesta, uno per ogni risultato verificato:

1. `docs(piani): aggiunge il piano di account e login`
2. `feat(accounts): aggiunge l'utente con codice tessera e il registro azioni`
3. `feat(accounts): aggiunge login con blocco dei tentativi, cambio password e lingua`
4. `feat(accounts): aggiunge la gestione utenti dell'admin`
5. `feat(accounts): aggiunge il comando create_admin`
6. `docs: aggiorna CLAUDE.md e decisioni del pezzo 2`

## 11. Note dall'esecuzione

- **Lingua senza `LocaleMiddleware`.** Il piano prevedeva il `LocaleMiddleware` di Django più un middleware per la lingua dell'utente. È diventato un solo middleware (`UserLanguageMiddleware`): `LocaleMiddleware` segue anche la lingua del browser, e con un browser in inglese la pagina di accesso sarebbe uscita in inglese, mentre l'italiano è la lingua predefinita (RNF-02). Il middleware sta prima di `MessageMiddleware`, così anche i messaggi di conferma sono nella lingua giusta.
- **"Il mio account" anche per l'admin.** RNF-02 dice che ogni utente sceglie la propria lingua: la pagina è aperta anche all'admin, senza la scadenza della tessera.
- **Codice troppo lungo nel database.** Un codice di 21 caratteri viene rifiutato con `DataError` (valore più lungo della colonna), non con `IntegrityError` (vincolo violato): il test accetta entrambi.
- **Test che passano prima del codice.** `test_rnf07_log_action_records_actor_object_values_and_time`, perché `log_action()` è stata scritta al passo 2 insieme al modello; `test_rf33_changepassword_command_uses_card_code`, perché il comando è di Django e funziona già con l'utente personalizzato.
- **Test corretto.** `test_rnf07_password_never_logged` controllava che la parola "password" non comparisse nel registro, ma il registro salva giustamente il campo `must_change_password`. Ora controlla che non ci siano la password né il suo hash.
- **Opzioni di `create_admin`.** Codice, nome e cognome si possono passare con `--card-code`, `--first-name` e `--last-name`, altrimenti il comando li chiede. La password si chiede sempre, senza mostrarla.
- **Durata dei test.** 104 test in circa 70 secondi, quasi tutti spesi a calcolare l'hash delle password. Si può accorciare in futuro con un hash veloce solo per i test, se diventa scomodo.

## 12. Verifiche eseguite

28/10/2026, sul PC.

| Verifica | Esito |
| --- | --- |
| Test rossi prima del codice | Eseguita a ogni passo: passo 1 `ImportError` (`User` mancante); passo 3: 33 errori e 1 fallimento (pagine mancanti, durata della sessione); passo 4: pagine dell'admin mancanti; passo 5: comando mancante (6 errori) |
| Test verdi | Eseguita: 104 test superati |
| `manage.py check` | Eseguita: "System check identified no issues (0 silenced)." |
| `makemigrations --check --dry-run` | Eseguita: "No changes detected" |
| Prima migrazione | Eseguita: `migrate` sul database di sviluppo, tutte le migrazioni applicate |
| Traduzioni | Eseguita: 71 testi nuovi tradotti, nessun `msgstr` vuoto oltre all'intestazione; `compilemessages` senza errori |
| Server vero | Eseguita con `runserver`: login in italiano, CSS servito, selettore che passa all'inglese con "Card code" |
| Prova nel browser | Eseguita dall'utente: `create_admin`, login, creazione di un tesserato, cambio password, lingua e disattivazione funzionano. L'aspetto grafico va rifatto in futuro |
| CI | **Da fare**: dopo il push |
