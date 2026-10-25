from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

FRAME_OFFSET = 14
FRAME_LENGTH = 28
MAX_MESSAGES = 400
SUPPORTED_TYPE_CODES = frozenset((*range(9, 19), *range(20, 23)))


@dataclass(frozen=True)
class DecodedAltitude:
    altitude_ft: int
    icao_address: str
    type_code: int
    q_bit: int
    frame: str


@dataclass(frozen=True)
class AltitudeRecord(DecodedAltitude):
    timestamp: datetime


@dataclass(frozen=True)
class Dataset:
    messages_scanned: int
    records: tuple[AltitudeRecord, ...]


def _decode_gillham_altitude(altitude_code: int) -> int | None:
    mode_a = 0
    for source_bit, target_bit in (
        (0x0800, 0x0010),
        (0x0400, 0x1000),
        (0x0200, 0x0020),
        (0x0100, 0x2000),
        (0x0080, 0x0040),
        (0x0040, 0x4000),
        (0x0020, 0x0100),
        (0x0008, 0x0200),
        (0x0004, 0x0002),
        (0x0002, 0x0400),
        (0x0001, 0x0004),
    ):
        if altitude_code & source_bit:
            mode_a |= target_bit

    one_hundreds = 0
    if mode_a & 0x0010:
        one_hundreds ^= 0x007
    if mode_a & 0x0020:
        one_hundreds ^= 0x003
    if mode_a & 0x0040:
        one_hundreds ^= 0x001
    if one_hundreds & 0x005 == 0:
        return None
    if one_hundreds & 0x002:
        one_hundreds = 6 - one_hundreds

    five_hundreds = 0
    for mode_a_bit, altitude_bit in (
        (0x0002, 0x0FF),
        (0x0004, 0x07F),
        (0x1000, 0x03F),
        (0x2000, 0x01F),
        (0x4000, 0x00F),
        (0x0100, 0x007),
        (0x0200, 0x003),
        (0x0400, 0x001),
    ):
        if mode_a & mode_a_bit:
            five_hundreds |= altitude_bit
    if five_hundreds & 1:
        one_hundreds = 6 - one_hundreds

    return (five_hundreds * 5 + one_hundreds - 13) * 100


def decode_altitude(frame_hex: str) -> DecodedAltitude | None:
    """Decode a qualifying 112-bit ADS-B airborne-position frame."""
    if len(frame_hex) != FRAME_LENGTH:
        return None
    if any(character not in "0123456789abcdefABCDEF" for character in frame_hex):
        return None
    try:
        frame_value = int(frame_hex, 16)
    except ValueError:
        return None

    bits = f"{frame_value:0112b}"
    downlink_format = int(bits[:5], 2)
    if downlink_format not in (17, 18):
        return None

    type_code = int(bits[32:37], 2)
    if type_code not in SUPPORTED_TYPE_CODES:
        return None

    altitude_bits = bits[40:52]
    q_bit = int(altitude_bits[7])
    altitude_code = int(altitude_bits, 2)
    if q_bit:
        n = int(altitude_bits[:7] + altitude_bits[8:], 2)
        altitude_ft = n * 25 - 1000
    else:
        altitude_ft = _decode_gillham_altitude(altitude_code)
        if altitude_ft is None:
            return None

    return DecodedAltitude(
        altitude_ft=altitude_ft,
        icao_address=frame_hex[2:8].upper(),
        type_code=type_code,
        q_bit=q_bit,
        frame=frame_hex.upper(),
    )


def read_first_messages(path: Path, limit: int = MAX_MESSAGES) -> Dataset:
    """Read and decode altitude frames from the first non-empty log messages."""
    records: list[AltitudeRecord] = []
    messages_scanned = 0

    with path.open(encoding="utf-8", errors="replace") as log_file:
        for raw_line in log_file:
            if not raw_line.strip():
                continue
            if messages_scanned >= limit:
                break
            messages_scanned += 1

            columns = raw_line.split()
            if len(columns) < 7:
                continue

            message_field = columns[6]
            frame_hex = message_field[FRAME_OFFSET : FRAME_OFFSET + FRAME_LENGTH]
            if len(frame_hex) != FRAME_LENGTH:
                continue

            decoded = decode_altitude(frame_hex)
            if decoded is None:
                continue

            try:
                message_date = datetime.strptime(columns[1], "%m/%d/%Y")
                seconds_of_day = float(columns[3])
                timestamp = message_date + timedelta(seconds=seconds_of_day)
            except (OverflowError, ValueError):
                continue

            records.append(
                AltitudeRecord(
                    altitude_ft=decoded.altitude_ft,
                    icao_address=decoded.icao_address,
                    type_code=decoded.type_code,
                    q_bit=decoded.q_bit,
                    frame=decoded.frame,
                    timestamp=timestamp,
                )
            )

    records.sort(key=lambda record: record.timestamp)
    return Dataset(messages_scanned=messages_scanned, records=tuple(records))
