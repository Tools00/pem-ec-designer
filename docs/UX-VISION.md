# UX-VISION — pem-ec-designer

**Status:** v0 — Diskussionsgrundlage, kein Vertrag.
**Datum:** 2026-05-12
**Geltungsbereich:** Bindendes UI/UX-Konzept für v1.0. Wird durch ADRs konkretisiert (UI-Polish, Stack-Composer, LCOH-Panel).
**Anti-Geltungsbereich:** Keine Feature-Wunschliste. Kein Backlog. Kein Marketing-Text.

---

## 1 · Was das Tool ist — und was nicht

| | |
|---|---|
| **Ist** | Desktop-Designer für **eine PEM-Elektrolyse-Zelle**. Komponenten-Auswahl + Operating-Point + sofortige Polarisationskurve + Loss-Decomposition + grobe LCOH-Schätzung. Geometrie-Export als STEP/STL. Quellen-Pflicht für jeden Wert. |
| **Ist nicht** | Kein CFD-Solver. Kein 1-D-Transport-Modell. Kein Multi-Cell-Stack-Simulator (Thermalkopplung, Strom-Verteilung über Stack-Länge). Kein Optimierer. Kein Multi-User. Kein Cloud-Dienst. Kein Plug-in-System. |

Das Tool macht **eine Sache richtig**: aus einer Komponenten-Auswahl eine zitierfähige V–I-Kurve mit Verlustaufschlüsselung erzeugen. Punkt.

---

## 2 · Personas

Drei reale Nutzer, alle mit demselben Kern-Workflow.

| Persona | Wofür nutzt er das Tool? | Worauf reagiert er empfindlich? |
|---|---|---|
| **R&D-Ingenieur** (Hauptpersona) — H₂-Tech-KMU, Forschungsinstitut | „Wenn ich von Nafion 117 auf 212 wechsle, was kostet mich das bei 1 A/cm² Design-Point?" — Komponenten vergleichen, Verlustbudget verstehen, Sensitivität gegen T und p prüfen | Strict-Quellen (jeder Wert braucht eine zitierte Quelle), Reproduzierbarkeit, Geschwindigkeit (live, nicht „Calculate"-Button) |
| **Masterstudent / Lehre** — Thesis, Praktikum | „Wo gehen meine 1.7 V hin?" — Loss-Waterfall verstehen, BibTeX-Liste für die Quellenangabe der Arbeit | Klarheit der Plots, keine versteckten Annahmen, dokumentierte Modell-Limits |
| **Tech-Sales / Consultant** | „Schnell ein Was-wäre-wenn-Diagramm und eine LCOH-Zahl fürs Kundengespräch" — PDF-Report mit ein paar Plots und einer Kosten-Zahl | Visueller Polish, Export-Qualität, sinnvolle Defaults beim ersten Öffnen |

**Was alle drei NICHT tun:** Hardware bauen, CFD-Sweeps fahren, mit Versuchsplänen umgehen, mit dem Tool produktive Simulationen für eine kommerzielle Pilot-Anlage durchführen. Wer das will, nimmt COMSOL.

---

## 3 · Core User Journeys

Die fünf Aktionen, die >90 % aller Sessions ausmachen. Wenn eine davon mehr als zwei Klicks braucht, ist die UI falsch.

### J1 · „V–I-Kurve für meinen Cell ansehen" (≥ 80 % der Sessions)

1. Tool öffnet sich → Default-Stack ist schon da → V–I-Kurve ist sofort sichtbar.
2. User schaut auf V(design_j) und auf die Waterfall-Aufschlüsselung.
3. Schließt das Tool.

**Anforderung:** Erster Plot ist <2 s nach App-Launch zu sehen. Kein Wizard, kein „erstelle ein Projekt"-Modal.

### J2 · „Komponente tauschen und Wirkung sehen" (≥ 60 % der Sessions)

1. Dropdown öffnen, andere Membrane wählen.
2. V–I-Kurve passt sich sofort an. Waterfall zeigt die neue ASR-Summe.
3. Validation-Badge bleibt grün/wechselt zu gelb wenn das Modell aus dem Literatur-Band fällt.

**Anforderung:** Dropdown-Change → Replot <100 ms. Kein „Apply"-Button.

### J3 · „Operating Point variieren" (≥ 50 % der Sessions)

