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
