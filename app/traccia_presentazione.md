# Traccia per la presentazione — Gruppo 3, Giorni di consegna

Copione per raccontare la dashboard a voce. Una pagina = un blocco di racconto, nell'ordine
in cui stanno nella barra laterale. Budget totale **12 minuti**, più le domande.

Regola generale: **la dashboard mostra, tu spieghi**. Non leggere i numeri sullo schermo,
digli cosa significano. Ogni sezione qui sotto ha una frase in grassetto: se il pubblico
si ricorda solo quella, hai fatto il tuo lavoro.

---

## 1 · Il problema — 90 secondi

> **«La promessa di consegna non è sbagliata: è larga, ed è larga nel punto sbagliato.»**

Cosa dire:

- Un e-commerce brasiliano, 96.470 ordini consegnati fra settembre 2016 e agosto 2018.
  Al checkout il cliente vede una data. Noi dobbiamo dire se quella data è tarata bene.
- Consegna reale media **12,6 giorni**. Promessa media **23,7**. Quasi il doppio.
- L'errore della promessa è **12,7 giorni**, e nel **92% dei casi è in eccesso**: il pacco
  arriva prima. Non è un errore innocuo — è un e-commerce che sembra più lento di quanto sia.

Poi indica il grafico e fai la pausa più importante della presentazione:

- «Guardate le due curve. Quella blu sono le consegne vere: da **17 giorni a febbraio 2018**
  a **7,7 ad agosto**. La logistica è migliorata del 55% in sei mesi.»
- «Quella grigia è la promessa. È rimasta ferma sui 23-24 giorni per quasi tutto il periodo.»
- «Lo spazio grigio fra le due curve è margine sprecato. **Tutto il progetto è lì dentro.**»

Chiudi introducendo le due metriche: MAE (di quanti giorni sbagliamo) e quota di ritardi
(quante promesse rompiamo). Dì subito che la seconda ha un vincolo: **sotto il 5%**.

> ⚠️ Non passare oltre senza aver detto che le due metriche sono in tensione. Tutto il
> resto della presentazione è la gestione di quella tensione.

---

## 2 · Il risultato — 2 minuti

> **«Si accorcia la promessa di 3,2 giorni e i ritardi scendono. Non è un compromesso.»**

Parti dal risultato, non dal metodo. Il pubblico decide nei primi venti secondi se ascoltarti.

- Promessa media da **21,4 a 18,2 giorni** sul periodo di test. **−3,2 giorni in media**,
  −1,7 mediani, e il **58,7% degli ordini** riceve una data più vicina.
- Ritardi da **5,3% a 4,4%**. Sotto l'obiettivo del 5%, con margine.
- «Di solito qui si negozia: quanto sei disposto a rischiare per accorciare la promessa.
  In questo caso la domanda non si pone, perché **si guadagna su entrambi i fronti**.
  Il motivo è che la promessa di oggi non è solo larga: è larga nel punto sbagliato.»

Poi, e questa parte non la salti mai, il grafico delle tolleranze:

- «Adesso la parte scomoda. **Il nostro modello non è più preciso della promessa attuale.**
  Entro ±3 giorni ci finisce il 7,4% degli ordini contro il 10,8% di oggi: perdiamo.»
- «Vinciamo quando si allarga la finestra: entro ±10 giorni, 52,4% contro 42,2%.
  Quello che facciamo è **tagliare le sovrastime assurde**, non azzeccare il giorno.»
- «E il MAE di 10 giorni va letto così: il **95,6% delle previsioni sovrastima**, l'errore
  mediano è **+9,6 giorni**. Non vuol dire "sbagliamo di 10 giorni in un senso o nell'altro".
  Vuol dire che siamo **prudenti in modo controllato**.»

> 💡 Dire tu per primo il limite del modello vale più di qualsiasi numero. Se non lo dici,
> te lo chiedono; e a quel punto sembra una cosa che stavi nascondendo.

---

## 3 · Dove sbaglia la promessa di oggi — 2 minuti

> **«Gli ordini che la promessa sbaglia di più sono lontani e sono a Rio. E il modello li aggredisce.»**

Questa sezione risponde a «ma lo sapete davvero dove si sbaglia?».

- Abbiamo preso il **decile peggiore** della promessa attuale: 1.930 ordini con errore
  sopra 25,5 giorni. E li abbiamo confrontati con tutti gli altri.
- **Distanza 1,5× più alta.** Prevedibile.
- **Il carico del venditore NON c'entra.** Era la nostra prima ipotesi — «il venditore è
  sommerso» — e i dati la smentiscono: nel gruppo difficile il carico è perfino *più basso*
  (0,88×). Questa è la slide che dimostra che abbiamo guardato e non tirato a indovinare.
