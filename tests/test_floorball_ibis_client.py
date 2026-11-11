"""Offline tests for iBIS session acquisition and request signing."""

import hashlib
import hmac
import unittest
from unittest.mock import Mock, patch

import requests

from ibis_client import BASE_URL, PUBLIC_ROOT, open_ibis_client


class TestIbisClient(unittest.TestCase):
    def response(self, payload, status=200):
        response = Mock(status_code=status)
        response.json.return_value = payload
        if status >= 400:
            response.raise_for_status.side_effect = requests.HTTPError(
                "Simulated failure"
            )
        return response

    def setUp(self):
        self.session = Mock()
        self.session.headers = {}
        self.session.__enter__ = Mock(return_value=self.session)
        self.session.__exit__ = Mock(return_value=False)
        self.session.get.side_effect = [
            self.response({
                "accessToken": "test-token",
                "apiRoot": PUBLIC_ROOT,
            }),
            self.response({"MatchID": 1750719}),
        ]
        self.session.post.return_value = self.response({
            "ss": "test-secret",
            "st": 1700000000000,
        })

        patcher = patch(
            "ibis_client.requests.Session",
            return_value=self.session,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_signing_and_session_reuse(self):
        with (
            patch(
                "ibis_client.time.monotonic",
                side_effect=[100, 100.25],
            ),
            patch(
                "ibis_client.uuid.uuid4",
                return_value="test-nonce",
            ),
            open_ibis_client() as client,
        ):
            result = client.get_json("matches/1750719")

        self.assertEqual(result["MatchID"], 1750719)
        self.assertEqual(
            self.session.headers["Authorization"],
            "Bearer test-token",
        )
        self.session.post.assert_called_once_with(
            f"{BASE_URL}/auth/handshake",
            timeout=30,
            allow_redirects=False,
        )

        call = self.session.get.call_args
        self.assertEqual(
            call.args[0],
            f"{PUBLIC_ROOT}/matches/1750719",
        )

        headers = call.kwargs["headers"]
        self.assertEqual(
            headers["X-Timestamp"],
            "1700000000250",
        )
        self.assertEqual(headers["X-Nonce"], "test-nonce")

        canonical = (
            "GET\n/v2/api/public/matches/1750719\n"
            "1700000000250\ntest-nonce\n"
            "e3b0c44298fc1c149afbf4c8996fb924"
            "27ae41e4649b934ca495991b7852b855"
        )
        expected = hmac.new(
            b"test-secret",
            canonical.encode(),
            hashlib.sha256,
        ).hexdigest()

        self.assertEqual(headers["X-Signature"], expected)
        self.assertFalse(call.kwargs["allow_redirects"])
        self.session.__exit__.assert_called_once()

    def test_competition_and_fresh_nonces(self):
        self.session.get.side_effect = [
            self.response({
                "accessToken": "token",
                "apiRoot": PUBLIC_ROOT,
            }),
            self.response([]),
            self.response([]),
        ]

        with open_ibis_client() as client:
            self.assertEqual(
                client.get_json("competitions/45004/matches"),
                [],
            )
            self.assertEqual(
                client.get_json("competitions/44356/matches"),
                [],
            )

        calls = self.session.get.call_args_list[1:]
        self.assertNotEqual(
            calls[0].kwargs["headers"]["X-Nonce"],
            calls[1].kwargs["headers"]["X-Nonce"],
        )
        self.session.post.assert_called_once()

    def test_invalid_api_root_rejected_before_handshake(self):
        self.session.get.side_effect = None
        self.session.get.return_value = self.response({
            "accessToken": "token",
            "apiRoot": "https://untrusted.example",
        })

        with self.assertRaises(ValueError):
            with open_ibis_client():
                self.fail("Client must not open")

        self.session.post.assert_not_called()
        self.session.__exit__.assert_called_once()

    def test_invalid_handshake_rejected(self):
        invalid_bodies = [
            {},
            {"ss": "secret", "st": True},
            {"ss": "secret", "st": "123"},
        ]

        for body in invalid_bodies:
            with self.subTest(body=body):
                self.session.get.side_effect = None
                self.session.get.return_value = self.response({
                    "accessToken": "token",
                    "apiRoot": PUBLIC_ROOT,
                })
                self.session.post.return_value = self.response(body)

                with self.assertRaises(ValueError):
                    with open_ibis_client():
                        self.fail("Client must not open")

    def test_rejected_request_propagates_without_retry(self):
        self.session.get.side_effect = [
            self.response({
                "accessToken": "token",
                "apiRoot": PUBLIC_ROOT,
            }),
            self.response({}, 401),
        ]

        with open_ibis_client() as client:
            with self.assertRaises(requests.HTTPError):
                client.get_json("matches/1750719")

        self.assertEqual(self.session.get.call_count, 2)

    def test_redirect_rejected(self):
        self.session.get.side_effect = None
        self.session.get.return_value = self.response({}, 302)

        with self.assertRaises(ValueError):
            with open_ibis_client():
                self.fail("Client must not open")

        self.session.post.assert_not_called()

    def test_invalid_resource_rejected_without_request(self):
        invalid_resources = [
            "https://untrusted.example",
            "../auth/login",
            "matches/1?x=1",
        ]

        with open_ibis_client() as client:
            for resource in invalid_resources:
                with self.subTest(resource=resource):
                    with self.assertRaises(ValueError):
                        client.get_json(resource)

        self.assertEqual(self.session.get.call_count, 1)


if __name__ == "__main__":
    unittest.main()
