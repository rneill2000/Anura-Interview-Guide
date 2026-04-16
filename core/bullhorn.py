"""
Bullhorn REST API integration for Interview Guide Tool.

Handles OAuth authentication, candidate search, and job order search
to auto-populate the interview guide form from Bullhorn records.

Auth flow (same as Resume Tool):
  1. Get auth code via direct login (username/password to authorize endpoint)
  2. Exchange auth code for access + refresh tokens
  3. REST login to get BhRestToken + restUrl
  4. Cache tokens in-memory, refresh on expiry
"""

import logging
import re
import threading
import time
from urllib.parse import parse_qs, urlparse

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Module-level token cache (shared across requests within the same process)
_token_cache = {
    "bh_rest_token": None,
    "rest_url": None,
    "refresh_token": None,
    "expires_at": 0,
}
_token_lock = threading.Lock()


class BullhornError(Exception):
    """Raised when a Bullhorn API call fails."""
    def __init__(self, message, status_code=None, response_data=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


# -- Authentication --------------------------------------------------------

def _get_auth_code():
    """
    Get an OAuth authorization code using the direct login approach.
    Bullhorn allows server-to-server auth by passing username/password
    directly to the authorize endpoint with action=Login.
    """
    logger.info("Bullhorn auth attempt: client_id=%s... username=%s", settings.BULLHORN_CLIENT_ID[:8], settings.BULLHORN_API_USERNAME)
    params = {
        "client_id": settings.BULLHORN_CLIENT_ID,
        "response_type": "code",
        "username": settings.BULLHORN_API_USERNAME,
        "password": settings.BULLHORN_API_PASSWORD,
        "action": "Login",
    }
    resp = requests.get(
        "https://auth.bullhornstaffing.com/oauth/authorize",
        params=params,
        allow_redirects=False,
        timeout=15,
    )
    location = resp.headers.get("Location", "")
    if not location:
        logger.error("Bullhorn auth response body: %s", resp.text[:500])
        logger.error("Bullhorn auth response headers: %s", dict(resp.headers))
        raise BullhornError(
            f"No redirect from Bullhorn authorize (status {resp.status_code})"
        )
    parsed = parse_qs(urlparse(location).query)
    code = parsed.get("code", [None])[0]
    if not code:
        error = parsed.get("error_description", parsed.get("error", ["unknown"]))
        raise BullhornError(f"Bullhorn auth failed: {error}")
    return code


def _get_access_token(auth_code):
    """Exchange authorization code for access + refresh tokens."""
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": settings.BULLHORN_CLIENT_ID,
        "client_secret": settings.BULLHORN_CLIENT_SECRET,
    }
    resp = requests.post(
        "https://auth.bullhornstaffing.com/oauth/token",
        data=data,
        timeout=15,
    )
    resp.raise_for_status()
    token_data = resp.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    if not access_token:
        raise BullhornError("No access_token in Bullhorn token response")
    return access_token, refresh_token


def _rest_login(access_token):
    """Use access token to get BhRestToken and restUrl."""
    resp = requests.get(
        "https://rest.bullhornstaffing.com/rest-services/login",
        params={"access_token": access_token, "version": "*"},
        timeout=15,
    )
    resp.raise_for_status()
    login_data = resp.json()
    bh_rest_token = login_data.get("BhRestToken")
    rest_url = login_data.get("restUrl")
    if not bh_rest_token or not rest_url:
        raise BullhornError("Missing BhRestToken or restUrl from Bullhorn login")
    return bh_rest_token, rest_url


def _refresh_access_token(refresh_token):
    """Use a refresh token to get a new access token."""
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": settings.BULLHORN_CLIENT_ID,
        "client_secret": settings.BULLHORN_CLIENT_SECRET,
    }
    resp = requests.post(
        "https://auth.bullhornstaffing.com/oauth/token",
        data=data,
        timeout=15,
    )
    resp.raise_for_status()
    token_data = resp.json()
    return token_data.get("access_token"), token_data.get("refresh_token")


