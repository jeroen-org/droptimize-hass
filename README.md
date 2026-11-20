# Droptimize for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Home Assistant-integratie die de waterstand van je eigen
[Droptimize](https://droptimize.be)-regenwaterput uitleest.

De integratie praat rechtstreeks met de cloud-API die de Droptimize-app
(`be.lmr.droptimize`) gebruikt. Je hebt enkel het **registratienummer** van je
sensor nodig — dat staat op de sticker op de sensor.

> **Let op:** dit is een onofficiële integratie. De API is niet openbaar en kan
> zonder aankondiging wijzigen. Gebruik op eigen risico.

## Inhoud

- [Installatie](#installatie) · [Configuratie](#configuratie) ·
  [Entities](#entities) · [Hoe het werkt](#hoe-het-werkt) ·
  [Aanpassen](#aanpassen) · [Problemen](#problemen)

## Installatie

### Optie A — via HACS (aanbevolen)

1. Open **HACS** in Home Assistant.
2. Klik rechtsboven op de drie puntjes → **Custom repositories**.
3. Vul in:
   - **Repository:** `https://github.com/jeroenvdw-bot/droptimize-hass`
   - **Category:** `Integration`
4. Klik op **Add**.
5. Zoek nu in HACS naar **Droptimize** en klik op **Download**.
6. Herstart Home Assistant.

### Optie B — handmatig

1. Download de laatste release.
2. Kopieer de map `custom_components/droptimize` naar
   `<config>/custom_components/droptimize` op je Home Assistant-instance.
3. Herstart Home Assistant.

## Configuratie

1. Ga naar **Instellingen → Apparaten & diensten**.
2. Klik op **Integratie toevoegen** en zoek **Droptimize**.
3. Voer het **registratienummer** in (de cijfers op de sticker van je sensor).
4. Klaar — de put verschijnt als apparaat met de bijbehorende entities.

### Opties aanpassen

Via **Instellingen → Apparaten & diensten → Droptimize → Configureeren** kan je
het poll-interval wijzigen (standaard **30 minuten**).

## Entities

| Entity | Eenheid | Omschrijving |
|---|---|---|
| `sensor.<put>_vullingsgraad` | % | Vullingsgraad van de put |
| `sensor.<put>_watervolume` | L | Resterend watervolume |
| `sensor.<put>_waterdiepte` | cm | Afstand radar → wateroppervlak |
| `sensor.<put>_batterij` | % | Batterij van de sensor |
| `sensor.<put>_batterijspanning` | V | Batterijspanning *(standaard uitgeschakeld)* |
| `sensor.<put>_temperatuur` | °C | Temperatuur in de put |
| `sensor.<put>_laatste_meting` | | Tijdstip van de laatste meting |
| `sensor.<put>_volumeverschil_7_dagen` | L | Verschil in volume t.o.v. 7 dagen geleden |
| `sensor.<put>_radarafstand` | mm | Ruwe radarafstand *(standaard uitgeschakeld)* |
| `sensor.<put>_signaalsterkte` | | RSSI van de sensor *(standaard uitgeschakeld)* |
| `binary_sensor.<put>_batterij_laag` | | Batterij onder de 20% |
| `binary_sensor.<put>_geen_meting_ontvangen` | | Geen meting ouder dan 3 uur |

De entity-namen zijn in het Engels als je Home Assistant op Engels ingesteld
staat; de Nederlandse namen verschijnen automatisch bij een NL-taalinstelling.

## Hoe het werkt

De API geeft enkel de **radar-afstand** (mm) terug — geen liters of percentage.
De Droptimize-app berekent die zelf uit de putgeometrie, die in de JWT-claims van
de sensor zit (`wellVolume`, `wellHeight`, `wellTunnelHeight`). Deze integratie
doet exact die berekening na:

```
waterniveau_cm   = afstand_mm / 10 - (tunnelhoogte - 52)
waterkolom_cm    = puthoogte - waterniveau_cm   (afgekapt op 0..puthoogte)
volume_L         = (putvolume / puthoogte) * waterkolom_cm
vullingsgraad_%  = round(volume_L / putvolume * 100)
```

Hierin zijn twee waarden hardcoded in de app, maar ze betekenen iets anders:

- **52 cm** is een echte, vaste hardwareconstante (`getTunnelOffsetConstantCm`).
  De tunnel moet minstens 52 cm diep zijn zodat de sensor niet onder water kan
  komen; in de formule wordt 52 van de tunnelhoogte afgetrokken.
- **60 cm** is géén constante maar de **standaardkeuze** uit de tunnel-dropdown
  (opties: 52/60/80/100/120/aangepast). De app gebruikt altijd jouw ingestelde
  tunnelhoogte (`wellTunnelHeight` uit de JWT-claims) en valt alleen terug op 60
  als die waarde ontbreekt. Deze integratie doet hetzelfde.

Beide staan in `custom_components/droptimize/const.py`. De formules zijn
gevalideerd tegen de echte API én de server-cijfers van de app.

De authenticatie verloopt met een kortlevende JWT (1 uur) die automatisch wordt
vernieuwd; het registratienummer wordt in de Home Assistant-config opgeslagen.

## Aanpassen

- **Poll-interval:** standaard 30 min, aanpasbaar via de opties (min. 5 min).
- **Constanten** (offset/tunnel): `custom_components/droptimize/const.py`.
- **Nieuwe velden:** de ruwe API-response is beschikbaar via de
  `droptimize.get_dashboard`-service... *(zie `/me/dashboard` in de API)*.

## Problemen

- Geen entities? Controleer of het registratienummer klopt en of de sensor
  recent nog gemeten heeft (de API geeft dan geen `lastReading`).
- Foutieve vullingsgraad? Controleer of `wellVolume`, `wellHeight` en
  `wellTunnelHeight` in de JWT-claims overeenkomen met je put.
- [Open een issue](https://github.com/jeroenvdw-bot/droptimize-hass/issues).

## Ontwikkelen

```bash
pip install pytest-homeassistant-custom-component
pytest
```

## Licentie

[MIT](LICENSE)