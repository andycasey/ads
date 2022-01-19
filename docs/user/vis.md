# Visualisations

The ADS visualisation service returns data that is suitable for using in a network visualisation (usually). You have probably seen [some of these network visualisations](https://ui.adsabs.harvard.edu/help/actions/visualize) in the NASA/ADS web interface. There are two visualisation API end-points that are exposed by the `ads` package: {func}`ads.services.vis.author_network` and {func}`ads.services.vis.paper_network`.

## Overview

The author network and paper network functions take in an iterable of {obj}`ads.Document` objects, {obj}`ads.Library` objects, or strings of bibcodes. The documents that you provide to this function will be used to generate the network data for authors or papers. 

## Author network



## Paper network



:::{Note}
Currently these functions just return the network data provided by ADS. You can use these data with a visualisation library (e.g., [D3](https://d3js.org/)) to generate figures. In future the `ads` package will produce these kinds of figures for you, but it is low priority. If you'd like to contribute to these efforts, please fork us on [GitHub](github.com/andycasey/ads)!
:::