import hvplot.pandas
import hvplot.xarray
from pystac_client import Client

# plot size settings
frame_width = 600
frame_height = 600

# line width of polygons
line_width = 3

# plot polygons as lines on a slippy map with background tiles.
def plot_polygons(data, *args, **kwargs):
    return data.hvplot.paths(*args, geo=True, tiles='OSM', xaxis=None, yaxis=None,
                             frame_width=frame_width, frame_height=frame_height,
                             line_width=line_width, **kwargs)


