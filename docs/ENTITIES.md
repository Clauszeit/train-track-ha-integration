# Geräte und Entities

Diese Referenz beschreibt vollständig, was die TrainTrack-Integration in Home Assistant anlegt und welche Daten sie über die dokumentierte TrainTrack-Verbindungen-API weitergibt. Maßgeblich sind die API-Antwort und der Stand der installierten Integration. Optionale Felder können fehlen, leer oder `null` sein. Die Integration berechnet aus den Fahrplandaten keine eigenen Verspätungen und verändert keine Verbindung in TrainTrack.

## Gerätezuordnung und Lebenszyklus

Für jede von TrainTrack zurückgegebene Verbindung legt die Integration ein Home-Assistant-Gerät an. Das Gerät gehört zur Integration **TrainTrack** und verwendet TrainTrack als Hersteller. Je Gerät werden drei Sensoren angelegt: `Status`, `Train` und `Delay`. Alle drei Sensoren teilen sich dieselben Verbindungsattribute; die Attribute werden nicht auf einen einzelnen Sensor beschränkt.

Home Assistant erhält für das Gerät einen stabilen Bezeichner aus der TrainTrack-Instanz und der Verbindungs-ID. Für jeden Sensor wird daraus zusammen mit dem Sensorschlüssel eine stabile eindeutige ID gebildet. Der Anzeigename kann sich ändern, wenn sich Fahrplanangaben oder die Position einer Teilstrecke ändern. Die Entity-ID enthält denselben Verbindungsnamen und den von Home Assistant ergänzten Sensoranteil. Bei einem Wechsel des Namensschemas aktualisiert die Integration bestehende, automatisch erzeugte Entity-IDs anhand des früheren Routennamens. Home Assistant kann die Entity-ID bei Namenskollisionen mit einem Suffix ergänzen.

Neue Verbindungen werden beim nächsten erfolgreichen Abruf als Geräte und Sensoren ergänzt. Verbindungen, die in einer erfolgreichen API-Antwort nicht mehr enthalten sind, machen die dazugehörigen Entities nicht verfügbar. Einzelfahrten (`connectionType = one_time`) bleiben bis zum Ende der konfigurierten Aufbewahrungsfrist nach `serviceDate` in Home Assistant. Danach entfernt die Integration ihre drei Entities und das zugehörige Gerät aus den Home-Assistant-Registern. Der Standard beträgt sieben Tage; der Zeitraum kann in den Integrationseinstellungen zwischen einem und 365 Tagen eingestellt werden. Einzelfahrten mit ungültigem oder fehlendem `serviceDate` werden nicht automatisch gelöscht. Wöchentliche Verbindungen sind von dieser Bereinigung ausgenommen. Bei einem fehlgeschlagenen Abruf sind alle Verbindungs-Entities nicht verfügbar. Ein ungültiger oder widerrufener API-Schlüssel führt in den Wiederherstellungs-/Reauthentifizierungsablauf.

Bei jedem erfolgreichen Abruf gleicht die Integration den automatisch vergebenen Gerätenamen mit dem aktuellen Fahrplan-Namensschema ab. Das aktualisiert auch bereits vorhandene Registry-Einträge. Einen in Home Assistant manuell gesetzten Gerätenamen (`name_by_user`) lässt die Integration unverändert. Alte, automatisch aus dem früheren Routennamen erzeugte Entity-IDs werden auf das aktuelle Namensschema mit Abfahrtszeit und Wochentagen beziehungsweise Datum umgestellt. Benutzerdefinierte Entity-Namen bleiben erhalten. Die drei Sensorarten selbst bleiben `Status`, `Train` und `Delay`; zusätzliche Fahrplaninformationen stehen als gemeinsame Attribute dieser Sensoren zur Verfügung.

## Namensschema

Der Gerätename wird aus den Verbindungsfeldern in folgender Reihenfolge gebildet:

