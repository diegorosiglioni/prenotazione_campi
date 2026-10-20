# Requisiti – Prenotazione campi sportivi

13/10/2026 · @diegogotty · revisione del 20/10/2026

## Panoramica

Un sito web sostituisce le prenotazioni a voce, al bar e per telefono. Impedisce che due persone prenotino lo stesso campo nello stesso orario.

**Problema attuale.** Le prenotazioni arrivano da più canali senza un registro unico, quindi capitano doppie prenotazioni. Non esiste uno storico di chi non si presenta o non paga.

**Obiettivo.** Un'unica agenda per 5 campi, consultabile dai tesserati. Il sistema applica le regole di prenotazione, cancellazione e sanzione.

**Volumi attesi.** Bassi per gran parte dell'anno. Picco a luglio e agosto, con circa 20 prenotazioni al giorno.

**Fuori perimetro**

- Pagamenti online: si paga in contanti in sede.
- App mobile nativa e layout responsive: la prima versione è per browser desktop (RNF-01). Il responsive è un possibile sviluppo futuro.
- Abbonamenti e sconti.
- Notifiche via email o SMS.
- Rinnovo automatico della tessera.
- Registrazione autonoma degli utenti.
- Scontrini e adempimenti fiscali: restano gestiti fuori dal sistema.
- Report e statistiche, oltre al riepilogo incassi giornaliero (RF-56).

**Convenzione sugli ID.** Ogni requisito ha un ID stabile: RF per i funzionali, RNF per i non funzionali. Gli ID non vengono riassegnati: RF-13, RF-37 e RNF-08 sono stati rimossi. Le decisioni prese e le ipotesi ancora aperte sono registrate in `decisioni.md`.

## Glossario

| Termine | Significato |
| --- | --- |
| Slot | Intervallo di gioco di durata fissa: 90 min per il calcio, 60 min per gli altri campi |
| Prenotazione attiva | Prenotazione nello stato Prenotata, Pagata o Offerta che non è ancora finita (RF-09) |
| Esito | Stato finale di una prenotazione: pagata, offerta, cancellata, cancellata dall'admin, annullata dal sistema, no-show o non pagata |
| Debito | Somma degli importi che il tesserato deve ancora pagare |
| Saldo | Pagamento in contanti di un importo a debito, registrato dall'admin |
| Movimento | Registrazione di denaro legata a una prenotazione: pagamento, addebito, saldo o rimborso |
| Strike | Sanzione registrata sull'account. Al secondo strike l'account viene bloccato |
| Tessera valida | Tessera con data di scadenza uguale o successiva a oggi |
| Tessera in scadenza | Tessera valida che scade entro 10 giorni (RF-36) |
| Account bloccato | Account che non può prenotare perché ha ricevuto il secondo strike. Il blocco lo toglie solo l'admin (RF-29), anche se nel frattempo gli strike scendono sotto 2 |
| Account disattivato | Account dismesso: non può accedere, ma il suo storico resta |

## Ruoli

Ci sono due ruoli: il tesserato, che prenota per sé entro le regole, e un unico admin (gestore o bar), senza i limiti del tesserato. Anche l'admin rispetta il divieto di sovrapposizione sullo stesso campo (RF-07) e per la stessa persona (RF-44), e gli orari di apertura (RF-47).

| Ruolo | Chi | Cosa può fare |
| --- | --- | --- |
| Tesserato | Persona con tessera cartacea valida | Vedere il calendario, prenotare, cancellare fino a 2 ore prima, vedere le proprie prenotazioni, il proprio debito e le notifiche, cambiare password e lingua |
| Admin | Un solo account, usato dal gestore o dal bar | Tutto ciò che fa il tesserato, senza i suoi limiti, più gestione utenti, tessere, pagamenti, no-show, strike, prezzi e blocchi dei campi |

**RF-01.** Esistono solo questi due ruoli. Non sono previsti più admin né permessi differenziati.

**RF-02.** Il tesserato non vede mai chi ha prenotato gli altri slot. L'admin vede nome e cognome su ogni prenotazione.

## Campi, orari e prezzi

Ci sono 5 campi prenotabili. Sono aperti tutti i giorni dalle 8:00 alle 23:00, festivi inclusi. Il prezzo è per tipo di campo: i due campi da tennis hanno sempre lo stesso prezzo.

| Campo | Quantità | Durata slot | Prezzo per slot |
| --- | --- | --- | --- |
| Calcio | 1 | 90 min | €60 |
| Tennis | 2 | 60 min | €18 |
| Pallacanestro | 1 | 60 min | €25 |
| Bocce | 1 | 60 min | €10 |

