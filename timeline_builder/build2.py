from br.parser2 import AllData
from models.battle_report_2 import *
from data.teams import Team
from data.teams import WhoseWho
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime
from models.timeline2 import BattleNode, TimelineTrace
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data import load_json

WHOSE_WHO = WhoseWho()


@dataclass
class SystemDate:
    name: str
    date: datetime


def get_battles_of_j_class(battles: Dict[str, Battle2], jclass_low=0, jclass_high=7):
    """
    Sorts unique_system_names into extract all battles of a jclass number rannge
    (inclusive low, exclusive high, so to get all c6 use (6, 7)) and order by date
    """
    unique_sorted = []
    battles_in_jclass = [
        b
        for b in battles.values()
        if int(b.system.j_class_number) >= jclass_low and int(b.system.j_class_number) < jclass_high
    ]

    battles_in_order = sorted(battles_in_jclass, key=lambda x: x.time_data.started, reverse=False)

    for b in battles_in_order:
        if b.system.name not in unique_sorted:
            unique_sorted.append(b.system.name)

    unique_sorted.reverse()
    return unique_sorted, battles_in_jclass


def determine_size_reference_variable(battles: List[Battle2], factor: float = 100.0):
    """
    determines the max size a circle on the chart can grow too, and how to scale all other circles appropriately

    bigger factor = bigger overall max circle
    """
    return 2.0 * max([t.br_totals.isk_lost for t in battles]) / (factor**2)


def build_scatter_trace(timeline: TimelineTrace) -> go.Scatter:
    return go.Scatter(
        x=timeline.x,
        y=timeline.y,
        name=timeline.name,
        mode="markers",
        marker=timeline.marker,
        customdata=timeline.customdata,
        hovertemplate=timeline.hovertemplate,
    )


def build_jclass_subplots(
    all_data: AllData, jclass_low, jclass_high, size_ref, name
) -> Tuple[TimelineTrace, List[str]]:
    system_order, subplot_battles = get_battles_of_j_class(
        all_data.battles, jclass_low=jclass_low, jclass_high=jclass_high
    )

    subplot = TimelineTrace(
        name=name, nodes=[BattleNode(battle=b).set_station_info(all_data) for b in subplot_battles], sizeref=size_ref
    )

    return subplot, system_order


def build_jspace_plots(all_data: AllData, fig: go.Figure, subplot_ranges):
    size_ref = determine_size_reference_variable(list(all_data.battles.values()))

    subplots = []
    yaxis_order = []
    for r in subplot_ranges:
        sp, yaxis = build_jclass_subplots(all_data, r[1], r[2], size_ref, r[0])

        subplots.append(sp)
        yaxis_order.extend(yaxis)

    for idx, subplot in enumerate(subplots):

        fig.append_trace(build_scatter_trace(subplot), row=idx + 1, col=1)

    fig.update_yaxes(categoryarray=yaxis_order, categoryorder="array", gridcolor="#808080")


def add_jclass_subplot_annotations(fig):
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


def build_page(all_data: AllData) -> go.Figure:

    jclass_subplot_ranges = [("C6", 6, 7), ("C5", 5, 6), ("KSpace-C4", 0, 5)]
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.01,
        row_heights=[0.425, 0.425, 0.15],
        subplot_titles=[x[0] for x in jclass_subplot_ranges],
    )

    build_jspace_plots(all_data, fig, jclass_subplot_ranges)
    add_jclass_subplot_annotations(fig)
    last_updated = datetime.today().isoformat()
    # add title and coloring
    fig.update_layout(
        title=f"There is no War in C6 Space<br>Hover over to see info, click to go to BR<br>Last Updated {last_updated}",
        template="plotly_dark",
        paper_bgcolor="#D3D3D3",
        plot_bgcolor="#808080",
        font=dict(color="black"),
    )

    return fig
