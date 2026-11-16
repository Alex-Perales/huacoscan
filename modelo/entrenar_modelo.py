"""
Entrena el clasificador final (SVM kernel RBF, con probabilidad) y lo exporta
a modelo.joblib para que la pagina web (app.py) lo cargue sin reentrenar.

Usa el mismo vector de caracteristicas (LBP + HoG, 1818 valores) ya calculado
en TODO_AVANCE/salidas/caracteristicas.npz por Parte1_EstracciónCaracteristicas.ipynb.

A diferencia del notebook de evaluacion (que separa 80/20 para comparar
modelos), aqui el modelo final se entrena con el 100% de los datos
disponibles, porque el objetivo ya no es medir, sino entregar el mejor
clasificador posible para produccion.

El umbral de confianza para la categoria "Otro" (UMBRAL_OTRO) se eligio
evaluando el modelo en un 80/20: con 0.40, ~6% de las piezas de prueba caen
por debajo del umbral y ~69% de esas eran justo los casos que el modelo
clasificaba mal, asi que es un punto razonable para decir "no estoy seguro".
"""
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

RAIZ = Path(__file__).resolve().parent.parent.parent  # TODO_AVANCE/
RUTA_CARACTERISTICAS = RAIZ / "salidas" / "caracteristicas.npz"
RUTA_SALIDA = Path(__file__).resolve().parent / "modelo.joblib"

SEMILLA = 42
UMBRAL_OTRO = 0.40


def main():
    datos = np.load(RUTA_CARACTERISTICAS)
    X, y, clases = datos["X"], datos["y"], list(datos["clases"])
    print("X:", X.shape, "clases:", clases)

    escalador = StandardScaler()
    X_esc = escalador.fit_transform(X)

    svm = SVC(kernel="rbf", probability=True, random_state=SEMILLA)
    svm.fit(X_esc, y)
    print("Modelo entrenado con el 100% de los datos:", X.shape[0], "piezas")

    joblib.dump(
        {
            "svm": svm,
            "escalador": escalador,
            "clases": clases,
            "umbral_otro": UMBRAL_OTRO,
        },
        RUTA_SALIDA,
    )
    print("Guardado en:", RUTA_SALIDA)


if __name__ == "__main__":
    main()