**RF-03.** Ogni campo ha una durata fissa dello slot. Una prenotazione corrisponde a un solo slot.

**RF-04.** Lo slot inizia a passi di 15 minuti (8:00, 8:15, 8:30…) e deve finire entro le 23:00. L'ultimo inizio è alle 21:30 per il calcio e alle 22:00 per gli altri campi.

**RF-05.** Solo l'admin può modificare i prezzi, per tipo di campo: il nuovo prezzo vale per tutti i campi di quel tipo. Il prezzo viene salvato sulla prenotazione al momento della creazione, quindi una modifica non cambia le prenotazioni già esistenti.

**RF-06.** I due campi da tennis sono distinti: si prenota il campo 1 o il campo 2.

## Regole di prenotazione

Un tesserato può avere al massimo 3 prenotazioni attive, tutte entro le prossime 2 settimane. Due prenotazioni non possono mai sovrapporsi sullo stesso campo.

**RF-07. Nessuna sovrapposizione.** Il sistema rifiuta una prenotazione che si sovrappone anche solo in parte a un'altra sullo stesso campo. La regola vale anche per l'admin e per due richieste nello stesso istante.

**RF-08. Finestra di prenotazione.** Si può prenotare uno slot che inizia dopo il momento attuale e cade entro 14 giorni di calendario da oggi, ultimo giorno incluso. Esempio: il 20 ottobre si può prenotare fino al 3 novembre compreso, a qualsiasi orario.

**RF-09. Massimo 3 prenotazioni attive.** Una prenotazione è attiva se è nello stato Prenotata, Pagata o Offerta e non è ancora finita. Contano anche quelle create o offerte dall'admin a nome del tesserato. L'admin può superare il limite (Funzioni admin, punto 2): in quel caso il tesserato non può prenotarne altre finché non torna sotto 3.

**RF-10. Condizioni per prenotare.** Il tesserato deve avere l'account attivo e non bloccato, la tessera valida e la data dello slot non successiva alla scadenza della tessera (RF-34).

**RF-11. Calendario.** Il tesserato vede, per campo e per giorno, gli intervalli liberi e quelli occupati, senza nomi.

**RF-12. Le mie prenotazioni.** Il tesserato vede le proprie prenotazioni future e passate, con stato e prezzo.

**RF-14. Campo bloccato.** L'admin può rendere un campo non prenotabile per un intervallo futuro, ad esempio per manutenzione o maltempo. Nel calendario l'intervallo appare non disponibile. Le prenotazioni non ancora iniziate che si sovrappongono anche solo in parte all'intervallo vengono annullate dal sistema, senza costi e con motivo "campo bloccato"; se erano pagate si rimborsano (RF-48). Il tesserato riceve una notifica. Una prenotazione già in corso non viene toccata: decide l'admin se cancellarla (RF-19). L'admin può rimuovere il blocco; le prenotazioni annullate non vengono ripristinate.

**RF-41. Prenotazione intestata.** Ogni prenotazione è intestata a un solo tesserato con account. Gli altri giocatori non vengono registrati. L'admin non può prenotare per persone senza account.

**RF-42. Riepilogo prima della conferma.** Prima di confermare, il sito mostra campo, data, orario di inizio e fine e prezzo.

**RF-43. Messaggi di errore.** Se una prenotazione viene rifiutata, il sito indica la regola violata: slot occupato o bloccato, limite di 3 raggiunto, oltre 14 giorni, fuori orario, tessera scaduta o in scadenza prima dello slot, account bloccato.

**RF-44. Una persona, un campo alla volta.** Un tesserato non può avere due prenotazioni sovrapposte, nemmeno su campi diversi. La regola vale anche per le prenotazioni create dall'admin.

**RF-45. Nessuna modifica.** Una prenotazione non si modifica: si cancella e se ne crea una nuova. Vale anche per l'admin.

**RF-46. Area personale.** Il tesserato vede il debito aperto con il dettaglio per prenotazione, il numero di strike attivi e la scadenza della tessera.

**RF-47. Orari anche per l'admin.** Anche le prenotazioni create dall'admin rispettano gli orari di apertura, le durate fisse e il passo di 15 minuti.

## Cancellazioni

Il tesserato può cancellare gratis fino a 2 ore prima dell'inizio. Dalle ultime 2 ore fino alla fine dello slot solo l'admin può cancellare la prenotazione.

