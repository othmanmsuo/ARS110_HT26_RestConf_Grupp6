# RESTCONF – Grupp 6

Detta projekt är en del av kursen ARS110 och går ut på att automatisera konfiguration och kontroll av ett mindre Cisco-nätverk med hjälp av Python och RESTCONF.

Projektet består huvudsakligen av två Python-program:

1. skilla.py – konfigurerar nätverket automatiskt.
2. Robert_Grupp6.py – kontrollerar att konfigurationen är korrekt.

# Topologi

Nätverket består av tre routrar och de nås via ett separat managementnät.

Enhetnamn + Management-IP visas nedan...

Hemma: 100.100.100.1
ISP: 100.100.100.2
Internet: 100.100.100.3

RESTCONF och HTTPS måste vara aktiverat på enheterna innan programmen körs.

# skilla.py

skilla.py använder RESTCONF med HTTP-metoderna PUT och PATCH för att konfigurera routrarna.

Programmet konfigurerar bland annat:

- Hostname
- IPv4-adresser på GigabitEthernet-interface
- Serial-interface
- Loopback-interface
- EIGRP AS 100
- EIGRP network statements
- Passive interface
- Redistribute static
- Default/static route

Där det är möjligt används standardiserade YANG-modeller, exempelvis "ietf-interfaces" och "ietf-ip". För funktioner där dessa modeller inte räcker används Cisco IOS XE Native YANG-modeller.

# IOS XE-versioner

Slutversionen av programmet är anpassad för routrar som använder den nyare EIGRP-strukturen i IOS XE 16.12.

Under utvecklingen användes även routrar med IOS XE 16.6, där EIGRP representeras med en annan YANG-struktur. Därför finns funktionen "konfigurera_eigrp_166()" kvar i koden som stöd för den äldre strukturen.

Den funktionen anropas dock inte i slutversionens normala programflöde.

# Robert_Grupp6.py

Robert_Grupp6.py fungerar som en automatisk rättare.

Programmet använder RESTCONF GET för att läsa både konfiguration och operational data från routrarna och kontrollerar bland annat:

- Hostname
- Interface och IPv4-adresser
- EIGRP AS
- EIGRP-neighbors
- Routing/FIB
- Next-hop
- Static/default route

Varje fel som upptäcks räknas och programmet avslutar med en text som säger ifall allt är godkänt eller inte (+ hur många upptäckta fel som hittades, ifall det finns.)

Eftersom EIGRP-neighbors och routes är operational data bör routingprotokollet ha hunnit konvergera innan rättningsprogrammet körs.

# Utveckling och testning

Under utvecklingen användes Postman för att skicka RESTCONF GET-requests direkt till routrarna.

Det användes för att undersöka hur olika YANG-modeller och resurser representerades i JSON och för att hitta rätt RESTCONF resource paths innan motsvarande funktioner implementerades i Python.

Testning utfördes därefter genom Python med biblioteket requests.

# Teknik sammanfattning.

Projektet använder:

- Python 3
- RESTCONF
- HTTPS
- YANG
- JSON
- Python requests
- Cisco IOS XE Native YANG
- IETF YANG-modeller
- Postman
- GitHub


# Egen Körning

1. Kontrollera att management-IP, HTTPS och RESTCONF är konfigurerat på routrarna.
2. Kör skilla.py för att konfigurera nätverket.
3. Låt EIGRP etablera neighbors och konvergera.
4. Kör Robert_Grupp6.py för att kontrollera resultatet.

Projektet använder RESTCONF för all konfiguration och kontroll efter den initiala management och RESTCONF-konfigurationen via CLI.
