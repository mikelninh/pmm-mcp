# 💶 Money-Flow Watch — 2026-08-07

Wo fließt das Geld der Steuerzahler:innen hin — und wo läuft es schief?
Quellen: Bundesrechnungshof (BRH), tagesschau, Bundesregierung. Alle Beträge aus den verlinkten Originalquellen.

---

## 1. Verschuldungsdynamik außer Kontrolle — 2,7 Billionen € Schuldenstand bis 2029
- **Was:** Der Bundesbeauftragte für Wirtschaftlichkeit (BRH-Präsident Kay Scheller) fordert in seiner Stellungnahme zu den Eckwerten für den Bundeshaushalt 2027 (20.04.2026) eine strukturelle Konsolidierung. "Eine gefährliche Verschuldungsdynamik ist entstanden."
- **Wie viel:** Ausgaben 2019→2026 von 357 auf über **524 Mrd. €** (+47 %); inkl. Sondervermögen von 362 auf knapp **633 Mrd. €** (+75 %). Einnahmen stiegen nur um ~20 %. Geplante neue Kredite 2025–2029: **über 800 Mrd. €**. Schuldenstand 2029: **2,7 Billionen €**.
- **Ministerium:** BMF (Klingbeil) / Gesamthaushalt, Einzelplan 32 (Bundesschuld).
- **Warum es zählt:** Zinsausgaben verdoppeln sich von 2026 bis 2029 auf **66,5 Mrd. €** — 11,6 % des Haushalts, Geld das weder in Schulen, Bahn noch Pflege fließt.
- **Quelle:** https://www.bundesrechnungshof.de/SharedDocs/Pressemitteilungen/DE/2026/bwv_eckwerte.html

## 2. Investitionsquote sinkt — Sondervermögen finanziert Konsum statt Zukunft
- **Was:** Trotz Sondervermögen Infrastruktur und Klimaneutralität (SVIK) bleiben die Investitionen aus dem Kernhaushalt hinter der Zielquote von 10 % zurück.
- **Wie viel:** Investitionsquote sinkt in der Finanzplanung 2027–2029 im Soll auf **8,1 %**.
- **Ministerium:** BMF, ressortübergreifend.
- **Warum es zählt:** Das Sondervermögen sollte zusätzliche Investitionen bringen — faktisch ersetzt es reguläre Investitionen und schafft Platz für laufende Ausgaben.
- **Quelle:** https://www.bundesrechnungshof.de/SharedDocs/Pressemitteilungen/DE/2026/bwv_eckwerte.html

## 3. Moselschleusen: 855 Mio. € für einen Ausbau, den kaum jemand braucht
- **Wie viel:** **855 Mio. €** — laut BRH "weder notwendig noch wirtschaftlich", da der Güterverkehr auf der Mosel stark gesunken ist.
- **Ministerium:** Bundesverkehrsministerium / Wasserstraßen- und Schifffahrtsverwaltung.
- **Warum es zählt:** Günstigere Alternative (Ersatzteilvorhaltung) wurde nicht ernsthaft geprüft.
- **Quelle:** https://www.tagesschau.de/wirtschaft/bundesrechnungshof-vorwuerfe-100.html

## 4. 17.000 unbrauchbare Zoll-Smartphones für 35 Mio. €
- **Wie viel:** **35 Mio. €** für über 17.000 Spezial-Smartphones, die für die vorgesehene verschlüsselte Kommunikation unbrauchbar waren; Großteil bereits ersetzt.
- **Ministerium:** Bundesfinanzministerium (Zoll).
- **Warum es zählt:** Beschaffung ohne belastbare Anforderungsprüfung — klassischer vermeidbarer Totalverlust.
- **Quelle:** https://www.tagesschau.de/wirtschaft/bundesrechnungshof-vorwuerfe-100.html