def get_session():
    """
    Get an authenticated Bullhorn REST session (BhRestToken + restUrl).
    Uses cached tokens when available, refreshes when expired.
    Returns (bh_rest_token, rest_url) tuple.
    """
    with _token_lock:
        now = time.time()

        # Reuse cached token if it's still valid (with 60s buffer)
        if _token_cache["bh_rest_token"] and now < _token_cache["expires_at"] - 60:
            return _token_cache["bh_rest_token"], _token_cache["rest_url"]

        # Try refresh first if we have a refresh token
        if _token_cache["refresh_token"]:
            try:
                access_token, refresh_token = _refresh_access_token(
                    _token_cache["refresh_token"]
                )
                bh_rest_token, rest_url = _rest_login(access_token)
                _token_cache.update({
                    "bh_rest_token": bh_rest_token,
                    "rest_url": rest_url,
                    "refresh_token": refresh_token or _token_cache["refresh_token"],
                    "expires_at": now + 540,  # ~9 min (tokens last 10 min)
                })
                logger.info("Bullhorn session refreshed successfully")
                return bh_rest_token, rest_url
            except Exception:
                logger.warning("Bullhorn token refresh failed, doing full auth")

        # Full auth flow
        auth_code = _get_auth_code()
        access_token, refresh_token = _get_access_token(auth_code)
        bh_rest_token, rest_url = _rest_login(access_token)
        _token_cache.update({
            "bh_rest_token": bh_rest_token,
            "rest_url": rest_url,
            "refresh_token": refresh_token,
            "expires_at": now + 540,
        })
        logger.info("Bullhorn full auth completed successfully")
        return bh_rest_token, rest_url


def _api_request(method, path, retried=False, **kwargs):
    """
    Make an authenticated Bullhorn API request.
    Automatically handles session management and token refresh on 401.
    """
    bh_rest_token, rest_url = get_session()
    url = f"{rest_url}{path}"

    headers = kwargs.pop("headers", {})
    headers["BhRestToken"] = bh_rest_token

    resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)

    # Token expired -- refresh and retry once
    if resp.status_code == 401 and not retried:
        with _token_lock:
            _token_cache["expires_at"] = 0  # Force re-auth
        return _api_request(method, path, retried=True, **kwargs)

    return resp


# -- Candidate Search ------------------------------------------------------

def search_candidates(query_text, count=10):
    """
    Search for candidates in Bullhorn by name.
    Returns a list of dicts with id, firstName, lastName, email.
    """
    safe_query = re.sub(r'([+\-&|!(){}\[\]^"~*?:\\/])', r'\\\1', query_text)
    query = f"(firstName:{safe_query}* OR lastName:{safe_query}*) AND isDeleted:0"

    resp = _api_request(
        "GET",
        "search/Candidate",
        params={
            "query": query,
            "fields": "id,firstName,lastName,email",
            "count": str(count),
            "sort": "lastName",
        },
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    for c in data.get("data", []):
        results.append({
            "id": c.get("id"),
            "firstName": c.get("firstName", ""),
            "lastName": c.get("lastName", ""),
            "email": c.get("email", ""),
        })
    return results


def get_candidate(candidate_id):
    """
    Fetch a single candidate by ID, returning name and email.
    """
    resp = _api_request(
        "GET",
        f"entity/Candidate/{candidate_id}",
        params={
            "fields": "id,firstName,lastName,email",
        },
    )
    resp.raise_for_status()
    data = resp.json().get("data", {})
    return {
        "id": data.get("id"),
        "firstName": data.get("firstName", ""),
        "lastName": data.get("lastName", ""),
        "email": data.get("email", ""),
    }


# -- Job Order Search ------------------------------------------------------

def search_job_orders(query_text, count=10):
    """
    Search for job orders in Bullhorn by title or keyword.
    Returns a list of dicts with id, title, client name, status,
    and the publicDescription (job description text).
    """
    safe_query = re.sub(r'([+\-&|!(){}\[\]^"~*?:\\/])', r'\\\1', query_text)
    query = f"title:{safe_query}* AND isDeleted:0"

    resp = _api_request(
        "GET",
        "search/JobOrder",
        params={
            "query": query,
            "fields": "id,title,clientCorporation,dateAdded,publicDescription,status",
            "count": str(count),
            "sort": "-dateAdded",
        },
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    for jo in data.get("data", []):
        corp = jo.get("clientCorporation") or {}
        results.append({
            "id": jo.get("id"),
            "title": jo.get("title", ""),
            "client": corp.get("name", "") if isinstance(corp, dict) else str(corp),
            "status": jo.get("status", ""),
            "description": jo.get("publicDescription", "") or "",
        })
    return results


def get_job_order(job_order_id):
    """
    Fetch a single job order by ID, returning its full description and client.
    """
    resp = _api_request(
        "GET",
        f"entity/JobOrder/{job_order_id}",
        params={
            "fields": "id,title,clientCorporation,publicDescription",
        },
    )
    resp.raise_for_status()
    data = resp.json().get("data", {})
    corp = data.get("clientCorporation") or {}
    return {
        "id": data.get("id"),
        "title": data.get("title", ""),
        "client": corp.get("name", "") if isinstance(corp, dict) else str(corp),
        "description": data.get("publicDescription", "") or "",
    }