1. Startbahnhof, Pfeil `→`, Zielbahnhof.
2. ` · ` und planmäßige Abfahrtszeit `departureTime`, sofern vorhanden.
3. Bei wöchentlichen Verbindungen: ` · ` und die ausgewählten Wochentage in ISO-Reihenfolge, als `Mo`, `Di`, `Mi`, `Do`, `Fr`, `Sa`, `So`. Leere oder unbekannte Tageswerte werden ausgelassen.
4. Bei einmaligen Verbindungen (`connectionType = one_time`): ` · ` und `serviceDate`, sofern vorhanden; Wochentage werden in diesem Fall nicht angehängt.
5. Bei gruppierten Verbindungen: ` · Abschnitt ` und `groupPosition`, sofern es eine Ganzzahl ist.

Fehlt der Startbahnhof, wird `Unbekannter Start` verwendet; fehlt der Zielbahnhof, `Unbekanntes Ziel`. Ein fehlender Zeitwert, ein fehlendes Datum oder eine fehlende Wochentagsauswahl wird nicht durch einen Platzhalter ersetzt.

Die Sensoren verwenden Home Assistants Entity-Namensschema (`has_entity_name`). Daher setzt sich der sichtbare Sensorname aus dem Gerätenamen und dem übersetzten Sensornamen zusammen. Die mitgelieferte Übersetzungsdatei benennt die Sensoren derzeit **Status**, **Train** und **Delay**. Die Übersetzungen werden von Home Assistant entsprechend der eingestellten Sprache verwendet. Die Spracheinstellung ändert nicht die Sensor-Schlüssel oder ihre Funktion.

## Sensoren und Zustände

| Entity-Schlüssel | Anzeigename (mitgelieferte Übersetzung) | Wert und Quelle | Einheit |
|---|---|---|---|
| `status` | Status | `status.status`; wenn das Feld im Monitorobjekt fehlt, `waiting` | keine |
| `train` | Train | `status.train`; leerer oder fehlender Wert wird als unbekannter Sensorwert (`None`) dargestellt | keine |
| `delay` | Delay | `status.delayMinutes`; wird nur als numerischer Wert ausgegeben, sonst unbekannter Sensorwert (`None`) | `min` |

`Status` ist ein Monitorzustand und kein Zugstatus im Sinne einer Garantie, dass der Zug fährt oder pünktlich ist. Die API kann unter anderem die folgenden Codes liefern:

| Statuscode | Bedeutung |
|---|---|
| `waiting` | Noch kein Monitorergebnis für diese Verbindung gespeichert. |
| `outside_window` | Die aktuelle Abfrage liegt außerhalb des Zeitfensters, in dem die Fahrt konkret zugeordnet werden kann. |
| `inactive_day` | Der heutige Wochentag beziehungsweise das Datum ist für diese Verbindung nicht ausgewählt. |
| `selection_required` | Die Fahrt ist nicht eindeutig zugeordnet; eine manuelle Auswahl ist erforderlich oder erneut erforderlich. Wenn vorhanden, enthält der Status Kandidaten. |
| `selection_saved` | Eine manuelle Fahrtauswahl wurde gespeichert und wird beim nächsten Datenabruf geprüft. |
| `unmatched` | Im geeigneten Zeitfenster wurde keine passende Fahrt und kein Kandidat gefunden. |
| `matched` | Eine passende Fahrt ist zugeordnet; es wurde keine relevante Änderung gemeldet. |
| `changed` | Eine passende Fahrt ist zugeordnet und es liegt eine relevante Änderung vor. |
| `unavailable` | Die Fahrplandatenquelle oder der zugehörige Abruf war nicht verfügbar. |
| `not_checked` | Die Quelle konnte wegen fehlender Stationskonfiguration nicht abgefragt werden. |
| `configuration_error` | Die Quellenkonfiguration verhindert eine Abfrage. |

