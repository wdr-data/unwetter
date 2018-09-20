#!/user/bin/env python3.6


def genitive(region):
    article_mapping = {
        'der': 'des',
        'die': 'der',
        'das': 'des',
    }
    grammar = region['grammar']
    if not grammar['gender']:
        return grammar['genitive']
    else:
        article = article_mapping[grammar['gender']]
        return f'{article} {grammar["genitive"]}'

def definite_article(region, adjective, adjective_genderless=None):
    """
    In: 'Westfalen', 'gesamte', 'ganz'
    Out: 'ganz Westfalen'

    In: 'Ruhrgebiet', 'gesamte', 'ganz'
    Out: 'das gesamte Ruhrgebiet'
    """
    if adjective_genderless is None:
        adjective_genderless = adjective
    
    gender = region['grammar']['gender']
    name = region['grammar'].get('definite_article', region['name'])
    if gender:
        return f'{gender} {adjective + " " if adjective else ""}{name}'
    else:
        return f'{adjective_genderless + " " if adjective_genderless else ""}{name}'
