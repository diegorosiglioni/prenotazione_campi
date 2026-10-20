# Requisiti – Prenotazione campi sportivi

Oct 13, 2026 · @diegogotty

## Panoramica

Un sito web sostituisce le prenotazioni a voce, al bar e per telefono. Impedisce che due persone prenotino lo stesso campo nello stesso orario.

**Problema attuale.** Le prenotazioni arrivano da più canali senza un registro unico, quindi capitano doppie prenotazioni. Non esiste uno storico di chi non si presenta o non paga.

**Obiettivo.** Un'unica agenda per 5 campi, consultabile dai tesserati. Il sistema applica le regole di prenotazione, cancellazione e sanzione.

**Volumi attesi.** Bassi per gran parte dell'anno. Picco a luglio e agosto, con circa 20 prenotazioni al giorno.

**Fuori perimetro**

- Pagamenti online: si paga in contanti in sede.
- App mobile nativa. La versione responsive è un nice to have.
- Abbonamenti e sconti.
- Notifiche via email o SMS.
- Rinnovo automatico della tessera.
- Registrazione autonoma degli utenti.
- Scontrini e adempimenti fiscali: restano gestiti fuori dal sistema.
- Report e statistiche, oltre al riepilogo incassi giornaliero (RF-56).

**Convenzione sugli ID.** Ogni requisito ha un ID stabile: RF per i funzionali, RNF per i non funzionali. Gli ID non vengono riassegnati: RF-13, RF-37 e RNF-08 sono stati rimossi. Le regole marcate "(ipotesi)" attendono conferma nell'ultima sezione dei requisiti.

## Glossario

| Termine | Significato |
| --- | --- |
| Slot | Intervallo di gioco di durata fissa: 90 min per il calcio, 60 min per gli altri campi |
| Prenotazione attiva | Prenotazione non cancellata e non ancora finita |
| Esito | Stato finale di una prenotazione: pagata, offerta, cancellata, annullata, no-show o non pagata |
| Debito | Somma degli importi che il tesserato deve ancora pagare |
| Saldo | Pagamento in contanti di un importo a debito, registrato dall'admin |
| Strike | Sanzione registrata sull'account. Al secondo l'account viene bloccato |
| Tessera valida | Tessera con data di scadenza uguale o successiva a oggi |
| Account bloccato | Account con 2 strike: non può prenotare finché l'admin non lo sblocca |
| Account disattivato | Account dismesso: non può accedere, ma il suo storico resta |

## Ruoli

Ci sono due ruoli: il tesserato, che prenota per sé entro le regole, e un unico admin (gestore o bar), senza i limiti del tesserato. Anche l'admin rispetta il divieto di sovrapposizione (RF-07) e gli orari di apertura (RF-47).

| Ruolo | Chi | Cosa può fare |
| --- | --- | --- |
| Tesserato | Persona con tessera cartacea valida | Vedere il calendario, prenotare, cancellare fino a 2 ore prima, vedere le proprie prenotazioni, il proprio debito e le notifiche, cambiare password e lingua |
| Admin | Un solo account, usato dal gestore o dal bar | Tutto ciò che fa il tesserato, senza i suoi limiti, più gestione utenti, tessere, pagamenti, no-show, strike, prezzi e blocchi dei campi |

**RF-01.** Esistono solo questi due ruoli. Non sono previsti più admin né permessi differenziati.

**RF-02.** Il tesserato non vede mai chi ha prenotato gli altri slot. L'admin vede nome e cognome su ogni prenotazione.

## Campi, orari e prezzi

Ci sono 5 campi prenotabili. Sono aperti tutti i giorni dalle 8:00 alle 23:00, festivi inclusi.

| Campo | Quantità | Durata slot | Prezzo per slot |
| --- | --- | --- | --- |
| Calcio | 1 | 90 min | €60 |
| Tennis | 2 | 60 min | €18 |
| Pallacanestro | 1 | 60 min | €25 |
| Bocce | 1 | 60 min | €10 |

**RF-03.** Ogni campo ha una durata fissa dello slot. Una prenotazione corrisponde a un solo slot.

**RF-04.** Lo slot inizia a passi di 15 minuti (8:00, 8:15, 8:30…) e deve finire entro le 23:00. L'ultimo inizio è alle 21:30 per il calcio e alle 22:00 per gli altri campi.

**RF-05.** Solo l'admin può modificare i prezzi. Il prezzo viene salvato sulla prenotazione al momento della creazione.

**RF-06.** I due campi da tennis sono distinti: si prenota il campo 1 o il campo 2.

## Regole di prenotazione