- **RJ è sovra-rappresentato 3,2 volte**: il 30% degli ordini difficili contro il 9% del
  resto. E San Paolo, il più vicino agli hub, è sotto-rappresentato (21% contro 49%).
  «La distanza in linea d'aria non lo spiega. Ci sono fattori di **rotta** che contano.»

Poi il grafico del confronto:

- «Sul decile peggiore l'errore passa da **31,4 a 13,2 giorni: meno 58%**. Sul resto del
  test il miglioramento è del 13%. Il modello non spalma: **corregge dove faceva più danno.**»
- Onestà: «il prezzo è che su quel gruppo i ritardi salgono dall'1,6% al 2,5%, mentre sul
  resto scendono. La correlazione fra i due errori è 0,38: gli ordini logisticamente
  complessi restano più difficili anche per noi. **In produzione vanno monitorati a parte.**»

---

## 4 · Dove sbaglia il nostro modello — 2 minuti e 30

> **«Il segmento a rischio è l'opposto di quello che sembra: sotto i 50 km.»**

È la sezione più controintuitiva. Vale la pena rallentare.

- Indica il grafico a doppio asse. «Le barre sono il MAE, la linea rossa i ritardi.
  **Vanno in direzioni opposte.** Il MAE cresce con la distanza, da 5,7 a 14,8 giorni.
  I ritardi fanno il contrario: **8,5% sotto i 50 km**, 2,7% nella fascia 200-500.»
- «Il motivo è aritmetico: sulle consegne vicine il margine di prudenza in giorni è piccolo
  in valore assoluto, basta poco per bucarlo. Sulle lunghe distanze mettiamo così tanto
  margine che il ritardo diventa raro — ma la promessa è larga.»
- «**Il 5% è sforato proprio dove il modello sembra più preciso.** Se avessimo guardato solo
  il MAE avremmo messo sotto controllo il segmento sbagliato.»
- Segmenti sopra soglia: **&lt;50 km (8,5%), peso &gt;10 kg (6,9%), BA (8,0%), SP (5,4%)**.
  E SP pesa il 46% del test, quindi sposta la media da solo.

Poi i casi strani, veloce, quattro carte:

- «Dati mancanti: 179 ordini, nessun degrado. Categorie rare: MAE 9,07, perfino meglio della
  media. **Queste due cose non vanno gestite**, XGBoost le assorbe.»
- «Quello che va gestito sono gli **ordini molto pesanti**: oltre il 99° percentile la quota
  di ritardi è del **9,3%**, più del doppio. È la fragilità vera.»

E la coda, che è il punto che fa la differenza fra "abbiamo guardato i numeri" e "abbiamo capito":

- «602 ordini con errore oltre 20 giorni, il 3,1% del test. Ma sono **due famiglie diverse**.»
- «Il **90% sono sovrastime**: consegne arrivate in 7 giorni mentre noi ne prevedevamo 28,
  su rotte di circa 935 km. **Questo è colpa nostra** e fra due minuti spiego perché.»
- «Il **10% sono anticipi su consegne davvero anomale**: 50 giorni reali mediani. Lì è andato
  storto qualcosa nella logistica, non nel modello. Pesano **l'1,6% del MAE totale**:
  non vale la pena progettare il modello attorno a loro.»

Se hai tempo, scorri la tabella degli errori peggiori e leggi una riga ad alta voce.
La colonna *ipotesi* è la nostra lettura, non un output del modello — dillo.

---

## 5 · Le feature — 2 minuti e 30

> **«La correlazione dice che tre feature su cinque sono inutili. A fasce si vede che non è vero.»**

- Sette feature, **tutte note al momento del checkout**. Vincolo non negoziabile: se usassimo
  informazioni sulla spedizione il modello sarebbe inutilizzabile nel momento in cui serve.
- La **distanza venditore-cliente** domina, Spearman 0,54. Tutto il resto sta sotto 0,09.
- «Se ci fossimo fermati qui avremmo buttato via metà delle variabili. Guardate i quattro
  grafici a fasce: **il segnale c'è, è solo a gradino.**»
- L'esempio migliore sono le **ore di approvazione del pagamento**: Spearman 0,09 perché
  quasi tutti pagano con carta e vengono approvati in meno di un'ora — la variabile è quasi
  costante. Ma a fasce: **12 giorni se approvato sotto l'ora, 15 se oltre tre giorni.**
  È l'effetto del *boleto*, il bollettino bancario brasiliano. «Un modello lineare non la
  vede, un modello ad alberi sì. **È il motivo per cui abbiamo scelto il gradient boosting.**»

Sulla domanda che vi faranno di sicuro — perché media *e* massimo della distanza:

- «Sono correlate a **0,999** e differiscono solo sull'**1,1% degli ordini**, quelli con più
  venditori. Sembra una ridondanza.»