**RF-15. Cancellazione gratuita.** Se mancano 2 ore o più all'inizio, il tesserato cancella senza costi. Se la prenotazione era già pagata, si rimborsa (RF-48).

**RF-16. Ultime 2 ore.** Nelle 2 ore prima dell'inizio il tesserato non può cancellare. Il sito disattiva il pulsante, spiega il motivo e invita a contattare l'admin.

**RF-17. Cancellazione dell'admin nelle ultime 2 ore o durante lo slot.** Da 2 ore prima dell'inizio fino alla fine dello slot, l'admin può cancellare e decide se addebitare l'importo e se assegnare uno strike. Se addebita l'importo, resta dovuto anche se lo slot viene riprenotato. Se la prenotazione era già pagata, il pagamento copre l'addebito: nessun nuovo debito e nessun rimborso.

**RF-18. Motivo.** Quando cancella l'admin, può indicare un motivo a testo libero e facoltativo, che non viene tradotto (RNF-02). Le cancellazioni del sistema hanno un motivo fisso, tradotto nella lingua dell'utente: "account bloccato", "account disattivato" o "campo bloccato". Il tesserato cancella senza motivo.

**RF-19. Cancellazione dell'admin.** L'admin può cancellare una prenotazione nello stato Prenotata, Pagata o Offerta in qualsiasi momento prima della fine dello slot. Una prenotazione già segnata come no-show o non pagata non si cancella: se l'esito è sbagliato, si corregge (RF-50). Lo slot torna subito prenotabile.

**RF-20. Storico.** Le prenotazioni cancellate o annullate restano nello storico con data, autore (tesserato, admin o sistema) e motivo, se presente.

**RF-48. Rimborso.** Se una prenotazione già pagata viene cancellata o annullata senza addebito, l'admin restituisce i contanti e registra il rimborso. Vale per la cancellazione del tesserato o dell'admin e per l'annullamento del sistema dovuto al blocco del campo o al blocco o alla disattivazione dell'account. Se l'admin cancella con addebito, il pagamento copre l'importo e non c'è rimborso (RF-17).

## Pagamenti, no-show e strike

Si paga in contanti in sede prima di entrare in campo, e l'admin registra il pagamento. Uno strike scatta sempre per no-show e mancato pagamento, e a scelta dell'admin quando cancella dalle ultime 2 ore in poi. Al primo strike arriva un avviso, al secondo l'account viene bloccato.

Esiti possibili di una prenotazione (da "Prenotata, da pagare in cassa"):

- paga in contanti → **Pagata** (incasso registrato)
- segnata come offerta → **Offerta** (nessun costo)
- cancellata 2 h o più prima → **Cancellata** (nessun costo, slot libero, rimborso se era pagata)
- blocco o disattivazione dell'account, blocco del campo → **Annullata dal sistema** (nessun costo, rimborso se era pagata)
- admin, dalle ultime 2 h alla fine dello slot → **Cancellata dall'admin** (debito e strike a scelta)
- non si presenta → **No-show** (debito + strike)
- gioca e non paga → **Non pagata** (debito + strike)

Dopo il primo strike arriva un avviso; il secondo blocca l'account (RF-27, RF-28). Saldare il debito rimuove lo strike collegato (RF-39), ma non sblocca l'account (RF-29).

**RF-21. Stati della prenotazione.** Lo stato appartiene alla prenotazione, non all'utente. Ogni prenotazione ha uno e un solo stato:

| Stato | Quando | Chi lo imposta | Importo a debito | Strike |
| --- | --- | --- | --- | --- |
| Prenotata | Dalla creazione fino all'esito | Tesserato o admin | No, si paga in sede | No |
| Pagata | Contanti ricevuti | Admin | No | No |
| Offerta | Prenotazione gratuita | Admin | No | No |
| Cancellata | Cancellazione 2 ore o più prima | Tesserato o admin | No | No |
| Cancellata dall'admin | Cancellazione dalle ultime 2 ore alla fine dello slot | Admin | A scelta dell'admin | A scelta dell'admin |
| Annullata dal sistema | Blocco o disattivazione dell'account, blocco del campo | Sistema | No | No |
| No-show | Il tesserato non si presenta | Admin | Sì | Sì |
| Non pagata | Gioca senza pagare | Admin | Sì | Sì |

**RF-22. Pagamento.** L'admin segna la prenotazione come pagata quando riceve i contanti.

