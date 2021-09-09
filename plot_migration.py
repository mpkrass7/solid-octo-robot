from logzero import logger
import numpy as np

import networkx as nx
import plotly.graph_objects as go


def build_migration_chart(G, direction="Incoming"):
    l = 1  # the arrow length
    widh = 0.035  # 2*widh is the width of the arrow base as triangle
    direction_map_dict = {
        "Incoming": {"tooltip": "Inflow % for state:", "color": "blue"},
        "Outgoing": {"tooltip": "Outflow % from source:", "color": "red"},
    }
    direction_label = direction_map_dict[direction]["tooltip"]
    edge_color = direction_map_dict[direction]["color"]
    # G = nx.random_geometric_graph(200, 0.125)

    fig = go.Figure()
    for edge in G.edges().data():
        #     print(edge)
        x0, y0 = G.nodes[edge[0]]["pos"]
        x1, y1 = G.nodes[edge[1]]["pos"]
        opaq = min(0.5, edge[2].get("pct_total") / 50)
        opaq = max(0.1, opaq)
        #     print(edge[2])
        fig = fig.add_trace(
            go.Scattergeo(
                locationmode="USA-states",
                lon=[x0, x1],
                lat=[y0, y1],
                hoverinfo="none",
                mode="lines",
                line=dict(width=1.5, color=edge_color),
                opacity=opaq,
            )
        )

        # The source node
        A = np.array([x0, y0])
        # The destination node
        B = np.array([x1, y1])
        v = B - A  # Subtract the source coordinates from the destination coordinates
        w = v / np.linalg.norm(v)  # scales length of B-A to 1
        u = np.array([-w[1], w[0]]) * 10  # u orthogonal on  w

        P = B - l * w  # Does a thing
        S = P - widh * u  # Does another thing
        T = P + widh * u  # Does yet another thing

        # Draw a triangle at destination to look like an arrow
        fig = fig.add_trace(
            go.Scattergeo(
                locationmode="USA-states",
                lon=[S[0], T[0], B[0], S[0]],
                lat=[S[1], T[1], B[1], S[1]],
                mode="lines",
                fill="toself",
                hoverinfo="none",
                opacity=opaq,
                fillcolor=edge_color,
                line_color=edge_color,
            )
        )

    node_x = []
    node_y = []
    states = []
    state_migs = []
    # template =
    for node in G.nodes():
        x, y = G.nodes[node]["pos"]
        state = f""
        state_migs.append(
            f"<i>{G.nodes[node]['state']}</i><br><br>{direction_label}<br>{G.nodes[node]['Migration']}"
        )
        node_x.append(x)
        node_y.append(y)
        states.append(state)

    fig = fig.add_trace(
        go.Scattergeo(
            #     locationmode = 'USA-states',
            lon=node_x,
            lat=node_y,
            hoverinfo="text",
            #     hovertext=states,
            hovertemplate="<b>%{text}</b><extra></extra>",
            #     hover_data=state_migs,
            #     text = states,
            text=state_migs,
            mode="markers",
            marker=dict(
                size=9,
                opacity=0.8,
                color="rgb(0, 200, 0)",
                line=dict(width=5, color="rgba(68, 68, 68, 0)"),
            ),
        )
    )

    fig = fig.update_layout(
        # title_text="Where states got at least 10% of their migration in 2019",
        showlegend=False,
        geo=go.layout.Geo(
            scope="north america",
            projection_type="azimuthal equal area",
            showland=True,
            landcolor="rgb(243, 243, 243)",
            countrycolor="rgb(204, 204, 204)",
        ),
        margin=dict(l=20, r=20, t=0, b=0, pad=0,),
        # width=1000,
        # height=700,
    )

    return fig