Die Statuscodes sind Zeichenketten aus der API. Statusmeldungen und weitere Details stehen in den Attributen `status_message` und `monitor_status`. Der Sensor `Train` ist die von der API zugeordnete Zugbezeichnung, kein eigener Fahrplandatensatz. Der Sensor `Delay` spiegelt ausschließlich ein numerisches Feld `delayMinutes` wider. Die aktuelle Monitorimplementierung liefert bei zugeordneten Fahrten derzeit keine Verspätungsprognose; es wird insbesondere keine Verspätung aus `plannedDeparture`, Fahrplanzeiten oder Historie abgeleitet. Deshalb kann der Sensor `Delay` unbekannt sein, obwohl die Fahrt bereits zugeordnet wurde.

## Entity-Attribute

Die folgenden Attribute stehen auf jedem der drei Sensoren zur Verfügung. Die Integration übernimmt zuerst alle Felder der API-Verbindung unverändert (einschließlich der ursprünglichen Schreibweise) und ergänzt danach die unten aufgeführten normalisierten Aliase. Ein Alias mit Wert `null` bleibt als Attribut vorhanden, wenn die Integrationslogik ihn explizit ergänzt. API-Felder, die fehlen, können beim unveränderten Durchreichen fehlen. Die API kann ihre Antwort in zukünftigen Versionen erweitern.

### Verbindungs- und Fahrplandaten

| API-Feld (unverändert) | Zusätzliches Attribut | Bedeutung und Verfügbarkeit |
|---|---|---|
| `id` | `connection_id` | TrainTrack-ID der einzelnen Verbindung. Als `connection_id` wird sie als Zeichenkette ausgegeben. |
| `origin` | — | Startbahnhof. |
| `destination` | — | Zielbahnhof. |
| `departureTime` | `departure_time` | Planmäßige Abfahrtszeit der überwachten Verbindung. |
| `arrivalTimesByWeekday` | `arrival_times_by_weekday` | Zu erwartende Ankunftszeiten nach ISO-Wochentag. Kann fehlen, wenn keine Werte gespeichert sind; der Alias fällt dann auf ein leeres Objekt zurück. |
| `weekdays` | — | Ausgewählte Wochentage als ISO-Zahlen 1 bis 7 (Montag bis Sonntag). Bei einmaligen Verbindungen nicht die maßgebliche Datumsangabe. |
| `connectionType` | `connection_type` | Verbindungstyp. Wenn im Alias nicht geliefert, verwendet die Integration `weekly` als Standard. Für einmalige Verbindungen ist der API-Wert `one_time`. |
| `serviceDate` | `service_date` | Betriebstag einer einmaligen Verbindung. Bei wöchentlichen Verbindungen üblicherweise leer. |
| `groupId` | — | Gemeinsame Gruppen-ID, falls diese Verbindung Teil einer mehrteiligen beziehungsweise gruppierten Verbindung ist. |
| `groupPosition` | `group_position` | Position dieser Verbindung in einer Gruppe, falls vorhanden. |
| `transferFromPrevious` | `transfer_from_previous` | Umstiegs-/Transferinformation vor diesem Abschnitt; beim ersten Abschnitt üblicherweise leer. |
| `createdAt` | — | Zeitstempel der Erstellung in TrainTrack. |
| `manualSelection` | `manual_selection` | Gespeicherte manuelle Fahrtauswahl oder `null`. Die Auswahl ist ein Objekt mit den Feldern `key` (stabile Auswahlkennung), `train` (Zugbezeichnung), `departure` (ausgewählte Abfahrtszeit) und `path` (Liste der Zielwegpunkte). Die API-Datenstruktur wird unverändert weitergegeben. |
| `historicalContext` | `historical_context` | Aggregierter historischer Kontext, sofern TrainTrack ihn für die Verbindung berechnet und zurückgibt. Die Struktur steht unten. |
| `observations` | `observations` | Beobachtungen früher zugeordneter Abfahrten für dieselbe Strecke und Abfahrtszeit. Standardwert ist ein leeres Array. |
| `history` | `history` | Änderungshistorie der Verbindung, sofern die API sie zurückgibt. Der Alias fällt auf ein leeres Array zurück. |

Der Alias `route` enthält den vollständigen, nach demselben Namensschema wie das Gerät formatierten Routennamen. Er ist ein Anzeigename und kein zusätzliches API-Identifikationsfeld.

