import plotly.express as px
import plotly.graph_objects as go
from timeline_builder.build import build_timelines
from models.battle_report import Battle
from models.timeline import TimelineNode
from typing import List
from pandas import DataFrame


def build_scatter(battles: List[Battle]):

    timeline_nodes, mapping = build_timelines(battles)

    fields = list(TimelineNode.model_fields.keys())
    # add calculated property fields
    fields.extend(TimelineNode.extra_properties())
    data = DataFrame({field_name: getattr(battle, field_name) for field_name in fields} for battle in timeline_nodes)

    fig = px.scatter(
        data,
        x="date",
        y="system_name",
        size="total_isk_destroyed",
        color="system_name",
        hover_name="system_name",
        size_max=60,
        title="There is no War in C6 Space",
        labels={
            "date": "Date of Battle",
            "system_class": "Wormhole Class",
            "system_weather": "Weather Effect",
            "system_name": "System Name",
        },
    )

    # for sys_name, sys_battles in mapping.systems.items():
    #     by_system_node, _ = build_timelines(sys_battles)
    #     system_df = DataFrame({field_name: getattr(battle, field_name) for field_name in fields} for battle in by_system_node)
    #     fig.add_trace(go.scatter.Line(name=sys_name, x=system_df["date"], y=system_df["system_name"], mode="lines"))

    fig.show()
