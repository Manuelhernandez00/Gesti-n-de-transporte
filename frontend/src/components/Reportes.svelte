<script>
  import { onMount } from 'svelte';
  import { api, sesionGuardada } from '../lib/api.js';
  import { crearPDF, crearExcel, descargar, aBase64 } from '../lib/exportar.js';
  import EncabezadoPagina from './EncabezadoPagina.svelte';

  const usuario = sesionGuardada.leer()?.usuario?.nombre_completo ?? 'Usuario';
  const hoy = new Date();
  const iso = (d) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  const fmt = (texto) => texto.split('-').reverse().join('/');

  // Cada reporte tiene 3 criterios: rango de fechas, ruta y un filtro propio.
  const reportes = {
    abordajes: { nombre: 'Reporte de abordajes', etiquetaExtra: 'Tipo', clave: 'tipo' },
    ausencias: { nombre: 'Reporte de ausencias', etiquetaExtra: 'Atención', clave: 'atencion' }
  };

  let tipo = $state('abordajes');
  let desde = $state(`${hoy.getFullYear()}-01-01`);
  let hasta = $state(iso(hoy));
  let ruta = $state('');
  let extra = $state('');
  let opciones = $state({ rutas: [], tipos: [], atenciones: [] });

  let resultado = $state(null); // lo último que se visualizó
  let cargando = $state(false);
  let exportando = $state(false);
  let error = $state('');
  let aviso = $state('');

  let correoAbierto = $state(false);
  let destinatario = $state('');
  let formatoCorreo = $state('pdf');
  let enviando = $state(false);

  const config = $derived(reportes[tipo]);
  const opcionesExtra = $derived(tipo === 'abordajes' ? opciones.tipos : opciones.atenciones);

  onMount(async () => {
    try {
      opciones = await api.opcionesReporte();
    } catch (e) {
      error = e.message;
    }
  });

  function cambiarReporte() {
    extra = '';
    resultado = null;
    error = '';
    aviso = '';
  }

  function validar() {
    if (!desde || !hasta) return 'Elige el rango de fechas (desde y hasta).';
    if (desde > hasta) return 'La fecha inicial no puede ser mayor que la final.';
    return '';
  }

  function textoFiltros() {
    const nombreRuta = opciones.rutas.find((r) => String(r.id) === String(ruta))?.nombre ?? 'Todas';
    return `Del ${fmt(desde)} al ${fmt(hasta)} · Ruta: ${nombreRuta} · ${config.etiquetaExtra}: ${extra || 'Todos'}`;
  }

  async function visualizar() {
    error = '';
    aviso = '';
    const problema = validar();
    if (problema) {
      error = problema;
      return;
    }
    cargando = true;
    try {
      const datos = await api.reporte(tipo, { desde, hasta, ruta_id: ruta, [config.clave]: extra });
      resultado = { ...datos, filtros: textoFiltros(), rango: `${desde}_a_${hasta}` };
    } catch (e) {
      error = e.message;
      resultado = null;
    } finally {
      cargando = false;
    }
  }

  const generar = (formato) => {
    const datos = {
      titulo: resultado.titulo,
      columnas: resultado.columnas,
      filas: resultado.filas,
      filtros: resultado.filtros,
      usuario
    };
    return formato === 'pdf' ? crearPDF(datos) : crearExcel(datos);
  };

  const nombreArchivo = (formato) =>
    `reporte_${resultado.tipo}_${resultado.rango}.${formato === 'pdf' ? 'pdf' : 'xlsx'}`;

  async function exportar(formato) {
    if (!resultado) return;
    error = '';
    aviso = '';
    exportando = true;
    try {
      descargar(await generar(formato), nombreArchivo(formato));
      aviso = `Se descargó el archivo ${formato === 'pdf' ? 'PDF' : 'Excel'}.`;
    } catch (e) {
      error = 'No se pudo generar el archivo. Intenta de nuevo.';
    } finally {
      exportando = false;
    }
  }

  async function enviar() {
    error = '';
    aviso = '';
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(destinatario.trim())) {
      error = 'Escribe un correo válido para el destinatario.';
      return;
    }
    enviando = true;
    try {
      const blob = await generar(formatoCorreo);
      const respuesta = await api.enviarReporte({
        destinatario: destinatario.trim(),
        asunto: `${resultado.titulo} - Gestión de Transporte Escolar`,
        mensaje: `Adjunto el ${resultado.titulo.toLowerCase()}.\n${resultado.filtros}`,
        nombre_archivo: nombreArchivo(formatoCorreo),
        contenido_base64: await aBase64(blob)
      });
      aviso = respuesta.mensaje;
      correoAbierto = false;
    } catch (e) {
      error = e.message;
    } finally {
      enviando = false;
    }
  }
</script>

<EncabezadoPagina
  sobretitulo="INFORMES"
  titulo="Reportes"
  subtitulo="Consulta por rango de fechas, ruta y estado. Visualiza, exporta o envía por correo."
/>

