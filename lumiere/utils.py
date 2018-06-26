from urllib.parse import urlparse, urlunparse, parse_qs


def discrete_url(url):
    result = urlparse(url)

    url = {
        'base': urlunparse((result.scheme, result.netloc, result.path, None, None, result.fragment)),
        'qs': result.query,
        'qs_dict': parse_qs(result.query)
    }

    return url
