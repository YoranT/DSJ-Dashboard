# De Slimme Jongens Dashboard — 0.1.2 testversie

Een eigen, automatisch opgebouwd Home Assistant-dashboard op basis van jullie demo-YAML. Gericht op Home Assistant OS met Core 2026.10. Dezelfde broncode kan bij verschillende klanten worden geïnstalleerd; klantnamen en entiteitsnamen staan niet vast in de code.

**Status:** installeerbaar ontwikkelpakket voor testen op de demo. De generator en opslaglogica zijn lokaal getest. Opstarten binnen Home Assistant, echte kaartbediening, vormgeving en de samenwerking met jullie geïnstalleerde custom cards zijn hier nog niet getest. Gebruik dit pakket eerst op de demo voordat jullie het aan klanten leveren.

## Installeren op Home Assistant OS

1. Pak `dsj-dashboard-0.1.2.zip` uit op je computer.
2. Kopieer de map `custom_components/dsj_dashboard` uit het pakket naar de configuratiemap van Home Assistant, via jullie bestaande bestandseditor, Studio Code Server of Samba. Het resultaat moet `/config/custom_components/dsj_dashboard/manifest.json` zijn. Kopieer de hele map, inclusief `frontend` en `translations`.
3. Herstart Home Assistant.
4. Open **Instellingen → Apparaten & diensten → Integratie toevoegen**. Zoek **De Slimme Jongens Dashboard** en voeg de integratie toe.
5. Open **De Slimme Jongens** in de zijbalk. Het adres is `/dsj-dashboard/hoofdpagina`.
6. Koppel apparaten aan ruimtes, en ruimtes aan verdiepingen, in Home Assistant. Apparaten erven de ruimte van hun apparaatregistratie; een expliciete ruimte op een entiteit gaat voor.
7. Open **Instellingen** in het DSJ-dashboard. Zoek een entiteit en klik op **Verbergen** of **Favoriet**. Verborgen apparaten kun je met **Tonen** terugzetten.
8. Stel de energiemeters in via het Energie-gedeelte van Home Assistant. De DSJ-energiepagina leest die instellingen; je hoeft geen sensornamen in DSJ-code in te vullen.

Er is geen toevoeging aan `configuration.yaml` nodig. Het pakket registreert zijn eigen dashboard en JavaScriptmodule, zowel als globale frontendmodule als in de Lovelace-resources. Het bestaande demo-dashboard en andere dashboards blijven bestaan. Bij een bestaande dashboard-URL `/dsj-dashboard` stopt de integratie met een melding in plaats van die te overschrijven.

Als de integratie na het kopiëren niet in de lijst verschijnt: controleer het mappad, herstart Home Assistant en vernieuw de browser volledig. Bekijk bij een fout **Instellingen → Systeem → Logboeken**, zoek op `dsj_dashboard` en bewaar de volledige foutmelding.

## Bijwerken vanaf 0.1.0 of 0.1.1

1. Pak het nieuwe ZIP-pakket uit en vervang de bestanden in `/config/custom_components/dsj_dashboard`, inclusief de map `frontend`. De mapnaam gebruikt een **underscore**, geen koppelteken. Als de bestaande integratiemap `dsj-dashboard` heet, hernoem die naar `dsj_dashboard`; laat geen twee kopieën van dezelfde integratie naast elkaar staan.
2. Herstart Home Assistant. Je hoeft de integratie niet te verwijderen; daardoor blijven favorieten en verborgen-keuzes behouden.
3. Sluit het dashboardtabblad en open het opnieuw. Vernieuw zo nodig zonder browsercache (op Mac: Cmd+Shift+R; op Windows: Ctrl+F5).
4. Open het DSJ-dashboard. De browserconsole moet `[DSJ Dashboard] 0.1.2 frontend geladen` tonen.

Versie 0.1.2 verandert drie dingen:

