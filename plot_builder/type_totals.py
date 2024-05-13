from plot_builder.daily_totals import split_battles_into_days
from br.parser2 import AllData
from plot_builder.timeline import HAWKS_COLOR, COALITION_COLOR, UNKNOWN_COLOR
from plotly.subplots import make_subplots
from data.teams import Team
from models.eve import EntityType
from models.type_totals import EntityTraceTotal, ShipTotals
import plotly.graph_objects as go


def build_ships_totals(all_data: AllData):

    ships = ShipTotals(all_data.battles.values(), entity_type=EntityType.SHIP)

    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=["Ships", "Ships"],
    )

    middle_point_of_ships = int(len(ships.x) / 2)

    for team, team_y in ships.y_values.items():
        if team == Team.UNKNOWN:
            continue
        top, bottom = team_y.build_traces(
            ships.x, middle_point_of_ships, offset_value=-0.4 if team == Team.HAWKS else 0
        )
        for trace in top:
            fig.append_trace(trace, row=1, col=1)
        for trace in bottom:
            fig.append_trace(trace, row=2, col=1)

    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Ships", row=1, col=1)
    fig.update_yaxes(showgrid=True, showspikes=True, spikedash="longdash", spikethickness=1, tickangle=-45)
    fig.update_xaxes(
        spikemode="marker", showgrid=False, showspikes=True, spikedash="dot", spikethickness=1, tickangle=30
    )

    return fig
