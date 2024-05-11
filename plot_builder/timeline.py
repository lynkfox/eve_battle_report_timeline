from br.parser2 import AllData
from models.battle_report_2 import *
from data.teams import WhoseWho, Team
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime
from models.timeline2 import (
    BattleNode,
    TimelineTrace,
    UNKNOWN_COLOR,
    HAWKS_BORDER,
    HAWKS_COLOR,
    COALITION_COLOR,
    COALITION_BORDER,
)
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
        showlegend=False,
    )


def build_jclass_subplots(
    all_data: AllData, jclass_low, jclass_high, size_ref, name
) -> Tuple[List[TimelineTrace], List[str]]:
    system_order, subplot_battles = get_battles_of_j_class(
        all_data.battles, jclass_low=jclass_low, jclass_high=jclass_high
    )
    subplot = [BattleNode(battle=b).set_station_info(all_data) for b in subplot_battles]
    hawks = [b for b in subplot if b.system_owner == Team.HAWKS]
    coalition = [b for b in subplot if b.system_owner == Team.COALITION]
    other = [b for b in subplot if b.system_owner != Team.HAWKS and b.system_owner != Team.COALITION]

    subplot = [
        TimelineTrace(name=f"Coalition {name}", nodes=coalition, sizeref=size_ref),
        TimelineTrace(name=f"Hawks {name}", nodes=hawks, sizeref=size_ref),
        TimelineTrace(name=f"Other {name}", nodes=other, sizeref=size_ref),
    ]

    return subplot, system_order


def build_jspace_plots(all_data: AllData, fig: go.Figure, subplot_ranges, split_by_jclass: bool = False):
    size_ref = determine_size_reference_variable(list(all_data.battles.values()))

    subplots = []
    subplot_yaxis_ranges = []

    for r in subplot_ranges:
        sp, yaxis = build_jclass_subplots(all_data, r[1], r[2], size_ref, r[0])
        subplots.append(sp)
        subplot_yaxis_ranges.append(yaxis)

    if split_by_jclass:
        for idx, subplot in enumerate(subplots):

            for trace in subplot:
                fig.append_trace(build_scatter_trace(trace), row=idx + 1, col=1)
            for idx, yaxis in enumerate(subplot_yaxis_ranges):
                update = {
                    f"yaxis{idx+1}": {
                        "range": [yaxis[0], yaxis[-1]],
                        "categoryarray": yaxis,
                        "categoryorder": "array",
                    }
                }
                fig.update_layout(update)
    else:
        combined_ycords = []
        subplot_yaxis_ranges.reverse()

        build_important_systems_lines(fig, split_by_jclass, all_data.start_date, all_data.end_date)

        for ycords in subplot_yaxis_ranges:
            combined_ycords.extend(ycords)

        for subplot in subplots:
            for trace in subplot:
                fig.add_trace(build_scatter_trace(trace))
            add_jclass_dividers(
                fig,
                subplot_yaxis_ranges,
                ["↓ C4-Kspace ↓", "↓ C5 ↓", "↓ C6 ↓"],
                all_data.start_date,
                all_data.end_date,
            )
            fig.update_yaxes(categoryarray=combined_ycords, categoryorder="array")

    build_dummy_plots(fig, subplot_yaxis_ranges[0], split_by_jclass)
    fig.update_yaxes(showgrid=False, showspikes=True, spikedash="longdash", spikethickness=1, tickangle=-45)
    fig.update_xaxes(showspikes=True, spikedash="dot", spikethickness=1)


def add_jclass_subplot_annotations(fig: go.Figure, split_by_jclass: bool = False):
    annotations = load_json("timeline_annotations.json")

    for note, details in annotations.items():
        offset = details.get("offset", 0)

        if split_by_jclass:
            if details["class"] == "C6":
                yref = "y"
            elif details["class"] == "C5":
                yref = "y2"
            else:
                yref = "y3"

            fig.add_annotation(
                x=datetime.strptime(details["date"], "%Y-%m-%dT%H:%M"),
                y=details["system"],
                yref=yref,
                text=note,
                textangle=-10,
                yshift=offset,
                showarrow=True,
                xanchor="left",
                arrowcolor="black",
            )
        else:
            fig.add_annotation(
                x=datetime.strptime(details["date"], "%Y-%m-%dT%H:%M"),
                y=details["system"],
                text=note,
                textangle=-10,
                yshift=offset,
                showarrow=True,
                xanchor="left",
                arrowcolor="black",
            )


