# Droptimize for Home Assistant

Custom integration voor Home Assistant die de waterstand van je eigen
[Droptimize](https://droptimize.be)-regenwaterput uitleest via de cloud-API.

De integratie praat rechtstreeks met de backend die de Droptimize-app gebruikt.
Je hebt enkel het **registratienummer** van je sensor nodig (de sticker op de
sensor).

## Installatie

### HACS ( aanbevolen)

1. Voeg deze repo toe als custom repository in HACS (type *Integration*).
2. Installeer **Droptimize**.
3. Herstart Home Assistant.

### Handmatig

Kopieer `custom_components/droptimize` naar `<config>/custom_components/droptimize`.

## Configuratie

Ga naar **Instellingen → Apparaten & diensten → Integratie toevoegen** en zoek
**Droptimize**. Voer het registratienummer in.

Via **Instellingen → Apparaten & diensten → Droptimize → Configureeren** kan je
het poll-interval aanpassen (standaard 30 minuten).

## Entities

| Entity | Eenheid | Omschrijving |
|---|---|---|
| `sensor.<put>_vullingsgraad` | % | Vullingsgraad van de put |
| `sensor.<put>_watervolume` | L | Resterend watervolume |
| `sensor.<put>_waterdiepte` | cm | Afstand radar → wateroppervlak |
| `sensor.<put>_batterij` | % | Batterij van de sensor |
| `sensor.<put>_batterijspanning` | V | Batterijspanning (uitgeschakeld standaard) |
| `sensor.<put>_temperatuur` | °C | Temperatuur in de put |
| `sensor.<put>_laatste_meting` | | Tijdstip van de laatste meting |
| `sensor.<put>_volumeverschil_7_dagen` | L | Verschil in volume t.o.v. 7 dagen geleden |
| `sensor.<put>_radarafstand` | mm | Ruwe radarafstand (uitgeschakeld standaard) |
| `sensor.<put>_signaalsterkte` | | RSSI (uitgeschakeld standaard) |
| `binary_sensor.<put>_batterij_laag` | | Batterij onder 20% |
| `binary_sensor.<put>_geen_meting_ontvangen` | | Geen meting ouder dan 3 uur |

De entity-namen zijn in het Engels als je HA op Engels staat; de `translation_key`
bepaalt de entity_id.

## Hoe het werkt

De API geeft enkel de radar-afstand (mm) terug. De app berekent zelf liters en
vullingsgraad uit de putgeometrie (`wellVolume`, `wellHeight`,
`wellTunnelHeight` — allemaal in de JWT-claims van de sensor). Deze integratie
doet exact die berekening na:

```
waterniveau_cm   = afstand_mm / 10 - (tunnelhoogte - 52)
waterkolom_cm    = puthoogte - waterniveau_cm   (0..puthoogte)
volume_L         = (putvolume / puthoogte) * waterkolom_cm
vullingsgraad_%  = round(volume_L / putvolume * 100)
```

De constanten (52 cm offset, 60 cm default tunnel) staan in `const.py`. Als de
app die ooit wijzigt, moet je ze daar aanpassen.

## Let op

- Dit is een **onofficiële** integratie. De API is niet openbaar en kan zonder
  aankondiging wijzigen.
- Het registratienummer is een geheim (gekoppeld aan je adres). Het wordt
  opgeslagen in `.storage/core.config_entries` van Home Assistant.
- Gepollt wordt standaard elke 30 minuten; de sensor meet ongeveer 1×/uur.

## Ontwikkelen

```bash
pip install pytest-homeassistant-custom-component
pytest
```