**RF-23. Prenotazione offerta.** Solo l'admin può creare una prenotazione offerta, cioè gratuita, o segnarla come tale. Non ha limiti sul numero di prenotazioni offerte.

**RF-24. No-show.** L'admin segna come no-show chi non si presenta. L'importo va a debito e scatta uno strike.

**RF-25. Mancato pagamento.** Se il tesserato gioca senza pagare, l'admin lo segna come non pagata. L'importo va a debito e scatta uno strike.

**RF-26. Debito.** Il debito è la somma degli importi dovuti. È visibile al tesserato e all'admin, che registra il saldo quando riceve i contanti. Un debito aperto non impedisce di prenotare.

**RF-39. Il saldo rimuove lo strike.** Quando il tesserato salda l'importo collegato a uno strike, lo strike viene rimosso. Se l'account è bloccato, resta bloccato finché non lo sblocca l'admin (RF-29).

**RF-27. Primo strike.** Il tesserato riceve un avviso interno e può continuare a prenotare.

**RF-28. Secondo strike.** L'account viene bloccato: il tesserato non può più prenotare e le sue prenotazioni non ancora iniziate vengono annullate dal sistema, con motivo "account bloccato" e rimborso se erano pagate (RF-48). Il tesserato può comunque accedere per vedere debito, storico e notifiche. Uno strike successivo su un account già bloccato viene registrato, ma non genera una nuova notifica di blocco.

**RF-29. Sblocco.** Solo l'admin può sbloccare un account, manualmente. Lo sblocco serve anche se nel frattempo gli strike sono scesi sotto 2 per un saldo, una rimozione manuale o una correzione dell'esito (RF-39, RF-50, RF-52). Allo sblocco gli strike si azzerano; il debito resta. Gli strike non scadono con il tempo.

**RF-49. Quando si imposta l'esito.** Pagata e offerta si possono impostare in qualsiasi momento. No-show e non pagata solo dopo l'inizio dello slot.

**RF-50. Correzione dell'esito.** L'admin può correggere un esito sbagliato. Debito e strike collegati si aggiornano di conseguenza e la correzione resta nel registro delle azioni (RNF-07). Se la correzione rimuove lo strike che aveva causato il blocco, l'account resta bloccato finché non lo sblocca l'admin (RF-29).

**RF-51. Già pagata e no-show.** Se una prenotazione pagata o offerta non viene usata, resta nel suo stato: nessun debito e nessuno strike.

**RF-52. Rimozione manuale dello strike.** L'admin può rimuovere a mano qualsiasi strike, compreso quello assegnato senza addebito. Rimuovere uno strike non sblocca l'account (RF-29).

**RF-53. Debito alla visita successiva.** Quando l'admin apre una prenotazione di un tesserato con debito aperto, il debito appare in evidenza, così può incassarlo prima dell'ingresso.

**RF-54. Saldo per prenotazione.** Il saldo si registra per intero su una singola prenotazione a debito. Non sono previsti pagamenti parziali.

## Account e tessere

L'admin crea ogni account. Il tesserato accede con codice tessera e password, e cambia la password temporanea data dall'admin.

**RF-30. Creazione account.** Solo l'admin crea gli account. Dati obbligatori: nome, cognome, codice tessera, data di scadenza della tessera. Email e telefono sono facoltativi.

**RF-31. Login.** Si accede con codice tessera e password. Il codice tessera è univoco, è fatto di lettere e numeri (da 1 a 20 caratteri) e non distingue maiuscole e minuscole. L'admin accede dallo stesso modulo con un codice riservato, che nessuna tessera può avere. L'account admin non ha scadenza della tessera e non può essere intestatario di prenotazioni.

**RF-32. Password temporanea.** L'admin assegna una password temporanea. Il tesserato deve cambiarla al primo accesso e può cambiarla in seguito.

**RF-33. Password dimenticata.** Non c'è recupero automatico: l'admin assegna una nuova password temporanea. Se la dimentica l'admin, la reimposta chi gestisce il server.

**RF-34. Scadenza tessera.** Con la tessera scaduta il tesserato può accedere, ma non può prenotare. Con la tessera valida non si possono prenotare slot successivi alla data di scadenza.

**RF-35. Rinnovo.** Il rinnovo non è automatico: l'admin aggiorna a mano la data di scadenza dopo il rinnovo della tessera cartacea.

**RF-36. Avviso di scadenza.** Il tesserato riceve un avviso interno 10 giorni prima della scadenza e uno il giorno della scadenza.