1. T-Slider auf 60 °C → V steigt sichtbar (Kurve verschiebt sich nach oben).
2. p_H₂-Slider auf 30 bar → V steigt nochmal (Nernst-Term).
3. Design-j-Slider auf 2 A/cm² → roter Marker wandert auf der Kurve mit, Waterfall-Werte aktualisieren sich an dieser Stelle.

**Anforderung:** Slider-Drag → Replot live (auf jedem `valueChanged`, nicht erst auf `sliderReleased`).

### J4 · „Quelle nachschlagen für einen Wert" (≥ 30 % der Sessions)

1. Hover über „SGL 39BB · 315 µm" in der Komponenten-Auswahl.
2. Tooltip zeigt: BibTeX-Key + erste 2 Zeilen des Zitats + URL.
3. Klick öffnet die volle Quellenangabe in einem Side-Panel.

**Anforderung:** Jeder Spec-Wert in der UI ist quellenklickbar. Nicht nur „im Hintergrund zitiert" — sichtbar.

### J5 · „Ergebnis exportieren" (≥ 20 % der Sessions)

1. Button „CSV" → V–I-Tabelle als `.csv` mit Header-Kommentaren (alle Stack-Einstellungen + BibTeX-Keys).
2. Button „STEP" → 3D-Geometrie der Stack-Anordnung.
3. Button „Citations" → `.bib`-Datei mit allen aktiv verwendeten Quellen.
4. (v1.x) Button „PDF" → Report-PDF mit Plots + Stack-Config + LCOH + Quellenliste.

**Anforderung:** Export-Datei muss selbstdokumentierend sein — wer die `.csv` öffnet, sieht ohne das Tool, mit welchen Inputs sie erzeugt wurde.

---

## 4 · UI-Archetyp: Notebook-Style Single-View

### Entschieden: scrollbare Single-Page mit nummerierten Sektionen

| Archetyp | Beispiel | Verworfen, weil … |
|---|---|---|
| CAD-Style (Tree+Viewport+Properties) | SolidWorks, FreeCAD | 80 % der Pixel für Geometrie verschwendet, die nicht der eigentliche Wert des Tools ist |
| Dashboard mit mehreren Panels | Grafana, Datadog | „Wo fange ich an?"-Angst beim ersten Öffnen, keine Workflow-Linearität |
| IDE-Style (Tabs + Files + Bottom-Panel) | VSCode, JetBrains | Fühlt sich nach Code-Editor an, nicht nach Engineering-Werkzeug |
| Multi-Window | klassische CAE-Tools | macOS/Windows-Multi-Window UX altert schlecht, Slider ↔ Plot-Sync fragil |
| Tab-Switcher (heutiger Zustand) | unser v0 | Pipeline „Auswahl → Operating-Point → Ergebnis → Kosten" wird durch Tab-Wechsel zerhackt — User verliert Kausalität |
| **Notebook-Style Scroll** | Jupyter, COMSOL App Builder, Streamlit | **Lesereihenfolge = Berechnungsreihenfolge.** Linearer Workflow. Alles auf einer Fläche sichtbar bei Standard-Fenstergröße (1400×900). Slider hier oben, Plot direkt drunter — direkter Cause-and-effect. |

### Window-Layout (v1.0 Soll)

