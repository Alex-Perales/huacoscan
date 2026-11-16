"""
Preprocesamiento y extraccion de caracteristicas (LBP + HoG).

Es el mismo pipeline usado en Parte1_EstracciónCaracteristicas.ipynb, portado
a un modulo normal para poder reusarlo desde la pagina web (subida de imagen
y camara en vivo), sin depender del notebook.
"""
import cv2 as cv
import numpy as np
from skimage.feature import local_binary_pattern

TAM = 256          # lado de la imagen preprocesada
TAM_HOG = 128       # lado de la imagen que recibe HoG
ESCALAS_LBP = [(8, 1), (16, 2), (24, 3)]   # (P vecinos, R radio)


def region_fondo(img, tolerancia=2):
    suave = cv.GaussianBlur(img, (5, 5), 0)
    alto, ancho = suave.shape[:2]

    copia = suave.copy()
    marca = (0, 255, 0)

    semillas = []
    for x in range(0, ancho, 10):
        semillas.append((x, 0))
        semillas.append((x, alto - 1))
    for y in range(0, alto, 10):
        semillas.append((0, y))
        semillas.append((ancho - 1, y))

    for (x, y) in semillas:
        if tuple(copia[y, x]) != marca:
            cv.floodFill(copia, None, (x, y), marca, (tolerancia,) * 3, (tolerancia,) * 3)

    fondo = np.all(copia == marca, axis=2).astype(np.uint8) * 255
    return fondo


def mayor_contorno(mascara):
    contornos, _ = cv.findContours(mascara, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    limpia = np.zeros_like(mascara)
    if len(contornos) > 0:
        mayor = max(contornos, key=cv.contourArea)
        cv.drawContours(limpia, [mayor], -1, 255, -1)
    return limpia


def segmentar_pieza(img):
    alto, ancho = img.shape[:2]

    marcas = np.full((alto, ancho), cv.GC_PR_FGD, np.uint8)
    marcas[region_fondo(img, 2) > 0] = cv.GC_PR_BGD
    mx, my = int(ancho * 0.04), int(alto * 0.04)
    marcas[:my] = cv.GC_BGD
    marcas[-my:] = cv.GC_BGD
    marcas[:, :mx] = cv.GC_BGD
    marcas[:, -mx:] = cv.GC_BGD
    if np.count_nonzero(marcas == cv.GC_PR_FGD) < 50:
        return np.zeros((alto, ancho), np.uint8)

    modelo_fondo = np.zeros((1, 65), np.float64)
    modelo_pieza = np.zeros((1, 65), np.float64)
    cv.grabCut(img, marcas, None, modelo_fondo, modelo_pieza, 3, cv.GC_INIT_WITH_MASK)
    mascara = np.where((marcas == cv.GC_FGD) | (marcas == cv.GC_PR_FGD), 255, 0).astype(np.uint8)

    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5))
    mascara = cv.morphologyEx(mascara, cv.MORPH_OPEN, kernel)
    mascara = cv.morphologyEx(mascara, cv.MORPH_CLOSE, kernel)
    return mayor_contorno(mascara)


def quitar_fondo(img, mascara):
    resultado = img.copy()
    resultado[mascara == 0] = 0
    return resultado


def recortar_y_redimensionar(img, mascara, lado):
    x, y, w, h = cv.boundingRect(mascara)
    recorte = img[y:y + h, x:x + w]
    recorte_mascara = mascara[y:y + h, x:x + w]

    tam = max(w, h)
    cuadrada = np.zeros((tam, tam, 3), np.uint8)
    cuadrada_mascara = np.zeros((tam, tam), np.uint8)
    dy, dx = (tam - h) // 2, (tam - w) // 2
    cuadrada[dy:dy + h, dx:dx + w] = recorte
    cuadrada_mascara[dy:dy + h, dx:dx + w] = recorte_mascara

    pieza = cv.resize(cuadrada, (lado, lado))
    pieza_mascara = cv.resize(cuadrada_mascara, (lado, lado), interpolation=cv.INTER_NEAREST)
    return pieza, pieza_mascara


def preprocesar(img):
    mascara = segmentar_pieza(img)
    fraccion = (mascara > 0).sum() / mascara.size

    if fraccion == 0:
        mascara[:] = 255

    sin_fondo = quitar_fondo(img, mascara)
    pieza, pieza_mascara = recortar_y_redimensionar(sin_fondo, mascara, TAM)
    return pieza, pieza_mascara, fraccion, mascara


def extraer_lbp(gris, mascara):
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (7, 7))
    zona = cv.erode(mascara, kernel) > 0
    if not zona.any():
        zona = mascara > 0

    histogramas = []
    for (p, r) in ESCALAS_LBP:
        lbp = local_binary_pattern(gris, p, r, "uniform")
        hist, _ = np.histogram(lbp[zona], bins=p + 2, range=(0, p + 2))
        histogramas.append(hist / max(hist.sum(), 1))
    return np.concatenate(histogramas).astype(np.float32)


def extraer_hog(gris):
    chica = cv.resize(gris, (TAM_HOG, TAM_HOG), interpolation=cv.INTER_AREA)
    desc = cv.HOGDescriptor((TAM_HOG, TAM_HOG), (32, 32), (16, 16), (16, 16), 9)
    return desc.compute(chica).flatten()


def extraer_caracteristicas(img):
    """Devuelve (vector_caracteristicas, fraccion_pieza, bbox_normalizado).

    bbox_normalizado es (x, y, w, h) en fraccion [0, 1] de la imagen original,
    util para dibujar el recuadro de deteccion en la pagina web.
    """
    pieza, pieza_mascara, fraccion, mascara_original = preprocesar(img)
    gris = cv.cvtColor(pieza, cv.COLOR_BGR2GRAY)
    vector = np.concatenate([extraer_lbp(gris, pieza_mascara), extraer_hog(gris)])

    alto, ancho = mascara_original.shape[:2]
    x, y, w, h = cv.boundingRect(mascara_original)
    if w == 0 or h == 0:
        bbox = (0.0, 0.0, 1.0, 1.0)
    else:
        bbox = (x / ancho, y / alto, w / ancho, h / alto)

    return vector, fraccion, bbox
