// Inicializar los gráficos una vez que el documento esté cargado
document.addEventListener('DOMContentLoaded', function() {
    // Obtener los elementos canvas de los gráficos
    const reservationChartEl = document.getElementById('reservationChart');
    const reservationTrendChartEl = document.getElementById('reservationTrendChart');
    const reservasDiariasChartEl = document.getElementById('reservasDiariasChart');
    const topClientesChartEl = document.getElementById('topClientesChart');

    // Estado de Reservas - Gráfico de Dona
    if (reservationChartEl) {
        new Chart(reservationChartEl, {
            type: 'doughnut',
            data: {
                labels: window.chartData?.status_labels || [],
                datasets: [{
                    data: window.chartData?.status_counts || [],
                    backgroundColor: [
                        '#fde68a',  // Amarillo para Pendiente
                        '#1aaf99',  // Verde para Confirmada
                        '#F87171',  // Rojo para Cancelada
                        '#169bcc'   // Celeste para No asistió
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
    }

    // Evolución - Gráfico de Líneas
    if (reservationTrendChartEl) {
        new Chart(reservationTrendChartEl, {
            type: 'line',
            data: {
                labels: window.chartData?.month_labels || [],
                datasets: [
                    {
                        label: 'Total Reservas',
                        data: window.chartData?.reservation_trend || [],
                        borderColor: '#5c652a',
                        fill: false
                    },
                    {
                        label: 'Confirmadas', 
                        data: window.chartData?.confirmed_trend || [],
                        borderColor: '#1aaf99',
                        fill: false
                    },
                    {
                        label: 'Pendientes',
                        data: window.chartData?.pending_trend || [],
                        borderColor: '#fde68a',
                        fill: false
                    },
                    {
                        label: 'No asistió',
                        data: window.chartData?.no_asistio_trend || [],
                        borderColor: '#169bcc',
                        fill: false
                    },
                    {
                        label: 'Canceladas',
                        data: window.chartData?.canceladas_trend || [],
                        borderColor: '#F87171',
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });
    }

    // Reservas Diarias - Gráfico de Barras
    if (reservasDiariasChartEl) {
        new Chart(reservasDiariasChartEl, {
            type: 'bar',
            data: {
                labels: window.chartData?.dias_labels || [],
                datasets: [
                    {
                        label: 'Reservas',
                        data: window.chartData?.reservas_counts || [],
                        backgroundColor: 'rgba(92, 101, 42, 0.8)',
                        order: 2
                    },
                    {
                        label: 'Personas',
                        data: window.chartData?.personas_counts_diarias || [],
                        backgroundColor: 'rgba(253, 230, 138, 0.8)',
                        order: 1
                    },                    {                        label: 'Ocupación %',
                        data: window.chartData?.ocupacion_diaria_pct || [],
                        type: 'line',
                        borderColor: '#fbc222',
                        backgroundColor: '#fbc222',
                        fill: false,
                        order: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 5
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });
    }

    // Top Clientes - Gráfico de Barras Horizontal
    if (topClientesChartEl) {
        new Chart(topClientesChartEl, {
            type: 'bar',
            data: {
                labels: window.chartData?.top_clientes_labels || [],
                datasets: [{
                    data: window.chartData?.top_clientes_counts || [],
                    backgroundColor: '#fde68a'
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
});
