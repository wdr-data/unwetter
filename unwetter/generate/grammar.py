#!/user/bin/env python3.6


def genitive(region):
    article_mapping = {
        'der': 'des',
        'die': 'der',
        'das': 'des',
    }
    if not region['gender']:
        return region['cases']['genitive']
    else:
        article = article_mapping[region['gender']]
        return f'{article} {region["cases"]["genitive"]}'
