# CIGO Mappe — motore PDF su GitHub

Questo repository contiene risorse **pubbliche** per il plugin **CIGO Mappe 2.0** (il plugin rimane privato).

## Mappe di prova

- [Arte gotica — standard](output/arte-gotica-standard.pdf)
- [Arte gotica — facilitata](output/arte-gotica-facilitata.pdf)

Entrambi i PDF sono A4 orizzontali e usano **Kalam Bold originale incorporato**. Le fotografie di Chartres e della Sainte-Chapelle sono conservate in `assets/` con gli autori e le licenze indicati nei rispettivi file di richiesta e nei PDF.

## Come funziona

1. ChatGPT, tramite il connettore GitHub, crea un JSON in `requests/`.
2. Il workflow `.github/workflows/generate.yml` avvia GitHub Actions.
3. `render_map.py` legge il JSON e produce il PDF in `output/`, usando `Kalam-Bold.ttf` già presente qui.
4. Un commit automatico pubblica i PDF. Non serve caricare il font nella conversazione.

Il generatore attuale supporta da 2 a 4 rami, fino a 3 voci per ramo, fotografie Commons accreditate e il diagramma dell'arco acuto per il Gotico. Ulteriori layout richiedono aggiornamenti al codice.

## Font e licenza

- [Kalam-Bold.ttf](Kalam-Bold.ttf) — fonte originale [Google Fonts](https://github.com/google/fonts/blob/main/ofl/kalam/Kalam-Bold.ttf)
- [OFL.txt](OFL.txt) — SIL Open Font License 1.1, copyright © 2014 Indian Type Foundry.

## Riservatezza

**Il repository è pubblico.** Non inserire materiali contenenti dati personali degli studenti, documenti PEI, fotografie degli alunni o informazioni scolastiche riservate. Per questi materiali, il motore remoto non è adatto.
