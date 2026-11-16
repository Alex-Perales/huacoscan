# ColibriScan &mdash; Clasificador de Culturas Precolombinas

Pagina web (Flask + HTML/CSS/JS, sin frameworks pesados) que clasifica ceramica
precolombina peruana en 7 culturas (Chancay, Chimu, Huari Norteno, Inca,
Lambayeque, Mochica, Nasca) o "Otro", subiendo una foto o usando la camara en
vivo. Usa el mismo pipeline de preprocesamiento (segmentacion + LBP/HoG) y el
modelo SVM entrenados en `TODO_AVANCE/Parte1_EstracciónCaracteristicas.ipynb`
y `TODO_AVANCE/Parte2_Clasificacion.ipynb`.

## Instalar y correr

```bash
pip install -r requirements.txt

# Solo la primera vez (o si TODO_AVANCE/salidas/caracteristicas.npz cambia):
python modelo/entrenar_modelo.py

python app.py
```

Abrir http://localhost:5000

## Estructura

- `app.py` — servidor Flask y endpoint `/api/clasificar`.
- `modelo/pipeline.py` — preprocesamiento + extraccion LBP/HoG (igual al notebook de Parte 1).
- `modelo/entrenar_modelo.py` — entrena y exporta el SVM final (`modelo.joblib`).
- `modelo/culturas.json` — texto descriptivo de cada cultura.
- `templates/index.html`, `static/` — interfaz (subida de imagen, camara en vivo con recuadro de deteccion, vista de culturas).