## 5. Fregatten-Modernisierung: 20 Mio. € zu viel, ohne Ausschreibung
- **Wie viel:** mindestens **20 Mio. €** Mehrkosten bei der Unterbringung der Besatzung von vier Fregatten, weil auf eine öffentliche Ausschreibung verzichtet wurde.
- **Ministerium:** BMVg (Bundeswehr).
- **Warum es zählt:** Vergaberecht umgangen = kein Preiswettbewerb = Steuergeld verbrannt.
- **Quelle:** https://www.tagesschau.de/wirtschaft/bundesrechnungshof-vorwuerfe-100.html

## 6. "Netze des Bundes": 1,3 Mrd. € IT-Projekt im "Blindflug"
- **Wie viel:** **1,3 Mrd. €**, laut BRH ohne grundlegende Planung.
- **Ministerium:** BMI / Bundesverwaltung.
- **Warum es zählt:** Größtes Muster deutscher IT-Großprojekte: Budget zuerst, Plan später.
- **Quelle:** https://www.tagesschau.de/wirtschaft/bundesrechnungshof-vorwuerfe-100.html

## 7. Förderprogramme mit fraglicher Wirkung: 120 Mio. € + 300 Mio. €/Jahr
- **Wie viel:** **120 Mio. €** für die europäische Klimaschutzinitiative ("kaum Wirkung"); **300 Mio. € jährlich** Luftfahrtforschung mit unklaren Zielen.
- **Ministerium:** BMUKN / BMWE bzw. BMFTR.
- **Warum es zählt:** Dauersubventionen ohne Wirksamkeitsnachweis — genau die Posten, die der BRH für die 2027er Lücke von ~34 Mrd. € streichen würde.
- **Quelle:** https://www.tagesschau.de/wirtschaft/bundesrechnungshof-vorwuerfe-100.html

---

## Bezug zu pmm-mcp Tools
- `get_budget` — Einzelplan-Zeitreihen 2019–2026 abrufbar machen (Ausgabenanstieg +47 % Kernhaushalt / +75 % inkl. Sondervermögen ist direkt aus Einzelplandaten ableitbar).
- **Anomalie-Heuristik Vorschlag 1 — "Zinslast-Ratio":** Flag, wenn Einzelplan 32 (Bundesschuld) > 10 % der Gesamtausgaben. Trigger 2029: 11,6 %.
- **Anomalie-Heuristik Vorschlag 2 — "Investitionsquote < 10 %":** Flag pro Haushaltsjahr; 2027–2029 bereits im Soll bei 8,1 %.
- **Anomalie-Heuristik Vorschlag 3 — "Schattenhaushalt-Anteil":** Verhältnis Sondervermögen-Ausgaben zu Kernhaushalt (2026: ~109 Mrd. € außerhalb des Kernhaushalts) als Transparenz-Warnsignal.
- **Anomalie-Heuristik Vorschlag 4 — "Vergabe ohne Ausschreibung":** Titel-Ebene-Marker für BRH-monierte Direktvergaben (Fregatten-Fall).

## Weitere Quellen
- BRH Einzelplananalysen zum Bundeshaushalt 2026: https://www.bundesrechnungshof.de/SharedDocs/Kurzmeldungen/DE/2025/einzelplananalyse_2026/epa-2026-kurzmeldung.html
- tagesschau, BRH-Gutachten zum Etat 2026 ("Der Bund lebt über seine Verhältnisse"): https://www.tagesschau.de/inland/innenpolitik/bundesrechnungshof-gutachten-etat-2026-100.html
- Bundesregierung, Bundeshaushalt 2026: https://www.bundesregierung.de/breg-de/aktuelles/bundeshaushalt-2026-2374030
- Bundeshaushalt-Portal (Zinsausgaben 2026: 30,26 Mrd. €): https://www.bundeshaushalt.de/

*Automatisch erstellt vom Money-Flow-Watch-Agent. Keine Wertung, nur Zahlen und Quellen. Human review required — dieser PR wird nicht automatisch gemerged.*
