from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from adsb_altitude_decoder import decode_altitude, read_first_messages


def make_frame(icao: int, type_code: int, altitude_code: int) -> str:
    me_field = (type_code << 51) | (altitude_code << 36)
    frame_value = (17 << 107) | (5 << 104) | (icao << 80) | (me_field << 24)
    return f"{frame_value:028X}"


def make_log_line(frame: str, sequence: int = 0) -> str:
    message_field = f"100201000E14F3{frame}10038D20"
    return f"{sequence} 10/4/2021 16:00:00 {57600 + sequence / 1000:.3f} 50 01 {message_field}"


class DecodeAltitudeTests(unittest.TestCase):
    def test_decodes_q_bit_altitude_and_icao(self) -> None:
        altitude_code = int("010010110000", 2)
        frame = make_frame(0x780F2A, 11, altitude_code)

        decoded = decode_altitude(frame)

        self.assertIsNotNone(decoded)
        assert decoded is not None
        self.assertEqual(decoded.icao_address, "780F2A")
        self.assertEqual(decoded.type_code, 11)
        self.assertEqual(decoded.q_bit, 1)
        self.assertEqual(decoded.altitude_ft, 13_800)

    def test_rejects_unsupported_type_codes(self) -> None:
        altitude_code = int("010010110000", 2)
        self.assertIsNone(decode_altitude(make_frame(0x780F2A, 8, altitude_code)))
        self.assertIsNone(decode_altitude(make_frame(0x780F2A, 19, altitude_code)))
        self.assertIsNone(decode_altitude(make_frame(0x780F2A, 23, altitude_code)))
        self.assertIsNone(decode_altitude("Z" + "0" * 27))

    def test_decodes_gillham_altitude_when_q_bit_is_zero(self) -> None:
        frame = make_frame(0x780F2A, 11, 0x0200)

        decoded = decode_altitude(frame)

        self.assertIsNotNone(decoded)
        assert decoded is not None
        self.assertEqual(decoded.q_bit, 0)
        self.assertEqual(decoded.altitude_ft, -1_000)

    def test_reads_only_first_400_messages_and_uses_embedded_frame(self) -> None:
        first_frame = make_frame(
            0x780F2A, 11, int("010010110000", 2)
        )
        later_frame = make_frame(0xABCDEF, 11, int("010010110000", 2))

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "messages.txt"
            lines = [make_log_line(first_frame, i) for i in range(400)]
            lines.append(make_log_line(later_frame, 400))
            path.write_text("\n".join(lines), encoding="utf-8")

            dataset = read_first_messages(path)

        self.assertEqual(dataset.messages_scanned, 400)
        self.assertEqual(len(dataset.records), 400)
        self.assertEqual({record.icao_address for record in dataset.records}, {"780F2A"})
        self.assertEqual(dataset.records[0].altitude_ft, 13_800)
        self.assertEqual(dataset.records[0].timestamp.hour, 16)


if __name__ == "__main__":
    unittest.main()
