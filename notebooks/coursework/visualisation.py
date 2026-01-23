def build_town_plot(
    *,
    town_layout,
    road_edges,
    optimisation_result,
    show_buildings,
    show_roads,
    show_energy,
    go,
    mo,
):
    icon_map = {
        "low density housing": "housing-low-density.png",
        "medium density housing": "housing-med-density.png",
        "high density housing": "housing-high-density.png",
        "potential energy centre location": "energy-centre.png",
        "hospital": "hospital.png",
        "shopping centre": "shopping-centre.png",
        "school": "school.png",
        "office": "office.png",
        "green space": "green-space.png",
        "open space": "open-space.png",
    }
    color_map = {
        "low density housing": "rgb(255, 178, 220)",
        "medium density housing": "rgb(255, 0, 255)",
        "high density housing": "rgb(220, 25, 25)",
        "green space": "rgb(20, 163, 58)",
        "potential energy centre location": "rgb(60, 60, 60)",
        "open space": "rgb(210, 210, 210)",
        "hospital": "rgb(0, 204, 255)",
        "shopping centre": "rgb(255, 204, 0)",
        "school": "rgb(160, 70, 20)",
        "office": "rgb(255, 255, 0)",
    }
    cell_size = 48

    max_x = max(building["x_max"] for building in town_layout)
    max_y = max(building["y_max"] for building in town_layout)

    building_traces = []
    building_metadata = []
    center_lookup = {}
    marker_x = []
    marker_y = []
    marker_sizes = []
    marker_customdata = []

    for idx, building in enumerate(town_layout):
        building_type = building["type"].value
        x0 = building["x_min"]
        x1 = building["x_max"]
        y0 = building["y_min"]
        y1 = building["y_max"]
        building_metadata.append(
            {
                "type": building_type,
                "x_min": x0,
                "x_max": x1,
                "y_min": y0,
                "y_max": y1,
            }
        )
        width = x1 - x0
        height = y1 - y0
        center_x = (x0 + x1) / 2
        center_y = (y0 + y1) / 2
        marker_x.append(center_x)
        marker_y.append(center_y)
        marker_customdata.append(idx)
        center_lookup[(round(center_x, 4), round(center_y, 4))] = idx
        marker_sizes.append(max(width, height) * cell_size * 0.8)
        fill_color = color_map.get(building_type, "rgb(180, 180, 180)")
        building_traces.append(
            go.Scatter(
                x=[x0, x1, x1, x0, x0],
                y=[y0, y0, y1, y1, y0],
                fill="toself",
                mode="lines",
                line={"color": "rgb(90, 90, 90)", "width": 1},
                fillcolor=fill_color.replace("rgb", "rgba").replace(")", ", 0.8)"),
                hoverinfo="skip",
                name="Buildings",
                legendgroup="buildings",
                showlegend=idx == 0,
            )
        )

    road_traces = []
    for idx, ((x0, y0), (x1, y1)) in enumerate(road_edges):
        road_traces.append(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line={"color": "rgb(0, 0, 0)", "width": 4},
                hoverinfo="skip",
                name="Roads",
                legendgroup="roads",
                showlegend=idx == 0,
            )
        )
    if not road_traces:
        road_traces.append(
            go.Scatter(
                x=[],
                y=[],
                mode="lines",
                line={"color": "rgb(0, 0, 0)", "width": 2},
                hoverinfo="skip",
                name="Roads",
                legendgroup="roads",
                showlegend=True,
            )
        )

    energy_network_edges = optimisation_result.get("energy_edges", [])
    energy_center_cells = optimisation_result.get("energy_centers", [])
    energy_traces = []
    for idx, (x0, y0, x1, y1) in enumerate(energy_network_edges):
        energy_traces.append(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line={"color": "rgb(224, 224, 0)", "width": 6},
                hoverinfo="skip",
                name="Energy network",
                legendgroup="energy",
                showlegend=idx == 0,
            )
        )
    for idx, (x, y) in enumerate(energy_center_cells):
        energy_traces.append(
            go.Scatter(
                x=[x + 0.5],
                y=[y + 0.5],
                mode="markers",
                marker={"size": cell_size * 0.8, "color": "rgb(224, 224, 0)"},
                hoverinfo="skip",
                name="Energy centre",
                legendgroup="energy",
                showlegend=idx == 0,
            )
        )
    for idx, (x0, y0, x1, y1) in enumerate(energy_network_edges):
        energy_traces.append(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line={"color": "rgb(192, 0, 0)", "width": 3},
                hoverinfo="skip",
                name="Energy network",
                legendgroup="energy",
                showlegend=idx == 0,
            )
        )
    for idx, (x, y) in enumerate(energy_center_cells):
        energy_traces.append(
            go.Scatter(
                x=[x + 0.5],
                y=[y + 0.5],
                mode="markers",
                marker={"size": cell_size * 0.6, "color": "rgb(192, 0, 0)"},
                hoverinfo="skip",
                name="Energy centre",
                legendgroup="energy",
                showlegend=idx == 0,
            )
        )
    if not energy_traces:
        energy_traces.append(
            go.Scatter(
                x=[],
                y=[],
                mode="lines",
                line={"color": "rgb(255, 0, 0)", "width": 3},
                hoverinfo="skip",
                name="Energy network",
                legendgroup="energy",
                showlegend=True,
            )
        )

    building_interaction_trace = go.Scatter(
        x=marker_x,
        y=marker_y,
        mode="markers",
        marker={"size": marker_sizes, "opacity": 0.01},
        customdata=marker_customdata,
        hovertemplate="cell_index=%{customdata}<extra></extra>",
        name="Building interactions",
        showlegend=False,
    )

    fig = go.Figure()
    if show_buildings.value:
        fig.add_traces(building_traces)
        fig.add_trace(building_interaction_trace)
    if show_roads.value:
        fig.add_traces(road_traces)
    if show_energy.value:
        fig.add_traces(energy_traces)

    fig.update_layout(
        title="Town layout",
        clickmode="event+select",
        xaxis={
            "visible": False,
            "range": [0, max_x],
            "constrain": "domain",
        },
        yaxis={
            "visible": False,
            "range": [max_y, 0],
            "scaleanchor": "x",
        },
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        width=int(max_x * cell_size + 80),
        height=int(max_y * cell_size + 80),
        showlegend=False,
    )
    plot = mo.ui.plotly(fig)
    return building_metadata, center_lookup, icon_map, plot