**RF-40. Disattivazione.** Un account non si cancella mai: l'admin lo disattiva. Un account disattivato non può accedere né prenotare, e l'admin non può prenotare a suo nome. Le sue prenotazioni non ancora iniziate vengono annullate dal sistema, con motivo "account disattivato" e rimborso se erano pagate (RF-48). Storico e debito restano.

**RF-55. Dati modificabili dal tesserato.** Il tesserato può cambiare solo password e lingua. Tutti gli altri dati li modifica l'admin.

## Notifiche interne

Le notifiche esistono solo dentro il sito: un elenco con il contatore dei non letti, senza email né SMS. Ogni notifica viene mostrata nella lingua scelta dall'utente al momento della lettura (RNF-02).

| Evento | Destinatario | Momento |
| --- | --- | --- |
| Prenotazione creata dall'admin a nome del tesserato | Tesserato | Alla creazione |
| Prenotazione cancellata dall'admin o annullata dal sistema | Tesserato | Alla cancellazione |
| Primo strike | Tesserato | Quando viene registrato |
| Account bloccato | Tesserato | Al secondo strike |
| Account bloccato | Admin | Al secondo strike |
| Account sbloccato | Tesserato | Allo sblocco |
| Tessera in scadenza | Tesserato | 10 giorni prima |
| La tessera scade oggi | Tesserato | Il giorno della scadenza |
| Debito aperto | Tesserato | Quando l'importo va a debito |
| Strike rimosso dopo il saldo | Tesserato | Al saldo del debito |

Le prenotazioni concluse senza esito non generano notifiche: compaiono nella lista "da chiudere" del pannello admin (Funzioni admin, punto 4).

**RF-38.** Le notifiche si possono segnare come lette e restano consultabili nello storico.

## Funzioni admin

L'admin gestisce tutto da un pannello unico. Non ha i limiti del tesserato, ma rispetta il divieto di sovrapposizione (RF-07, RF-44) e gli orari di apertura (RF-47).

1. **Calendario completo** di tutti i campi, con nome e stato di ogni prenotazione.
2. **Prenotare a nome di un tesserato** senza i limiti di finestra, numero, blocco account e scadenza tessera. Restano RF-07, RF-44 e RF-47, e non può prenotare per un account disattivato (RF-40). Può anche creare prenotazioni offerte.
3. **Esito delle prenotazioni**: segnare pagata, offerta, no-show o non pagata, e correggere un esito sbagliato (RF-49, RF-50).
4. **Lista "da chiudere"**: le prenotazioni concluse che non hanno ancora un esito, con un contatore sempre visibile nel pannello.
5. **Cancellare** le prenotazioni Prenotata, Pagata o Offerta prima della fine dello slot, con motivo facoltativo (RF-19). Dalle ultime 2 ore in poi sceglie se addebitare l'importo e se assegnare uno strike (RF-17).
6. **Gestione utenti**: creare, modificare e disattivare account, assegnare password temporanee, aggiornare la scadenza della tessera.
7. **Strike e blocchi**: vedere gli strike di ogni utente, rimuoverne uno a mano e sbloccare un account.
8. **Debiti e rimborsi**: vedere i debiti aperti e i rimborsi da restituire, registrare i saldi, che rimuovono lo strike collegato, e i rimborsi.
9. **Prezzi**: modificare il prezzo di ogni tipo di campo (RF-05).
10. **Blocchi dei campi**: rendere un campo non prenotabile per un intervallo futuro e rimuovere un blocco (RF-14).
11. **Riepilogo incassi** del giorno (RF-56).

**RF-56. Riepilogo incassi.** L'admin vede, per ogni giorno, i pagamenti, i saldi e i rimborsi registrati, con il totale in contanti (pagamenti + saldi − rimborsi).

## Requisiti non funzionali

Si tratta di una web app per desktop, in italiano e inglese, con un carico basso. Il requisito tecnico critico è garantire che non ci siano doppie prenotazioni.

**RNF-01. Piattaforma.** Web app per browser desktop, nelle versioni recenti di Chrome, Firefox, Edge e Safari. Un layout responsive non fa parte della prima versione.

**RNF-02. Lingue.** Interfaccia in italiano e inglese, con italiano come lingua predefinita. Ogni utente sceglie la propria lingua. I motivi di cancellazione scritti dall'admin non vengono tradotti; quelli del sistema sì (RF-18).