### Monitorstatus und Fahrtdetails

| API-Feld innerhalb von `status` | Zusätzliches Attribut | Bedeutung und Verfügbarkeit |
|---|---|---|
| `status` | `status_code` | Statuscode, der zugleich den Sensorzustand `Status` bildet. |
| `message` | `status_message` | Menschenlesbare Erläuterung des aktuellen Monitorzustands. |
| `train` | `train` | Zugeordnete Zugbezeichnung; zugleich Sensorzustand `Train`. |
| `delayMinutes` | `delay_minutes` | Numerische Verspätung in Minuten, falls von der API geliefert; zugleich Sensorzustand `Delay`. |
| `checkedAt` | `checked_at` | Zeitpunkt, zu dem TrainTrack den Verbindungsstatus zuletzt ermittelt hat. Dieser Quell-/Monitorzeitpunkt ist unabhängig vom späteren Home-Assistant-Abrufzeitpunkt. |
| `operatingDate` | `operating_date` | Betriebstag der zugeordneten Fahrt. |
| `tripId` | `trip_id` | Kennung der zugeordneten Fahrt in der Fahrplandatenquelle. |
| `plannedDeparture` | `planned_departure` | Abfahrtszeit der konkret zugeordneten Fahrt aus dem Plan. Sie kann von den in TrainTrack gespeicherten Sollangaben abweichen. |
| `plannedPlatform` | `planned_platform` | Im Plan angegebener Bahnsteig, sofern bekannt. |
| `changeStation` | `change_station` | Bahnhof, an dem eine gemeldete Änderung festgestellt wurde. |
| `changeDetails` | `change_details` | Liste von Änderungstexten, standardmäßig leeres Array. |
| `urgency` | `urgency` | Von TrainTrack bereitgestufte Dringlichkeit, sofern verfügbar. Für zugeordnete Fahrten verwendet TrainTrack `normal`, `elevated` oder `high`. |
| `precedingAffectedDepartures` | `preceding_affected_departures` | Zahl früherer betroffener Abfahrten auf derselben Strecke; Alias-Standardwert ist `0`. |
| `candidateCount` | — | Anzahl der angebotenen Auswahlkandidaten, wenn eine manuelle Auswahl erforderlich ist. |
| `candidates` | — | Kandidatenliste, wenn eine manuelle Auswahl erforderlich ist. Die vom Monitor erzeugten Kandidaten enthalten `key` (Auswahlkennung), `departure` (Abfahrtszeit), `train` (Zugbezeichnung), `path` (Wegpunkte als Liste) und `platform` (Bahnsteig oder `null`). |

Das vollständige originale `status`-Objekt ist zusätzlich im Attribut `status` enthalten. Der Alias `monitor_status` enthält dasselbe Objekt. Beide behalten die originalen API-Feldnamen und eventuell künftig ergänzte Statusfelder. Die Tabelle beschreibt die aktuell vom TrainTrack-Monitor erzeugten Felder; bei Zuständen ohne zugeordnete Fahrt sind Fahrt-, Bahnsteig- und Änderungsfelder häufig nicht vorhanden.

### Historischer Kontext

`historicalContext` / `historical_context` wird nur geliefert, wenn passende vergangene Beobachtungen vorhanden sind. Es bezieht sich auf dieselbe Start-Ziel-Verbindung und Abfahrtszeit sowie passende Wochentage. Es enthält:

| Feld | Bedeutung |
|---|---|
| `lookbackDays` | Länge des betrachteten Rückblickzeitraums in Tagen. |
| `observedDepartures` | Anzahl der in diesem Zeitraum beobachteten passenden Abfahrten. |
| `departuresWithReportedChanges` | Anzahl der beobachteten Abfahrten, für die Änderungen gemeldet wurden. |
| `byWeekday` | Aufschlüsselung nach Wochentag. Jeder Eintrag enthält `weekday` (ISO 1–7), `observedDepartures` und `departuresWithReportedChanges`. |

