# Decisioni di progetto

Registro delle decisioni prese durante il progetto. I requisiti sono in `requisiti-prenotazione-campi.md`.
Questo è l'unico elenco delle ipotesi aperte: i requisiti rimandano qui.

## Decisioni prese

| Data | Tema | Decisione |
| --- | --- | --- |
| 2026-10-20 | Stack | Django + PostgreSQL, template lato server, HTMX solo per il calendario, Docker per sviluppo e deploy |
| 2026-10-20 | Lingue | Comunicazione, documenti e descrizioni dei commit in italiano; codice (nomi e commenti) in inglese |
| 2026-10-20 | Branch | Gitflow semplificato: `main` (versioni rilasciabili), `develop` (integrazione), `feature/<nome>` da `develop` |
| 2026-10-20 | Integrazione | Pull Request su GitHub (feature → develop, develop → main); il merge lo fa l'utente |
| 2026-10-20 | Commit | Conventional Commits, descrizione in italiano |
| 2026-10-20 | Saldo parziale (RF-54) | Confermata l'ipotesi: il saldo si registra per intero, una prenotazione alla volta |
| 2026-10-20 | Riepilogo incassi (RF-56) | Confermata l'ipotesi: riepilogo giornaliero di pagamenti, saldi e rimborsi, con totale in contanti |
| 2026-10-20 | Codice tessera (RF-31) | Lettere e numeri, da 1 a 20 caratteri, maiuscole e minuscole non distinte. L'admin usa un codice riservato |
| 2026-10-20 | Sblocco (RF-29) | Resta solo manuale: saldo, rimozione o correzione di uno strike non sbloccano l'account |
| 2026-10-20 | Prezzi (RF-05) | Il prezzo è per tipo di campo: i due campi da tennis hanno sempre lo stesso prezzo |
| 2026-10-20 | Admin e RF-44 | Anche l'admin non può creare due prenotazioni sovrapposte per la stessa persona |
| 2026-10-20 | Finestra (RF-08) | 14 giorni di calendario da oggi, ultimo giorno incluso; lo slot deve iniziare dopo il momento attuale |
| 2026-10-20 | Prenotazione attiva (RF-09) | Stato Prenotata, Pagata o Offerta e slot non ancora finito |
| 2026-10-20 | Cancellazione dell'admin (RF-17, RF-19) | Dalle ultime 2 ore alla fine dello slot valgono addebito e strike a scelta; si cancellano solo Prenotata, Pagata e Offerta |
| 2026-10-20 | Motivo (RF-18) | Motivi di sistema fissi e tradotti; motivo dell'admin a testo libero, non tradotto |
| 2026-10-20 | Rimborsi (RF-48) | Rimborso per ogni prenotazione pagata cancellata o annullata senza addebito; con addebito il pagamento copre l'importo |
| 2026-10-20 | Disattivazione (RF-40) | Le prenotazioni non ancora iniziate vengono annullate dal sistema; l'admin non prenota per account disattivati |
| 2026-10-20 | Strike su account bloccato (RF-28, RF-50) | Uno strike successivo si registra senza nuova notifica; una correzione non sblocca l'account |
| 2026-10-20 | Blocco campo (RF-14, RNF-04) | Solo intervalli futuri; annulla le prenotazioni non ancora iniziate sovrapposte anche in parte; garantito anche nel database |
| 2026-10-20 | Sicurezza (RNF-05) | 5 tentativi di login falliti bloccano il codice per 15 minuti; sessione di 30 minuti per tutti gli utenti |
| 2026-10-20 | Formati (RNF-10) | Date gg/mm/aaaa in entrambe le lingue, orari a 24 ore |
| 2026-10-20 | Prenotazioni da chiudere | Nessuna notifica: contatore nella lista "da chiudere" del pannello admin |
| 2026-10-20 | Notifiche (RNF-02) | Si salvano tipo e dati, non il testo; la notifica di scadenza del giorno stesso dice "La tessera scade oggi" |
| 2026-10-20 | Movimenti | Un'unica entità con pagamento, addebito, saldo e rimborso |
| 2026-10-20 | Strike | Non si cancellano: si segnano come rimossi, con data e causa |
| 2026-10-20 | Responsive (RNF-01) | Fuori dalla prima versione, possibile sviluppo futuro |
| 2026-10-20 | Specifiche tecniche | Unico file `specifiche-tecniche.md` per tutta l'app; piani di realizzazione un pezzo alla volta; niente user story |
| 2026-10-20 | Architettura | Pagine proprie per tesserato e admin, regole nelle funzioni di servizio; pannello admin di Django non esposto |
| 2026-10-20 | Job giornaliero | Comando `send_card_reminders` eseguito ogni ora dal servizio `scheduler` di Docker Compose, senza duplicare gli avvisi |
| 2026-10-20 | Tentativi di login | Gestiti nel progetto, senza librerie esterne |
| 2026-10-20 | Dipendenze | Django, psycopg, gunicorn, python-dotenv; HTMX come file statico; test con il runner di Django |
| 2026-10-20 | Backup del database | Escluso per ora, per scelta dell'utente |

## Ipotesi aperte

Da confermare prima di implementare le parti collegate.

- [ ] **Conservazione dei dati (RNF-06).** Per quanto tempo si tiene lo storico di prenotazioni e strike? Da decidere con il titolare insieme all'informativa privacy, prima della messa in produzione.
