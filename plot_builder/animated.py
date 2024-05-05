import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plot_builder.build import build_timeline_nodes, map_battles, build_timelines
from models.battle_report import Battle
from models.timeline import TimelineNode
from typing import List
from pandas import DataFrame
from datetime import datetime, timedelta
from data import load_json
from dataclasses import dataclass
from plot_builder.output import determine_size_reference_variable, create_subplot_traces


@dataclass
class FrameBattles:
    start: datetime
    end: datetime  # non inclusive
    battles: dict = {}
    traces: list = []

    def render(self):

        pass


def build_animated_scatter(battles: List[Battle], frame_datetime_period: int = 12):

    frames = get_datetime_ranges_of_period_length(frame_datetime_period, battles)

    for battle in battles:
        frame_number = 0
        for time_period in frames:
            frame_number += 1
            if battle.time_data.started >= time_period.start and battle.time_data.started < time_period.end:
                j_class = battle.system.j_class
                subplot_key = j_class if j_class == "C6" or j_class == "C5" else "C1-C4, K-Space"
                time_period.battles.setdefault(subplot_key, []).append(battle)


def get_datetime_ranges_of_period_length(frame_datetime_period, battles):
    all_dates = [b.time_data.started for b in battles]
    earliest = min(all_dates)
    latest = max(all_dates)

    number_of_frames = (latest - earliest) / timedelta(hours=frame_datetime_period)
    frame_time_ranges = []
    starting = earliest
    for i in range(1, number_of_frames + 1):
        ending = starting + i * timedelta(hours=frame_datetime_period)
        frame_time_ranges.append(FrameBattles(start=starting, end=ending))
        starting = ending

    return frame_time_ranges
