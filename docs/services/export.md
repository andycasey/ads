# Export

The ADS export service returns BibTeX and other formats for a set of records. 

## Overview

The export service in ADS ({obj}`ads.services.export`) has functions to export citation strings for documents and libraries. You can use these function to export records into any format. These functions always returns a string, and it takes in any combination of:
 - {obj}`ads.Document` objects,
 - {obj}`ads.Library` objects, or 
 - strings of bibcodes.

You can use these formats together in the command. For example, when calling {obj}`ads.services.export.ads` you can give bibcode strings, some {obj}`ads.Library` objects, and some {obj}`ads.Document` objects all in the one function call.

## API

```{eval-rst}
.. autosummary::
    :nosignatures:

    ads.services.export.ads
    ads.services.export.bibtex
    ads.services.export.bibtexabs
    ads.services.export.endnote
    ads.services.export.medlars
    ads.services.export.procite
    ads.services.export.refworks
    ads.services.export.ris
    ads.services.export.aastex
    ads.services.export.icarus
    ads.services.export.mnras
    ads.services.export.soph
    ads.services.export.dcxml
    ads.services.export.refxml
    ads.services.export.refabsxml
    ads.services.export.votable
    ads.services.export.csl
    ads.services.export.custom
    ads.services.export.ieee
```

:::{note}
Most (*but not all*) of these API end points have the same arguments. Here are some contrarian examples:

- {obj}`ads.services.export.custom` requires a ``format`` argument and does not allow for ``sort``
- {obj}`ads.services.export.csl` requires both a ``style`` and ``format`` argument
- {obj}`ads.services.export.bibtex` has optional arguments: ``max_author``, ``author_cutoff``, ``key_format``, and ``journal_format``
- {obj}`ads.services.export.bibtexabs` has the same optional arguments as {obj}`ads.services.export.bibtex`, but the default value for ``max_author`` is different (the difference comes from the defaults in the ADS API endpoints, not from the ``ads`` package).

Be sure to check the required and optional arguments for each function.
:::


## Export a single record

In the example below you can see the Python code and the example output in different tabs.

``````{tab} Python
```python
from ads import Document
import ads.services.export as export

# Retrieve any document.
doc = Document.get()

# Print the exported citation for this document.
print(export.bibtex(doc))
```
``````
``````{tab} Output
```bibtex
@ARTICLE{1996PhRvL..77.3865P,
       author = {{Perdew}, John P. and {Burke}, Kieron and {Ernzerhof}, Matthias},
        title = "{Generalized Gradient Approximation Made Simple}",
      journal = {\prl},
         year = 1996,
        month = oct,
       volume = {77},
       number = {18},
        pages = {3865-3868},
          doi = {10.1103/PhysRevLett.77.3865},
       adsurl = {https://ui.adsabs.harvard.edu/abs/1996PhRvL..77.3865P},
      adsnote = {Provided by the SAO/NASA Astrophysics Data System}
}
```
``````

## Export multiple records

Exporting data for multiple records is very similar to a single record request. In the example below you can see the Python code and the example output in different tabs.

