"""FNV-1a hash implementation for firmware key hashing."""

from functools import cache


@cache
def fnv1a_hash(string: str) -> int:
    """
    Compute FNV-1a 32-bit hash of a string.

    This matches the firmware's hash implementation used for parameter
    and telemetry keys. Results are cached to avoid recomputing hashes
    for previously seen strings.

    Args:
        string: The string to hash.

    Returns:
        32-bit FNV-1a hash value.

    Example:
        >>> hex(fnv1a_hash("parameter"))
        '0x100b'
    """
    FNV_OFFSET_BASIS = 0x811C9DC5
    FNV_PRIME = 0x01000193

    hash_value = FNV_OFFSET_BASIS

    for byte in string.encode("utf-8"):
        hash_value ^= byte
        hash_value = (hash_value * FNV_PRIME) & 0xFFFFFFFF

    return hash_value
