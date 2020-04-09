from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, quote

exclude_parameters = ["utm_medium", "utm_source", "utm_campaign", "utm_term", "utm_content", "xtor", "type", "share",
                      "ref", "ncid", "fbclid", "__twitter_impression", "partageApp", "accesVia", "igshid",
                      "reflink", "emailToken", "ocid"]


def clean_url(url):
    parsed_url = urlparse(url)
    if parsed_url.path == "" or parsed_url.path == "/":
        return url

    parameters = parse_qs(parsed_url.query)
    if "url" in parameters:
        parsed_url = urlparse(parameters["url"][0])
        parameters = parse_qs(parsed_url.query)
    for param in parameters.copy():
        if param in exclude_parameters:
            parameters.pop(param, None)
        elif isinstance(parameters[param], list):
            parameters[param] = parameters[param][0]
    parsed_url = parsed_url._replace(query=urlencode({param: parameters[param] for param in sorted(parameters)},
                                                     quote_via=quote, safe="/ :?="))
    parsed_url = parsed_url._replace(fragment="")
    if "#" in parsed_url.path:
        parsed_url = parsed_url._replace(path=parsed_url.path.split("#")[0])

    return urlunparse(parsed_url)


if __name__ == "__main__":
    url = "http://mamakuka.stonefeuer.info/US/categories/twt/?id=http://rover.ebay.com/rover/1/711-53200-19255-0/1?ff3=2&toolid=10039&campid=5337797091&item=283502695501&vectorid=229466&lgeo=1"
    cleanurl = clean_url(url)
    print(cleanurl)