```
┌─ pem-ec-designer ─────────────────────────────────[?][⚙]──┐
│  Header: app name · Validation: ✓ Bernt-band (Δ 1.2%)      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ ① STACK DESIGN                              ▸ 3D-Vorschau │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ Membrane         [Nafion 212 ▼]    50 µm · σ 10 S/m   ⓘ│ │
│ │ Anode CL         [Bernt 2016 opt ▼] 2.0 mg_Ir/cm²    ⓘ│ │
│ │ Cathode CL       [Zhang 2024 base ▼] 0.10 mg_Pt/cm²  ⓘ│ │
│ │ Anode GDL        [SGL 39BB ▼]       315 µm           ⓘ│ │
│ │ Cathode GDL      [SGL 39BB ▼]       315 µm           ⓘ│ │
│ │ Anode BPP        [POCO 5mm ▼]      ⚠ no ASR cited    ⓘ│ │
│ │ Cathode BPP      [POCO 5mm ▼]      ⚠ no ASR cited    ⓘ│ │
│ │                                                        │ │
│ │ Total ASR: 0.077 Ω·cm²  ·  Footprint: ⌀ 50 mm (19.6 cm²)│ │
│ └──────────────────────────────────────────────────────┘ │
│                                                            │
│ ② OPERATING POINT                                          │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ Temperature   [────●────] 80 °C    range 50–95         │ │
│ │ p(H₂, cathode)[●────────]  1 bar   range 1–30          │ │
│ │ p(O₂, anode) [●────────]  1 bar   range 1–30          │ │
│ │ Design j      [──●──────] 1.0 A/cm² ← marker in plot   │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                            │
│ ③ RESULTS                                       ◉ live    │
│ ┌──────────────────────┬─────────────────────────────────┐│
│ │ V–I curve            │ Loss waterfall @ design_j       ││
│ │                      │                                 ││
│ │     [matplotlib]     │  E_rev  1.182 V  ████████ 73 % ││
│ │  V(1) = 1.610 V  ●   │  η_OER  0.281 V  ██       17 % ││
│ │  V(2) = 1.764 V      │  η_HER  0.070 V  █         4 % ││
│ │                      │  η_ohm  0.077 V  █         5 % ││
│ │                      │  ───────────────                ││
│ │                      │  V      1.610 V                 ││
│ │                      │  η_LHV  0.736                   ││
│ └──────────────────────┴─────────────────────────────────┘│
│                                                            │
│ ④ ECONOMICS                                    (v1.0 lite)│
│ ┌──────────────────────────────────────────────────────┐ │
│ │ CapEx  [───●────] 1100 €/kW  Schmidt 2017 current    ⓘ│ │
│ │ Strom  [──●─────]   50 €/MWh                          │ │
│ │ → LCOH ≈ 5.20 €/kg H₂   (CF=90%, 25y, 5% discount)    │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                            │
│ ⑤ EXPORT                                                   │
│ [STEP] [STL] [V–I CSV] [Citations .bib] [Report PDF]ⁱ      │
│                                              ⁱ v1.x         │
│                                                            │
│ Status: 20 sources active · 2 layers skipped (no ASR cited)│
└────────────────────────────────────────────────────────────┘
```

### Window-Constraints

- **Minimal:** 1280 × 800. Unterhalb wird gewarnt (Statusbar).
- **Standard:** 1400 × 900. Alle 5 Sektionen sichtbar ohne scroll bei collapsed §1-Detail.
- **Maximal:** beliebig. Plots wachsen mit, Slider-Spalten haben Max-Breite.
- **3D-Vorschau** ist ein einklappbares Detail innerhalb §1. Default: zugeklappt. Sie war Geometry-Layer-Nachweis, ist nicht zentral für den V–I-Workflow.

---

## 5 · Sieben tragende Design-Prinzipien

| # | Prinzip | Konkret |
|---|---|---|
| **P1** | Lesereihenfolge = Pipeline | §1 Auswahl → §2 Bedingungen → §3 Ergebnis → §4 Kosten → §5 Export. Top-to-bottom. Cause-and-effect ist räumlich, nicht zeitlich (kein Tab-Wechsel). |
| **P2** | Live everywhere | Jeder Dropdown / Slider recomputed sofort (<100 ms). **Kein „Calculate"-Button.** Modell ist 0-D, Python rechnet das in <10 ms — alles andere ist UI-Overhead. |
| **P3** | Quelle hinter jedem Wert | Hover über jeden Spec-Wert → Tooltip mit BibTeX-Key + Zitat. Klick öffnet Quellen-Side-Panel. Strict-Quellen ist der einzigartige Wertbeitrag des Tools — nicht verstecken. |
| **P4** | Validation immer sichtbar | Badge oben rechts: **✓** = im Literatur-Band, **⚠** = ausserhalb. Klick erklärt welche Anker (Bernt 2016, Carmo 2013). Das ist die ehrliche Ansage: "stimmt dein Modell mit cited literature überein?" |
| **P5** | Skipped Layers transparent | Wenn eine Komponente keinen zitierbaren ASR-Wert hat (z. B. POCO BPP), wird sie in der ohmschen Summe weggelassen — und das wird **in der UI sichtbar** (⚠ Symbol direkt am Dropdown, Statusbar-Zähler). Niemals stillschweigend ignorieren oder mit Schätzung füllen. |
| **P6** | Konsistente Farben | E_rev = `#4F81BD` blau · η_OER = `#C0504D` rot · η_HER = `#9BBB59` grün · η_ohmic = `#F79646` orange. Über alle Plots, Legenden, Waterfall, PDF-Export. Diese vier Farben werden zur sichtbaren „Sprache" des Tools. |
| **P7** | Default ist sinnvoll | Beim ersten App-Start ist ein voller Stack vorausgewählt (Nafion 212 + IrO₂ + Pt + 2× SGL 39BB), 80 °C, 1 bar. User sieht **sofort** ein Ergebnis. Kein leerer Bildschirm, kein „bitte erst auswählen". |

