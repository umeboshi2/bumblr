import pytumblr

def make_client(config):
    apikey = config.get('main', 'api_key')
    apisecret = config.get('main', 'api_secret')
    token = config.get('main', 'token')
    token_secret = config.get('main', 'token_secret')
    return pytumblr.TumblrRestClient(apikey, apisecret, token, token_secret)

