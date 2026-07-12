// const API_BASE_URL = 'http://127.0.0.1:8000';
// console.log(API_BASE_URL);

//for fetching available lines of a factory
const client_code_element = document.getElementById("client_codes");
const fact_dropdown = document.getElementById("factory_codes");
const line_dropdown = document.getElementById("line_numbers");

async function fetchFactoryByClientCode() {
    const clientCode = client_code_element.value;

    fact_dropdown.innerHTML = `
        <option value="" disabled selected>
            Select Factory
        </option>
    `;

    if (!clientCode) return;

    try {

        // ✅ API call
        const response = await fetch(`/api/v1/get-factory-by-client-code/?client_code=${clientCode}`);

        // ✅ Convert response to JSON
        const data = await response.json();

        // ✅ Populate dropdown
        data.factories.forEach(factory => {

            const option = document.createElement("option");

            option.value = factory.fact_code;
            option.textContent = `${factory.fact_code} - ${factory.name}`;
            option.className = "text-black cursor-pointer";
            fact_dropdown.appendChild(option);
        });

    } catch (error) {

        console.error("Error fetching factory codes:", error);

    }
}

client_code_element.addEventListener("change", async () => {

    // ✅ Clear factory dropdown
    fact_dropdown.innerHTML = `
        <option value="" disabled selected>
            Select Factory
        </option>
    `;

    // ✅ Clear line dropdown
    line_dropdown.innerHTML = `
        <option value="" disabled selected>
            Select Line
        </option>
    `;

    // ✅ Fetch new factories
    await fetchFactoryByClientCode();

});


// Use async so we can use await for the API response
async function fetchLinesByFactory() {
    // 1. Get the SELECTED value (not innerText)
    const factCode = fact_dropdown.value;
    
    // 2. Get client code (handles input value or static text)
    const clientCode = client_code_element.value || client_code_element.innerText.trim();

    // Check if a valid factory is selected
    if (factCode && factCode !== "Select") {
        try {
            // 3. Must 'await' the fetch and the .json() parsing
            const response = await fetch(`/api/v1/lines_by_fact_and_client_code/?client_code=${clientCode}&fact_code=${factCode}`);
            
            if (!response.ok) throw new Error("API response was not ok.");

            const data = await response.json();

            // 4. Clear and add the default "Select" AND the "All" option
            line_dropdown.innerHTML = `
                <option value="" disabled selected class="text-black cursor-pointer">Select Line</option>
                <option value="All" class="text-black cursor-pointer">All</option>
            `;

            data.forEach(line => {
                const option = document.createElement("option");
                option.value = line;
                option.textContent = line;
                option.className = "text-black cursor-pointer";
                line_dropdown.appendChild(option);
            });

        } catch (err) {
            console.error("API Error:", err);
        }
    }
}

// for production for a selected line, factory and client updates
async function fetchDataByLine() {
    const clientCode = client_code_element.value || client_code_element.innerText.trim();
    const lineNo = line_dropdown.value;
    const factCode = fact_dropdown.value;
    
    if (!lineNo) return;
    
    await fetch(`/api/v1/data_by_client_factory_and_line/?client_code=${clientCode}&fact_code=${factCode}&line_no=${lineNo}`)
    .then(res => res.json())
    .then(data => {
        
        // 🟦 Production Today
        document.getElementById("production_value").innerText = data.production_today ?? 0;
        document.getElementById("production_target").innerText = "Target: " + (data.target ?? 0);
        
        // 🟩 Efficiency → actually "below target"
        document.getElementById("efficiency_value").innerText = (data.below_target_percentage ?? 0) + "%";
        
        // 🟧 Rejections → use both over + under
        const totalRejections = (data.total_overweight_unit ?? 0) + (data.total_underweight_unit ?? 0);
        
        document.getElementById("rejection_value").innerText = totalRejections;
        document.getElementById("rejection_rate").innerText = "Rate: " + (data.line_rejection_rate ?? 0) + "%";
        
        // 🟪 Cases Packed
        document.getElementById("total_cases_packed_value").innerText = data.total_cases_packed ?? 0;
        document.getElementById("total_cases_packed_target").innerText = "Target: " + (data.cases_packed_target ?? 0);
        
        // 🟥 Downtime (not in API → placeholder)
        //document.getElementById("downtime_value").innerText = "0 min";
        
        //Meterial loss section
        //total overweight loss
        document.getElementById("total_overweight_loss").innerText = (data.total_overweight_in_kg ?? 0.00) + " kg";
        document.getElementById("total_overweight_loss_in_gm").innerText = (data.total_overweight_in_gm ?? 0.00) + "g total";
        
        //estimated cost loss
        document.getElementById("estimated_cost_loss").innerText = "₹" + (data.total_overweight_cost ?? 0);

        //overweight units
        document.getElementById("overweight_units").innerText = data.total_overweight_unit ?? 0;
        
        //underweight units
        document.getElementById("underweight_units").innerText = data.total_underweight_unit ?? 0;
    })
    .catch(err => console.error("API Error:", err));
}