- «Le teniamo entrambe per una ragione che viene dal target, non dalla statistica:
  *giorni di consegna* significa l'arrivo dell'**ultimo** articolo. Se un ordine ha un
  venditore a 50 km e uno a 1.500, è il secondo a decidere quando l'ordine è chiuso.
  Il **massimo è la variabile concettualmente corretta**, la media descrive lo sforzo
  logistico complessivo.»
- «Nei fatti la permutation importance dice che il modello usa davvero solo la media.
  **Il massimo è un'assicurazione, non un pilastro.** Costo zero, lo teniamo.»

Poi la feature importance, e qui c'è la nota metodologica che vale la pena raccontare:

- «Misurare l'importanza col MAE ci dava importanze **negative** su quasi tutte le feature.
  Ci siamo cascati. Il motivo: il nostro modello non stima il giorno tipico, stima un
  livello prudente, e il MAE premia la mediana. Abbiamo rifatto tutto con **la loss che il
  modello ottimizza davvero**.»

E infine il risultato più interessante del progetto:

> **«La geografia si è fatta stantia, e il modello non se n'è accorto.»**

- «Le tre viste non concordano, e **la discordanza è il risultato**. In addestramento il
  modello si appoggia soprattutto allo stato del cliente e alla distanza. Su aprile-maggio
  quelle feature sono le più utili: +20,2 e +17,8. Su giugno-agosto diventano **negative**:
  −4,6 e −6,5. **Mescolarle migliora il modello.**»
- «Non è un artefatto. Guardate l'errore per fascia di distanza: in calibrazione è uniforme
  (+5,1 / +7,9 / +6,6 giorni), sul test esplode sulle rotte lunghe (+5,6 / +10,6 / **+12,6**).
  Il modello ha imparato dal 2016-17 che *lontano = lento*. Nel frattempo le rotte lunghe
  sono diventate molto più veloci e lui continua a gonfiare la previsione.»
- «**È l'argomento tecnico per il riaddestramento periodico**, ed è il primo numero che
  metteremmo sotto monitoraggio in produzione.»

---

## 6 · Perché questo modello — 2 minuti

> **«Il MAE da solo sceglie il modello sbagliato.»**

- Indica il grafico. «Ogni punto è un modello. Sull'asse verticale la precisione, su quello
  orizzontale le promesse rotte. La fascia verde è la zona accettabile.»
- «La **Random Forest** ha un MAE di 6 giorni: quasi la metà del nostro. Ed è **inutilizzabile**,
  perché rompe la promessa nel 12,7% dei casi, più del doppio di oggi. Se avessimo ottimizzato
  la metrica standard avremmo presentato quel modello.»
- «Abbiamo provato a **calibrarla con un margine fisso**, +9 giorni stimati su aprile-maggio.
  Sul test i ritardi crollano all'1,8% ma il MAE sale a 14,1: **peggio della promessa attuale**.
  Il motivo è lo stesso di prima — il fenomeno non è stazionario, e un margine storico non
  regge un futuro più veloce.»
- «La **regressione logistica** per soglia centrava il vincolo (2,2%) ma con un MAE di 27,5
  giorni: un confine lineare per bucket non cattura le soglie che abbiamo visto prima.»
- «Quello che funziona è **mettere l'asimmetria dentro la loss**: penalizziamo gli anticipi
  cinque volte più delle sovrastime, direttamente nell'obiettivo di XGBoost.»

Poi la frontiera:

- «Ogni punto è lo stesso modello con una penalità diversa. Muoversi lungo la curva significa
  comprare meno promesse rotte pagando in precisione. **Non esiste un valore giusto
  statisticamente**: è la soglia del 5% a dire dove fermarsi. È una decisione di business,
  e l'abbiamo trattata come tale.»
- «Le due curve sono due architetture. Quella blu, scelta con `RandomizedSearchCV` e
  `TimeSeriesSplit`, **domina**: a parità di penalità ha MAE più basso *e* meno ritardi.
  Abbiamo tunato l'architettura con loss simmetrica e scelto la penalità **dopo**:
  mescolarle avrebbe prodotto architetture storte per compensare la penalità.»
- «Penalità 5 → MAE 10,00 e 4,4%. Penalità 4 guadagna 0,7 giorni di MAE ma sale al 5,1%:
  sfora. **Abbiamo preferito il margine.**»

---

## 7 · Simulatore — 1 minuto e 30

> **«Il modello non è una scatola nera: ditemi un ordine e vi dico la data.»**

Non spiegare gli slider, **usali**. Tre casi, in quest'ordine:

1. **Ordine tipico di San Paolo** (valori di default) → ~17-18 giorni.
   «Questa è la data che prometteremmo. Nessun avviso: siamo in zona affidabile.»
