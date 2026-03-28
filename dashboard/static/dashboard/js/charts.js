// Initialize chart only after DOM is loaded and only if the canvas exists
let energyUsageChart = null;

document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('energyUsageChart');
    if (!canvas) return; // No chart on this page

    const ctx = canvas.getContext('2d');
    energyUsageChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [], // Populated via `updateChartData`
            datasets: [{
                label: 'Energy Usage (kWh)',
                data: [],
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderWidth: 1,
                fill: true,
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Energy Usage (kWh)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            }
        }
    });
});

// Function to update chart data (safe if chart not yet created)
function updateChartData(labels, data) {
    if (!energyUsageChart) {
        // Chart not initialized yet; initialize with data after DOM ready
        document.addEventListener('DOMContentLoaded', function() {
            if (!energyUsageChart && document.getElementById('energyUsageChart')) {
                updateChartData(labels, data);
            }
        });
        return;
    }
    energyUsageChart.data.labels = labels;
    energyUsageChart.data.datasets[0].data = data;
    energyUsageChart.update();
}

// Expose to global scope for inline scripts
window.updateEnergyUsageChart = updateChartData;