<section class="panel filtros">
  <label>
    Reporte
    <select bind:value={tipo} onchange={cambiarReporte}>
      <option value="abordajes">Abordajes de estudiantes</option>
      <option value="ausencias">Ausencias reportadas</option>
    </select>
  </label>
  <label>
    Desde
    <input type="date" bind:value={desde} />
  </label>
  <label>
    Hasta
    <input type="date" bind:value={hasta} />
  </label>
  <label>
    Ruta
    <select bind:value={ruta}>
      <option value="">Todas las rutas</option>
      {#each opciones.rutas as r (r.id)}
        <option value={r.id}>{r.nombre}</option>
      {/each}
    </select>
  </label>
  <label>
    {config.etiquetaExtra}
    <select bind:value={extra}>
      <option value="">Todos</option>
      {#each opcionesExtra as valor (valor)}
        <option value={valor}>{valor}</option>
      {/each}
    </select>
  </label>
  <div class="acciones">
    <button type="button" class="boton primario" disabled={cargando} onclick={visualizar}>
      {cargando ? 'Consultando…' : 'Visualizar'}
    </button>
  </div>
</section>

{#if error}
  <div class="alerta error"><span class="alerta-texto">{error}</span></div>
{/if}
{#if aviso}
  <div class="alerta ok"><span class="alerta-texto">{aviso}</span></div>
{/if}

{#if resultado}
  <section class="panel resultado">
    <div class="barra">
      <div>
        <strong>{resultado.titulo}</strong>
        <small>{resultado.filtros}</small>
        <small>{resultado.total} registro{resultado.total === 1 ? '' : 's'}</small>
      </div>
      <div class="botones">
        <button type="button" class="boton secundario" disabled={exportando || resultado.total === 0} onclick={() => exportar('pdf')}>
          Exportar PDF
        </button>
        <button type="button" class="boton secundario" disabled={exportando || resultado.total === 0} onclick={() => exportar('excel')}>
          Exportar Excel
        </button>
        <button type="button" class="boton suave" disabled={resultado.total === 0} onclick={() => (correoAbierto = !correoAbierto)}>
          Enviar por correo
        </button>
      </div>
    </div>

    {#if correoAbierto}
      <div class="correo">
        <label>
          Correo del destinatario
          <input type="email" placeholder="nombre@correo.com" bind:value={destinatario} />
        </label>
        <label>
          Formato
          <select bind:value={formatoCorreo}>
            <option value="pdf">PDF</option>
            <option value="excel">Excel</option>
          </select>
        </label>
        <button type="button" class="boton primario" disabled={enviando} onclick={enviar}>
          {enviando ? 'Enviando…' : 'Enviar'}
        </button>
      </div>
    {/if}

    {#if resultado.total === 0}
      <div class="vacio">
        <span class="vacio-icono">📄</span>
        No hay registros con esos filtros.
      </div>
    {:else}
      <div class="tabla-caja">
        <table>
          <thead>
            <tr>{#each resultado.columnas as columna}<th>{columna}</th>{/each}</tr>
          </thead>
          <tbody>
            {#each resultado.filas.slice(0, 300) as fila}
              <tr>{#each fila as celda}<td>{celda}</td>{/each}</tr>
            {/each}
          </tbody>
        </table>
      </div>
      {#if resultado.total > 300}
        <p class="nota">Se muestran los primeros 300 registros. El archivo exportado incluye todos.</p>
      {/if}
    {/if}
  </section>
{/if}

<style>
  .filtros {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 14px;
    align-items: end;
    margin-bottom: 16px;
  }
  label { display: grid; gap: 5px; font-size: 12px; font-weight: 600; color: #38506e; }
  input, select {
    font: 400 13px 'DM Sans', sans-serif; padding: 9px 10px; width: 100%;
    border: 1px solid var(--borde); border-radius: 8px; background: #fff; color: var(--texto);
  }
  .acciones { display: flex; }
  .acciones .boton { width: 100%; }

  .barra { display: flex; justify-content: space-between; gap: 14px; flex-wrap: wrap; align-items: center; margin-bottom: 14px; }
  .barra strong { display: block; font: 600 16px Outfit, sans-serif; color: #122440; }
  .barra small { display: block; color: var(--suave); font-size: 12px; margin-top: 2px; }
  .botones { display: flex; gap: 8px; flex-wrap: wrap; }

  .correo {
    display: grid; grid-template-columns: 2fr 1fr auto; gap: 12px; align-items: end;
    background: #f5f8fe; border: 1px solid var(--borde); border-radius: 10px; padding: 12px; margin-bottom: 14px;
  }

  .tabla-caja { overflow-x: auto; border: 1px solid var(--borde); border-radius: 10px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { background: var(--marino); color: #fff; text-align: left; padding: 10px 12px; white-space: nowrap; }
  td { padding: 9px 12px; border-top: 1px solid var(--borde); }
  tbody tr:nth-child(even) { background: #f5f7fb; }
  .nota { color: var(--suave); font-size: 12px; margin: 10px 0 0; }

  @media (max-width: 700px) { .correo { grid-template-columns: 1fr; } }
</style>