``````{tab} Python
```python
from ads import Document
import ads.services.export as export

# Retrieve 3 documents
docs = Document.select().limit(3)

# Some hand-crafted bibcodes:
other_docs = ["2015ApJ...808...16N", "2017arXiv171103234K"]

# Print the exported citations.
print(export.bibtex(other_docs, docs))
```
``````
``````{tab} Output
```bibtex
@ARTICLE{2017arXiv171103234K,
       author = {{Kollmeier}, Juna A. and {Zasowski}, Gail and {Rix}, Hans-Walter and {Johns}, Matt and {Anderson}, Scott F. and {Drory}, Niv and {Johnson}, Jennifer A. and {Pogge}, Richard W. and {Bird}, Jonathan C. and {Blanc}, Guillermo A. and {Brownstein}, Joel R. and {Crane}, Jeffrey D. and {De Lee}, Nathan M. and {Klaene}, Mark A. and {Kreckel}, Kathryn and {MacDonald}, Nick and {Merloni}, Andrea and {Ness}, Melissa K. and {O'Brien}, Thomas and {Sanchez-Gallego}, Jose R. and {Sayres}, Conor C. and {Shen}, Yue and {Thakar}, Ani R. and {Tkachenko}, Andrew and {Aerts}, Conny and {Blanton}, Michael R. and {Eisenstein}, Daniel J. and {Holtzman}, Jon A. and {Maoz}, Dan and {Nandra}, Kirpal and {Rockosi}, Constance and {Weinberg}, David H. and {Bovy}, Jo and {Casey}, Andrew R. and {Chaname}, Julio and {Clerc}, Nicolas and {Conroy}, Charlie and {Eracleous}, Michael and {G{\"a}nsicke}, Boris T. and {Hekker}, Saskia and {Horne}, Keith and {Kauffmann}, Jens and {McQuinn}, Kristen B.~W. and {Pellegrini}, Eric W. and {Schinnerer}, Eva and {Schlafly}, Edward F. and {Schwope}, Axel D. and {Seibert}, Mark and {Teske}, Johanna K. and {van Saders}, Jennifer L.},
        title = "{SDSS-V: Pioneering Panoptic Spectroscopy}",
      journal = {arXiv e-prints},
     keywords = {Astrophysics - Astrophysics of Galaxies},
         year = 2017,
        month = nov,
          eid = {arXiv:1711.03234},
        pages = {arXiv:1711.03234},
archivePrefix = {arXiv},
       eprint = {1711.03234},
 primaryClass = {astro-ph.GA},
       adsurl = {https://ui.adsabs.harvard.edu/abs/2017arXiv171103234K},
      adsnote = {Provided by the SAO/NASA Astrophysics Data System}
}

@ARTICLE{2015ApJ...808...16N,
       author = {{Ness}, M. and {Hogg}, David W. and {Rix}, H. -W. and {Ho}, Anna. Y.~Q. and {Zasowski}, G.},
        title = "{The Cannon: A data-driven approach to Stellar Label Determination}",
      journal = {\apj},
     keywords = {methods: data analysis, methods: statistical, stars: abundances, stars: fundamental parameters, surveys, techniques: spectroscopic, Astrophysics - Solar and Stellar Astrophysics, Astrophysics - Astrophysics of Galaxies, Astrophysics - Instrumentation and Methods for Astrophysics},
         year = 2015,
        month = jul,
       volume = {808},
       number = {1},
          eid = {16},
        pages = {16},
          doi = {10.1088/0004-637X/808/1/16},
archivePrefix = {arXiv},
       eprint = {1501.07604},
 primaryClass = {astro-ph.SR},
       adsurl = {https://ui.adsabs.harvard.edu/abs/2015ApJ...808...16N},
      adsnote = {Provided by the SAO/NASA Astrophysics Data System}
}

@ARTICLE{1996PhRvL..77.3865P,
       author = {{Perdew}, John P. and {Burke}, Kieron and {Ernzerhof}, Matthias},
        title = "{Generalized Gradient Approximation Made Simple}",
      journal = {\prl},
         year = 1996,
        month = oct,
       volume = {77},
       number = {18},
        pages = {3865-3868},
          doi = {10.1103/PhysRevLett.77.3865},
       adsurl = {https://ui.adsabs.harvard.edu/abs/1996PhRvL..77.3865P},
      adsnote = {Provided by the SAO/NASA Astrophysics Data System}
}

@ARTICLE{1996PhRvB..5411169K,
       author = {{Kresse}, G. and {Furthm{\"u}ller}, J.},
        title = "{Efficient iterative schemes for ab initio total-energy calculations using a plane-wave basis set}",
      journal = {\prb},
     keywords = {71.10.-w, 71.15.-m, 71.15.Ap, 71.15.Hx, Theories and models of many-electron systems, Methods of electronic structure calculations, Basis sets  and related methodology},
         year = 1996,
        month = oct,
       volume = {54},
       number = {16},
        pages = {11169-11186},
          doi = {10.1103/PhysRevB.54.11169},
       adsurl = {https://ui.adsabs.harvard.edu/abs/1996PhRvB..5411169K},
      adsnote = {Provided by the SAO/NASA Astrophysics Data System}
}

@ARTICLE{1965PhRv..140.1133K,
       author = {{Kohn}, W. and {Sham}, L.~J.},
        title = "{Self-Consistent Equations Including Exchange and Correlation Effects}",
      journal = {Physical Review},
         year = 1965,
        month = nov,
       volume = {140},
       number = {4A},
        pages = {1133-1138},
          doi = {10.1103/PhysRev.140.A1133},
       adsurl = {https://ui.adsabs.harvard.edu/abs/1965PhRv..140.1133K},
      adsnote = {Provided by the SAO/NASA Astrophysics Data System}
}
```
``````

