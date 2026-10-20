# Decisioni di progetto

Registro delle decisioni prese durante il progetto. I requisiti sono in `requisiti-prenotazione-campi.md`.

## Decisioni prese

| Data | Tema | Decisione |
| --- | --- | --- |
| 2026-10-20 | Stack | Django + PostgreSQL, template lato server, HTMX solo per il calendario, Docker per sviluppo e deploy |
| 2026-10-20 | Lingue | Comunicazione, documenti e descrizioni dei commit in italiano; codice (nomi e commenti) in inglese |
| 2026-10-20 | Branch | Gitflow semplificato: `main` (versioni rilasciabili), `develop` (integrazione), `feature/<nome>` da `develop` |
| 2026-10-20 | Integrazione | Pull Request su GitHub (feature → develop, develop → main); il merge lo fa l'utente |
| 2026-10-20 | Commit | Conventional Commits, descrizione in italiano |

## Ipotesi aperte

Da confermare prima di implementare le parti collegate.

- [ ] **Saldo parziale (RF-54).** Ipotesi: il saldo si fa sempre per intero, una prenotazione alla volta.
- [ ] **Riepilogo incassi (RF-56).** Ipotesi: serve un riepilogo giornaliero dei contanti.
- [ ] **Formato del codice tessera.** Solo numeri, lettere e numeri, lunghezza?
- [ ] **Conservazione dei dati.** Per quanto tempo si tiene lo storico di prenotazioni e strike (RNF-06)?
