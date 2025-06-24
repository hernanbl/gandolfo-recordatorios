// Initialize Estado de Reservas chart
function initReservationChart(data) {
    const ctx = document.getElementById('reservationChart').getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Pendiente', 'Confirmada', 'Cancelada', 'No asistió'],
            datasets: [{
                data: data,
                backgroundColor: [
                    '#fde68a', // yellow for pending
                    '#1aaf99', // green for confirmed
                    '#F87171', // red for cancelled
                    '#169bcc'  // gray for no-show
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Initialize Monthly Trend chart
function initTrendChart(data) {
    const ctx = document.getElementById('reservationTrendChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Reservas',
                data: data.values,
                borderColor: '#5C652A',
                backgroundColor: 'rgba(92, 101, 42, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// Initialize Daily Reservations chart
function initDailyReservationsChart(data) {
    const ctx = document.getElementById('reservasDiariasChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Reservas',
                    data: data.reservations,
                    backgroundColor: 'rgba(92, 101, 42, 0.8)',
                    order: 2
                },
                {
                    label: 'Ocupación %',
                    data: data.occupancy,
                    type: 'line',
                    borderColor: '#8B6914',
                    backgroundColor: 'rgba(139, 105, 20, 0.1)',
                    yAxisID: 'y1',
                    order: 1
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Número de Reservas'
                    }
                },
                y1: {
                    beginAtZero: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Porcentaje de Ocupación'
                    },
                    grid: {
                        drawOnChartArea: false
                    },
                    max: 100
                }
            }
        }
    });
}

// Initialize Top Clients chart
function initTopClientsChart(data) {
    const ctx = document.getElementById('topClientesChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(data),
            datasets: [{
                data: Object.values(data),
                backgroundColor: '#FCD34D',
                borderColor: '#8B6914',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
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

// Initialize all charts when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Status Chart
    initReservationChart(window.chartData.status_counts);

    // Trend Chart
    initTrendChart({
        labels: window.chartData.month_labels,
        values: window.chartData.reservation_trend
    });

    // Daily Reservations Chart
    initDailyReservationsChart({
        labels: window.chartData.dias_labels,
        reservations: window.chartData.reservas_counts,
        occupancy: window.chartData.ocupacion_diaria_pct
    });

    // Top Clients Chart
    const topClientsData = {};
    window.chartData.top_clientes_labels.forEach((label, index) => {
        topClientsData[label] = window.chartData.top_clientes_counts[index];
    });
    initTopClientsChart(topClientsData);
});