## Export records from an {obj}`ads.Library`

You can supply {obj}`ads.Document`, a bibcode string, or a {obj}`ads.Library` to the {func}`ads.services.export.export` function. If a {obj}`ads.Library` is given, then all {obj}`ads.Document`s in that library will be exported.

``````{tab} Python
```python
from ads import Library
import ads.services.export as export

# Retrieve a public library with ~50 papers.
lib = Library.get(id="7vKRL51sSFKXUfFVMZHC6g")

# Export all documents in the library in AASTeX format.
output = export.aastex(lib)

# Print it.
print(output)

# Or write it to a file.
with open("bibliography.bbl", "w") as fp:
    fp.write(output)
```
``````
``````{tab} Output
```latex
\bibitem[Gaia Collaboration et al.(2020)]{2020A&A...642C...1G} Gaia Collaboration, Helmi, A., van Leeuwen, F., et al.\ 2020, \aap, 642, C1. doi:10.1051/0004-6361/202039217
\bibitem[Gaia Collaboration et al.(2020)]{2020A&A...637C...3G} Gaia Collaboration, Helmi, A., van Leeuwen, F., et al.\ 2020, \aap, 637, C3. doi:10.1051/0004-6361/201832698e
\bibitem[Pelisoli \& Vos(2019)]{2019MNRAS.488.2892P} Pelisoli, I. \& Vos, J.\ 2019, \mnras, 488, 2892. doi:10.1093/mnras/stz1876
\bibitem[Gandhi et al.(2019)]{2019MNRAS.485.2642G} Gandhi, P., Rao, A., Johnson, M.~A.~C., et al.\ 2019, \mnras, 485, 2642. doi:10.1093/mnras/stz438
\bibitem[Rimoldini et al.(2019)]{2019A&A...625A..97R} Rimoldini, L., Holl, B., Audard, M., et al.\ 2019, \aap, 625, A97. doi:10.1051/0004-6361/201834616
\bibitem[Gaia Collaboration et al.(2019)]{2019A&A...623A.110G} Gaia Collaboration, Eyer, L., Rimoldini, L., et al.\ 2019, \aap, 623, A110. doi:10.1051/0004-6361/201833304
\bibitem[Katz et al.(2019)]{2019A&A...622A.205K} Katz, D., Sartoretti, P., Cropper, M., et al.\ 2019, \aap, 622, A205. doi:10.1051/0004-6361/201833273
\bibitem[Clementini et al.(2019)]{2019A&A...622A..60C} Clementini, G., Ripepi, V., Molinaro, R., et al.\ 2019, \aap, 622, A60. doi:10.1051/0004-6361/201833374
\bibitem[Marrese et al.(2019)]{2019A&A...621A.144M} Marrese, P.~M., Marinoni, S., Fabrizio, M., et al.\ 2019, \aap, 621, A144. doi:10.1051/0004-6361/201834142
\bibitem[Roelens et al.(2018)]{2018A&A...620A.197R} Roelens, M., Eyer, L., Mowlavi, N., et al.\ 2018, \aap, 620, A197. doi:10.1051/0004-6361/201833357
\bibitem[Moln{\'a}r et al.(2018)]{2018A&A...620A.127M} Moln{\'a}r, L., Plachy, E., Juh{\'a}sz, {\'A}. L., et al.\ 2018, \aap, 620, A127. doi:10.1051/0004-6361/201833514
\bibitem[Mowlavi et al.(2018)]{2018A&A...618A..58M} Mowlavi, N., Lecoeur-Ta{\"\i}bi, I., Lebzelter, T., et al.\ 2018, \aap, 618, A58. doi:10.1051/0004-6361/201833366
\bibitem[Holl et al.(2018)]{2018A&A...618A..30H} Holl, B., Audard, M., Nienartowicz, K., et al.\ 2018, \aap, 618, A30. doi:10.1051/0004-6361/201832892
\bibitem[Forveille et al.(2018)]{2018A&A...616E...1F} Forveille, T., Kotak, R., Shore, S., et al.\ 2018, \aap, 616, E1. doi:10.1051/0004-6361/201833955
\bibitem[Arenou et al.(2018)]{2018A&A...616A..17A} Arenou, F., Luri, X., Babusiaux, C., et al.\ 2018, \aap, 616, A17. doi:10.1051/0004-6361/201833234
\bibitem[Lanzafame et al.(2018)]{2018A&A...616A..16L} Lanzafame, A.~C., Distefano, E., Messina, S., et al.\ 2018, \aap, 616, A16. doi:10.1051/0004-6361/201833334
\bibitem[Hambly et al.(2018)]{2018A&A...616A..15H} Hambly, N.~C., Cropper, M., Boudreault, S., et al.\ 2018, \aap, 616, A15. doi:10.1051/0004-6361/201832716
\bibitem[Gaia Collaboration et al.(2018)]{2018A&A...616A..14G} Gaia Collaboration, Mignard, F., Klioner, S.~A., et al.\ 2018, \aap, 616, A14. doi:10.1051/0004-6361/201832916
\bibitem[Gaia Collaboration et al.(2018)]{2018A&A...616A..13G} Gaia Collaboration, Spoto, F., Tanga, P., et al.\ 2018, \aap, 616, A13. doi:10.1051/0004-6361/201832900
\bibitem[Gaia Collaboration et al.(2018)]{2018A&A...616A..12G} Gaia Collaboration, Helmi, A., van Leeuwen, F., et al.\ 2018, \aap, 616, A12. doi:10.1051/0004-6361/201832698
\bibitem[Gaia Collaboration et al.(2018)]{2018A&A...616A..11G} Gaia Collaboration, Katz, D., Antoja, T., et al.\ 2018, \aap, 616, A11. doi:10.1051/0004-6361/201832865
\bibitem[Gaia Collaboration et al.(2018)]{2018A&A...616A..10G} Gaia Collaboration, Babusiaux, C., van Leeuwen, F., et al.\ 2018, \aap, 616, A10. doi:10.1051/0004-6361/201832843
\bibitem[Luri et al.(2018)]{2018A&A...616A...9L} Luri, X., Brown, A.~G.~A., Sarro, L.~M., et al.\ 2018, \aap, 616, A9. doi:10.1051/0004-6361/201832964
\bibitem[Andrae et al.(2018)]{2018A&A...616A...8A} Andrae, R., Fouesneau, M., Creevey, O., et al.\ 2018, \aap, 616, A8. doi:10.1051/0004-6361/201732516
\bibitem[Soubiran et al.(2018)]{2018A&A...616A...7S} Soubiran, C., Jasniewicz, G., Chemin, L., et al.\ 2018, \aap, 616, A7. doi:10.1051/0004-6361/201832795
\bibitem[Sartoretti et al.(2018)]{2018A&A...616A...6S} Sartoretti, P., Katz, D., Cropper, M., et al.\ 2018, \aap, 616, A6. doi:10.1051/0004-6361/201832836
\bibitem[Cropper et al.(2018)]{2018A&A...616A...5C} Cropper, M., Katz, D., Sartoretti, P., et al.\ 2018, \aap, 616, A5. doi:10.1051/0004-6361/201832763
\bibitem[Evans et al.(2018)]{2018A&A...616A...4E} Evans, D.~W., Riello, M., De Angeli, F., et al.\ 2018, \aap, 616, A4. doi:10.1051/0004-6361/201832756
\bibitem[Riello et al.(2018)]{2018A&A...616A...3R} Riello, M., De Angeli, F., Evans, D.~W., et al.\ 2018, \aap, 616, A3. doi:10.1051/0004-6361/201832712
\bibitem[Lindegren et al.(2018)]{2018A&A...616A...2L} Lindegren, L., Hern{\'a}ndez, J., Bombrun, A., et al.\ 2018, \aap, 616, A2. doi:10.1051/0004-6361/201832727
\bibitem[Gaia Collaboration et al.(2018)]{2018A&A...616A...1G} Gaia Collaboration, Brown, A.~G.~A., Vallenari, A., et al.\ 2018, \aap, 616, A1. doi:10.1051/0004-6361/201833051
\bibitem[Marrese et al.(2017)]{2017A&A...607A.105M} Marrese, P.~M., Marinoni, S., Fabrizio, M., et al.\ 2017, \aap, 607, A105. doi:10.1051/0004-6361/201730965
\bibitem[Gaia Collaboration et al.(2017)]{2017A&A...605A..79G} Gaia Collaboration, Clementini, G., Eyer, L., et al.\ 2017, \aap, 605, A79. doi:10.1051/0004-6361/201629925
\bibitem[Moitinho et al.(2017)]{2017A&A...605A..52M} Moitinho, A., Krone-Martins, A., Savietto, H., et al.\ 2017, \aap, 605, A52. doi:10.1051/0004-6361/201731059
\bibitem[Carrasco et al.(2017)]{2017A&A...601C...1C} Carrasco, J.~M., Evans, D.~W., Montegriffo, P., et al.\ 2017, \aap, 601, C1. doi:10.1051/0004-6361/201629235e
\bibitem[Gaia Collaboration et al.(2017)]{2017A&A...601A..19G} Gaia Collaboration, van Leeuwen, F., Vallenari, A., et al.\ 2017, \aap, 601, A19. doi:10.1051/0004-6361/201730552
\bibitem[Evans et al.(2017)]{2017A&A...600A..51E} Evans, D.~W., Riello, M., De Angeli, F., et al.\ 2017, \aap, 600, A51. doi:10.1051/0004-6361/201629241
\bibitem[Arenou et al.(2017)]{2017A&A...599A..50A} Arenou, F., Luri, X., Babusiaux, C., et al.\ 2017, \aap, 599, A50. doi:10.1051/0004-6361/201629895
\bibitem[van Leeuwen et al.(2017)]{2017A&A...599A..32V} van Leeuwen, F., Evans, D.~W., De Angeli, F., et al.\ 2017, \aap, 599, A32. doi:10.1051/0004-6361/201630064
\bibitem[Eyer et al.(2017)]{2017arXiv170203295E} Eyer, L., Mowlavi, N., Evans, D.~W., et al.\ 2017, arXiv:1702.03295
\bibitem[Clementini et al.(2016)]{2016A&A...595A.133C} Clementini, G., Ripepi, V., Leccia, S., et al.\ 2016, \aap, 595, A133. doi:10.1051/0004-6361/201629583
\bibitem[Carrasco et al.(2016)]{2016A&A...595A...7C} Carrasco, J.~M., Evans, D.~W., Montegriffo, P., et al.\ 2016, \aap, 595, A7. doi:10.1051/0004-6361/201629235
\bibitem[Crowley et al.(2016)]{2016A&A...595A...6C} Crowley, C., Kohley, R., Hambly, N.~C., et al.\ 2016, \aap, 595, A6. doi:10.1051/0004-6361/201628990
\bibitem[Mignard et al.(2016)]{2016A&A...595A...5M} Mignard, F., Klioner, S., Lindegren, L., et al.\ 2016, \aap, 595, A5. doi:10.1051/0004-6361/201629534
\bibitem[Lindegren et al.(2016)]{2016A&A...595A...4L} Lindegren, L., Lammers, U., Bastian, U., et al.\ 2016, \aap, 595, A4. doi:10.1051/0004-6361/201628714
\bibitem[Fabricius et al.(2016)]{2016A&A...595A...3F} Fabricius, C., Bastian, U., Portell, J., et al.\ 2016, \aap, 595, A3. doi:10.1051/0004-6361/201628643
\bibitem[Gaia Collaboration et al.(2016)]{2016A&A...595A...2G} Gaia Collaboration, Brown, A.~G.~A., Vallenari, A., et al.\ 2016, \aap, 595, A2. doi:10.1051/0004-6361/201629512
```
``````

## Supported formats

The formats that are currently supported are:

**Tagged formats** 

- ADS (generic tagged) format 
- BibTeX + abstract format
- BibTeX format
- EndNote format
- MEDLARS format
- ProCite format
- RefWorks format
- RIS (Refman) format

**LaTeX formats**

- AASTeX format
- Icarus format
- Monthly Notices of the Royal Astronomical Society format
- Solar Physics (SoPh) format

**XML formats**

- Dublin Core (DC) XML format
- REF-XML format
- REFABS-XML format
- VOTables format

**Other formats**

- Custom formats
- IEEE (Unicode-encoded) format