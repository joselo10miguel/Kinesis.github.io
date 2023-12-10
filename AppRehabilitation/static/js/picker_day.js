const elem = document.querySelector('input[name="fechas"]');


const datepicker = new Datepicker(elem, {
  maxNumberOfDates: 1,
  
});

$("#id_rutinas_asignadas").on("change", function () {
  const numRutinas = parseInt($(this).val());
  if (!isNaN(numRutinas)) {
    datepicker.setOptions({
      maxNumberOfDates: numRutinas,
    });
    updateRutinaList(numRutinas);

  } 
});


datepicker.element.addEventListener( 'changeDate', ( event ) =>{
    const fechaSeleccionada = datepicker.getDate();
    console.log("Fecha seleccionada: " + fechaSeleccionada);
    updateRutinaList(null, fechaSeleccionada);
} );



function updateRutinaList(numeroRutina, fechaSeleccionada) {
    const rutinaList = $("#rutina-list");
    rutinaList.empty(); // Limpia la lista
  
    if (numeroRutina && fechaSeleccionada) {
      for (let i = 1; i <= numeroRutina; i++) {
        const listItem = document.createElement("li");
        listItem.innerHTML = `Número de Rutina ${i}: Fecha ${fechaSeleccionada}`;
        rutinaList.append(listItem);
      }
      rutinaList.show();
    } else {
      rutinaList.hide();
    }
  }


