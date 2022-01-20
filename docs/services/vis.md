# Visualisations

The ADS visualisation service returns data that is suitable for using in a network visualisation (usually). You have probably seen [some of these network visualisations](https://ui.adsabs.harvard.edu/help/actions/visualize) in the NASA/ADS web interface. 

There are two visualisation API end-points that are exposed by the `ads` package: {func}`ads.services.vis.author_network` and {func}`ads.services.vis.paper_network`. The author network and paper network functions take in an iterable of {obj}`ads.Document` objects, {obj}`ads.Library` objects, or strings of bibcodes. The documents that you provide to this function will be used to generate the network data for authors or papers. 

## Author network

Given a set of input documents, libraries, or bibcodes, you can generate data for an author network visualisation. See the example below.

```python
from ads import Document, Library
from ads.services import vis

# Retrieve a public library with ~50 papers.
lib = Library.get(id="7vKRL51sSFKXUfFVMZHC6g")

# Retrieve a couple of unrelated documents.
docs = Document.select().limit(2)

# Generate the data for the author network.
data = vis.author_network(docs, lib)
```

## Paper network

input documents, libraries, or bibcodes, you can generate data for a paper network visualisation. See the example below.

```python
from ads import Document, Library
from ads.services import vis

# Retrieve a public library with ~50 papers.
lib = Library.get(id="7vKRL51sSFKXUfFVMZHC6g")

# Retrieve a couple of unrelated documents.
docs = Document.select().limit(2)

# Generate the data for the paper network.
data = vis.paper_network(docs, lib)
```


:::{Note}
Currently these functions just return the network data provided by ADS. You can use these data with a visualisation library (e.g., [D3](https://d3js.org/)) to generate figures. In future the `ads` package will produce these kinds of figures for you, but it is low priority. If you'd like to contribute to these efforts, please submit a pull request through [GitHub](https://github.com/andycasey/ads).
:::