---

## 6 · Komponenten-Patterns

Wie sich die einzelnen UI-Elemente verhalten — bindend, damit jede Session denselben Stil produziert.

### 6.1 · Dropdowns (Komponentenauswahl §1)

- **Inhalt:** alle Library-Einträge der Kategorie, sortiert nach Schlüsselgröße (z. B. GDL nach Dicke, Membrane nach Dicke, BPP nach Material).
- **Label:** kurze, menschenlesbare Form. `"Nafion 212 · 50 µm"` statt `"membrane.nafion.212"`.
- **Hover-Tooltip:** zeigt vollständigen Component-Name + Source-Key + relevante Properties.
- **Skipped-Layer-Badge:** wenn das ausgewählte Item nicht alle Felder hat, die §3 brauchen würde, erscheint `⚠ no ASR cited` rechts neben dem Dropdown.
- **Klick auf Dropdown-Pfeil ⓘ:** öffnet Source-Side-Panel mit der vollen BibTeX-Eintragung.

### 6.2 · Slider (Operating Point §2)

- **Integer-Steps:** T in °C, p in bar, j in A/cm². Echte Engineering-Einheiten am UI-Boundary; SI passiert intern.
- **Label rechts neben Slider:** immer sichtbar mit Einheit, **nicht nur Tooltip**. Engineering ist Einheiten-getrieben.
- **valueChanged-Replot:** live, auch während Slider-Drag. Auf macOS arm64 mit M-Chip ist das problemlos performant für 0-D-Modell.
- **Range-Hint rechts:** „range 50–95" zeigt physikalische Sinngrenzen. Outside-Range wird nicht zugelassen (Slider-Max), nicht erst nachgemeldet.
- **Design-j-Slider hat besondere Rolle:** er setzt nicht den Sweep-Bereich, sondern wo der **rote Marker** auf der V–I-Kurve sitzt und für welchen Punkt die Waterfall berechnet wird.

### 6.3 · Plots (Results §3)

- **Backend:** Matplotlib `FigureCanvasQTAgg`. Bewusst nicht plotly/bokeh — bessere Export-Qualität, bessere PDF-Integration, weniger Dependencies.
- **Linker Plot:** V_cell(j) auf linearen Achsen. Marker bei design_j, V(1 A/cm²), V(2 A/cm²). Gestrichelte Linie bei E_rev,STP = 1.229 V als Referenz. Optional Log-X-Toggle für Aktivierungs-Region-Zoom (v1.x).
- **Rechter Plot:** Stacked-Area-Waterfall mit konsistenten P6-Farben. Drei Layer-Stapel: E_rev (Boden) → η_OER → η_HER → η_ohm → V_cell (Deckel).
- **Auf Mouse-Hover über die V–I-Kurve:** Crosshair zeigt j und V an dieser Stelle (v1.x — optional, kein v1.0-Blocker).

### 6.4 · Validation-Badge (Header rechts oben)

- **Grün ✓** wenn `|V(design_j) − V_literature_band| < 5%`. Default-Anker: Bernt 2016 (1 A/cm²) und Carmo 2013 (2 A/cm²).
- **Gelb ⚠** wenn 5–15 %. Tooltip: „V(1 A/cm²) = 1.71 V — Bernt 2016 reports 1.57 V (8.9 % deviation). Check membrane choice or T."
- **Rot ✗** wenn >15 %. Tooltip: „Likely model error or wrong stack — review skipped layers, check σ-Quelle der Membran."
- **Klick auf Badge:** öffnet Side-Panel mit den verwendeten Anker-Werten, ihren Quellen, und der prozentualen Abweichung.

### 6.5 · Statusbar (unten)

