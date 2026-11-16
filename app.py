"""
Clasificador de Culturas Precolombinas - backend Flask.

Sirve la pagina (templates/index.html) y el endpoint /api/clasificar, que
recibe una imagen (subida o un frame de la camara), la pasa por el mismo
pipeline de preprocesamiento + LBP/HoG de Parte1_EstracciónCaracteristicas.ipynb
y la clasifica con el SVM entrenado en Parte2_Clasificacion.ipynb
(ver modelo/entrenar_modelo.py).
"""
import base64
import json
import mimetypes
from pathlib import Path

import cv2 as cv
import joblib
import numpy as np
from flask import Flask, jsonify, render_template, request

from modelo import pipeline

RAIZ = Path(__file__).resolve().parent
RUTA_MODELO = RAIZ / "modelo" / "modelo.joblib"
RUTA_CULTURAS = RAIZ / "modelo" / "culturas.json"

LADO_MAX_ENTRADA = 700  # redimensiona fotos/frames grandes antes de segmentar, para que sea rapido

mimetypes.add_type("image/webp", ".webp")

app = Flask(__name__)

if not RUTA_MODELO.exists():
    raise RuntimeError(
        f"No se encontro {RUTA_MODELO}. Corre primero: python modelo/entrenar_modelo.py"
    )

_modelo = joblib.load(RUTA_MODELO)
SVM = _modelo["svm"]
ESCALADOR = _modelo["escalador"]
CLASES = _modelo["clases"]
UMBRAL_OTRO = _modelo["umbral_otro"]

with open(RUTA_CULTURAS, encoding="utf-8") as f:
    CULTURAS = json.load(f)

# Nombre corto para mostrar en chips/etiquetas (la clave interna no lleva tildes
# porque viene de los nombres de carpeta de la base de datos).
ETIQUETAS = {
    "Chancay": "Chancay",
    "Chimu": "Chimú",
    "Huari_Norteno": "Huari Norteño",
    "Inca": "Inca",
    "Lambayeque": "Lambayeque",
    "Mochica": "Mochica",
    "Nasca": "Nasca",
    "Otro": "Otro",
}


def decodificar_imagen(imagen_base64: str):
    if "," in imagen_base64:
        imagen_base64 = imagen_base64.split(",", 1)[1]
    datos = base64.b64decode(imagen_base64)
    arreglo = np.frombuffer(datos, dtype=np.uint8)
    img = cv.imdecode(arreglo, cv.IMREAD_COLOR)
    if img is None:
        raise ValueError("No se pudo leer la imagen enviada")

    alto, ancho = img.shape[:2]
    lado_mayor = max(alto, ancho)
    if lado_mayor > LADO_MAX_ENTRADA:
        escala = LADO_MAX_ENTRADA / lado_mayor
        img = cv.resize(img, (int(ancho * escala), int(alto * escala)))
    return img


@app.route("/")
def index():
    return render_template(
        "index.html", culturas=CULTURAS, clases=CLASES, etiquetas=ETIQUETAS
    )


@app.route("/api/clasificar", methods=["POST"])
def clasificar():
    cuerpo = request.get_json(silent=True) or {}
    imagen_base64 = cuerpo.get("imagen")
    if not imagen_base64:
        return jsonify({"error": "No se envio ninguna imagen"}), 400

    try:
        img = decodificar_imagen(imagen_base64)
    except Exception:
        return jsonify({"error": "Imagen invalida"}), 400

    vector, fraccion, bbox = pipeline.extraer_caracteristicas(img)

    # Fraccion de pieza casi nula: no se detecto nada parecido a un objeto solido.
    if fraccion < 0.01:
        return jsonify(
            {
                "cultura": None,
                "es_otro": True,
                "confianza": 0.0,
                "bbox": {"x": bbox[0], "y": bbox[1], "w": bbox[2], "h": bbox[3]},
                "fraccion_pieza": round(float(fraccion), 3),
                "info": None,
            }
        )

    vector_esc = ESCALADOR.transform([vector])
    probabilidades = SVM.predict_proba(vector_esc)[0]
    idx = int(np.argmax(probabilidades))
    confianza = float(probabilidades[idx])
    cultura = CLASES[idx]
    es_otro = confianza < UMBRAL_OTRO

    return jsonify(
        {
            "cultura": cultura,
            "etiqueta": ETIQUETAS.get(cultura, cultura),
            "es_otro": bool(es_otro),
            "confianza": round(confianza, 3),
            "bbox": {"x": bbox[0], "y": bbox[1], "w": bbox[2], "h": bbox[3]},
            "fraccion_pieza": round(float(fraccion), 3),
            "info": None if es_otro else CULTURAS.get(cultura),
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
