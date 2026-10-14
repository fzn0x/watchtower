import urllib.parse


def extract_hostname(target: str) -> str:
    """Return the bare hostname or IP for a target.

    Strips the URL scheme, userinfo, port, path, query, and fragment so that
    host- and DNS-oriented tools (``subfinder``, ``amass``, ``dnsrecon``,
    ``nmap``, ``sslyze`` ...) receive a value they can actually resolve.

        https://user@karafa.net:8443/path?q=1  ->  karafa.net
        karafa.net/admin                        ->  karafa.net
        192.168.0.1:8080                        ->  192.168.0.1

    If a hostname cannot be determined, the stripped input is returned
    unchanged so the caller still has something to work with.
    """
    if not target:
        return target

    candidate = target.strip()
    # urlparse only populates netloc when a scheme (or a leading "//") is
    # present, so add one for bare "host[:port]/path" inputs.
    if "://" not in candidate:
        candidate = "//" + candidate

    hostname = urllib.parse.urlparse(candidate).hostname
    return hostname or target.strip()


def normalize_url(target: str, default_scheme: str = "https") -> str:
    """Return a full URL (with a scheme) for web-oriented tools.

    A bare host/IP gets ``default_scheme`` prepended; a target that already
    carries a scheme is returned unchanged.

        karafa.net            ->  https://karafa.net
        http://karafa.net     ->  http://karafa.net
        https://karafa.net/x  ->  https://karafa.net/x
    """
    if not target:
        return target

    candidate = target.strip()
    parsed = urllib.parse.urlparse(candidate)
    if parsed.scheme and parsed.netloc:
        return candidate

    return f"{default_scheme}://{candidate}"