Un tesserato può avere al massimo 3 prenotazioni attive, tutte entro le prossime 2 settimane. Due prenotazioni non possono mai sovrapporsi sullo stesso campo.

**RF-07. Nessuna sovrapposizione.** Il sistema rifiuta una prenotazione che si sovrappone anche solo in parte a un'altra sullo stesso campo. La regola vale anche per l'admin e per due richieste nello stesso istante.

**RF-08. Finestra di prenotazione.** Si può prenotare da adesso fino a 14 giorni in avanti.

**RF-09. Massimo 3 prenotazioni attive.** Una prenotazione è attiva se non è cancellata e non è ancora finita, pagata o no. Contano anche quelle create o offerte dall'admin a nome del tesserato.

**RF-10. Condizioni per prenotare.** Il tesserato deve avere l'account attivo e non bloccato, la tessera valida e la data dello slot non successiva alla scadenza della tessera (RF-34).

**RF-11. Calendario.** Il tesserato vede, per campo e per giorno, gli intervalli liberi e quelli occupati, senza nomi.

**RF-12. Le mie prenotazioni.** Il tesserato vede le proprie prenotazioni future e passate, con stato e prezzo.

**RF-14. Campo bloccato.** L'admin può rendere un campo non prenotabile per un intervallo, ad esempio per manutenzione o maltempo. Nel calendario l'intervallo appare non disponibile. Le prenotazioni già presenti vengono annullate senza costi e il tesserato riceve una notifica. L'admin può rimuovere il blocco.

**RF-41. Prenotazione intestata.** Ogni prenotazione è intestata a un solo tesserato con account. Gli altri giocatori non vengono registrati. L'admin non può prenotare per persone senza account.

**RF-42. Riepilogo prima della conferma.** Prima di confermare, il sito mostra campo, data, orario di inizio e fine e prezzo.

**RF-43. Messaggi di errore.** Se una prenotazione viene rifiutata, il sito indica la regola violata: slot occupato o bloccato, limite di 3 raggiunto, oltre 14 giorni, fuori orario, tessera scaduta o in scadenza prima dello slot, account bloccato.

**RF-44. Una persona, un campo alla volta.** Un tesserato non può avere due prenotazioni sovrapposte, nemmeno su campi diversi.

**RF-45. Nessuna modifica.** Una prenotazione non si modifica: si cancella e se ne crea una nuova. Vale anche per l'admin.

**RF-46. Area personale.** Il tesserato vede il debito aperto con il dettaglio per prenotazione, il numero di strike attivi e la scadenza della tessera.

**RF-47. Orari anche per l'admin.** Anche le prenotazioni create dall'admin rispettano gli orari di apertura, le durate fisse e il passo di 15 minuti.

## Cancellazioni

Il tesserato può cancellare gratis fino a 2 ore prima dell'inizio. Nelle ultime 2 ore solo l'admin può cancellare la prenotazione.

**RF-15. Cancellazione gratuita.** Se mancano 2 ore o più all'inizio, il tesserato cancella senza costi.

**RF-16. Ultime 2 ore.** Nelle 2 ore prima dell'inizio il tesserato non può cancellare. Il sito disattiva il pulsante, spiega il motivo e invita a contattare l'admin.

**RF-17. Cancellazione dell'admin nelle ultime 2 ore.** L'admin può cancellare e decide se addebitare l'importo e se assegnare uno strike. Se addebita l'importo, resta dovuto anche se lo slot viene riprenotato.

**RF-18. Motivo.** Solo quando cancella l'admin si può indicare un motivo, a testo libero e facoltativo. Il tesserato cancella senza motivo.

**RF-19. Cancellazione dell'admin.** L'admin può cancellare qualsiasi prenotazione in qualsiasi momento prima della fine dello slot. Lo slot torna subito prenotabile.

**RF-20. Storico.** Le prenotazioni cancellate restano nello storico con data, autore e, se indicato, motivo della cancellazione.

**RF-48. Rimborso.** Se una prenotazione già pagata viene cancellata senza addebito, l'admin restituisce i contanti e il sistema registra il rimborso.

## Pagamenti, no-show e strike

Si paga in contanti in sede prima di entrare in campo, e l'admin registra il pagamento. Uno strike scatta sempre per no-show e mancato pagamento, e a scelta dell'admin quando cancella nelle ultime 2 ore. Al primo strike arriva un avviso, al secondo l'account viene bloccato.

Esiti possibili di una prenotazione (da "Prenotata, da pagare in cassa"):

