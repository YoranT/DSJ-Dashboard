# 0.1.2 — 14 oktober 2026

- Ruimtepagina gebruikt voortaan DSJ-pop-ups; geen direct geneste Bubble-pop-ups die de hele bovenliggende paginakaart kunnen verbergen. Geïnstalleerde Navroom-kaarten blijven optioneel beschikbaar.
- Alleen entiteiten met een bestaande ruimte worden op klantpagina’s getoond. De apparaatruimte wordt geërfd; een expliciete entiteitsruimte gaat voor. Ook bestaande favorieten zonder ruimte vallen weg, tot ze weer een ruimte hebben.
- ‘Aanstaande lampen’ en de teller op Home gebruiken alleen lichtgroepen. Herkenning via groepsintegratie, groepsleden of expliciet label `light_group` / `dsj_light_group`, en `is_hue_group` indien aanwezig. Individuele lampen blijven in de ruimte-pop-up.
- Het beheerscherm vermeldt waarom entiteiten zonder ruimte niet getoond worden. Home Assistant Energie-bronnen blijven los van deze presentatiekeuze.
- 35 Python-tests geslaagd. JavaScript-componenttests omvatten nu ook een geïnstalleerde Bubble Card, DSJ-pop-ups en de lichtgroepenteller. Dit zijn tests met een DOM-testmodel; controle op de demo blijft nodig.

# 0.1.1 — 14 oktober 2026

- Gebruik de huidige iteratie-interface voor apparaatregistraties; verwijder de gemelde waarschuwing over `.devices.values()`.
- Registreer de DSJ-module ook als Lovelace-resource. Werk bestaande DSJ-resourceadressen bij zonder andere resources te wijzigen.
- Nieuw versieadres voor de browsercache en een herkenbare opstartmelding in de console.
- Expliciete labels voor navigatielinks en knoppen, inclusief iconen zonder tekst.
- Initialisatie beschermt tegen status vóór kaartconfiguratie. Asynchrone opbouwfouten worden zichtbaar weergegeven.
- 29 Python-tests geslaagd, plus JavaScript-componenttests met een vereenvoudigd DOM-model en syntaxiscontroles.

De door de gebruiker gemelde `getAttribute("aria-label").trim`-fout kon niet aan een bronbestand worden gekoppeld; de definitieve werking van deze update moet op de demo worden bevestigd. Geen live Home Assistant- of visuele browsercontrole uitgevoerd.

# 0.1.0 — 14 oktober 2026

Eerste DSJ-testversie voor Home Assistant Core 2026.10 op OS: automatische ruimte-indeling, zeven pagina's, verborgen entiteiten en favorieten, energie vanuit HA-voorkeuren, optioneel hergebruik van geïnstalleerde Navroom/Bubble/Sonos-kaarten, DSJ-terugvalkaarten en beheer via de interface.

25 logische tests geslaagd; Python- en JavaScript-syntaxis gecontroleerd. Geen live Home Assistant-test of visuele browsercontrole uitgevoerd. Lees README.md voor de exacte beperkingen en demo-controles.
