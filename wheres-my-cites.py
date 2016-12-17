"""
Check if ADS has correctly extracted all your references.
"""
import ads

def wheres_my_cites():
    """
    This requires you to maintain a curated list of your papers,
    either as a text file, or via an ORCiD id.
    """

    orcid_id = None
    curated_papers = 'my_papers.txt'
    author_name = 'Longobardi'
    
    if orcid_id:
        print('Not implemented')
        pass
    elif curated_papers:
        with open(curated_papers, 'r') as f:
            my_papers = [i.strip() for i in f.readlines()]

    print('You currently have {} papers'.format(len(my_papers)))


    q = ads.SearchQuery(q='body:"{}" year:2013-2016 database:astronomy'.format(author_name), hl=['body'], fl=['title', 'bibcode'], rows=1000, max_pages=10)
    p = list(q)

    highlights = []
    cited = 0
    for paper in p:

        highlights = q.highlights(paper)
        number_referenced = len(highlights)
        references = paper.reference
        number_match = len([i for i in my_papers if i in references])
        cited += number_match

        if number_match == 0 or number_match < number_referenced:
            print('Check, ADS did not extract properly):')
            if number_match < number_referenced:
                print('[triage only]')
                print('Number matches: {}'.format(number_match))
            print('Bibcode:  {}'.format(paper.bibcode))
            print('Author: {}'.format(paper.author))
            print('Title: {}'.format(paper.title))
            print('References: {}'.format(paper.reference))
            print('Highlights: {}'.format(highlights))
            print('\n\n')
        else:
            print('Matched: {}\n\n'.format(number_match))

    print('You have {} correctly extracted citations'.format(cited))
    print('')

if __name__ == '__main__':
    wheres_my_cites()