- paga in contanti → **Pagata** (incasso registrato)
- segnata come offerta → **Offerta** (nessun costo)
- cancellata 2 h o più prima → **Cancellata** (nessun costo, slot libero)
- blocco account o campo → **Annullata dal sistema** (nessun costo)
- admin, ultime 2 h → **Cancellata dall'admin** (debito e strike a scelta)
- non si presenta → **No-show** (debito + strike)
- gioca e non paga → **Non pagata** (debito + strike)

Dopo il primo strike arriva un avviso; il secondo blocca l'account (RF-27, RF-28). Saldare il debito elimina lo strike collegato (RF-39).

**RF-21. Stati della prenotazione.** Lo stato appartiene alla prenotazione, non all'utente. Ogni prenotazione ha uno e un solo stato:

| Stato | Quando | Chi lo imposta | Importo a debito | Strike |
| --- | --- | --- | --- | --- |
| Prenotata | Dalla creazione fino all'esito | Tesserato o admin | No, si paga in sede | No |
| Pagata | Contanti ricevuti | Admin | No | No |
| Offerta | Prenotazione gratuita | Admin | No | No |
| Cancellata | Cancellazione 2 ore o più prima | Tesserato o admin | No | No |
| Cancellata dall'admin | Cancellazione nelle ultime 2 ore | Admin | A scelta dell'admin | A scelta dell'admin |
| Annullata dal sistema | Account bloccato o campo bloccato | Sistema | No | No |
| No-show | Il tesserato non si presenta | Admin | Sì | Sì |
| Non pagata | Gioca senza pagare | Admin | Sì | Sì |

**RF-22. Pagamento.** L'admin segna la prenotazione come pagata quando riceve i contanti.

**RF-23. Prenotazione offerta.** Solo l'admin può creare una prenotazione offerta, cioè gratuita, o segnarla come tale. Non ha limiti sul numero di prenotazioni offerte.

**RF-24. No-show.** L'admin segna come no-show chi non si presenta. L'importo va a debito e scatta uno strike.

**RF-25. Mancato pagamento.** Se il tesserato gioca senza pagare, l'admin lo segna come non pagata. L'importo va a debito e scatta uno strike.

**RF-26. Debito.** Il debito è la somma degli importi dovuti. È visibile al tesserato e all'admin, che registra il saldo quando riceve i contanti. Un debito aperto non impedisce di prenotare.

**RF-39. Il saldo elimina lo strike.** Quando il tesserato salda l'importo collegato a uno strike, lo strike viene eliminato.

**RF-27. Primo strike.** Il tesserato riceve un avviso interno e può continuare a prenotare.

**RF-28. Secondo strike.** L'account viene bloccato, il tesserato non può più prenotare e le sue prenotazioni future vengono cancellate in automatico, con motivo "account bloccato". Il tesserato può comunque accedere per vedere debito, storico e notifiche.

**RF-29. Sblocco.** Solo l'admin può sbloccare un account, manualmente. Saldare il debito non sblocca l'account in automatico. Allo sblocco gli strike si azzerano. Gli strike non scadono con il tempo.

**RF-49. Quando si imposta l'esito.** Pagata e offerta si possono impostare in qualsiasi momento. No-show e non pagata solo dopo l'inizio dello slot.

**RF-50. Correzione dell'esito.** L'admin può correggere un esito sbagliato. Debito e strike collegati si aggiornano di conseguenza e la correzione resta nel registro delle azioni (RNF-07).

**RF-51. Già pagata e no-show.** Se una prenotazione pagata o offerta non viene usata, resta nel suo stato: nessun debito e nessuno strike.

**RF-52. Rimozione manuale dello strike.** L'admin può eliminare a mano qualsiasi strike, compreso quello assegnato senza addebito.

**RF-53. Debito alla visita successiva.** Quando l'admin apre una prenotazione di un tesserato con debito aperto, il debito appare in evidenza, così può incassarlo prima dell'ingresso.

**RF-54. Saldo per prenotazione.** Il saldo si registra per intero su una singola prenotazione a debito. Non sono previsti pagamenti parziali (ipotesi).

## Account e tessere

L'admin crea ogni account. Il tesserato accede con codice tessera e password, e cambia la password temporanea data dall'admin.

**RF-30. Creazione account.** Solo l'admin crea gli account. Dati obbligatori: nome, cognome, codice tessera, data di scadenza della tessera. Email e telefono sono facoltativi.

**RF-31. Login.** Si accede con codice tessera e password. Il codice tessera è univoco.

**RF-32. Password temporanea.** L'admin assegna una password temporanea. Il tesserato deve cambiarla al primo accesso e può cambiarla in seguito.