- **Ruimtes blijft zichtbaar:** DSJ gebruikt eigen pop-ups met de bestaande ruimte-inhoud. Er worden geen Bubble-pop-ups meer binnen de volledige DSJ-paginakaart gemonteerd. Bubble kan de bovenliggende Home Assistant-kaart verbergen wanneer een pop-up gesloten is; in deze opzet is dat de hele ruimtepagina. Navroom Card kan nog steeds worden gebruikt en opent nu de DSJ-pop-up via dezelfde ruimtelink.
- **Zonder ruimte automatisch weg:** een entiteit verschijnt alleen als die zelf, of via het apparaat, aan een bestaande ruimte is gekoppeld. Dit geldt ook voor favorieten, media, klimaat, beveiliging en weer. In het beheerscherm blijft de entiteit vindbaar met de reden ‘Geen ruimte toegewezen — niet getoond’, zodat je weet wat je moet indelen. Energiegrafieken blijven de aparte Home Assistant Energie-instellingen gebruiken.
- **Alleen lichtgroepen op Home:** ‘Aanstaande lampen’ bevat alleen zichtbare, aan ruimtes gekoppelde lichtgroepen. Individuele lampen blijven beschikbaar in de ruimte-pop-up. De teller op Home telt nu lichtgroepen, geen individuele lampen.

Groepen worden herkend aan de Home Assistant-groepsintegratie, een lijst met `light.*`-groepsleden in het attribuut `entity_id`, `is_hue_group: true` indien aanwezig, of het entiteitslabel `light_group` / `dsj_light_group`. Namen zoals ‘Woonkamer’ of ‘Groep’ worden niet als bewijs gebruikt. De groep moet zelf ook aan een ruimte zijn gekoppeld. Dat de losse leden een ruimte hebben, geeft de groep niet automatisch een ruimte. Gebruik voor virtuele groepen zonder groepsmetadata het label `light_group`, zoals in jullie oorspronkelijke demo-YAML. Deze versie maakt geen nieuwe lichtgroephulpen aan.

De waarschuwing over het verouderde gebruik van `device_registry.devices.values()` is sinds 0.1.1 aangepast. De JavaScriptkaart wordt sinds die versie ook als Lovelace-resource geregistreerd.

Als het rode scherm blijft: bewaar de volledige consolemelding inclusief **bestandsnaam en regelnummer**. Controleer of de versieboodschap verschijnt. Verschijnt die niet, open dan op hetzelfde Home Assistant-adres `/dsj_dashboard/dsj-dashboard.js?v=0.1.2`; daar hoort JavaScripttekst te staan en geen 404. Rapporteer alleen de status en foutmelding; deel geen tokens of sessiegegevens.

## Wat automatisch wordt opgebouwd

| Pagina | Werking |
| --- | --- |
| Home | Begroeting, favorieten, ingeschakelde lichtgroepen en de eerste zichtbare, aan een ruimte gekoppelde weerentiteit. |
| Ruimtes | Ruimtekaarten per verdieping, met verlichting, temperatuur en luchtvochtigheid. Een klik opent de apparaten in die ruimte. |
| Media | Zichtbare mediaspelers per ruimte. Met geïnstalleerde Sonos Card worden echte Sonos-entiteiten samengebracht in die kaart. |
| Energie | Datumselectie, energieverdeling, verbruik, opwek en kosten vanuit Home Assistant. Gas, water en individuele apparaten verschijnen wanneer ze in Energie zijn ingesteld. Vermogensgrafieken worden toegevoegd als vermogensbronnen zijn ingesteld. |
| Klimaat | Thermostaten, ventilatoren, luchtbevochtigers, boilers en klimaatsensoren. |
| Beveiliging | Sloten, alarmen, camera's, sirenes en relevante binaire sensoren. |
| Instellingen | Zoeken, verbergen, terugzetten en favorieten kiezen. Alleen beheerders kunnen deze instellingen lezen of aanpassen. |

Nieuwe, verwijderde en gewijzigde apparaten, ruimtes en verdiepingen zorgen voor een nieuwe dashboardconfiguratie. Normale statuswijzigingen worden doorgegeven aan de kaarten. Home Assistant kan bij een gewijzigde dashboardconfiguratie vragen de weergave te vernieuwen.

Temperatuur en luchtvochtigheid worden herkend aan `device_class`. Als in Home Assistant een voorkeurssensor voor een ruimte is ingesteld, krijgt die voorrang zolang die zichtbaar is. Anders kiest DSJ de eerste passende sensor op naam. Tijdelijk onbeschikbare entiteiten blijven in beeld, zodat apparaten tijdens een storing niet verdwijnen.

## Vormgeving uit jullie demo

Overgenomen als uitgangspunt: de zeven pagina's, navigatie links op desktop en onderaan op mobiel, goudkleurig accent `#b98c27`, afgeronde ruimtekaarten, pop-ups en de standaard Home Assistant-kaarten voor apparaten.

