// Clasificador de Culturas Precolombinas - logica de interfaz (subida, camara, resultado)

const el = (id) => document.getElementById(id);

const vistaClasificador = el('vista-clasificador');
const vistaCulturas = el('vista-culturas');
const btnIrClasificador = el('btn-ir-clasificador');
const btnIrCulturas = el('btn-ir-culturas');

const inputArchivo = el('input-archivo');
const btnSubir = el('btn-subir');
const btnCamara = el('btn-camara');
const textoBtnCamara = el('texto-btn-camara');
const controlesCamara = el('controles-camara');
const btnVoltear = el('btn-voltear');
const btnCerrarCamara = el('btn-cerrar-camara');
const errorCamara = el('error-camara');

const cajaPreview = el('caja-preview');
const video = el('video');
const imagenSubida = el('imagen-subida');
const imagenDefault = el('imagen-default');
const etiquetaPreview = el('etiqueta-preview');
const canvasCaptura = el('canvas-captura');

const tarjetaResultado = el('tarjeta-resultado');
const resultadoImagen = el('resultado-imagen');
const resultadoCultura = el('resultado-cultura');
const resultadoConfianza = el('resultado-confianza');
const resultadoDescripcion = el('resultado-descripcion');
const resultadoRasgos = el('resultado-rasgos');

let stream = null;
let isCameraActive = false;
let facingMode = 'environment';

// El recuadro de deteccion se calcula en % sobre el frame nativo (video.videoWidth
// x videoHeight). Si el contenedor se queda con su aspect-ratio fijo (4:3) y el
// video real es, por ejemplo, 16:9, "object-fit: cover" recorta la imagen y el
// recuadro queda desalineado. Por eso el contenedor ajusta su aspect-ratio al
// tamano real del video/imagen apenas se conoce, para que no haya recorte.
function ajustarAspecto(ancho, alto) {
  if (ancho && alto) cajaPreview.style.aspectRatio = `${ancho} / ${alto}`;
}
video.addEventListener('loadedmetadata', () => ajustarAspecto(video.videoWidth, video.videoHeight));
imagenSubida.addEventListener('load', () => ajustarAspecto(imagenSubida.naturalWidth, imagenSubida.naturalHeight));

// ---------------- Navegacion entre vistas ----------------
function irAClasificador() {
  vistaClasificador.classList.remove('oculto');
  vistaCulturas.classList.add('oculto');
  btnIrClasificador.classList.add('es-activo');
  btnIrCulturas.classList.remove('es-activo');
}

