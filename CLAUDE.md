# Prenotazione campi sportivi

Web app che sostituisce le prenotazioni a voce, al bar e per telefono per 5 campi sportivi.
I requisiti sono in `docs/requisiti-prenotazione-campi.md` e sono la fonte di verità.
Le decisioni prese durante il progetto sono in `docs/decisioni.md`.

## Stato attuale
- Il progetto contiene solo documentazione: non ci sono ancora codice, dipendenze né test automatici.
- Stack concordato: Django + PostgreSQL, template lato server (HTMX solo per il calendario), Docker per sviluppo e deploy.
- Le versioni delle librerie si fissano in `requirements.txt`, verificandole sulla documentazione ufficiale.

## Lingua
- Rispondere in italiano. I documenti in `docs/` sono in italiano.
- Codice in inglese: nomi di classi, funzioni, variabili e commenti.
- Ogni testo dell'interfaccia passa da gettext: italiano predefinito, inglese (RNF-02).

## Metodo: Ask → Plan → Execute → Verifica e commit
1. Ask: leggere i file e i requisiti coinvolti senza modificarli; separare i fatti dalle assunzioni da verificare.
2. Plan: proporre un piano breve con file, modifiche e prove; attendere l'approvazione prima di modificare.
3. Execute: applicare solo il piano concordato, con modifiche circoscritte.
4. Verifica: distinguere le prove eseguite davvero da quelle ancora da fare; non simulare risultati.
   Un risultato inatteso richiede una nuova diagnosi, non un commit.

- Una funzionalità alla volta. Non ampliare il perimetro oltre la richiesta né oltre il "Fuori perimetro" dei requisiti.
- Non inventare regole: se un requisito è ambiguo o marcato "(ipotesi)", fermarsi e chiedere.
  Le risposte vanno registrate in `docs/decisioni.md`.
- Non aggiungere dipendenze senza motivarle e concordarle.

## Regole critiche dei requisiti
- Nessuna sovrapposizione (RF-07, RF-44) e massimo 3 prenotazioni attive (RF-09), garantiti lato server e nel
  database anche con richieste simultanee (RNF-04): vincolo di esclusione PostgreSQL e transazioni, non solo controlli nelle view.
- Orari timezone-aware in Europe/Rome, con gestione corretta dell'ora legale (RNF-03).
- Le azioni dell'admin su prenotazioni, pagamenti, strike e utenti scrivono nel registro azioni (RNF-07).
- I test citano l'ID del requisito che verificano (es. `test_rf07_...`). Gli ID RF/RNF non si riassegnano.

## Ambiente (Windows)
- Comandi in PowerShell.
- Ambiente Python in `.venv`, creato con `py -m venv .venv`; usare direttamente `.\.venv\Scripts\python.exe`, senza attivarlo.
- Configurazione reale in `.env`, esclusa da Git; il modello condiviso è `.env.example`, senza segreti.

## Git
- Branch: `main` contiene solo versioni rilasciabili; `develop` integra il lavoro;
  ogni funzionalità ha un `feature/<nome>` creato da `develop`.
- Integrazione con Pull Request su GitHub (feature → develop, develop → main). Il merge lo fa l'utente.
- Prima di ogni commit: `git status`, `git diff`, `git add` dei soli file scelti, `git diff --staged`.
- Un commit per ogni modifica verificata e spiegabile; codice, test e documentazione dello stesso risultato possono stare insieme.
- Conventional Commits, `tipo(ambito): descrizione`, con descrizione in italiano. Tipi: feat, fix, docs, test, chore.
  Esempio: `feat(prenotazioni): impedisce la sovrapposizione sullo stesso campo`.
- Commit, push e Pull Request solo su richiesta esplicita.
- Niente reset distruttivi, force push o riscrittura della storia; in caso di blocco indicare l'ultimo commit funzionante.
- Niente segreti, `.env` o `.venv/` in Git.

## Comandi
Nessuno ancora. Avvio, test e migrazioni si aggiungono qui solo dopo averli eseguiti davvero.
