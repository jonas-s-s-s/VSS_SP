function render_table(table_data_json, table_container_selector, sort_by_column_index = 1, sort_direction="asc") {
    const tableData = table_data_json

    const columns = Object.keys(tableData[0] || {}).map((key) => {
        const firstValue = tableData[0]?.[key];
        const isNumeric = typeof firstValue === "number";
        return {
            title: key.replace(/_/g, ' ').toUpperCase(),
            field: key,
            ...(isNumeric ? {sorter: "number"} : {})
        };
    });

    // Sort the row names alphabetically
    columns.sort((a, b) => {
        return a.title.toLowerCase().localeCompare(b.title.toLowerCase());
    });

    const nameIndex = columns.findIndex(item => item.title === 'NAME' || item.field === 'name');
    // Make sure that the NAME row is always first
    if (nameIndex !== -1) {
        const [nameItem] = columns.splice(nameIndex, 1);
        columns.unshift(nameItem);
    }

    // Find "field" of the default sort row
    const SortColumnField = columns[sort_by_column_index].field;

    const table = new Tabulator(table_container_selector, {
        data: tableData,
        layout: "fitColumns",
        columns: columns,
        initialSort: [
            {column: SortColumnField, dir: sort_direction}
        ]
    });
}

function render_histogram(svg_selector, data, title_x, title_y, sort_direction = "asc") {
    if (sort_direction === "asc") {
        data = data.slice().sort((a, b) => a.y_value - b.y_value);
    } else if (sort_direction === "desc") {
        data = data.slice().sort((a, b) => b.y_value - a.y_value);
    } else if (sort_direction === "alpha") {
        data = data.slice().sort((a, b) => a.x_label.localeCompare(b.x_label));
    }

    const svg = d3.select(svg_selector);
    const margin = {top: 20, right: 30, bottom: 70, left: 85};
    const width = +svg.attr("width") - margin.left - margin.right;
    const height = +svg.attr("height") - margin.top - margin.bottom;

    svg.selectAll("*").remove();

    const chart = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand()
        .domain(data.map(d => d.x_label))
        .range([0, width])
        .padding(0.1);

    const y = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.y_value)]).nice()
        .range([height, 0]);

    chart.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x))
        .selectAll("text")
        .attr("transform", "rotate(-45)")
        .attr("text-anchor", "end");

    chart.append("g")
        .call(d3.axisLeft(y));

    chart.selectAll("rect")
        .data(data)
        .enter().append("rect")
        .attr("x", d => x(d.x_label))
        .attr("y", d => y(d.y_value))
        .attr("width", x.bandwidth())
        .attr("height", d => height - y(d.y_value))
        .attr("fill", "steelblue");

    svg.append("text")
        .attr("x", margin.left + width / 2)
        .attr("y", height + margin.top + 70)
        .attr("text-anchor", "middle")
        .attr("font-weight", "bold")
        .text(title_x);

    svg.append("text")
        .attr("x", -(margin.top + height / 2))
        .attr("y", 20)
        .attr("transform", "rotate(-90)")
        .attr("text-anchor", "middle")
        .attr("font-weight", "bold")
        .text(title_y);
}

function render_curves_graph(svg_selector, data, x_labels, curve_labels, title_x, title_y) {
    if (data.length !== curve_labels.length) {
        throw new Error("Each curve must have a corresponding label.");
    }

    const svg = d3.select(svg_selector);
    const margin = {top: 20, right: 150, bottom: 70, left: 85};
    const width = +svg.attr("width") - margin.left - margin.right;
    const height = +svg.attr("height") - margin.top - margin.bottom;

    svg.selectAll("*").remove();

    const chart = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const allYValues = data.flat();
    const y = d3.scaleLinear()
        .domain([0, d3.max(allYValues)]).nice()
        .range([height, 0]);

    const x = d3.scalePoint()
        .domain(x_labels)
        .range([0, width])
        .padding(0.25);

    chart.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x))
        .selectAll("text")
        .attr("transform", "rotate(-45)")
        .style("text-anchor", "end");

    chart.append("g")
        .call(d3.axisLeft(y));

    const line = d3.line()
        .x((d, i) => x(x_labels[i]))
        .y(d => y(d));

    const color = d3.scaleOrdinal(d3.schemeCategory10);

    data.forEach((curve, idx) => {
        chart.append("path")
            .datum(curve)
            .attr("fill", "none")
            .attr("stroke", color(idx))
            .attr("stroke-width", 2)
            .attr("d", line);
    });

    // Axis labels
    svg.append("text")
        .attr("x", margin.left + width / 2)
        .attr("y", height + margin.top + 70)
        .attr("text-anchor", "middle")
        .attr("font-weight", "bold")
        .text(title_x);

    svg.append("text")
        .attr("x", -(margin.top + height / 2))
        .attr("y", 20)
        .attr("transform", "rotate(-90)")
        .attr("text-anchor", "middle")
        .attr("font-weight", "bold")
        .text(title_y);

    // Legend
    const legend = svg.append("g")
        .attr("transform", `translate(${margin.left + width + 10}, ${margin.top})`);

    curve_labels.forEach((label, i) => {
        const legendRow = legend.append("g")
            .attr("transform", `translate(0, ${i * 20})`);

        legendRow.append("rect")
            .attr("width", 12)
            .attr("height", 12)
            .attr("fill", color(i));

        legendRow.append("text")
            .attr("x", 18)
            .attr("y", 10)
            .attr("text-anchor", "start")
            .style("font-size", "12px")
            .text(label);
    });
}
