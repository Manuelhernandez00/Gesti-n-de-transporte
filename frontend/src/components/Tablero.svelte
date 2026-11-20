<script>
  import EncabezadoPagina from './EncabezadoPagina.svelte';

  // Tablero de Power BI publicado en la web (Archivo > Insertar informe > Publicar en la web).
  // Si algún día cambias de informe, solo reemplaza este vínculo.
  const TABLERO_URL =
    'https://app.powerbi.com/view?r=eyJrIjoiYzQ5ZWZkYTgtZTVlNC00YTBlLWIzZWUtYTkzMTU2ZGJkYzQ2IiwidCI6IjAwOGU1MWNkLTNiNzItNDA0NS05MjUwLWI0MzY4MzM0NzBkNyJ9';
</script>

<EncabezadoPagina
  sobretitulo="ANÁLISIS"
  titulo="Tablero"
  subtitulo="Indicadores y gráficos de la operación del transporte escolar."
/>

<div class="contenedor-tablero">
  <iframe title="gestion" src={TABLERO_URL} frameborder="0" allowfullscreen></iframe>
</div>

<style>
  .contenedor-tablero {
    width: 100%;
    height: calc(100vh - 200px);
    min-height: 480px;
    background: #fff;
    border: 1px solid var(--borde);
    border-radius: 14px;
    overflow: hidden;
  }
  iframe {
    display: block;
    width: 100%;
    height: 100%;
    border: 0;
  }
</style>
