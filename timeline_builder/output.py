from typing import List

import plotly.express as px
from pandas import DataFrame

from models.battle_report import Battle
from models.timeline import TimelineNode
from timeline_builder.build import build_timelines


def build_scatter(battles: List[Battle]):

    timeline_nodes = build_timelines(battles)

    fields = list(TimelineNode.model_fields.keys())
    # add calculated property fields
    fields.extend(TimelineNode.extra_properties())
    data = DataFrame({field_name: getattr(battle, field_name) for field_name in fields} for battle in timeline_nodes)

    fig = px.scatter(
        data,
        x="date",
        y="system_class",
        size="total_isk_destroyed",
        color="hawks_won",
        symbol="system_weather",
        hover_name="system_name",
        size_max=45,
        labels={"date": "Date of Battle", "system_class": "Wormhole Class", "system_weather": "Weather Effect"},
    )

    fig.show()
