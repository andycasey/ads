---
hide-toc: true
---

## Getting started

You will find detailed guides to get started with the ``ads`` package linked below, and in the left side bar. This page gives you just a teaser for how to use ADS services with the ``ads`` Python package.


Here are some examples of how to search for documents:

```python
from ads import Document, Affiliation

# Search by author name.
docs = (
    Document.select()
            .where(Document.author == "Ghez, Andrea M.")
            .limit(50)
)

# Retrieve a single document.
doc = Document.get(title="SDSS-V")

# See what down under is up to lately.
docs = (
    Document.select()
            .where(Document.affiliation.country == "Australia")
            .order_by(Document.entry_date.desc())
            .limit(10)
)

# Search by journal name.
docs = (
    Document.select()
            .where(Document.journal.title == "The Astrophysical Journal")
            .order_by(Document.citation_count.desc())
            .limit(3)
)

# Search by a curated list of affiliations.
monash = Affiliation.get(abbreviation="Monash U")
docs = (
    Document.select()
            .where(Document.affiliation == monash)
            .limit(10)
)
```

You can also access public and private ADS libraries, and export them to whatever format you need. In the Python tab below you can see the executable Python code, and in the second tab you can see the output.

``````{tab} Python
```python
from ads import Library
from ads.services.export import aastex

gaia_data_release_papers = Library.get(id="7vKRL51sSFKXUfFVMZHC6g")

print(f"# {gaia_data_release_papers}")
print(aastex(gaia_data_release_papers))
```
``````
``````{tab} Output
```
# <Library 7vKRL51sSFKXUfFVMZHC6g: Gaia Data Release papers (47 documents)>
\bibitem[Gaia Collaboration et al.(2018)]{2018A&A...616A...1G} Gaia Collaboration, Brown, A.~G.~A., Vallenari, A., et al.\ 2018, \aap, 616, A1. doi:10.1051/0004-6361/201833051
\bibitem[Gaia Collaboration et al.(2016)]{2016A&A...595A...2G} Gaia Collaboration, Brown, A.~G.~A., Vallenari, A., et al.\ 2016, \aap, 595, A2. doi:10.1051/0004-6361/201629512
\bibitem[Lindegren et al.(2018)]{2018A&A...616A...2L} Lindegren, L., Hern{\'a}ndez, J., Bombrun, A., et al.\ 2018, \aap, 616, A2. doi:10.1051/0004-6361/201832727
\bibitem[Lindegren et al.(2016)]{2016A&A...595A...4L} Lindegren, L., Lammers, U., Bastian, U., et al.\ 2016, \aap, 595, A4. doi:10.1051/0004-6361/201628714
\bibitem[Luri et al.(2018)]{2018A&A...616A...9L} Luri, X., Brown, A.~G.~A., Sarro, L.~M., et al.\ 2018, \aap, 616, A9. doi:10.1051/0004-6361/201832964
\bibitem[Evans et al.(2018)]{2018A&A...616A...4E} Evans, D.~W., Riello, M., De Angeli, F., et al.\ 2018, \aap, 616, A4. doi:10.1051/0004-6361/201832756
\bibitem[Gaia Collaboration et al.(2018)]{2018A&A...616A..10G} Gaia Collaboration, Babusiaux, C., van Leeuwen, F., et al.\ 2018, \aap, 616, A10. doi:10.1051/0004-6361/201832843
\bibitem[Arenou et al.(2018)]{2018A&A...616A..17A} Arenou, F., Luri, X., Babusiaux, C., et al.\ 2018, \aap, 616, A17. doi:10.1051/0004-6361/201833234
\bibitem[Gaia Collaboration et al.(2018)]{2018A&A...616A..12G} Gaia Collaboration, Helmi, A., van Leeuwen, F., et al.\ 2018, \aap, 616, A12. doi:10.1051/0004-6361/201832698
\bibitem[Andrae et al.(2018)]{2018A&A...616A...8A} Andrae, R., Fouesneau, M., Creevey, O., et al.\ 2018, \aap, 616, A8. doi:10.1051/0004-6361/201732516
\bibitem[Gaia Collaboration et al.(2018)]{2018A&A...616A..11G} Gaia Collaboration, Katz, D., Antoja, T., et al.\ 2018, \aap, 616, A11. doi:10.1051/0004-6361/201832865
\bibitem[Katz et al.(2019)]{2019A&A...622A.205K} Katz, D., Sartoretti, P., Cropper, M., et al.\ 2019, \aap, 622, A205. doi:10.1051/0004-6361/201833273
\bibitem[Clementini et al.(2019)]{2019A&A...622A..60C} Clementini, G., Ripepi, V., Molinaro, R., et al.\ 2019, \aap, 622, A60. doi:10.1051/0004-6361/201833374
\bibitem[Gaia Collaboration et al.(2018)]{2018A&A...616A..14G} Gaia Collaboration, Mignard, F., Klioner, S.~A., et al.\ 2018, \aap, 616, A14. doi:10.1051/0004-6361/201832916
\bibitem[Riello et al.(2018)]{2018A&A...616A...3R} Riello, M., De Angeli, F., Evans, D.~W., et al.\ 2018, \aap, 616, A3. doi:10.1051/0004-6361/201832712
\bibitem[Holl et al.(2018)]{2018A&A...618A..30H} Holl, B., Audard, M., Nienartowicz, K., et al.\ 2018, \aap, 618, A30. doi:10.1051/0004-6361/201832892
\bibitem[Cropper et al.(2018)]{2018A&A...616A...5C} Cropper, M., Katz, D., Sartoretti, P., et al.\ 2018, \aap, 616, A5. doi:10.1051/0004-6361/201832763
\bibitem[Sartoretti et al.(2018)]{2018A&A...616A...6S} Sartoretti, P., Katz, D., Cropper, M., et al.\ 2018, \aap, 616, A6. doi:10.1051/0004-6361/201832836
\bibitem[Arenou et al.(2017)]{2017A&A...599A..50A} Arenou, F., Luri, X., Babusiaux, C., et al.\ 2017, \aap, 599, A50. doi:10.1051/0004-6361/201629895
\bibitem[Gaia Collaboration et al.(2019)]{2019A&A...623A.110G} Gaia Collaboration, Eyer, L., Rimoldini, L., et al.\ 2019, \aap, 623, A110. doi:10.1051/0004-6361/201833304
\bibitem[Fabricius et al.(2016)]{2016A&A...595A...3F} Fabricius, C., Bastian, U., Portell, J., et al.\ 2016, \aap, 595, A3. doi:10.1051/0004-6361/201628643
\bibitem[Gandhi et al.(2019)]{2019MNRAS.485.2642G} Gandhi, P., Rao, A., Johnson, M.~A.~C., et al.\ 2019, \mnras, 485, 2642. doi:10.1093/mnras/stz438
\bibitem[Gaia Collaboration et al.(2017)]{2017A&A...605A..79G} Gaia Collaboration, Clementini, G., Eyer, L., et al.\ 2017, \aap, 605, A79. doi:10.1051/0004-6361/201629925
\bibitem[Gaia Collaboration et al.(2017)]{2017A&A...601A..19G} Gaia Collaboration, van Leeuwen, F., Vallenari, A., et al.\ 2017, \aap, 601, A19. doi:10.1051/0004-6361/201730552
\bibitem[Soubiran et al.(2018)]{2018A&A...616A...7S} Soubiran, C., Jasniewicz, G., Chemin, L., et al.\ 2018, \aap, 616, A7. doi:10.1051/0004-6361/201832795
\bibitem[Marrese et al.(2019)]{2019A&A...621A.144M} Marrese, P.~M., Marinoni, S., Fabrizio, M., et al.\ 2019, \aap, 621, A144. doi:10.1051/0004-6361/201834142
\bibitem[Carrasco et al.(2016)]{2016A&A...595A...7C} Carrasco, J.~M., Evans, D.~W., Montegriffo, P., et al.\ 2016, \aap, 595, A7. doi:10.1051/0004-6361/201629235
\bibitem[Clementini et al.(2016)]{2016A&A...595A.133C} Clementini, G., Ripepi, V., Leccia, S., et al.\ 2016, \aap, 595, A133. doi:10.1051/0004-6361/201629583
\bibitem[Mignard et al.(2016)]{2016A&A...595A...5M} Mignard, F., Klioner, S., Lindegren, L., et al.\ 2016, \aap, 595, A5. doi:10.1051/0004-6361/201629534
\bibitem[Gaia Collaboration et al.(2018)]{2018A&A...616A..13G} Gaia Collaboration, Spoto, F., Tanga, P., et al.\ 2018, \aap, 616, A13. doi:10.1051/0004-6361/201832900
\bibitem[Mowlavi et al.(2018)]{2018A&A...618A..58M} Mowlavi, N., Lecoeur-Ta{\"\i}bi, I., Lebzelter, T., et al.\ 2018, \aap, 618, A58. doi:10.1051/0004-6361/201833366
\bibitem[van Leeuwen et al.(2017)]{2017A&A...599A..32V} van Leeuwen, F., Evans, D.~W., De Angeli, F., et al.\ 2017, \aap, 599, A32. doi:10.1051/0004-6361/201630064
\bibitem[Eyer et al.(2017)]{2017arXiv170203295E} Eyer, L., Mowlavi, N., Evans, D.~W., et al.\ 2017, arXiv:1702.03295
\bibitem[Pelisoli \& Vos(2019)]{2019MNRAS.488.2892P} Pelisoli, I. \& Vos, J.\ 2019, \mnras, 488, 2892. doi:10.1093/mnras/stz1876
\bibitem[Rimoldini et al.(2019)]{2019A&A...625A..97R} Rimoldini, L., Holl, B., Audard, M., et al.\ 2019, \aap, 625, A97. doi:10.1051/0004-6361/201834616
\bibitem[Marrese et al.(2017)]{2017A&A...607A.105M} Marrese, P.~M., Marinoni, S., Fabrizio, M., et al.\ 2017, \aap, 607, A105. doi:10.1051/0004-6361/201730965
\bibitem[Lanzafame et al.(2018)]{2018A&A...616A..16L} Lanzafame, A.~C., Distefano, E., Messina, S., et al.\ 2018, \aap, 616, A16. doi:10.1051/0004-6361/201833334
\bibitem[Crowley et al.(2016)]{2016A&A...595A...6C} Crowley, C., Kohley, R., Hambly, N.~C., et al.\ 2016, \aap, 595, A6. doi:10.1051/0004-6361/201628990
\bibitem[Hambly et al.(2018)]{2018A&A...616A..15H} Hambly, N.~C., Cropper, M., Boudreault, S., et al.\ 2018, \aap, 616, A15. doi:10.1051/0004-6361/201832716
\bibitem[Evans et al.(2017)]{2017A&A...600A..51E} Evans, D.~W., Riello, M., De Angeli, F., et al.\ 2017, \aap, 600, A51. doi:10.1051/0004-6361/201629241
\bibitem[Moln{\'a}r et al.(2018)]{2018A&A...620A.127M} Moln{\'a}r, L., Plachy, E., Juh{\'a}sz, {\'A}. L., et al.\ 2018, \aap, 620, A127. doi:10.1051/0004-6361/201833514
\bibitem[Roelens et al.(2018)]{2018A&A...620A.197R} Roelens, M., Eyer, L., Mowlavi, N., et al.\ 2018, \aap, 620, A197. doi:10.1051/0004-6361/201833357
\bibitem[Forveille et al.(2018)]{2018A&A...616E...1F} Forveille, T., Kotak, R., Shore, S., et al.\ 2018, \aap, 616, E1. doi:10.1051/0004-6361/201833955
\bibitem[Moitinho et al.(2017)]{2017A&A...605A..52M} Moitinho, A., Krone-Martins, A., Savietto, H., et al.\ 2017, \aap, 605, A52. doi:10.1051/0004-6361/201731059
\bibitem[Gaia Collaboration et al.(2020)]{2020A&A...642C...1G} Gaia Collaboration, Helmi, A., van Leeuwen, F., et al.\ 2020, \aap, 642, C1. doi:10.1051/0004-6361/202039217
\bibitem[Gaia Collaboration et al.(2020)]{2020A&A...637C...3G} Gaia Collaboration, Helmi, A., van Leeuwen, F., et al.\ 2020, \aap, 637, C3. doi:10.1051/0004-6361/201832698e
\bibitem[Carrasco et al.(2017)]{2017A&A...601C...1C} Carrasco, J.~M., Evans, D.~W., Montegriffo, P., et al.\ 2017, \aap, 601, C1. doi:10.1051/0004-6361/201629235e
```
``````

Or you can create and edit your own libraries:

```python
from ads import Document, Library

lib = Library.create(name="My refereed papers", public=True)
lib.documents = (
    Document.select()
            .where(
                (Document.author == "Kreidberg, Laura")
            &   (Document.property == "refereed")
            )
)
lib.save()
```

There's a whole lot more you can do with the new ``ads``. You can find more details information in the contents linked below.

```{toctree}
document
journal
affiliation
library
```