def add_jclass_dividers(fig: go.Figure, jclass_system_order, names, start_date, end_date):
    for idx, jclass in enumerate(jclass_system_order):
        fig.add_shape(
            type="line",
            x0=start_date,
            x1=end_date,
            y0=jclass[-1],
            y1=jclass[-1],
            line=dict(color="darkviolet", width=1),
            name=names[idx],
            layer="between",
            showlegend=False,
            label=dict(text=names[idx], padding=15),
            opacity=0.7,
        )


def build_important_systems_lines(fig: go.Figure, split_by_jclass: bool, start_date, end_date):
    for key, value in WHOSE_WHO.SystemsOfNote.items():
        fig.add_shape(
            type="line",
            x0=start_date,
            x1=end_date,
            y0=key,
            y1=key,
            line=dict(color="#828282", width=1, dash="dash"),
            name=value[0],
            layer="between",
            showlegend=False,
            opacity=0.6,
            label=dict(
                text=f"{key}: {value[0]}",
                textposition="start",
                font=(dict(size=12, color="#828282")),
                yanchor=value[1],
            ),
        )


def build_dummy_plots(fig: go.Figure, system_names, split_by_jclass: bool = False):

    fake_legend_traces = [
        go.Scatter(
            x=[datetime(2024, 3, 26)],
            y=[system_names[0]],
            name="Hawks Structure Ref/Destroyed",
            text="Hawks Structure Ref/Destroyed",
            mode="markers+text",
            textposition="middle right",
            marker=go.scatter.Marker(color=HAWKS_COLOR, size=15, line=dict(color=HAWKS_BORDER, width=3)),
            legendgroup="fake_legend",
            showlegend=False,
            hoverinfo="skip",
        ),
        go.Scatter(
            x=[datetime(2024, 3, 26)],
            y=[system_names[7]],
            name="Hawks Systems",
            text="Hawks Systems",
            mode="markers+text",
            textposition="middle right",
            marker=go.scatter.Marker(color=HAWKS_COLOR, size=15, line=dict(color="white", width=1)),
            legendgroup="fake_legend",
            showlegend=False,
            hoverinfo="skip",
        ),
        go.Scatter(
            x=[datetime(2024, 3, 26)],
            y=[system_names[14]],
            name="Coalition Structure Ref/Destroyed",
            text="Coalition Structure Ref/Destroyed",
            mode="markers+text",
            textposition="middle right",
            marker=go.scatter.Marker(color=COALITION_COLOR, size=15, line=dict(color=COALITION_BORDER, width=3)),
            legendgroup="fake_legend",
            showlegend=False,
            hoverinfo="skip",
        ),
        go.Scatter(
            x=[datetime(2024, 3, 26)],
            y=[system_names[21]],
            name="Coalition Systems",
            text="Coalition Systems",
            mode="markers+text",
            textposition="middle right",
            marker=go.scatter.Marker(color=COALITION_COLOR, size=15, line=dict(color="white", width=1)),
            legendgroup="fake_legend",
            showlegend=False,
            hoverinfo="skip",
        ),
        go.Scatter(
            x=[datetime(2024, 3, 26)],
            y=[system_names[28]],
            name="Undetermined Owner",
            text="Undetermined Owner",
            mode="markers+text",
            textposition="middle right",
            marker=go.scatter.Marker(color=UNKNOWN_COLOR, size=15, line=dict(color="white", width=1)),
            legendgroup="fake_legend",
            showlegend=False,
            hoverinfo="skip",
        ),
    ]

    for plot in fake_legend_traces:
        if split_by_jclass:
            fig.append_trace(
                plot,
                row=1,
                col=1,
            )
        else:
            fig.add_trace(plot)


def build_timeline_page(all_data: AllData, split_by_jclass: bool = False) -> go.Figure:

    jclass_subplot_ranges = [("C6", 6, 7), ("C5", 5, 6), ("KSpace-C4", 0, 5)]
    if split_by_jclass:
        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.01,
            row_heights=[0.425, 0.425, 0.15],
            subplot_titles=[x[0] for x in jclass_subplot_ranges],
        )
    else:
        fig = go.Figure()

    build_jspace_plots(all_data, fig, jclass_subplot_ranges, split_by_jclass=split_by_jclass)

    add_jclass_subplot_annotations(fig, split_by_jclass=split_by_jclass)
    last_updated = datetime.today().isoformat()
    # add title and coloring
    fig.update_layout(
        title=f"There is no War in C6 Space<br>Hover over to see info, click to go to BR<br>Last Updated {last_updated}",
        template="plotly_dark",
        paper_bgcolor="#D3D3D3",
        plot_bgcolor="#ababab",
        font=dict(color="black"),
    )

    return fig
