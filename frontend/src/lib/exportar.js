// Genera el PDF y el Excel de un reporte, con encabezado, pie, letra y colores propios.
// Las librerías se cargan solo cuando se exporta (no pesan al abrir la app).

const MARINO = [11, 31, 58]; // #0b1f3a
const AMARILLO = [243, 185, 69]; // #f3b945
const GRIS_FILA = [245, 247, 251];
const GRIS_TEXTO = [107, 123, 145];

const AHORA = () =>
  new Date().toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' });

/** datos = { titulo, columnas, filas, filtros, usuario } */
export async function crearPDF({ titulo, columnas, filas, filtros, usuario }) {
  const { jsPDF } = await import('jspdf');
  const autoTable = (await import('jspdf-autotable')).default;

  const doc = new jsPDF({
    orientation: columnas.length > 5 ? 'landscape' : 'portrait',
    unit: 'pt',
    format: 'a4'
  });
  const ancho = doc.internal.pageSize.getWidth();
  const alto = doc.internal.pageSize.getHeight();
  const generado = AHORA();

  // Encabezado (se dibuja en todas las páginas).
  const cabecera = () => {
    doc.setFillColor(...MARINO);
    doc.rect(0, 0, ancho, 64, 'F');
    doc.setFillColor(...AMARILLO);
    doc.rect(0, 64, ancho, 4, 'F');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(16);
    doc.setTextColor(255, 255, 255);
    doc.text('Gestión de Transporte Escolar', 40, 30);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(11);
    doc.setTextColor(...AMARILLO);
    doc.text(titulo, 40, 50);
    doc.setFontSize(9);
    doc.setTextColor(255, 255, 255);
    doc.text(generado, ancho - 40, 30, { align: 'right' });
    doc.setTextColor(...GRIS_TEXTO);
    doc.text(`Filtros: ${filtros}`, 40, 88, { maxWidth: ancho - 80 });
  };

  autoTable(doc, {
    head: [columnas],
    body: filas,
    foot: [[{ content: `Total de registros: ${filas.length}`, colSpan: columnas.length, styles: { halign: 'right' } }]],
    margin: { top: 104, left: 40, right: 40, bottom: 56 },
    styles: { font: 'helvetica', fontSize: 8.5, cellPadding: 5, textColor: [27, 42, 65] },
    headStyles: { fillColor: MARINO, textColor: 255, fontStyle: 'bold' },
    footStyles: { fillColor: GRIS_FILA, textColor: MARINO, fontStyle: 'bold' },
    alternateRowStyles: { fillColor: GRIS_FILA },
    showFoot: 'lastPage',
    didDrawPage: cabecera
  });

  // Pie de página con número de página.
  const paginas = doc.getNumberOfPages();
  for (let i = 1; i <= paginas; i++) {
    doc.setPage(i);
    doc.setDrawColor(...AMARILLO);
    doc.setLineWidth(1.2);
    doc.line(40, alto - 40, ancho - 40, alto - 40);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(...GRIS_TEXTO);
    doc.text(`Generado por ${usuario} · ${generado}`, 40, alto - 26);
    doc.text(`Página ${i} de ${paginas}`, ancho - 40, alto - 26, { align: 'right' });
  }

  return doc.output('blob');
}

/** Mismos datos que el PDF, en un libro de Excel con formato. */
export async function crearExcel({ titulo, columnas, filas, filtros, usuario }) {
  const ExcelJS = (await import('exceljs')).default;
  const libro = new ExcelJS.Workbook();
  libro.creator = 'Gestión de Transporte Escolar';
  libro.created = new Date();

  const hoja = libro.addWorksheet('Reporte', {
    views: [{ state: 'frozen', ySplit: 5 }],
    pageSetup: { orientation: 'landscape', fitToPage: true, fitToWidth: 1, fitToHeight: 0 }
  });
  hoja.headerFooter.oddFooter = '&LGestión de Transporte Escolar&RPágina &P de &N';

  const n = columnas.length;
  hoja.columns = columnas.map((nombre, i) => ({
    width: Math.min(
      45,
      Math.max(13, nombre.length + 4, ...filas.map((f) => String(f[i] ?? '').length + 2))
    )
  }));

  const borde = { style: 'thin', color: { argb: 'FFDCE3ED' } };
  const bordes = { top: borde, left: borde, bottom: borde, right: borde };
  const relleno = (argb) => ({ type: 'pattern', pattern: 'solid', fgColor: { argb } });

  const filaTexto = (numero, texto, estilo) => {
    hoja.mergeCells(numero, 1, numero, n);
    const celda = hoja.getCell(numero, 1);
    celda.value = texto;
    celda.alignment = { vertical: 'middle', horizontal: 'left' };
    Object.assign(celda, estilo);
  };

  filaTexto(1, 'Gestión de Transporte Escolar', {
    font: { name: 'Calibri', size: 16, bold: true, color: { argb: 'FFFFFFFF' } },
    fill: relleno('FF0B1F3A')
  });
  hoja.getRow(1).height = 28;
  filaTexto(2, titulo, {
    font: { name: 'Calibri', size: 12, bold: true, color: { argb: 'FF0B1F3A' } },
    fill: relleno('FFF3B945')
  });
  filaTexto(3, `Filtros: ${filtros}`, {
    font: { name: 'Calibri', size: 10, italic: true, color: { argb: 'FF6B7B91' } }
  });
  filaTexto(4, `Generado por ${usuario} · ${AHORA()}`, {
    font: { name: 'Calibri', size: 10, color: { argb: 'FF6B7B91' } }
  });

  const cabecera = hoja.addRow(columnas);
  cabecera.height = 22;
  cabecera.eachCell((celda) => {
    celda.font = { name: 'Calibri', size: 11, bold: true, color: { argb: 'FFFFFFFF' } };
    celda.fill = relleno('FF0B1F3A');
    celda.alignment = { vertical: 'middle', horizontal: 'center', wrapText: true };
    celda.border = bordes;
  });

  filas.forEach((fila, i) => {
    const r = hoja.addRow(fila);
    r.eachCell({ includeEmpty: true }, (celda) => {
      celda.font = { name: 'Calibri', size: 10 };
      celda.alignment = { vertical: 'middle', wrapText: true };
      celda.border = bordes;
      if (i % 2 === 1) celda.fill = relleno('FFF5F7FB');
    });
  });

  const total = hoja.addRow([`Total de registros: ${filas.length}`]);
  hoja.mergeCells(total.number, 1, total.number, n);
  total.getCell(1).font = { name: 'Calibri', size: 11, bold: true, color: { argb: 'FF0B1F3A' } };
  total.getCell(1).alignment = { horizontal: 'right' };

  const buffer = await libro.xlsx.writeBuffer();
  return new Blob([buffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  });
}

/** Descarga un Blob como archivo. */
export function descargar(blob, nombre) {
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement('a');
  enlace.href = url;
  enlace.download = nombre;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Convierte un Blob a texto base64 (para enviarlo por correo). */
export function aBase64(blob) {
  return new Promise((resolver, rechazar) => {
    const lector = new FileReader();
    lector.onload = () => resolver(String(lector.result).split(',')[1]);
    lector.onerror = () => rechazar(new Error('No se pudo leer el archivo.'));
    lector.readAsDataURL(blob);
  });
}
