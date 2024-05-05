import plotly.graph_objects as go
from plotly.offline import plot
from plot_builder.timeline import build_timeline_page
from plot_builder.totals import build_totals_page
import re
from br.parser2 import AllData
import webbrowser
import os


def build_scatter(all_data: AllData):  ## attempt to add onclick go to battle report
    print("creating timeline plot")
    fig = build_timeline_page(all_data)
    file_path = "docs/war.html"
    build_onclick_link_html(fig, "customdata[0]", file_path)
    webbrowser.open("file://" + os.path.realpath(file_path))

    print("creating totals data")
    fig2 = build_totals_page(all_data)
    file_path2 = "docs/daily_totals.html"
    fig2.show()
    fig2.write_html(file_path2)


def build_onclick_link_html(fig, link_value: str = "customdata[0]", file_name: str = "with_hyperlinks.html"):
    # Get HTML representation of plotly.js and this figure
    plot_div = plot(fig, output_type="div", include_plotlyjs=True)

    # Get id of html div element that looks like
    # <div id="301d22ab-bfba-4621-8f5d-dc4fd855bb33" ... >
    res = re.search('<div id="([^"]*)"', plot_div)
    div_id = res.groups()[0]

    # Build JavaScript callback for handling clicks
    # and opening the URL in the trace's customdata
    js_callback = """
    <script>
    var plot_element = document.getElementById("{div_id}");
    plot_element.on('plotly_click', function(data){{
        console.log(data);
        var point = data.points[0];
        if (point) {{
            console.log(point.LINK_VALUE);
            window.open(point.LINK_VALUE);
        }}
    }})
    </script>
    """.format(
        div_id=div_id
    ).replace(
        "LINK_VALUE", link_value
    )

    # Build HTML string
    html_str = """
    <html>
    <body>
    {plot_div}
    {js_callback}
    </body>
    </html>
    """.format(
        plot_div=plot_div, js_callback=js_callback
    )

    with open(file_name, "w", encoding="utf-8") as f:
        f.write(html_str)