**RF-33. Password dimenticata.** Non c'è recupero automatico: l'admin assegna una nuova password temporanea. Se la dimentica l'admin, la reimposta chi gestisce il server.

**RF-34. Scadenza tessera.** Con la tessera scaduta il tesserato può accedere, ma non può prenotare. Con la tessera valida non si possono prenotare slot successivi alla data di scadenza.

**RF-35. Rinnovo.** Il rinnovo non è automatico: l'admin aggiorna a mano la data di scadenza dopo il rinnovo della tessera cartacea.

**RF-36. Avviso di scadenza.** Il tesserato riceve un avviso interno 10 giorni prima della scadenza.

**RF-40. Disattivazione.** Un account non si cancella mai: l'admin lo disattiva. Un account disattivato non può accedere né prenotare, ma il suo storico resta.

**RF-55. Dati modificabili dal tesserato.** Il tesserato può cambiare solo password e lingua. Tutti gli altri dati li modifica l'admin.

## Notifiche interne

Le notifiche esistono solo dentro il sito: un elenco con il contatore dei non letti, senza email né SMS.

| Evento | Destinatario | Momento |
| --- | --- | --- |
| Prenotazione creata dall'admin a proprio nome | Tesserato | Alla creazione |
| Prenotazione cancellata dall'admin o dal sistema | Tesserato | Alla cancellazione |
| Primo strike | Tesserato | Quando viene registrato |
| Account bloccato | Tesserato | Al secondo strike |
| Account bloccato | Admin | Al secondo strike |
| Account sbloccato | Tesserato | Allo sblocco |
| Tessera in scadenza | Tesserato | 10 giorni prima |
| Tessera scaduta | Tesserato | Il giorno della scadenza |
| Debito aperto | Tesserato | Quando l'importo va a debito |
| Strike eliminato dopo il saldo | Tesserato | Al saldo del debito |
| Prenotazioni concluse senza esito | Admin | Dopo la fine dello slot |

**RF-38.** Le notifiche si possono segnare come lette e restano consultabili nello storico.

## Funzioni admin

L'admin gestisce tutto da un pannello unico. Non ha i limiti del tesserato, ma rispetta il divieto di sovrapposizione (RF-07) e gli orari di apertura (RF-47).

1. **Calendario completo** di tutti i campi, con nome e stato di ogni prenotazione.
2. **Prenotare a nome di un tesserato** senza i limiti di finestra, numero, blocco account e scadenza tessera. Può anche creare prenotazioni offerte.
3. **Esito delle prenotazioni**: segnare pagata, offerta, no-show o non pagata, e correggere un esito sbagliato (RF-49, RF-50).
4. **Lista "da chiudere"**: le prenotazioni concluse che non hanno ancora un esito.
5. **Cancellare** qualsiasi prenotazione, con motivo facoltativo. Nelle ultime 2 ore sceglie se addebitare l'importo e se assegnare uno strike.
6. **Gestione utenti**: creare, modificare e disattivare account, assegnare password temporanee, aggiornare la scadenza della tessera.
7. **Strike e blocchi**: vedere gli strike di ogni utente, eliminarne uno a mano e sbloccare un account.
8. **Debiti e rimborsi**: vedere i debiti aperti, registrare i saldi, che eliminano lo strike collegato, e i rimborsi.
9. **Prezzi**: modificare il prezzo di ogni tipo di campo.
10. **Blocchi dei campi**: rendere un campo non prenotabile per un intervallo e rimuovere un blocco.
11. **Riepilogo incassi** del giorno (RF-56).

**RF-56. Riepilogo incassi.** L'admin vede, per ogni giorno, le prenotazioni pagate, i saldi e i rimborsi registrati, con il totale in contanti (ipotesi).

## Requisiti non funzionali

Si tratta di una web app per desktop, in italiano e inglese, con un carico basso. Il requisito tecnico critico è garantire che non ci siano doppie prenotazioni.

**RNF-01. Piattaforma.** Web app per browser desktop, nelle versioni recenti di Chrome, Firefox, Edge e Safari. Un layout responsive è un nice to have, non un requisito.

**RNF-02. Lingue.** Interfaccia in italiano e inglese, con italiano come lingua predefinita. Ogni utente sceglie la propria lingua. I motivi di cancellazione scritti dall'admin non vengono tradotti.

**RNF-03. Fuso orario.** Tutti gli orari sono in Europe/Rome, con gestione corretta del passaggio all'ora legale.

**RNF-04. Concorrenza.** Il divieto di sovrapposizione (RF-07, RF-44) e il limite di 3 prenotazioni attive (RF-09) vanno garantiti lato server e database, non solo dall'interfaccia. Così reggono anche due richieste nello stesso istante.