2. **Porta la distanza sotto i 50 km.** Compare l'avviso rosso.
   «Guardate: previsione più bassa, ma il modello ci avverte che **questo è il segmento con
   il rischio di ritardo più alto**. È esattamente il punto controintuitivo di prima, reso
   operativo.»
3. **Porta il peso oltre i 10 kg e lo stato su BA.** Due avvisi.
   «Qui stiamo cumulando due fragilità note. Un operatore che vede questa schermata sa
   che deve aggiungere margine a mano.»

Chiudi sulle curve di sensitività: «sono **monotone** — se allontano il cliente la previsione
sale, sempre. Il simulatore non zigzaga, ed è il motivo per cui ci si può fidare di quello
che mostra.»

---

## La risposta alla domanda della plenaria

> *Di quanti giorni si può accorciare la promessa senza superare il 5% di ritardi?*

**Di 3,2 giorni in media (1,7 mediani), e i ritardi scendono dal 5,3% al 4,4% invece di salire.**
La promessa media passa da 21,4 a 18,2 giorni e il 58,7% degli ordini riceve una data più vicina.

Se vuoi la versione lunga: «non è un compromesso perché la promessa di oggi non è solo larga,
è larga nel punto sbagliato — concede tantissimo margine dove non serve, come Rio e il Ceará
dove i ritardi sono già all'1-3%, e poco dove servirebbe.»

---

## Domande che vi faranno, e cosa rispondere

**«Un MAE di 10 giorni non è pessimo?»**
Sì, se lo leggi come precisione. Ma il 95,6% di quell'errore è sovrastima e l'errore mediano
è +9,6 giorni: il modello è *tarato* per essere prudente, non *impreciso*. La metrica che
conta per il business è la quota di ritardi, e lì siamo al 4,4% contro il 5,3% di oggi,
promettendo 3,2 giorni in meno. Se volessimo il MAE più basso ce l'abbiamo: 5,7 giorni con
penalità 1 — al prezzo del 12,9% di promesse rotte.

**«Perché non un ensemble / una rete neurale?»**
Con sette feature tabellari e 65.000 righe di addestramento il gradient boosting è già vicino
al limite del segnale disponibile. Il guadagno atteso da un ensemble è nell'ordine dei decimi
di giorno; il problema vero, come mostra la sezione 5, non è la capacità del modello ma il
fatto che la relazione fra geografia e tempi **cambia nel tempo**. Quello un ensemble non lo risolve.

**«Avete controllato il leakage?»**
Sì, in due modi. Tutte le feature sono note al checkout — nessuna informazione sulla
spedizione o sulla consegna. E il carico del venditore è calcolato su finestra strettamente
causale, solo ordini precedenti: verificato che il primo ordine di ogni venditore abbia
carico 0. Lo split è temporale, mai casuale.

**«Perché l'R² della Random Forest era 0,06?»**
Perché il target ha una varianza enorme dominata da eventi logistici che nessuna feature del
checkout può vedere. L'R² basso e il MAE migliore della baseline non sono in contraddizione:
la promessa ufficiale è tarata per stare cauta, non per essere accurata. Noi non stiamo
cercando di spiegare la varianza, stiamo cercando di **battere una promessa mal tarata**.

**«Ogni quanto va riaddestrato?»**
I dati dicono almeno ogni tre mesi. Le feature geografiche sono utili sul periodo adiacente
all'addestramento (+20 e +18) e diventano controproducenti tre mesi dopo (−4,6 e −6,5).
Il segnale da monitorare è l'errore medio sulle rotte oltre i 1.000 km: è passato da +6,6
a +12,6 giorni in tre mesi.

**«Il modello si può usare così com'è?»**
Sulla maggior parte degli ordini sì. Su tre segmenti no, e sono segnalati nel simulatore:
sotto i 50 km e sopra i 10 kg servono margini aggiuntivi, sopra i 1.000 km la previsione va
considerata prudente e da rivedere al prossimo riaddestramento.

---

## Se il tempo si accorcia

Taglia in quest'ordine:

1. La tabella degli errori peggiori nella sezione 4 (mostra solo le quattro carte).
2. La parte su Random Forest calibrata e regressione logistica nella sezione 6
   (tieni solo «il MAE da solo sceglie il modello sbagliato» e il grafico).
3. I quattro grafici a fasce nella sezione 5 (tieni solo le ore di approvazione).

**Non tagliare mai:** il grafico delle due curve nella sezione 1, la risposta alla domanda
della plenaria nella sezione 2, il grafico a direzioni opposte nella sezione 4, e la
geografia stantia nella sezione 5. Sono i quattro momenti in cui si capisce che avete
fatto un lavoro e non un esercizio.