Bij de integratieopties kun je een bestaand thema kiezen, bijvoorbeeld **DSJ Border**, en de accentkleur aanpassen. Laat de themanaam leeg om het huidige Home Assistant-thema te gebruiken. De aangeleverde YAML verwijst naar DSJ Border, maar bevat de themadefinitie zelf niet. Het volledige thema moet daarom apart op iedere installatie aanwezig zijn om dezelfde themavormgeving te krijgen.

De optie **Geïnstalleerde Navroom Card en Sonos Card gebruiken** staat standaard aan:

- Navroom Card aanwezig: gebruik jullie ruimtekaartstijl met expliciet gekozen zichtbare sensoren en één representatieve lichtentiteit per ruimte. Automatische ontdekking binnen Navroom staat uit, zodat verborgen entiteiten niet opnieuw worden ontdekt. De aan/uitknop van Navroom bedient die ene lichtentiteit; gebruik een lichtgroep als je daarmee de hele ruimte wilt bedienen.
- Ruimte-pop-ups worden altijd door DSJ getoond, met afgeronde vormgeving en de gegenereerde apparaatkaarten. Bubble Card wordt op deze pagina niet meer ingebouwd om te voorkomen dat die de bovenliggende dashboardkaart verbergt. Bubble Card op jullie andere dashboards wordt niet aangepast.
- Een kaart niet aanwezig, of de optie uit: gebruik de meegeleverde DSJ-ruimtekaart en DSJ-pop-up. De aan/uitknop van de DSJ-kaart bedient alle zichtbare lichtentiteiten in die ruimte.
- Sonos Card aanwezig en echte Sonos-entiteiten gedetecteerd: gebruik Sonos Card; anders verschijnen standaard mediaspelerkaarten.

De integratie installeert deze externe kaarten niet automatisch en bundelt hun broncode niet. De compatibiliteit met jullie kaartversies moet op de demo worden gecontroleerd. Zet bij een probleem de optie voor originele kaarten uit en test eerst met de DSJ-terugvalkaarten. De kaartdetectie gebeurt bij het opbouwen van de pagina; ververs de browser na het installeren of bijwerken van een kaart.

De navigatie is een meegeleverd DSJ-component dat de positie en indeling van jullie navbar volgt; de externe Navbar Card is niet nodig.

## Verbergen en favorieten

De keuzes worden op de betreffende Home Assistant-installatie opgeslagen, ook na een herstart. Bij het hernoemen van een entiteits-ID worden de DSJ-keuzes bijgewerkt. Ze gelden voor alle gebruikers van dat DSJ-dashboard, niet afzonderlijk per gebruiker.

Entiteiten die in Home Assistant verborgen of uitgeschakeld zijn, worden niet getoond. Configuratie- en diagnose-entiteiten worden standaard overgeslagen. De beheerpagina legt dit uit; zichtbaar maken van zo'n entiteit regel je in Home Assistant. Verbergen is een presentatiekeuze en verandert geen toegangsrechten of apparaatinstellingen.

Verbergen geldt voor apparaatoverzichten, favorieten, ruimtekaarten en pop-ups. De ingebouwde energiekaarten gebruiken de bronnen en statistieken die jullie in Home Assistant Energie instellen. Wijzig daar welke energiebronnen getoond worden.

Entiteiten zonder bestaande ruimte verschijnen niet op de klantpagina’s, ook niet als ze eerder als favoriet gekozen zijn. Na het koppelen aan een ruimte verschijnen ze automatisch weer volgens hun zichtbaarheid en opgeslagen favorietkeuze. Een ruimtekaart verschijnt pas als de ruimte zichtbare ondersteunde entiteiten bevat. De overige bedienbare entiteiten en sensoren verschijnen in de ruimte-pop-up.

## Onderdelen die nog geen exacte kopie zijn

- De afvalmelding op Home gebruikt geen automatisch gekozen afvalsensor: er is geen vaste standaard die elke afvalintegratie hetzelfde toepast.
- De Nordpool-prijsgrafiek met toekomstige prijzen en de specifieke Power Flow Card Plus-indeling uit jullie YAML zijn vervangen door Home Assistant-energiekaarten. Tarieven en kosten volgen jullie Energie-instellingen; de specifieke vooruitblik uit Nordpool is nog niet overgenomen.
- Kiosk Mode met het verbergen van de Home Assistant-header is niet ingeschakeld door dit pakket. Het DSJ-menu is wel aanwezig. Bestaande kiosk-instellingen horen apart bij jullie installatie.
- Favorieten worden door een beheerder gekozen; de demo-sloten en het demo-alarm worden niet automatisch favoriet op iedere nieuwe klantinstallatie.
- Deze versie heeft nog geen scherm om ruimtevolgorde of individuele kaartindeling te wijzigen. Ruimtes worden op verdiepingsniveau en naam gesorteerd.