**RNF-05. Sicurezza.** Password salvate con hash, HTTPS obbligatorio, limite ai tentativi di login falliti. Password di almeno 8 caratteri. La sessione scade dopo 30 minuti di inattività, perché l'admin usa un PC condiviso al bar.

**RNF-06. Privacy (GDPR).** Va scritta un'informativa privacy. I dati raccolti sono il minimo necessario. Va definito per quanto tempo si conserva lo storico.

**RNF-07. Tracciabilità.** Le azioni dell'admin su prenotazioni, pagamenti, strike e utenti restano registrate con data e ora.

**RNF-09. Carico.** Il picco atteso è di circa 20 prenotazioni al giorno. Non serve un'architettura distribuita.

**RNF-10. Formati.** Orari nel formato 24 ore, importi in euro. Le date seguono la lingua scelta: gg/mm/aaaa in italiano.

## Modello dati concettuale

Bastano 8 entità. La prenotazione è il centro: lega utente e campo e porta con sé prezzo, stato ed esito.

| Entità | Dati principali | Note |
| --- | --- | --- |
| Utente | nome, cognome, codice tessera, scadenza tessera, hash password, password da cambiare (sì/no), ruolo, lingua, bloccato, attivo, email e telefono (facoltativi) | Ruolo: tesserato o admin |
| Campo | nome, tipo, durata slot, prezzo attuale, attivo | 5 record: calcio, tennis 1, tennis 2, pallacanestro, bocce |
| Prenotazione | utente, campo, inizio, fine, prezzo applicato, stato, addebito e strike (sì/no), creata da, esito impostato da e quando, data della cancellazione, motivo (solo se cancella l'admin) | Stati elencati in RF-21 |
| Strike | utente, prenotazione, tipo (no-show, non pagata o cancellazione dell'admin), data | Si elimina al saldo e si azzera allo sblocco; il numero di strike decide avviso o blocco |
| Movimento di debito | utente, prenotazione, importo, tipo (addebito, saldo o rimborso), data | Il debito è la somma degli addebiti meno i saldi |
| Blocco campo | campo, inizio, fine | Impedisce prenotazioni nell'intervallo |
| Notifica | utente, tipo, testo, data, letta | Solo interna |
| Registro azioni | autore, azione, oggetto, valori prima e dopo, data e ora | Tracciabilità delle azioni dell'admin (RNF-07) |

## Ipotesi da confermare

Questi punti non sono ancora stati decisi. Per ognuno indico l'ipotesi che ho usato nel documento: spunta quelle che confermi.

- [ ] **Saldo parziale (RF-54).** Ipotesi: il saldo si fa sempre per intero, una prenotazione alla volta.
- [ ] **Riepilogo incassi (RF-56).** Ipotesi: serve un riepilogo giornaliero dei contanti.
- [ ] **Formato del codice tessera.** Come è fatto il codice stampato sulla tessera (solo numeri, lettere e numeri, lunghezza)?
- [ ] **Conservazione dei dati.** Per quanto tempo si tiene lo storico di prenotazioni e strike? Da decidere insieme all'informativa privacy.

## Proposta tecnica e prossimi passi

Propongo Django con PostgreSQL, renderizzato lato server. È una proposta, non una decisione. Il livello di fiducia che sia adatta è alto, visto il carico e i requisiti.

| Componente | Proposta | Perché |
| --- | --- | --- |
| Backend | Django | Login, pannello admin e traduzioni IT/EN sono già inclusi |
| Database | PostgreSQL | Un vincolo di esclusione sugli intervalli impedisce le sovrapposizioni direttamente nel database (RNF-04) |
| Frontend | Template Django, con HTMX opzionale per il calendario | Niente SPA: meno codice per un'app desktop con poche schermate |
| Job pianificati | Comando eseguito ogni giorno | Avvisi di tessera in scadenza e scaduta, lista delle prenotazioni da chiudere |
| Deploy | Docker su un piccolo VPS | Basta un'istanza singola |

Le versioni delle librerie si fissano all'avvio del progetto, verificandole sulla documentazione ufficiale.

**Prossimi passi**

1. Confermare o correggere le ipotesi della sezione precedente.
2. Scrivere le user story con i criteri di accettazione, partendo dagli RF.
3. Disegnare le schermate principali: calendario, le mie prenotazioni, pannello admin.
4. Definire lo schema del database e i vincoli.
5. Preparare la base del progetto: repository, Docker, CI e traduzioni.
