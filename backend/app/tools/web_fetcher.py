from __future__ import annotations

from dataclasses import dataclass

import ipaddress
import socket

from urllib.parse import (
    urljoin,
    urlsplit,
)

import httpx


class UnsafeURL(ValueError):
    pass


@dataclass(slots=True)
class FetchedPage:
    final_url: str
    content_type: str
    html: str
    bytes_downloaded: int


def validate_public_url(
    url: str,
) -> None:

    parts = urlsplit(
        url.strip()
    )

    if parts.scheme not in {
        "http",
        "https",
    }:
        raise UnsafeURL(
            "Only HTTP/HTTPS URLs are allowed"
        )

    hostname = parts.hostname

    if not hostname:
        raise UnsafeURL(
            "URL has no hostname"
        )

    normalized_host = (
        hostname
        .lower()
        .rstrip(".")
    )

    if (
        normalized_host == "localhost"
        or normalized_host.endswith(
            ".localhost"
        )
    ):
        raise UnsafeURL(
            "Localhost URLs are not allowed"
        )

    try:
        literal_ip = ipaddress.ip_address(
            normalized_host
        )

    except ValueError:
        literal_ip = None

    if literal_ip is not None:

        if not literal_ip.is_global:
            raise UnsafeURL(
                "Non-public IP addresses "
                "are not allowed"
            )

        return

    port = (
        parts.port
        or (
            443
            if parts.scheme == "https"
            else 80
        )
    )

    try:
        addresses = socket.getaddrinfo(
            normalized_host,
            port,
            type=socket.SOCK_STREAM,
        )

    except socket.gaierror as exc:
        raise RuntimeError(
            f"DNS lookup failed for "
            f"{normalized_host}: {exc}"
        ) from exc

    if not addresses:
        raise RuntimeError(
            f"No DNS addresses found for "
            f"{normalized_host}"
        )

    for address in addresses:

        ip_text = (
            address[4][0]
            .split("%", 1)[0]
        )

        ip = ipaddress.ip_address(
            ip_text
        )

        if not ip.is_global:
            raise UnsafeURL(
                "Hostname resolves to a "
                "non-public IP address"
            )


class SafeWebFetcher:

    ALLOWED_CONTENT_TYPES = {
        "text/html",
        "application/xhtml+xml",
        "text/plain",
    }

    REDIRECT_CODES = {
        301,
        302,
        303,
        307,
        308,
    }

    def __init__(
        self,
        *,
        timeout_seconds: float = 20.0,
        max_bytes: int = 1_500_000,
        max_redirects: int = 3,
    ) -> None:

        if timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be positive"
            )

        if max_bytes < 10_000:
            raise ValueError(
                "max_bytes is too small"
            )

        if max_redirects < 0:
            raise ValueError(
                "max_redirects cannot be negative"
            )

        self.timeout_seconds = (
            timeout_seconds
        )

        self.max_bytes = max_bytes

        self.max_redirects = (
            max_redirects
        )

    def fetch(
        self,
        url: str,
    ) -> FetchedPage:

        current_url = (
            url.strip()
        )

        headers = {
            "User-Agent": (
                "ResearchIntelligenceAgent/0.3 "
                "(evidence research bot)"
            ),
            "Accept": (
                "text/html,"
                "application/xhtml+xml,"
                "text/plain;q=0.9,*/*;q=0.1"
            ),
        }

        with httpx.Client(
            timeout=self.timeout_seconds,
            follow_redirects=False,
            headers=headers,
        ) as client:

            for redirect_number in range(
                self.max_redirects + 1
            ):

                validate_public_url(
                    current_url
                )

                with client.stream(
                    "GET",
                    current_url,
                ) as response:

                    if (
                        response.status_code
                        in self.REDIRECT_CODES
                    ):

                        location = (
                            response.headers.get(
                                "location"
                            )
                        )

                        if not location:
                            raise RuntimeError(
                                "Redirect response "
                                "has no Location header"
                            )

                        if (
                            redirect_number
                            >= self.max_redirects
                        ):
                            raise RuntimeError(
                                "Too many redirects"
                            )

                        current_url = urljoin(
                            current_url,
                            location,
                        )

                        continue

                    response.raise_for_status()

                    raw_content_type = (
                        response.headers.get(
                            "content-type",
                            ""
                        )
                    )

                    content_type = (
                        raw_content_type
                        .split(";", 1)[0]
                        .strip()
                        .lower()
                    )

                    if (
                        content_type
                        and content_type
                        not in
                        self.ALLOWED_CONTENT_TYPES
                    ):
                        raise RuntimeError(
                            "Unsupported content type: "
                            f"{content_type}"
                        )

                    chunks: list[bytes] = []

                    downloaded = 0

                    for chunk in (
                        response.iter_bytes()
                    ):

                        downloaded += len(
                            chunk
                        )

                        if (
                            downloaded
                            > self.max_bytes
                        ):
                            raise RuntimeError(
                                "Page exceeds maximum "
                                "allowed size"
                            )

                        chunks.append(
                            chunk
                        )

                    body = b"".join(
                        chunks
                    )

                    encoding = (
                        response.encoding
                        or "utf-8"
                    )

                    html = body.decode(
                        encoding,
                        errors="replace",
                    )

                    return FetchedPage(
                        final_url=current_url,
                        content_type=(
                            content_type
                            or "text/html"
                        ),
                        html=html,
                        bytes_downloaded=(
                            downloaded
                        ),
                    )

        raise RuntimeError(
            "Unable to fetch URL"
        )
