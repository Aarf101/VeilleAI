"""Configuration validation for VeilleAI."""

from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import logging

from watcher.exceptions import (
    ConfigValidationError,
    ConfigMissingKeyError,
    ConfigInvalidValueError,
)

LOG = logging.getLogger("watcher.config_validator")


def is_valid_url(url: str) -> bool:
    """Validate that a string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https", "ftp"), result.netloc])
    except (ValueError, AttributeError):
        return False


def validate_feed_url(url: str) -> str:
    """Validate and return a feed URL.

    Args:
        url: URL to validate

    Returns:
        The validated URL

    Raises:
        ConfigInvalidValueError: If URL is invalid
    """
    url = url.strip()
    if not is_valid_url(url):
        raise ConfigInvalidValueError(
            f"Invalid feed URL: '{url}'. Must be a valid http/https/ftp URL."
        )
    return url


def validate_feeds_list(feeds: Any) -> List[str]:
    """Validate and return feeds list.

    Args:
        feeds: Raw feeds configuration

    Returns:
        Validated list of feed URLs

    Raises:
        ConfigInvalidValueError: If feeds is not a list or contains invalid URLs
    """
    if not isinstance(feeds, list):
        raise ConfigInvalidValueError(
            f"'feeds' must be a list, got {type(feeds).__name__}"
        )

    if not feeds:
        LOG.warning("No feeds configured. Pipeline will have no data sources.")

    validated_feeds = []
    for i, feed in enumerate(feeds):
        if not isinstance(feed, str):
            raise ConfigInvalidValueError(
                f"Feed at index {i} must be a string, got {type(feed).__name__}"
            )
        try:
            validated_feeds.append(validate_feed_url(feed))
        except ConfigInvalidValueError as e:
            raise ConfigInvalidValueError(f"Feed at index {i}: {str(e)}")

    return validated_feeds


def validate_feeds_enabled(feeds_enabled: Any, feeds: List[str]) -> Dict[str, bool]:
    """Validate feeds_enabled configuration.

    Args:
        feeds_enabled: Raw feeds_enabled configuration
        feeds: List of valid feed URLs for cross-reference

    Returns:
        Validated feeds_enabled dictionary

    Raises:
        ConfigInvalidValueError: If structure is invalid or references non-existent feeds
    """
    if feeds_enabled is None:
        return {}

    if not isinstance(feeds_enabled, dict):
        raise ConfigInvalidValueError(
            f"'feeds_enabled' must be a dict, got {type(feeds_enabled).__name__}"
        )

    validated = {}
    for feed_url, enabled in feeds_enabled.items():
        if not isinstance(feed_url, str):
            raise ConfigInvalidValueError(
                f"feeds_enabled key must be string, got {type(feed_url).__name__}"
            )
        if not isinstance(enabled, bool):
            raise ConfigInvalidValueError(
                f"feeds_enabled['{feed_url}'] must be boolean, got {type(enabled).__name__}"
            )

        # Check if this feed URL exists in feeds list
        if feed_url not in feeds:
            LOG.warning(f"Feed '{feed_url}' in feeds_enabled not found in feeds list")

        validated[feed_url] = enabled

    return validated


def validate_feeds_weight(feeds_weight: Any, feeds: List[str]) -> Dict[str, float]:
    """Validate feeds_weight configuration.

    Args:
        feeds_weight: Raw feeds_weight configuration
        feeds: List of valid feed URLs for cross-reference

    Returns:
        Validated feeds_weight dictionary

    Raises:
        ConfigInvalidValueError: If weights are invalid or out of range
    """
    if feeds_weight is None:
        return {}

    if not isinstance(feeds_weight, dict):
        raise ConfigInvalidValueError(
            f"'feeds_weight' must be a dict, got {type(feeds_weight).__name__}"
        )

    validated = {}
    for feed_url, weight in feeds_weight.items():
        if not isinstance(feed_url, str):
            raise ConfigInvalidValueError(
                f"feeds_weight key must be string, got {type(feed_url).__name__}"
            )

        # Convert int to float if needed
        if isinstance(weight, int):
            weight = float(weight)

        if not isinstance(weight, float):
            raise ConfigInvalidValueError(
                f"feeds_weight['{feed_url}'] must be numeric, got {type(weight).__name__}"
            )

        if weight < 0:
            raise ConfigInvalidValueError(
                f"feeds_weight['{feed_url}'] must be >= 0, got {weight}"
            )

        if feed_url not in feeds:
            LOG.warning(f"Feed '{feed_url}' in feeds_weight not found in feeds list")

        validated[feed_url] = weight

    return validated


def validate_topics(topics: Any) -> List[Dict[str, str]]:
    """Validate topics configuration.

    Args:
        topics: Raw topics configuration

    Returns:
        List of validated topic dicts with 'name' and 'description'

    Raises:
        ConfigInvalidValueError: If topics structure is invalid
    """
    if topics is None:
        return []

    if not isinstance(topics, list):
        raise ConfigInvalidValueError(
            f"'topics' must be a list, got {type(topics).__name__}"
        )

    validated = []
    for i, topic in enumerate(topics):
        if isinstance(topic, dict):
            if "name" not in topic:
                raise ConfigInvalidValueError(
                    f"Topic at index {i}: dict must have 'name' key"
                )
            if not isinstance(topic["name"], str):
                raise ConfigInvalidValueError(
                    f"Topic at index {i}: 'name' must be string"
                )

            validated.append(
                {
                    "name": topic["name"].strip(),
                    "description": topic.get("description", topic["name"]),
                }
            )
        elif isinstance(topic, str):
            validated.append(
                {"name": topic.strip(), "description": topic.strip()}
            )
        else:
            raise ConfigInvalidValueError(
                f"Topic at index {i} must be string or dict, got {type(topic).__name__}"
            )

    return validated


def validate_chroma_path(chroma_path: Any) -> str:
    """Validate chroma_path configuration.

    Args:
        chroma_path: Raw chroma_path value

    Returns:
        Validated path string

    Raises:
        ConfigInvalidValueError: If path is invalid
    """
    if chroma_path is None:
        return "./chroma_db"

    if not isinstance(chroma_path, str):
        raise ConfigInvalidValueError(
            f"'chroma_path' must be string, got {type(chroma_path).__name__}"
        )

    return chroma_path.strip()


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate entire configuration dictionary.

    Validates all config keys and returns a cleaned, validated config.
    Raises specific exceptions with helpful messages on validation failure.

    Args:
        config: Raw configuration dictionary from YAML

    Returns:
        Validated configuration dictionary

    Raises:
        ConfigValidationError: If validation fails
    """
    if not isinstance(config, dict):
        raise ConfigValidationError(
            f"Configuration must be a dictionary, got {type(config).__name__}"
        )

    try:
        # Validate feeds (required)
        feeds = config.get("feeds", [])
        validated_feeds = validate_feeds_list(feeds)

        # Validate optional fields
        feeds_enabled = config.get("feeds_enabled")
        validated_feeds_enabled = validate_feeds_enabled(feeds_enabled, validated_feeds)

        feeds_weight = config.get("feeds_weight")
        validated_feeds_weight = validate_feeds_weight(feeds_weight, validated_feeds)

        topics = config.get("topics")
        validated_topics = validate_topics(topics)

        chroma_path = config.get("chroma_path", "./chroma_db")
        validated_chroma_path = validate_chroma_path(chroma_path)

        # Boolean flags
        enable_autonomous_search = config.get("enable_autonomous_search", False)
        if not isinstance(enable_autonomous_search, bool):
            raise ConfigInvalidValueError(
                f"'enable_autonomous_search' must be boolean, got {type(enable_autonomous_search).__name__}"
            )

        enable_rss_feeds = config.get("enable_rss_feeds", True)
        if not isinstance(enable_rss_feeds, bool):
            raise ConfigInvalidValueError(
                f"'enable_rss_feeds' must be boolean, got {type(enable_rss_feeds).__name__}"
            )

        enable_trending_weighting = config.get("enable_trending_weighting", False)
        if not isinstance(enable_trending_weighting, bool):
            raise ConfigInvalidValueError(
                f"'enable_trending_weighting' must be boolean, got {type(enable_trending_weighting).__name__}"
            )

        enable_youtube_transcripts = config.get("enable_youtube_transcripts", False)
        if not isinstance(enable_youtube_transcripts, bool):
            raise ConfigInvalidValueError(
                f"'enable_youtube_transcripts' must be boolean, got {type(enable_youtube_transcripts).__name__}"
            )

        # Build validated config
        validated_config = {
            "feeds": validated_feeds,
            "feeds_enabled": validated_feeds_enabled,
            "feeds_weight": validated_feeds_weight,
            "topics": validated_topics,
            "chroma_path": validated_chroma_path,
            "enable_autonomous_search": enable_autonomous_search,
            "enable_rss_feeds": enable_rss_feeds,
            "enable_trending_weighting": enable_trending_weighting,
            "enable_youtube_transcripts": enable_youtube_transcripts,
        }

        # Preserve any additional unknown keys for forward compatibility
        for key, value in config.items():
            if key not in validated_config:
                validated_config[key] = value

        LOG.debug("Configuration validation successful")
        return validated_config

    except (ConfigValidationError, ConfigInvalidValueError, ConfigMissingKeyError):
        raise
    except Exception as e:
        raise ConfigValidationError(f"Unexpected validation error: {str(e)}")
