"""
OAuth authentification keys to Twitter API in format :
(
consumer_key,
consumer_secret,
oauth_token,
oauth_token_secret
)

You should get your own keys to run the app. Do not try with these credentials, they are just random strings.
"""
ACCESS = [
    (
        "mIsU1P0NNjUTf9DjuN6pdqyOF",
        "KAd5dpgRlu0X3yizTfXTD3lZOAkF7x0QAEhAMHpVCufGW4y0t0",
        "4087833385208874171-k6UR7OGNFdfBcqPye8ps8uBSSqOYXm",
        "Z9nZBVFHbIsU5WQCGT7ZdcRpovQm0QEkV4n4dDofpYAEK"
    ),
    (
        "mIsU1P0NNjUTf9DjuN6pdqyOF",
        "KAd5dpgRlu0X3yizTfXTD3lZOAkF7x0QAEhAMHpVCufGW4y0t0",
        "4087833385208874171-k6UR7OGNFdfBcqPye8ps8uBSSqOYXm",
        "Z9nZBVFHbIsU5WQCGT7ZdcRpovQm0QEkV4n4dDofpYAEK"
    ),
    (
        "mIsU1P0NNjUTf9DjuN6pdqyOF",
        "KAd5dpgRlu0X3yizTfXTD3lZOAkF7x0QAEhAMHpVCufGW4y0t0",
        "4087833385208874171-k6UR7OGNFdfBcqPye8ps8uBSSqOYXm",
        "Z9nZBVFHbIsU5WQCGT7ZdcRpovQm0QEkV4n4dDofpYAEK"
    ),
    (
        "mIsU1P0NNjUTf9DjuN6pdqyOF",
        "KAd5dpgRlu0X3yizTfXTD3lZOAkF7x0QAEhAMHpVCufGW4y0t0",
        "4087833385208874171-k6UR7OGNFdfBcqPye8ps8uBSSqOYXm",
        "Z9nZBVFHbIsU5WQCGT7ZdcRpovQm0QEkV4n4dDofpYAEK"
    )

]

# keywords to be tracked using the Twitter filter API and tags to indicate the collection method within the tweet body
# there should be maximum len(ACCESS)-1 collection methods (the first key in ACCESS is dedicated to Twitter sample API)
KEYWORDS = [
    {"tag": "pronouns", "track": ["je", "tu"]},
    {"tag": "adverbs", "track": ["hier", "toujours", "beaucoup"]},
    {"tag": "verbs", "track": ["etre", "avoir", "faire"]}
]

# language to be tracked using the Twitter filter API.
LANG = "fr"

# approximate file size
FILEBREAK = 300


PROXY = {}