Zeigt **immer**: aktive Source-Anzahl · skipped-layer-Zähler · letzte Aktion (z. B. „CSV exported to ~/Desktop/run_2026-05-12.csv").

Zeigt **nie**: Spinner, Progress-Bars (es gibt nichts, was länger als 100 ms dauert).

---

## 7 · Farb-System (verbindlich)

```
E_rev      #4F81BD   ████  blau      — Thermodynamik, unkontrollierbar
η_OER      #C0504D   ████  rot       — Anode-Kinetik (typ. dominanter Verlust)
η_HER      #9BBB59   ████  grün      — Kathode-Kinetik (typ. klein)
η_ohmic    #F79646   ████  orange    — alle ohmschen Verluste zusammen

V_cell     #000000   ────  schwarz   — Kurvenlinie selbst, Konturen
Hinweis    #808080   ────  grau      — Annotations, Referenzlinien (E_rev,STP)

Validation grün  #2E7D32      ✓
Validation gelb  #ED6C02      ⚠
Validation rot   #C62828      ✗

Background      #FFFFFF        — wissenschaftliche Plots brauchen Weiss
Skipped-Layer  #FFA000  ⚠     — Warn-Orange, deutlich anders als η_ohmic
```

**Kein Dark Mode in v1.0.** Engineering-Reports werden in weisser Konvention erstellt. Dark Mode v1.x nur, wenn explizit gefordert und nur für die UI selbst, nicht für Plot-Exports.

---

## 8 · Onboarding

**Erstes Öffnen:**
1. App öffnet sich mit Default-Stack vorausgewählt → V–I-Kurve sofort sichtbar.
2. **Ein einziger** dismissible Banner unter dem Header:
   > „Erste Session? Die Kurve unten zeigt, wo jeder Volt deiner Zelle hingeht. Bewege einen Slider, um Sensitivität zu erkunden."
3. Banner verschwindet beim ersten Klick oder Slider-Move. `QSettings` merkt sich, dass er gezeigt wurde — kein weiteres Mal.

**Keine:** Wizards. Tutorials. Splash-Screen. Konto-Eingabe. Privacy-Banner.

Anti-Pattern, das vermieden werden muss: „bitte wählen Sie zuerst eine Membrane" — das wäre eine **leere Default-Konfiguration**, was sofortige Hürde ist.

---

## 9 · State-Persistenz

Was zwischen Sessions erhalten bleibt (via `QSettings`):

| Was | Warum | Speicher-Key |
|---|---|---|
| Stack-Auswahl (7 Komponenten + 2 Catalyst-Materials) | User hat seine bevorzugte Konfiguration | `stack.{layer}` |
| Operating-Point (T, p_H₂, p_O₂, design_j) | User arbeitet meist mit konstantem Designpoint | `op.{T,pH2,pO2,j_design}` |
| LCOH-Parameter (CapEx, Strompreis) | individuell projektabhängig | `lcoh.{capex,electricity}` |
| Fenstergröße + Splitter-Position | trivialer Komfort | `window.{w,h,split}` |
| 3D-Vorschau aufgeklappt? | persönliche Präferenz | `ui.show3d` |
| Onboarding-Banner schon gesehen? | Anti-Nag | `ui.onboardingSeen` |

Was **nicht** persistiert wird: Plot-Zustand (Zoom etc. — wird neu generiert), Validation-Badge (wird live berechnet), Mock-Daten.

**Project-Files (`*.pemcell`-Format):** ausdrücklich **nicht v1.0**. Erst wenn Compare-Drawer (v1.x) kommt, wird ein speicherbares Projekt sinnvoll.

---

## 10 · Export-Formate

### v1.0 (alle implementiert vor Release):

| Format | Inhalt | Selbstdokumentierend? |
|---|---|---|
| `.csv` | V–I-Tabelle: `j_A_cm2, V_cell, E_rev, eta_OER, eta_HER, eta_ohm` | ✓ Header-Kommentar mit Stack-Config + 80 °C + Quellen-Liste |
| `.step` | 3D-Geometrie des gesamten Stacks (alle gewählten Komponenten gestapelt) | ✓ STEP-Headers tragen Bezeichnung |
| `.stl` | dito für 3D-Druck / Mesh-Tools | ✓ |
| `.bib` | BibTeX-Datei mit **nur** den aktiv verwendeten Quellen — nicht der ganzen Library | ✓ |

### v1.x:

| Format | Inhalt |
|---|---|
| `.pdf` (Report) | Stack-Tabelle + V–I-Plot + Waterfall + LCOH-Zahl + Quellenliste · 1–2 Seiten · für Manager / Thesis-Kapitel |
| `.pemcell` (Projekt) | Gespeicherte Konfiguration zum Wiederöffnen + Versionierung |
| `.parquet` (Sweep-Output) | Parametric-Sweep-Ergebnisse mit allen Punkten |

---

## 11 · Keyboard-Shortcuts

| Shortcut | Aktion | v1.0? |
|---|---|---|
| `Cmd+Q` | Quit | ✓ (Standard) |
| `Cmd+R` | Reset to default stack + default operating point | ✓ |
| `Cmd+S` | Save current config (snapshot in `QSettings.lastSnapshot`) | ✓ |
| `Cmd+E` | Export-Dialog öffnen | ✓ |
| `Cmd+D` | 3D-Vorschau ein/ausklappen | ✓ |
| `Cmd+1` ... `Cmd+5` | Scroll zur jeweiligen Sektion | ✓ |
| `?` | Hilfe-Side-Panel mit Shortcut-Liste | ✓ |
| `Cmd+P` | Print Report | v1.x |
| `Cmd+K` | Compare-Drawer öffnen | v1.x |

Engineers lieben Tastaturkürzel. Jede Aktion, die mit Maus möglich ist, hat eine Tastatur-Alternative.

---

## 12 · Failure Modes (graceful)

Was passiert wenn etwas schief läuft — definiert, damit die UI nicht crasht und der User versteht warum.

| Fall | Verhalten |
|---|---|
| Library-Eintrag fehlt erforderliches Feld | Dropdown zeigt Item mit `⚠`-Suffix. Tooltip erklärt welches Feld fehlt. Item wird trotzdem auswählbar — die fehlende Größe wird in §3 als „skipped" geführt. |
| User wählt Material, das keine kinetischen Felder hat, als „Anode Catalyst" | Inline-Fehler unter §1: „Material 'POCO AXF-5Q' has no j0_anode. Choose a catalyst material (iro2-tio2-catalyst)." Keine modale Dialog-Box. |
| Operating-Point ausserhalb sinnvoller Range gewählt | Slider lässt es nicht zu (Min/Max ist hart). Edge-Case-Defense, keine Fehlermeldung nötig. |
| BibTeX-Quelle nicht in `sources.bib` | Library-Loader würde beim Start fehlschlagen — Statusbar zeigt rote Meldung „Library failed to load: 'foo.bar' not in sources.bib" und App bleibt funktionslos sichtbar. Lieber leer als falsche Daten. |
| Matplotlib-Fehler beim Plot | Plot-Panel zeigt „No curve loaded — check stack and operating point" statt zu crashen. |
| Export-Pfad nicht beschreibbar | Statusbar zeigt OS-Fehler, kein Modal. |

---

## 13 · v1.0 Scope vs. v1.x Scope

### v1.0 — was im Release drin sein muss

| Section | Feature | Pfad |
|---|---|---|
| §1 | Komponenten-Dropdowns für alle 7 Layer + 2 Catalyst-Materials | I (Stack-Composer) |
| §1 | Skipped-Layer-Indikator pro Dropdown | C+ |
| §1 | Total-ASR + Footprint-Summary unter den Dropdowns | C+ |
| §1 | 3D-Vorschau einklappbar | bereits da, nur layout-Umstellung |
| §2 | T/p_H₂/p_O₂-Slider | bereits da |
| §2 | Design-j-Slider mit Marker-Sync zu §3 | C+ |
| §3 | V–I + Waterfall | bereits da, +Design-j-Marker, +η_LHV-Zahl |
| §3 | Validation-Badge in Header | C+ |
| §4 | LCOH-Modul + 2 Slider + Anzeige | G |
| §5 | STEP-Export-Button | C+ |
| §5 | CSV-Export | C+ |
| §5 | BibTeX-Export (used sources) | C+ |
| cross | Tooltip-Quellen-System auf allen Werten | C+ |
| cross | Tabs → Single-Page-Scroll Umbau | C+ |
| cross | Default-Stack beim ersten Öffnen | bereits da |
| cross | State-Persistenz via QSettings | C+ |
| cross | Onboarding-Banner | C+ |
| cross | Keyboard-Shortcuts | C+ |

### v1.x — explizit später

- **Compare-Drawer:** Side-Panel von rechts, pinnt eine Konfiguration, zeigt Δ-V–I im selben Plot. **Killer-Feature** für „lohnt sich der Tausch?"-Workflow. Geschätzt: 1 ADR + 2 Sessions.
- **Parametric Sweep:** „Membran-Dicke 25–250 µm sweepen, plot V(1 A/cm²) als f(L)". 1 ADR + 1 Session.
- **Multi-Cell Stack:** N Zellen × V_cell mit thermischem De-rating. Eigenes ADR-Modell. 2+ Sessions.
- **PDF-Report:** mit reportlab oder weasyprint. 1 Session + ein bisschen Design.
- **Project-Files (`.pemcell`):** sinnvoll erst zusammen mit Compare-Drawer.

### Niemals (out of scope)

- Multi-User / Cloud
- Web-UI
- Plug-in-Architektur für Custom-Physik-Modelle
- Eigene Library-Edit-UI (Library bleibt JSON, editiert über Editor + Git)
- Animationen / Transitions
- Splash-Screens / Marketing-Branding in der App

---

## 14 · Roadmap bis v0.1 — Release

5 Sessions, jede 2–3 h, jede atomar.

| Session | Was | Pfad | Ergebnis-Commit |
|---|---|---|---|
| **N+1** | ADR-005 (LCOH-Modell) + `physics/efficiency.py` + `physics/lcoh.py` + Tests + UI §4 Economics-Panel | G | `feat(physics): LCOH module` + `feat(ui): Economics section` |
| **N+2** | ADR-006 (Stack-Composer) + 7 Dropdowns für §1 + `assembly` Refactor (Library-Filter pro Kategorie) + Skipped-Layer-Indikator + Total-ASR-Summary | I | `feat(ui): full stack composer with 7 layer dropdowns` |
| **N+3** | Tabs → Single-Page-Scroll Umbau + Tooltip-Quellen-System auf allen Spec-Werten + Validation-Badge im Header | C+ Teil 1 | `refactor(ui): single-page scroll layout + source tooltips` |
| **N+4** | Design-j-Slider mit Marker-Sync + Export-Buttons (STEP/CSV/BibTeX) + Keyboard-Shortcuts + State-Persistenz + Onboarding-Banner | C+ Teil 2 | `feat(ui): design-j slider + exports + persistence` |
| **N+5** | v0.1-Release-Prep: CHANGELOG fully updated · README mit Demo-Animated-GIF · `LICENSE` (Diskussion mit User) · `git tag v0.1.0` · GitHub-Release-Note schreiben | Release | `chore: release v0.1.0` |

Nach Session N+5 hat das Projekt:
- Eine echte, funktionierende, zitierfähige PEM-EC-Designer-App
- Eine sauber dokumentierte Library mit 5 Component-Kategorien
- Eine validierte 0-D-Physik
- Ein GitHub-Release v0.1.0 mit Tag und Release-Notes
- Eine Persona-passende UI ohne Tab-Hopping

Das ist Portfolio-tauglich, Lehre-tauglich und Anschluss-fähig für v1.x-Erweiterungen.

---

## 15 · Was dieses Dokument **nicht** ist

| | |
|---|---|
| **Kein Vertrag** | Wenn beim Implementieren bessere UX-Ideen kommen, wird dieses Dokument angepasst. ADRs gehen vor. |
| **Kein Backlog** | Jede Session zieht ihre Aufgaben aus STATUS.md, nicht hier. |
| **Kein Style-Guide** | Farben/Spacings/Typography landen ggf. später in einer kleinen `docs/STYLE.md`. |
| **Kein Marketing** | Wer das Tool für „1-Click PEM Designer" verkauft, hat verloren. Es ist ein Werkzeug für Leute, die wissen, was sie tun. |

---

## 16 · Querverweise

- `docs/adr/001-framework-choice.md` — PyQt6 + pyvistaqt + build123d (PySide6 final laut ADR-003)
- `docs/adr/002-library-architecture.md` — Schema + BibTeX-Strict-Quellen
- `docs/adr/003-qt-binding-license.md` — PySide6 / LGPL
- `docs/adr/004-physics-model.md` — 0-D + steady + isotherm + BV+ASR
- `docs/STATUS.md` — was gerade konkret läuft
- `docs/UI-LAUNCH-NOTES.md` — Qt/macOS-Plugin-Fallen

ADRs, die dieses Dokument antizipiert:

- **ADR-005** — LCOH-Modell (Session N+1)
- **ADR-006** — Stack-Composer-Architektur (Session N+2)
- **ADR-007** *(evtl.)* — Compare-Drawer-Architektur (v1.x)