**RNF-03. Fuso orario.** Tutti gli orari sono in Europe/Rome, con gestione corretta del passaggio all'ora legale. Il cambio dell'ora avviene di notte, fuori dall'orario di apertura (8:00–23:00), quindi nessuno slot lo attraversa. Le regole basate sul tempo (2 ore, 14 giorni, scadenze) si calcolano comunque con orari che tengono conto del fuso.

**RNF-04. Concorrenza.** Il divieto di sovrapposizione (RF-07, RF-44), il limite di 3 prenotazioni attive per le prenotazioni del tesserato (RF-09) e il rispetto dei blocchi dei campi (RF-14) vanno garantiti lato server e database, non solo dall'interfaccia. Così reggono anche due richieste nello stesso istante.

**RNF-05. Sicurezza.** Password salvate con hash, HTTPS obbligatorio. Dopo 5 tentativi di login falliti, il codice viene bloccato per 15 minuti. Password di almeno 8 caratteri. La sessione di ogni utente scade dopo 30 minuti di inattività, perché l'admin usa un PC condiviso al bar.

**RNF-06. Privacy (GDPR).** Va scritta un'informativa privacy. I dati raccolti sono il minimo necessario. Prima della messa in produzione va definito per quanto tempo si conserva lo storico (`decisioni.md`).

**RNF-07. Tracciabilità.** Le azioni dell'admin su prenotazioni, pagamenti, strike e utenti restano registrate con data e ora. L'account admin è condiviso tra gestore e bar (RF-01), quindi il registro non distingue quale persona ha agito: è un compromesso accettato.

**RNF-09. Carico.** Il picco atteso è di circa 20 prenotazioni al giorno. Non serve un'architettura distribuita.

**RNF-10. Formati.** Orari nel formato 24 ore, importi in euro. Date nel formato gg/mm/aaaa in entrambe le lingue.

## Modello dati concettuale

Bastano 9 entità. La prenotazione è il centro: lega utente e campo e porta con sé prezzo, stato ed esito.

| Entità | Dati principali | Note |
| --- | --- | --- |
| Utente | nome, cognome, codice tessera (codice riservato per l'admin), scadenza tessera (non per l'admin), hash password, password da cambiare (sì/no), ruolo, lingua, bloccato, attivo, email e telefono (facoltativi) | Ruolo: tesserato o admin |
| Tipo campo | nome, durata slot, prezzo attuale | 4 record: calcio, tennis, pallacanestro, bocce |
| Campo | nome, tipo, attivo | 5 record: calcio, tennis 1, tennis 2, pallacanestro, bocce |
| Prenotazione | utente, campo, inizio, fine, prezzo applicato, stato, addebito e strike (sì/no), creata da, esito impostato da e quando, cancellata da e quando, motivo di sistema (codice) o motivo dell'admin (testo) | Stati elencati in RF-21 |
| Strike | utente, prenotazione, tipo (no-show, non pagata o cancellazione dell'admin), data, rimosso il, causa della rimozione (saldo, manuale, correzione o sblocco) | Non si cancella: si segna come rimosso. Gli strike attivi sono quelli non rimossi |
| Movimento | utente, prenotazione, tipo (pagamento, addebito, saldo o rimborso), importo, data, registrato da | Debito = addebiti − saldi. Incassi del giorno = pagamenti + saldi − rimborsi |
| Blocco campo | campo, inizio, fine | Impedisce prenotazioni nell'intervallo |
| Notifica | utente, tipo, dati, data, letta | Solo interna. Si salvano tipo e dati, non il testo, che si genera nella lingua dell'utente |
| Registro azioni | autore, azione, oggetto, valori prima e dopo, data e ora | Tracciabilità delle azioni dell'admin (RNF-07) |

## Stack e prossimi passi

Lo stack è deciso (`decisioni.md`): Django e PostgreSQL, template lato server con HTMX solo per il calendario, Docker per sviluppo e deploy. Un vincolo di esclusione di PostgreSQL impedisce le sovrapposizioni direttamente nel database (RNF-04). Un comando giornaliero invia gli avvisi sulla tessera (RF-36); come pianificarlo nel deploy è ancora da decidere.

**Prossimi passi**

1. Scrivere le user story con i criteri di accettazione, partendo dagli RF.
2. Disegnare le schermate principali: calendario, le mie prenotazioni, pannello admin.
3. Definire lo schema del database e i vincoli.
4. Preparare la base del progetto: repository, Docker, CI e traduzioni.
5. Definire la conservazione dei dati insieme all'informativa privacy (RNF-06), prima della messa in produzione.