// for updating the table
async function UpdateTable() {
    try {
        const clientCode = client_code_element.value || client_code_element.innerText.trim();
        const factCode = fact_dropdown.value;
        const lineNo = line_dropdown.value || 'All';

        const response = await fetch(`/api/v1/data_retrieve/?client_code=${clientCode}&fact_code=${factCode}&line_no=${lineNo}`);
        if (!response.ok) throw new Error("Network response was not ok.");

        const data = await response.json();
        const tableBody = document.querySelector('#latest_data_table tbody');

        // 🔥 Detect screen size
        const isMd = window.innerWidth >= 768;
        const isLg = window.innerWidth >= 1024;

        let rowsHTML = '';

        data.forEach(element => {
            // console.log(element)
            const dtString = element.dttime ? String(element.dttime) : "";
            const status = element.product_status ? String(element.product_status).toLowerCase() : "unknown";

            rowsHTML += `
            <tr class="hover:bg-white/5 transition">

                <td class="px-2 py-2 text-center text-red-400 text-[10px] sm:text-xs md:text-sm wrap-break-word">
                    ${element.sequence_id}
                </td>

                <td class="px-2 py-2 text-yellow-400 text-[10px] sm:text-xs md:text-sm wrap-break-word">
                    <div class="flex flex-col items-center leading-tight">
                        ${dtString.includes('T') ?
                            `<span>${dtString.split('T')[0]}</span>
                             <span class="opacity-80 text-[9px] sm:text-[10px] md:text-xs">
                                ${dtString.split('T')[1]}
                             </span>`
                            : dtString
                        }
                    </div>
                </td>

                <td class="px-2 py-2 text-center text-green-400 font-mono text-[10px] sm:text-xs md:text-sm">
                    ${element.weight}
                </td>

                <td class="px-2 py-2 text-center text-[10px] sm:text-xs md:text-sm 
                    ${status.toLowerCase() === 'pass' ? 'text-[#bdf090]' : 'text-[#f1819b]'}">
                    ${status.toUpperCase()}
                </td>

                <!-- MD columns -->
                <td class="text-center px-2 py-2 text-blue-400 text-[10px] sm:text-xs md:text-sm wrap-break-word ${!isMd ? 'hidden' : ''}">
                    ${element.sku_name}
                </td>

                <td class="text-center px-2 py-2 text-emerald-400 text-[10px] sm:text-xs md:text-sm wrap-break-word ${!isMd ? 'hidden' : ''}">
                    ${element.client_code}
                </td>

                <!-- LG columns -->
                <td class="text-center px-2 py-2 text-purple-400 text-[10px] sm:text-xs md:text-sm wrap-break-word ${!isLg ? 'hidden' : ''}">
                    ${element.sku_code}
                </td>

                <td class="text-center px-2 py-2 text-pink-400 text-[10px] sm:text-xs md:text-sm wrap-break-word ${!isLg ? 'hidden' : ''}">
                    ${element.fact_code}
                </td>

                <td class="text-center px-2 py-2 text-indigo-400 text-[10px] sm:text-xs md:text-sm wrap-break-word ${!isLg ? 'hidden' : ''}">
                    ${element.line_no}
                </td>

                <td class="text-center px-2 py-2 text-cyan-400 text-[10px] sm:text-xs md:text-sm wrap-break-word ${!isLg ? 'hidden' : ''}">
                    ${element.batch_no}
                </td>
            </tr>`;
        });

        tableBody.innerHTML = rowsHTML;

    } catch (error) {
        console.error('Fetch error:', error);
    }
}

