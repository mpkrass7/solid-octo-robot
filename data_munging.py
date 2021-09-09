import networkx as nx
import numpy as np
import pandas as pd
import streamlit as st

ALL_STATES_TITLE = "OVERALL US"
DIRECT_DICT = {"Outgoing": "mig_state", "Incoming": "state"}
OPPOSITE_DICT = {"Incoming": "mig_state", "Outgoing": "state"}


def get_coordinates():
    state_coordinates = pd.read_csv("data/state_coordinates.csv")
    # state_coordinates['pos'] = [(i,j) for i,j in zip(minmax_scale(state_coordinates.longitude,(0,1)), minmax_scale(state_coordinates.latitude,(0,1)))]
    state_coordinates["pos"] = [
        (i, j) for i, j in zip(state_coordinates.longitude, state_coordinates.latitude)
    ]
    state_coordinates["name"] = state_coordinates.name.str.upper()
    return state_coordinates


def compute_edges(state_migration, threshold, state=None, direction="Incoming"):

    assert direction is not None
    assert state is not None

    df_direction = DIRECT_DICT[direction]
    df_opposite_direction = OPPOSITE_DICT[direction]

    if state != ALL_STATES_TITLE:
        state_migration = state_migration.loc[lambda x: x[df_direction] == state]
    else:
        threshold = min(threshold, 5)
    state_migration["rank"] = state_migration.groupby(df_direction)[
        "household_weight"
    ].rank("dense", ascending=False)

    state_migration_total = state_migration.groupby(df_direction)[
        "household_weight"
    ].sum()
    state_migration = (
        state_migration.assign(
            pct_total=np.round(
                state_migration.household_weight
                / state_migration[df_direction].map(state_migration_total)
                * 100,
                2,
            )
        )
        .loc[lambda x: x["rank"] <= threshold]
        .sort_values(by="pct_total", ascending=False)
    )
    state_migration["combine"] = (
        state_migration[df_opposite_direction]
        + " "
        + state_migration.pct_total.astype(str)
        + "% Total: "
        + state_migration["household_weight"].astype(int).map("{:,d}".format)
    )

    return state_migration


def compute_nodes(state_coordinates, migration_edges, direction="Incoming"):

    df_direction = DIRECT_DICT[direction]

    total_migration = pd.DataFrame(
        migration_edges.groupby(df_direction)["combine"]
        .transform(lambda x: "<br>".join(x))
        .reset_index(drop=True)
        .drop_duplicates()
    )
    total_migration["state"] = migration_edges[df_direction].unique()
    state_coordinates["Migration"] = (
        state_coordinates["name"]
        .map(dict(zip(total_migration.state, total_migration["combine"])))
        .fillna("")
    )
    return state_coordinates


def build_network(nodes, edges):
    node_dict = nodes.set_index("name").to_dict("index")
    G = nx.from_pandas_edgelist(
        edges,
        source="mig_state",
        target="state",
        edge_attr=["household_weight", "pct_total"],
        create_using=nx.DiGraph(),
    )
    nx.set_node_attributes(G, node_dict)
    return G


def do_the_whole_thing():
    """ Thinking about making this call all of the previous functions"""
    pass


def table_edges(edges, direction):
    direction_map_dict = {
        "Incoming": {"colname": "% of Incoming Migration from Source"},
        "Outgoing": {"colname": "% of Outgoing Migration from Source"},
    }
    edges = (
        edges.drop(columns="combine")
        .sort_values(by="pct_total", ascending=False)
        .assign(
            household_weight=lambda x: x.household_weight.astype(int).map(
                "{:,d}".format
            ),
            pct_total=lambda x: np.round(x.pct_total, 2).astype(str) + "%",
            hack="",
        )
        .set_index("hack")
    )[["mig_state", "state", "household_weight", "pct_total"]]
    edges.columns = [
        "Source State",
        "Destination State",
        "Total People",
        direction_map_dict[direction].get("colname"),
    ]
    return edges


def paginate_dataframe(dataframe, page_size, page_num):

    page_size = page_size

    if page_size is None:

        return None

    offset = page_size * (page_num - 1)

    return dataframe[offset : offset + page_size]


def display_state(state):
    return state if state != ALL_STATES_TITLE else ""


def display_state_summary(state, df):
    if state == ALL_STATES_TITLE:
        return ""
    else:
        df = (
            df.loc[lambda x: x.state == state]
            .reset_index()
            .assign(
                total_migration=lambda x: x.inbound_migration
                + x.outbound_migration
                + x.within_state_migration
            )
        )

        total_migration = df.total_migration[0]

        inbound_migration = df.inbound_migration[0]
        inbound_pct_total = f"{round(inbound_migration / total_migration * 100,1)}%"
        outbound_migration = df.outbound_migration[0]
        outbound_pct_total = f"{round(outbound_migration / total_migration * 100,1)}%"
        within_state_migration = df.within_state_migration[0]
        within_state_pct_total = (
            f"{round(within_state_migration / total_migration * 100,1)}%"
        )

        return f"""
        **Inbound Migration Total (%):** 
        
        {"{:,}".format(inbound_migration)} ({inbound_pct_total})

        **Outbound Migration Total (%):** 
        
        {"{:,}".format(outbound_migration)} ({outbound_pct_total}) 

        **Within State Migration Total (%):** 
        
        {"{:,}".format(within_state_migration)} ({within_state_pct_total})
        """