Dit is dus een eerste functionele implementatie van het automatische principe, geen bewezen productierelease of volledige visuele kopie van alle 2.235 regels uit de demo.

## Controle op jullie demo

1. Controleer of de integratie zonder fout start en de zeven pagina's openen.
2. Verplaats een testapparaat naar een andere ruimte: controleer de nieuwe indeling.
3. Verberg een lichtentiteit: controleer Home, Ruimtes, de pop-up en eventuele favorieten. Zet hem terug met Tonen.
4. Kies een favoriet, herstart Home Assistant en controleer of die keuze behouden blijft.
5. Controleer ruimtekaarten en pop-ups met originele kaarten aan én uit, op tablet en telefoon.
6. Vergelijk de energiegetallen bij dezelfde datumselectie met de ingebouwde Home Assistant-energiepagina. Controleer ook een installatie zonder gas of zonder zonnepanelen.
7. Controleer klimaatbediening, media, sloten, alarm en camera's met de echte apparaten en hun ondersteunde functies. Sloten openen via de normale Home Assistant-bediening; alarmcodes worden niet omzeild.
8. Open als gebruiker zonder beheerdersrechten: bediening moet werken volgens Home Assistant-rechten, maar aanpassen van DSJ-instellingen niet.
9. Test een tweede klantindeling met andere ruimtes en entiteitsnamen.

## Technische controle en onderhoud

Lokaal uitgevoerd: Python-syntaxiscontrole, JavaScript-syntaxiscontrole en 35 tests voor de generator, voorkeurenopslag, apparaatregistratie en frontendresources. Daarnaast zijn de JavaScript-opstartlogica van alle zeven pagina’s, de ruimtepagina met Bubble Card geregistreerd, het openen/sluiten van de DSJ-pop-up en de lichtgroepenteller gecontroleerd met een vereenvoudigd DOM-testmodel; dat is geen echte browser- of Home Assistant-test. De opslagtests gebruiken een nep-opslag; ze testen onder meer gelijktijdige wijzigingen, foutafhandeling en het behouden van keuzes bij hernoemen. Er was geen Home Assistant-runtime beschikbaar. Een browsercontrole kon door de beperkingen van deze omgeving niet worden uitgevoerd.

Voer de logische tests uit vanuit de uitgepakte projectmap:

```sh
python3 -m unittest discover -s tests -v
node tests/test_frontend.cjs
```

De integratie gebruikt de interne Lovelace-dashboardklassen van Home Assistant om een eigen gegenereerd dashboard te registreren. Dat is gericht op de gecontroleerde 2026.10-broncode; test dit opnieuw bij toekomstige Core-updates. HACS-projectstructuur is voorbereid met `hacs.json`, maar het pakket is nog niet gepubliceerd in een GitHub-repository of HACS-catalogus. Automatische installatie en updates via HACS vereisen die vervolgstap.

Uitschakelen kan via de integratie; verwijderen wist de DSJ-favorieten en verborgen-keuzes. Verwijder daarna desgewenst alleen `/config/custom_components/dsj_dashboard` en herstart Home Assistant.

Technische bronnen gebruikt bij het maken van deze testversie:

- [Home Assistant Core 2026.10 Lovelace-dashboardinterface](https://github.com/home-assistant/core/blob/2026.10.0/homeassistant/components/lovelace/dashboard.py)
- [Home Assistant Core 2026.10 energievoorkeuren](https://github.com/home-assistant/core/blob/2026.10.0/homeassistant/components/energy/data.py)
- [Home Assistant ruimteregister](https://developers.home-assistant.io/docs/area_registry_index/)
- [Bubble Card-documentatie](https://github.com/Clooos/Bubble-Card)
- [Dwains Dashboard als functionele referentie](https://github.com/dwainscheeren/dwains-lovelace-dashboard)

Dwains-broncode is niet overgenomen. Deze versie is geschreven op basis van jullie gewenste werking, jullie demo-opzet en de Home Assistant-interfaces.