fact_dropdown.addEventListener('change', fetchLinesByFactory);
function getDataAndUpdate() {
    // fetchLinesByFactory();
    const factCode = fact_dropdown.value;
    
    // 🛑 STOP: If no factory is selected, don't call the APIs
    if (!factCode || factCode === "" || factCode === "Select") {
        console.log("Waiting for factory selection...");
        return; 
    }
    fetchDataByLine();
    UpdateTable();
}


// for datewise consolidated table update
// document.getElementById('search-form').addEventListener('submit', function (e) {
//     e.preventDefault();
    
//     const dateValue = document.getElementById('date-input').value;
//     const tbody = document.getElementById('table-body');
//     const url = this.action + `?date_search=${dateValue}`;
    
//     // Show a loading state while fetching
//     tbody.innerHTML = `<tr><td colspan="8" class="px-6 py-12 text-gray-400 italic">Searching...</td></tr>`;
    
//     fetch(url)
//     .then(response => response.json())
//     .then(data => {
//         tbody.innerHTML = ""; // Clear the loading/placeholder row
        
//         if (data.data_by_date && data.data_by_date.length > 0) {
//             data.data_by_date.forEach(item => {
//                 let row = `
//                 <tr class="hover:bg-white/5 transition-colors">
//                 <td class="px-2 py-4 border-r border-white/5">${item.sequence_number}</td>
//                 <!-- break-words allows the date to stack (e.g., 2026- on one line, 04-06 on next) -->
//                 <td class="px-2 py-4 wrap-break-word leading-tight">${item.production_date}</td>
//                 <td class="px-2 py-4 text-white font-medium">${item.product_code}</td>
//                 <td class="px-2 py-4 text-green-400 font-medium">${item.total_passed_count}</td>
//                 <td class="px-2 py-4 text-green-400 font-medium">${item.total_passed_weight}</td>
//                 <td class="px-2 py-4 text-orange-400 font-medium">${item.total_rejected_count}</td>
//                 <td class="px-2 py-4 text-orange-400 font-medium">${item.total_rejected_weight}</td>
//                 <td class="px-2 py-4 border-l border-white/10 font-semibold">${item.total_count}</td>
//                 <td class="px-2 py-4 font-semibold">${item.total_weight}</td>
//                 </tr>`;
//                 tbody.insertAdjacentHTML('beforeend', row);
//             });
//         } else {
//             tbody.innerHTML = `
//             <tr>
//             <td colspan="8" class="px-6 py-12 text-gray-400 italic">
//             No data found for ${dateValue}.
//             </td>
//             </tr>`;
//         }
//     })
//     .catch(error => {
//         console.error('Error:', error);
//         tbody.innerHTML = `<tr><td colspan="8" class="px-6 py-12 text-red-400">An error occurred. Please try again.</td></tr>`;
//     });
// });

// const defaultDateInput = document.getElementById('date-input');
// if (defaultDateInput && defaultDateInput.value) {
//     performSearch(defaultDateInput.value);
// }




line_dropdown.addEventListener('change', getDataAndUpdate);
setInterval(getDataAndUpdate, 1000);

// dropdown.addEventListener("change", () => {
    //     fetchDataByLine();
    // });
    
    // setInterval(fetchDataByLine, 1500);
    

    // console.log("connected");
// const API_BASE_URL = window.location.origin;
// const API_PORT = "8000";
// API_BASE_URL = API_BASE_URL + API_PORT;