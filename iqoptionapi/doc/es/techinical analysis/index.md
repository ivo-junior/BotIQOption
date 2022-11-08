## Tecnical analysis

Está disponible en los assets que puedes comprobar en "asset info":

![asset Info](image/info.jpg)

Si hay una sesión como esta tu puedes obtener los datos

NOTA: Si no hay análisis técnico en el asset que tu quieres, no podrás uarlo

![techinical Analysis menu](image/technical-analysis.jpg)

Hay algunos indicadores disponibles

## Pivotes

![Pivots](image/pivots.JPG)

## Osciladores

![Oscillators](image/Oscillators.JPG)

## Promedioss móviles

![Moving Averages](image/Oscillators.JPG)

## Cómo usar:

```python

asset="GBPUSD"
indicators = Iq.get_technical_indicators(asset)
print(indicators)

```
Si el asset no contiene el análisis técnico, devolverá:

```
{
  "code": "no_technical_indicator_available",
  "message": "Active is not supported: active id 'ACTIVE_ID_PASSED'"
}
```
Si lo contiene, devolverá algo parecido a esto:

NOTA: DEBE ANALIZAR EL CONTENIDO QUE SE IMPRIME

```json
[
  {
    "action": "hold",
    "candle_size": 60,
    "group": "OSCILLATORS",
    "name": "Relative Strength Index (14)",
    "value": 59.168583
  },
  {
    "action": "hold",
    "candle_size": 60,
    "group": "PIVOTS",
    "name": "Classic s3",
    "value": 1.057292
  }
  .....
]
```
