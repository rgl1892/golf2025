function getThemeColor(property) {
    return getComputedStyle(document.documentElement).getPropertyValue(property).trim();
}

function getResponsiveDimensions(containerId) {
    const container = document.getElementById(containerId);
    const containerWidth = container.offsetWidth;
    const margin = {top: 20, right: 30, bottom: 40, left: 40};
    
    // Calculate responsive dimensions
    const width = Math.max(200, containerWidth - margin.left - margin.right);
    const height = Math.max(150, width * 0.6); // 0.6 aspect ratio
    
    return { width, height, margin };
}

function createChart(containerId, data, metric, title, colorVar) {
    const { width, height, margin } = getResponsiveDimensions(containerId);

    // Clear any existing chart
    d3.select(`#${containerId}`).selectAll("*").remove();

    // Filter out holes without scores
    const filteredData = data.filter(d => d.shots !== null && d.shots !== undefined);

    // If no data, show empty state
    if (filteredData.length === 0) {
        const container = d3.select(`#${containerId}`)
            .attr("class", "chart-container");
        container.append("div")
            .style("text-align", "center")
            .style("padding", "20px")
            .style("color", getThemeColor('--chart-text-color'))
            .text("No scores entered yet");
        return;
    }

    const container = d3.select(`#${containerId}`)
        .attr("class", "chart-container");

    const svg = container
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .attr("viewBox", `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .style("width", "100%")
        .style("height", "auto")
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand()
        .domain(filteredData.map(d => d.hole))
        .range([0, width])
        .padding(0.1);

    const y = d3.scaleLinear()
        .domain([0, d3.max(filteredData, d => d[metric])])
        .nice()
        .range([height, 0]);

    // Add bars
    svg.selectAll(".bar")
        .data(filteredData)
        .enter().append("rect")
        .attr("class", "bar")
        .attr("x", d => x(d.hole))
        .attr("width", x.bandwidth())
        .attr("y", d => y(d[metric]))
        .attr("height", d => height - y(d[metric]))
        .attr("fill", getThemeColor(colorVar));

    // Add x axis
    svg.append("g")
        .attr("class", "axis")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x))
        .selectAll("text")
        .style("fill", getThemeColor('--chart-text-color'));

    // Add y axis
    svg.append("g")
        .attr("class", "axis")
        .call(d3.axisLeft(y))
        .selectAll("text")
        .style("fill", getThemeColor('--chart-text-color'));

    // Style axis lines
    svg.selectAll(".axis path, .axis line")
        .style("stroke", getThemeColor('--chart-axis-color'));

    // Add title
    svg.append("text")
        .attr("x", width / 2)
        .attr("y", 0 - (margin.top / 2))
        .attr("text-anchor", "middle")
        .style("font-size", "12px")
        .style("font-weight", "bold")
        .style("fill", getThemeColor('--chart-text-color'))
        .text(title);
}

function createToParChart(containerId, data) {
    const { width, height, margin } = getResponsiveDimensions(containerId);

    // Clear any existing chart
    d3.select(`#${containerId}`).selectAll("*").remove();

    // Filter out holes without scores and calculate to par values
    const toParData = data
        .filter(d => d.shots !== null && d.shots !== undefined)
        .map(d => ({
            hole: d.hole,
            toPar: d.shots - d.par,
            shots: d.shots,
            par: d.par
        }));

    // If no data, show empty state
    if (toParData.length === 0) {
        const container = d3.select(`#${containerId}`)
            .attr("class", "chart-container");
        container.append("div")
            .style("text-align", "center")
            .style("padding", "20px")
            .style("color", getThemeColor('--chart-text-color'))
            .text("No scores entered yet");
        return;
    }

    const container = d3.select(`#${containerId}`)
        .attr("class", "chart-container");

    const svg = container
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .attr("viewBox", `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .style("width", "100%")
        .style("height", "auto")
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand()
        .domain(toParData.map(d => d.hole))
        .range([0, width])
        .padding(0.1);

    // Scale should include negative values (under par)
    const yExtent = d3.extent(toParData, d => d.toPar);
    const y = d3.scaleLinear()
        .domain([Math.min(yExtent[0], -2), Math.max(yExtent[1], 3)])
        .nice()
        .range([height, 0]);

    // Add zero line (par line)
    svg.append("line")
        .attr("x1", 0)
        .attr("x2", width)
        .attr("y1", y(0))
        .attr("y2", y(0))
        .attr("stroke", getThemeColor('--chart-axis-color'))
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "3,3");

    // Add bars
    svg.selectAll(".bar")
        .data(toParData)
        .enter().append("rect")
        .attr("class", "bar")
        .attr("x", d => x(d.hole))
        .attr("width", x.bandwidth())
        .attr("y", d => d.toPar >= 0 ? y(d.toPar) : y(0))
        .attr("height", d => Math.abs(y(d.toPar) - y(0)))
        .attr("fill", d => {
            if (d.toPar < 0) return getThemeColor('--chart-success-color'); // Green for under par
            if (d.toPar === 0) return getThemeColor('--chart-success-color'); // Orange for par
            return getThemeColor('--chart-success-color'); // Red for over par
        });

    // Add x axis
    svg.append("g")
        .attr("class", "axis")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x))
        .selectAll("text")
        .style("fill", getThemeColor('--chart-text-color'));

    // Add y axis
    svg.append("g")
        .attr("class", "axis")
        .call(d3.axisLeft(y))
        .selectAll("text")
        .style("fill", getThemeColor('--chart-text-color'));

    // Style axis lines
    svg.selectAll(".axis path, .axis line")
        .style("stroke", getThemeColor('--chart-axis-color'));

    // Add title
    svg.append("text")
        .attr("x", width / 2)
        .attr("y", 0 - (margin.top / 2))
        .attr("text-anchor", "middle")
        .style("font-size", "12px")
        .style("font-weight", "bold")
        .style("fill", getThemeColor('--chart-text-color'))
        .text("Score To Par");

}

function initializeRoundCharts(playerData) {
    // Create charts for each player
    let playerIndex = 1;
    Object.keys(playerData).forEach(player => {
        const data = playerData[player].scores;
        
        createChart(`shots-chart-${playerIndex}`, data, 'shots', 'Shots per Hole', '--chart-success-color');
        createChart(`points-chart-${playerIndex}`, data, 'points', 'Points per Hole', '--chart-success-color');
        createToParChart(`to-par-chart-${playerIndex}`, data);
        
        playerIndex++;
    });
}

function redrawAllCharts(playerData) {
    // Redraw all charts with new dimensions
    let playerIndex = 1;
    Object.keys(playerData).forEach(player => {
        const data = playerData[player].scores;
        
        createChart(`shots-chart-${playerIndex}`, data, 'shots', 'Shots per Hole', '--chart-success-color');
        createChart(`points-chart-${playerIndex}`, data, 'points', 'Points per Hole', '--chart-success-color');
        createToParChart(`to-par-chart-${playerIndex}`, data);
        
        playerIndex++;
    });
}

function showTable(tableName) {
    document.querySelectorAll(".scoring-table tbody").forEach(tbody => {
        tbody.style.display = "none";
    });
    document.querySelector(`tbody[name='${tableName}']`).style.display = "table-row-group";
}