Diese Statistik beschreibt beobachtete frühere Meldungen. Sie ist keine Verspätungsprognose und bedeutet nicht, dass eine künftige Fahrt betroffen sein wird.

### Beobachtungen

Jeder Eintrag in `observations` beschreibt eine konkret beobachtete Fahrt für dieselbe Strecke und Abfahrtszeit. Enthaltene Felder umfassen:

| Feld | Bedeutung |
|---|---|
| `operatingDate` | Betriebstag der beobachteten Fahrt. |
| `departureTime` | Planmäßige Abfahrtszeit der Verbindung. |
| `tripId` | ID der beobachteten Fahrt. |
| `observedAt` | Zeitpunkt der Beobachtung durch TrainTrack. |
| `status` | Beim Ereignis gespeicherter Monitorstatus, sofern vorhanden. |
| `changeReported` | Boolescher Wert, ob für diese Fahrt eine Änderung gemeldet wurde. |
| `changeDetails` | Änderungstexte, wenn solche protokolliert wurden. |
| `changeStation` | Bahnhof der Änderung, wenn übermittelt. |

Zusätzliche beim Monitorereignis gespeicherte API-Felder werden ebenfalls unverändert übernommen. Die Liste kann leer sein. Sie ist eine historische Beobachtungsliste und nicht mit dem aktuellen Statusobjekt gleichzusetzen.

### Änderungshistorie

`history` ist eine nach Beobachtungszeit absteigend sortierte Liste neu erkannter, relevanter Monitoränderungen für die Verbindung. Ein Eintrag enthält die Ereigniszeit `observedAt` und die gespeicherten Statusdaten, insbesondere `status`, `message` und – wenn die Fahrt zugeordnet wurde – Fahrtdetails wie `tripId`, `train`, `plannedDeparture`, `plannedPlatform`, `changeStation`, `changeDetails`, `urgency` und `precedingAffectedDepartures`. Ein Eintrag kann je nach Ereignis nur eine Teilmenge dieser Felder enthalten. TrainTrack speichert keine erneuten Historieneinträge für einen unveränderten Zustand. Wenn die API für die Verbindung keine Historie mitsendet, existiert das rohe Feld `history` nicht; der Alias `history` in Home Assistant ist dann eine leere Liste.

## Zeitbezug und Abrufverhalten

Die Entity-Zustände und -Attribute spiegeln die letzte erfolgreiche Antwort der Verbindungen-API wider. Home Assistant fragt diese API im einstellbaren Intervall erneut ab. `checked_at` stammt aus TrainTracks Monitorlauf und bezeichnet den Zeitpunkt der fachlichen Prüfung. Er ist nicht der Zeitpunkt, an dem Home Assistant die Antwort abgerufen hat. `createdAt`, `checkedAt`, `observedAt`, `operatingDate`, `plannedDeparture` und die gespeicherten Abfahrts-/Ankunftszeiten sind unterschiedliche Zeitangaben und dürfen nicht gleichgesetzt werden.

Fällt die TrainTrack-API aus oder liefert sie eine ungültige Antwort, markiert Home Assistant die Entities als nicht verfügbar. Das bedeutet nicht, dass der letzte zuvor gespeicherte Status sich fachlich geändert hat. Wird eine Verbindung bei einem erfolgreichen Abruf aus der Antwort entfernt, werden ihre Entities ebenfalls nicht verfügbar. Leere oder fehlende `train`-/`delayMinutes`-Daten bedeuten einen unbekannten Sensorwert, keine Nullverspätung.

## Versions- und Schemahinweis

Diese Dokumentation beschreibt die Daten, die der aktuelle TrainTrack-API-Vertrag und die aktuelle Integration verwenden. Die Integration reicht unbekannte API-Verbindungsfelder durch und bewahrt unbekannte Statusfelder im rohen `status`-/`monitor_status`-Objekt. Das erlaubt das Anzeigen ergänzender API-Daten, ersetzt aber keine künftige Dokumentationspflege, wenn TrainTrack Feldnamen, Bedeutungen oder Statuscodes ändert.
