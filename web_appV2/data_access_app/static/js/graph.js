// const API_BASE_URL = 'http://127.0.0.1:8000';

document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('weightChart');

    const client_code_element = document.getElementById("client_codes");
    const fact_dropdown = document.getElementById("factory_codes");
    const line_dropdown = document.getElementById("line_numbers");

    const clientCode = client_code_element.value || client_code_element.innerText.trim();
    const factCode = fact_dropdown.value;
    const lineNo = line_dropdown.value || 'All';

    if (canvas) {
        const ctx = canvas.getContext('2d');

        window.weightChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Live Weight Data',
                    data: [],
                    // borderColor: '#397367',
                    borderColor: '#6FA99D',
                    backgroundColor: 'rgba(78, 115,223,0.05)',

                    pointBackgroundColor: '#4ade80',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 1,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: '#ffffff',

                    tension: 0.3,
                    fill: false,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                onHover: (event, chartElement) => {
                    event.native.target.style.cursor = chartElement.length ? 'pointer' : 'default';
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#E5E7EB',
                            font: { size: 14 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const item = context.raw;
                                const label = `Weight: ${item.y}`;
                                const code = `Product Code: ${item.product_code || 'N/A'}`;
                                const name = `Product Name: ${item.product_name || 'N/A'}`;
                                const upper = `Upper Threshold: ${item.upper_threshold || 'N/A'}`;
                                const lower = `Lower Threshold: ${item.lower_threshold || 'N/A'}`;
                                return [label, code, name, upper, lower]; // Returns multiple lines in tooltip
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: { color: '#9CA3AF' },
                        grid: { color: '#6b6356' }
                    },
                    x: {
                        ticks: { color: '#9CA3AF' },
                        grid: { color: '#6b6356' }
                    }
                }
            }
        });

        // =========================
        //     FETCH GRAPH DATA
        // =========================

        async function fetchGraphData() {

            try {

                const clientCode = client_code_element.value || client_code_element.innerText.trim();

                const factCode = factory_codes.value;
                const lineNo = line_numbers.value;

                // build url dynamically
                const url = new URL("/api/v1/data_retrieve_for_graph/", window.location.origin);

                url.searchParams.append("limit", "70");

                if (clientCode) {
                    url.searchParams.append("client_code", clientCode);
                }

                if (factCode) {
                    url.searchParams.append("fact_code", factCode);
                }

                if (lineNo) {
                    url.searchParams.append("line_no", lineNo);
                }

                const response = await fetch(url);

                if (!response.ok) {
                    throw new Error("Failed to fetch graph data");
                }

                const result = await response.json();

                updateWeightChart(result.all_data);

            } catch (error) {
                console.error("Graph Fetch Error:", error);
            }
        }

        // =========================
        //      UPDATE GRAPH
        // =========================

        function updateWeightChart(data) {

            if (!window.weightChart) return;

            window.weightChart.data.labels =
                data.map(item => item.date_time);

            window.weightChart.data.datasets[0].data =
                data.map(item => ({
                    x: item.date_time,
                    y: item.weight,

                    product_code: item.product_code,
                    product_name: item.product_name,
                    upper_threshold: item.upper_threshold,
                    lower_threshold: item.lower_threshold
                }));

            window.weightChart.data.datasets[0].pointRadius =
                data.map(item =>
                    item.status === 'pass' ? 4 : 5
                );

            window.weightChart.data.datasets[0].pointBackgroundColor =
                data.map(item =>
                    item.status === 'pass'
                        ? '#facd06'
                        : 'red'
                );

            window.weightChart.data.datasets[0].pointBorderColor =
                data.map(item =>
                    item.status === 'pass'
                        ? '#facd06'
                        : 'red'
                );

            window.weightChart.update('none');
        }

        // initial fetch
        fetchGraphData();

        // auto refresh every 2 sec
        setInterval(fetchGraphData, 2000);

        // refetch when dropdown changes
        factory_codes.addEventListener("change", fetchGraphData);
        line_numbers.addEventListener("change", fetchGraphData);

    }
});

// window.updateWeightChart = function (event) {
//     const response = JSON.parse(event.detail.xhr.response);
//     const data = response.all_data;
//     // const data = JSON.parse(event.detail.xhr.response);

//     if (window.weightChart) {
//         const dataset = window.weightChart.data.datasets[0];

//         window.weightChart.data.labels = data.map(item => item.date_time);

//         window.weightChart.data.datasets[0].data = data.map(item => ({
//             x: item.date_time,
//             y: item.weight,
//             product_code: item.product_code,
//             product_name: item.product_name,
//             upper_threshold: item.upper_threshold,
//             lower_threshold: item.lower_threshold
//         }));

//         window.weightChart.data.datasets[0].pointRadius = data.map(item => item.status === 'pass' ? 4 : 5);
//         window.weightChart.data.datasets[0].pointBackgroundColor = data.map(item => item.status === 'pass' ? '#facd06' : 'red');
//         window.weightChart.data.datasets[0].pointBorderColor = data.map(item => item.status === 'pass' ? '#facd06' : 'red');

//         weightChart.update('none');
//     }
// };
