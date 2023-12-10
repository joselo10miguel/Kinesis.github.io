const ctx = document.getElementById("pacientes_mes");

let myChart;

const configDatePiker = {
    format: "mm/yyyy",
    language: "es-ES",
    autoPick: true,
};

const date = $("#datepicker").datepicker(configDatePiker);

document.addEventListener("DOMContentLoaded", function () {
    const date = $("#datepicker").datepicker("getDate", true);
    cargarGrafica(date);
});


function updateChart(labels, dataFemeninos, dataMasculinos) {

    if (myChart) {
        console.log('destroy')
        myChart.destroy();
    }

    const data = {
        labels: labels,
        datasets: [
            {
                label: "Femeninos",
                data: dataFemeninos,
                backgroundColor: "#FFB1C1",
            },
            {
                label: "Masculinos",
                data: dataMasculinos,
                backgroundColor: "#9AD0F5",
            },
        ],
    };

    const config = {
        type: "bar",
        data: data,
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    stepSize: 1,
                },
            },
        },
    };

    myChart = new Chart(ctx, config);
}



function cargarGrafica(date) {

    fetch(`get/pacientes/month/?fecha=${date}`, {
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
            const labels = [`${data.nombre_mes}`];
            const dataFemeninos = [`${data.pacientes_femeninos}`, 0];
            const dataMasculinos = [`${data.pacientes_masculinos}`, 0];

            updateChart(labels, dataFemeninos, dataMasculinos);
        })
        .catch(function (error) {
            console.error(error);
            alert(error.message);
        });
}

$("#datepicker")
    .datepicker()
    .on("change", function () {
        var fechaSeleccionada = $(this).val();
        cargarGrafica(fechaSeleccionada);
});

