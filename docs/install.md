# Install

:::{warning}
Version 1 of this package is unstable and under active development. If you want to test Version 1 before it is released then you should install directly from source using the ``v1`` branch on GitHub. 

This warning message should be removed when Version 1 is released.

To install Version 1 from source code using the ``v1`` branch on [GitHub](https://github.com/andycasey/ads):

```bash
git clone -b v1 https://github.com/andycasey/ads.git
cd ads
python setup.py install

# Run the post-install script to setup a local database
ads-setup
```

If you encounter any unexpected behaviour with Version 1 and [there isn't an issue about it](https://github.com/andycasey/ads/issues) already, please [create one](https://github.com/andycasey/ads/issues/new). Your experience is invaluable for building the best tool for the community!
:::

## Installation

The recommended method to install ``ads`` is with [conda](https://conda.io/). You can also install ``ads`` using [pip](https://pip.pypa.io/en/stable/), or download the source code directly from GitHub.

The ``ads`` package comes with a post-installation script, ``ads-setup``. This is used to create a local [SQLite](https://www.sqlite.org/index.html) database, which enables a powerful query syntax. SQLite comes bundled with Python, so you won't need to install anything extra.

``````{tab} Using conda
```bash
conda install -c conda-forge ads

# Run the post-install script to setup a local database
ads-setup
```
``````
``````{tab} Using pip
```bash
python -m pip install -U ads

# Run the post-install script to setup a local database
ads-setup
```
``````
``````{tab} Source code
```bash
git clone https://github.com/andycasey/ads.git
cd ads
python setup.py install

# Run the post-install script to setup a local database
ads-setup
```
``````

:::{note}
`ads` requires Python 3.6 or later.
:::

&nbsp;

## Testing

If you want to run the unit tests, you will need to install ``ads`` from source code.

Unit tests are [executed through GitHub Actions](https://github.com/andycasey/ads/actions/) after every push, or pull request. To execute the tests:
```bash
pytest
```

All of the tests should pass. If they don't, and there is no obvious reason why they do not, you can [open an issue on GitHub](https://github.com/andycasey/ads/issues/create).

&nbsp;

## Building documentation locally

If you want to view the documentation locally, then you will need to install ``ads`` from source code.

Building the documentation requires a number of additional dependencies. After you have installed ``ads`` using the 'Source code' instructions above, you can install the additional dependencies using the following command:
```bash
pip install -r docs/requirements.txt
```

Now to build and view the documentation:
```bash
cd docs/
make html
open _build/html/index.html
```
