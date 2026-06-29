# MagicObject

## Klasse `MagicObject`

`@dataclass` –  Die dataclass ermöglicht uns das iterieren über die verschiedenen Objekte auf dem Förderband.

## Felder

| Feld | Typ | Beschreibung |
|---|---|---|
| `object_type` | `int` | Objekttyp (`0` = Unicorn, `1` = Cat) |
| `position` | `list[float]` | Position `[x, y, z]` in Meter |
| `ts` | `float` | Zeitstempel der Erkennung |

## Rücksprung zur [Dokumentation](../../documentation/documentation.md#43-position-prediction--datenhaltung)