function irACulturas(scrollId) {
  detenerCamara();
  vistaCulturas.classList.remove('oculto');
  vistaClasificador.classList.add('oculto');
  btnIrCulturas.classList.add('es-activo');
  btnIrClasificador.classList.remove('es-activo');
  if (scrollId) {
    const destino = document.getElementById(scrollId);
    if (destino) destino.scrollIntoView({ behavior: 'smooth', block: 'center' });
  } else {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

btnIrClasificador.addEventListener('click', irAClasificador);
btnIrCulturas.addEventListener('click', () => irACulturas(null));

// ---------------- Camara ----------------
async function iniciarCamara() {
  errorCamara.classList.add('oculto');
  try {
    if (stream) detenerStream();
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode, width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
    video.srcObject = stream;
    await video.play();

    isCameraActive = true;
    video.classList.remove('oculto');
    imagenSubida.classList.add('oculto');
    imagenDefault.classList.add('oculto');
    etiquetaPreview.classList.add('oculto');

    textoBtnCamara.textContent = 'Capturar foto';
    controlesCamara.classList.remove('oculto');
  } catch (err) {
    console.warn('No se pudo acceder a la camara:', err);
    errorCamara.textContent = 'No se pudo acceder a la camara. Revisa los permisos del navegador.';
    errorCamara.classList.remove('oculto');
    isCameraActive = false;
  }
}

function detenerStream() {
  if (stream) {
    stream.getTracks().forEach((t) => t.stop());
    stream = null;
  }
}

function detenerCamara() {
  detenerStream();
  isCameraActive = false;
  video.classList.add('oculto');
  controlesCamara.classList.add('oculto');
  textoBtnCamara.textContent = 'Usar camara';
  if (imagenSubida.classList.contains('oculto')) {
    imagenDefault.classList.remove('oculto');
    etiquetaPreview.classList.remove('oculto');
  }
}

btnCamara.addEventListener('click', () => {
  if (!isCameraActive) {
    iniciarCamara();
  } else {
    capturarFotoFinal();
  }
});

btnCerrarCamara.addEventListener('click', detenerCamara);

btnVoltear.addEventListener('click', async () => {
  facingMode = facingMode === 'environment' ? 'user' : 'environment';
  if (isCameraActive) {
    detenerStream();
    await iniciarCamara();
  }
});

function capturarFrameComoDataURL() {
  const ancho = video.videoWidth || 640;
  const alto = video.videoHeight || 480;
  canvasCaptura.width = ancho;
  canvasCaptura.height = alto;
  const ctx = canvasCaptura.getContext('2d');
  ctx.drawImage(video, 0, 0, ancho, alto);
  return canvasCaptura.toDataURL('image/jpeg', 0.88);
}

async function capturarFotoFinal() {
  const dataUrl = capturarFrameComoDataURL();
  detenerCamara();
  mostrarImagenEstatica(dataUrl);
  btnSubir.disabled = true;
  btnCamara.disabled = true;
  try {
    const resultado = await clasificar(dataUrl);
    renderizarResultado(dataUrl, resultado);
  } catch (err) {
    mostrarErrorClasificacion();
  } finally {
    btnSubir.disabled = false;
    btnCamara.disabled = false;
  }
}

// ---------------- Subida de archivo / arrastrar y soltar ----------------
btnSubir.addEventListener('click', () => {
  detenerCamara();
  inputArchivo.click();
});

inputArchivo.addEventListener('change', (e) => {
  const archivo = e.target.files && e.target.files[0];
  if (archivo) procesarArchivo(archivo);
  e.target.value = '';
});

const tarjetaUpload = document.querySelector('.tarjeta-upload');
tarjetaUpload.addEventListener('dragover', (e) => { e.preventDefault(); tarjetaUpload.classList.add('arrastrando'); });
tarjetaUpload.addEventListener('dragleave', () => tarjetaUpload.classList.remove('arrastrando'));
tarjetaUpload.addEventListener('drop', (e) => {
  e.preventDefault();
  tarjetaUpload.classList.remove('arrastrando');
  const archivo = e.dataTransfer.files && e.dataTransfer.files[0];
  if (archivo) procesarArchivo(archivo);
});

function procesarArchivo(archivo) {
  if (!archivo.type.startsWith('image/')) {
    alert('Por favor selecciona un archivo de imagen valido (JPG, PNG, WEBP).');
    return;
  }
  detenerCamara();
  const lector = new FileReader();
  lector.onload = async (e) => {
    const dataUrl = e.target.result;
    mostrarImagenEstatica(dataUrl);
    btnSubir.disabled = true;
    btnCamara.disabled = true;
    try {
      const resultado = await clasificar(dataUrl);
      renderizarResultado(dataUrl, resultado);
    } catch (err) {
      mostrarErrorClasificacion();
    } finally {
      btnSubir.disabled = false;
      btnCamara.disabled = false;
    }
  };
  lector.readAsDataURL(archivo);
}

function mostrarImagenEstatica(dataUrl) {
  imagenSubida.src = dataUrl;
  imagenSubida.classList.remove('oculto');
  imagenDefault.classList.add('oculto');
  etiquetaPreview.classList.add('oculto');
  video.classList.add('oculto');
}

// ---------------- Llamada al backend ----------------
async function clasificar(dataUrl) {
  const res = await fetch('/api/clasificar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ imagen: dataUrl }),
  });
  if (!res.ok) throw new Error('Error al clasificar la imagen');
  return res.json();
}

// ---------------- Tarjeta de resultado ----------------
function renderizarResultado(dataUrl, resultado) {
  tarjetaResultado.classList.remove('oculto');
  resultadoImagen.src = dataUrl;
  resultadoRasgos.innerHTML = '';

  if (resultado.es_otro || !resultado.cultura) {
    resultadoCultura.textContent = 'Otro';
    resultadoConfianza.textContent = `Confianza baja (${Math.round(resultado.confianza * 100)}%): no coincide con certeza con ninguna de las 7 culturas entrenadas.`;
    resultadoDescripcion.textContent = 'El modelo no esta seguro, o la pieza no pertenece a Chancay, Chimu, Huari Norteno, Inca, Lambayeque, Mochica o Nasca.';
  } else {
    const info = resultado.info || {};
    resultadoCultura.textContent = resultado.etiqueta || resultado.cultura;
    resultadoConfianza.textContent = `Confianza: ${Math.round(resultado.confianza * 100)}%`;
    resultadoDescripcion.textContent = info.resumen || '';
    (info.rasgos || []).forEach((rasgo) => {
      const div = document.createElement('div');
      div.textContent = `• ${rasgo}`;
      resultadoRasgos.appendChild(div);
    });
  }
  tarjetaResultado.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function mostrarErrorClasificacion() {
  tarjetaResultado.classList.remove('oculto');
  resultadoCultura.textContent = 'Error';
  resultadoConfianza.textContent = '';
  resultadoDescripcion.textContent = 'No se pudo clasificar la imagen. Intenta de nuevo.';
  resultadoRasgos.innerHTML = '';
}

// ---------------- Chips de categorias ----------------
document.querySelectorAll('.chip-categoria').forEach((chip) => {
  chip.addEventListener('click', () => {
    const cultura = chip.dataset.cultura;
    document.querySelectorAll('.chip-categoria').forEach((c) => c.classList.remove('es-activo'));
    chip.classList.add('es-activo');
    if (cultura === 'Otro') {
      irACulturas(null);
      return;
    }
    irACulturas(`cultura-${cultura}`);
  });
});

// ---------------- Culturas: abrir descripcion al click en la imagen ----------------
document.querySelectorAll('.tarjeta-cultura__imagen').forEach((imagen) => {
  imagen.addEventListener('click', () => {
    const detalles = imagen.closest('.tarjeta-cultura').querySelector('details');
    if (detalles) detalles.open = !detalles.open;
  });
});

// ---------------- Culturas: boton "Leer menos" al final ----------------
document.querySelectorAll('.tarjeta-cultura .toggle-cerrar').forEach((boton) => {
  boton.addEventListener('click', () => {
    boton.closest('details').open = false;
  });
});
