const ctx_day = document.getElementById("pacientes_dia");

let myChartDay;

const configDatePikerDay = {
    format: "dd/mm/yyyy",
    language: "es-ES",
    autoPick: true,
};

const dateNow = $("#date_picker_day").datepicker(configDatePikerDay);

document.addEventListener("DOMContentLoaded", function () {
    const date = $("#date_picker_day").datepicker("getDate", true);
    loadGrafica(date);
});


function updateChartDay(label, dataPacientes) {

    if (myChartDay) {
        myChartDay.destroy();
    }

    const data = {
        labels: ['Masculino','Femenino'],
        datasets: [
            {
                label: label,
                data: dataPacientes,
                backgroundColor: ["#FF6384", "#FF9020"]
            },
        ],
    };

    const config_day = {
        type: 'doughnut',
        data: data,
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: 'top',
            },
            title: {
              display: true,
              text: 'Pacientes por Dia'
            }
          }
        },
    };

    myChartDay = new Chart(ctx_day, config_day);
}



function loadGrafica(date) {
    fetch(`get/pacientes/day/?fecha=${date}`, {
        method: "GET",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
        },
    })
        .then(function (response) {
            if (!response.ok) {
                throw new Error("Hubo un error al obtener los datos de Django.");
            }
            return response.json();
        })
        .then(function (data) {
            const label = [`${data.nombre_dia}`];
            const dataPacientes = [`${data.pacientes_masculinos}`,`${data.pacientes_femeninos}`];

            updateChartDay(label, dataPacientes);
        })
        .catch(function (error) {
            console.error(error);
            alert(error.message);
        });
}

$("#date_picker_day")
    .datepicker()
    .on("change", function () {
        var fechaSeleccionada = $(this).val();
        loadGrafica(fechaSeleccionada);
});
