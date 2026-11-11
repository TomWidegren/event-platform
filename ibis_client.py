"""Temporary iBIS v2 sessions and signed, read-only data acquisition."""

import hashlib
import hmac
import math
import re
import time
import uuid
from contextlib import contextmanager

import requests


BASE_URL = "https://api.innebandy.se/v2/api"
PUBLIC_ROOT = f"{BASE_URL}/public"
ORIGIN = "https://stats.innebandy.se"


def read_json(response):
    response.raise_for_status()
    if response.status_code != 200:
        raise ValueError("Unexpected iBIS HTTP status")
    return response.json()


class IbisClient:
    def __init__(self, session, secret, server_time, received_at):
        self.session = session
        self.secret = secret
        self.server_time = server_time
        self.received_at = received_at

    def get_json(self, resource):
        if not isinstance(resource, str) or not re.fullmatch(
            r"(?:matches/[0-9]+|competitions/[0-9]+/matches)",
            resource,
        ):
            raise ValueError("Unexpected iBIS resource")

        path = f"/v2/api/public/{resource}"
        timestamp = str(int(
            self.server_time
            + (time.monotonic() - self.received_at) * 1000
        ))
        nonce = str(uuid.uuid4())
        body_hash = hashlib.sha256(b"").hexdigest()
        message = "\n".join(("GET", path, timestamp, nonce, body_hash))
        signature = hmac.new(
            self.secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        response = self.session.get(
            f"{PUBLIC_ROOT}/{resource}",
            headers={
                "X-Signature": signature,
                "X-Timestamp": timestamp,
                "X-Nonce": nonce,
            },
            timeout=30,
            allow_redirects=False,
        )
        return read_json(response)


@contextmanager
def open_ibis_client():
    with requests.Session() as session:
        session.headers.update({
            "Accept": "application/json",
            "Origin": ORIGIN,
            "Referer": f"{ORIGIN}/",
        })
        credentials = read_json(session.get(
            f"{BASE_URL}/auth/startkit",
            timeout=30,
            allow_redirects=False,
        ))
        if not isinstance(credentials, dict):
            raise ValueError("Unexpected iBIS credentials format")

        token = credentials.get("accessToken")
        api_root = credentials.get("apiRoot")

        if not isinstance(token, str) or not token:
            raise ValueError("Missing iBIS access token")
        if (
            not isinstance(api_root, str)
            or api_root.rstrip("/") != PUBLIC_ROOT
        ):
            raise ValueError("Unexpected iBIS API root")

        session.headers["Authorization"] = f"Bearer {token}"
        response = session.post(
            f"{BASE_URL}/auth/handshake",
            timeout=30,
            allow_redirects=False,
        )
        received_at = time.monotonic()
        handshake = read_json(response)

        if not isinstance(handshake, dict):
            raise ValueError("Unexpected iBIS handshake format")

        secret = handshake.get("ss")
        server_time = handshake.get("st")

        if not isinstance(secret, str) or not secret:
            raise ValueError("Missing iBIS session secret")
        if (
            type(server_time) not in (int, float)
            or not math.isfinite(server_time)
            or server_time <= 0
        ):
            raise ValueError("Unexpected iBIS server timestamp")

        yield IbisClient(session, secret, server_time, received_at)
