import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from timeline_builder.build import build_timeline_nodes, map_battles, build_timelines
from models.battle_report import Battle
from models.timeline import TimelineNode
from typing import List
from pandas import DataFrame
from datetime import datetime
from data import load_json


def build_scatter(battles: List[Battle]):

    # fig = go.Figure(
    #     layout=dict(
    #         title="There is no war in C6 Wormhole Space",
    #         hovermode="closest"
    #     )
    # )

    timeline_nodes, mapping = build_timelines(battles)

    fields = list(TimelineNode.model_fields.keys())
    # add calculated property fields
    fields.extend(TimelineNode.extra_properties())

    system_name_order = get_system_order_by_class(battles)

    sizeref = determine_size_reference_variable(timeline_nodes)

    fig = make_subplots(
        rows=len(system_name_order.keys()),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.01,
        row_heights=[0.425, 0.425, 0.15],
        subplot_titles=[*list(system_name_order.keys())],
    )

    for idx, j_c in enumerate(list(system_name_order.keys())):
        traces = create_subplot_traces(mapping, fields, system_name_order, sizeref, idx, j_c)

        for trace in traces:
            fig.append_trace(trace, idx + 1, 1)

    add_annotations_and_format(fig)

    fig.show()
    fig.write_html("docs/war.html")


def determine_size_reference_variable(timeline_nodes, factor: float = 100.0):
    """
    determines the max size a circle on the chart can grow too, and how to scale all other circles appropriately

    bigger factor = bigger overall max circle
    """
    return 2.0 * max([t.raw_isk_destroyed for t in timeline_nodes]) / (factor**2)


def create_subplot_traces(mapping, fields, system_name_order, sizeref, idx, j_c):
    nodes = build_timeline_nodes(system_name_order[j_c], mapping)
    data = DataFrame({field_name: getattr(battle, field_name) for field_name in fields} for battle in nodes)
    unique_system_names = list(set([b.system.name for b in system_name_order[j_c]]))
    unique_system_names = sorted(
        unique_system_names, key=lambda x: mapping.systems[x][0].time_data.started, reverse=True
    )
    traces = [
        go.Scatter(
            x=data[data["system_name"] == system_name]["date"],
            y=data[data["system_name"] == system_name]["system_name"],
            name=system_name,
            mode="markers",
            marker=dict(
                color=data[data["system_name"] == system_name]["owner_color"],
                size=data[data["system_name"] == system_name]["raw_isk_destroyed"],
                line=dict(
                    color=data[data["system_name"] == system_name]["border_color"],
                    width=data[data["system_name"] == system_name]["border_width"],
                ),
                sizemode="area",
                sizeref=sizeref,
                sizemin=4,
            ),
            # marker_symbol=data[data["system_name"]== system_name]["symbol"],
            legendgroup=j_c,
            legend=f"legend{idx+1}",
            legendgrouptitle_text=j_c,
            customdata=data[data["system_name"] == system_name]["hover_text"],
            hovertemplate="%{customdata[0]}<br>%{customdata[1]}<br><br>%{customdata[2]}<br>%{customdata[3]}<br>%{customdata[4]}<br>%{customdata[5]}<extra>%{customdata[6]}</extra>",
        )
        for system_name in unique_system_names
    ]

    return traces


def add_annotations_and_format(fig):
    annotations = load_json("special_systems.json")

    for note, details in annotations.items():
        if details["class"] == "C6":
            yref = "y"
        elif details["class"] == "C5":
            yref = "y2"
        else:
            yref = "y3"

        offset = details.get("offset", 0)
        fig.add_annotation(
            x=datetime.strptime(details["date"], "%Y-%m-%dT%H:%M"),
            y=details["system"],
            yref=yref,
            text=note,
            textangle=-10,
            yshift=offset,
            showarrow=True,
            xanchor="left",
        )

    fig.update_layout(
        title="There is no War in C6 Space ( circle size = total isk destroyed (including trash) ) - Some things are still inaccurate - WIP",
        legend=dict(groupclick="toggleitem", indentation=10, xref="container", yref="paper", x=0.8),
        legend2=dict(groupclick="toggleitem", indentation=10, xref="container", yref="paper", x=0.9),
        legend3=dict(groupclick="toggleitem", indentation=10, xref="container", yref="paper", x=1),
        template="plotly_dark",
        paper_bgcolor="#D3D3D3",
        plot_bgcolor="#808080",
        font=dict(color="black"),
    )


def get_system_order_by_class(battles: List[Battle]):

    output = {}
    for battle in battles:
        j_class = battle.system.j_class
        if j_class in ["C4", "C3", "C2", "C1", "CNone"]:
            j_class = "C1-C4, K-Space"
        output.setdefault(j_class, []).append(battle)

    # for key, value in output.items():
    #     sorted_battles = sorted(value, key=lambda x: x.time_data.started)

    #     output[key] = sorted_battles

    return output
