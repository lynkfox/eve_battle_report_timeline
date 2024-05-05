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
from models.totals import DailyTotal, TotalsTraceData, TotalsTraces
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data import load_json

WHOSE_WHO = WhoseWho()


def split_battles_into_days(all_data: AllData) -> List[DailyTotal]:
    output = {}
    all_battles = list(all_data.battles.values())
    sorted(all_battles, key=lambda x: x.time_data.started)

    for battle in all_battles:
        output.setdefault(battle.time_data.started.strftime("%b %d"), []).append(battle)

    return [DailyTotal(battles=v) for v in output.values()]


def BuildTotals(all_data: AllData):

    daily_totals = split_battles_into_days(all_data)

    hawks = TotalsTraceData(team=Team.HAWKS, daily_totals=daily_totals)
    coalition = TotalsTraceData(team=Team.COALITION, daily_totals=daily_totals)

    return hawks, coalition, daily_totals


def build_totals_page(all_data: AllData):
    fig = make_subplots(
        rows=4,
        cols=2,
        shared_xaxes=True,
        vertical_spacing=0.04,
        subplot_titles=[
            "Total Isk Lost",
            "Total Ships Lost",
            "Daily Isk Lost",
            "Daily Ships Lost",
            "Total Structures Lost",
            'Total Systems "Lost"',
            "Daily Structures Lost",
            'Daily Systems "Lost"',
        ],
    )

    hawks, coalition, all_daily = BuildTotals(all_data)

    add_traces(fig, hawks, coalition, "isk", 1, 1)
    add_traces(fig, hawks, coalition, "ship", 1, 2)
    add_traces(fig, hawks, coalition, "structure", 3, 1)
    add_traces(fig, hawks, coalition, "system", 3, 2)

    fig.append_trace(
        go.Scatter(
            name="Total Battles",
            x=hawks.x,
            y=hawks.total_battles,
            mode="lines+markers",
            line=dict(color="darkorchid", width=2, dash="dash"),
            hovertemplate="Battles To Date: %{y}<extra></extra>",
        ),
        row=3,
        col=2,
    )
    last_updated = datetime.today().strftime("%Y-%m-%d")
    fig.update_layout(
        title=f"There is no War in C6 Space<br>Daily Totals. Lines are cumulative to date. - Bigger numbers are BAD<br>Last Updated {last_updated}<br><br>",
        template="plotly_dark",
        paper_bgcolor="#D3D3D3",
        plot_bgcolor="#ababab",
        font=dict(color="black"),
    )
    return fig


def add_traces(fig: go.Figure, hawks: TotalsTraces, coalition: TotalsTraces, trace_type: str, row, col):
    hawks_totals, hawks_daily = hawks.all_plots.get_traces(trace_type)
    coalition_totals, coalition_daily = coalition.all_plots.get_traces(trace_type)
    fig.append_trace(hawks_totals, row=row, col=col)
    fig.append_trace(coalition_totals, row=row, col=col)
    fig.append_trace(hawks_daily, row=row + 1, col=col)
    fig.append_trace(coalition_daily, row=row + 1, col=col)

    if trace_type == "isk":
        y_title = "Isk (Billions)"
    if trace_type == "ship":
        y_title = "Ships"
    if trace_type == "structure":
        y_title = "Structures"
    if trace_type == "system":
        y_title = "Systems/Battles"

    fig.update_yaxes(title_text=y_title, row=row, col=col)
    fig.update_yaxes(showgrid=True, showspikes=True, spikedash="longdash", spikethickness=1, tickangle=-45)
    fig.update_xaxes(showgrid=False, showspikes=True, spikedash="dot", spikethickness=1, tickangle=30)
