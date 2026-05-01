def checksum(id: int, length: int, instruction: int, params: list[int]) -> int:
    s = id + length + instruction + sum(params)
    return (~s) & 0xFF


class Packet:
    def __init__(self, id: int, instruction: int, params: list[int] | None = None):
        self.id = id
        self.instruction = instruction
        self.params = params or []

    def to_bytes(self) -> bytes:
        length = len(self.params) + 2  # instruction + checksum
        cks = checksum(self.id, length, self.instruction, self.params)

        data = [0xFF, 0xFF, self.id, length, self.instruction]
        data.extend(self.params)
        data.append(cks)
        return bytes(data)

    @staticmethod
    def parse(data: bytes) -> tuple["Packet", int]:
        """
        Parses a packet from bytes.
        Returns (Packet, consumed_bytes) if successful, or raises ValueError.
        """
        if len(data) < 6:
            raise ValueError("Data too short")

        # Check header
        if data[0] != 0xFF or data[1] != 0xFF:
            raise ValueError("Invalid Header")

        id = data[2]
        length = data[3]

        if len(data) < 4 + length:
            raise ValueError("Incomplete packet")

        instruction = data[4]
        params_len = length - 2
        params = list(data[5 : 5 + params_len])
        cks = data[4 + length - 1]

        calc_cks = checksum(id, length, instruction, params)
        if cks != calc_cks:
            raise ValueError("Invalid Checksum")

        # consumed bytes = 4 + length
        return Packet(id, instruction, params), 4 + length


class PacketReader:
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, data: bytes):
        self.buffer.extend(data)

    def has_packet(self) -> bool:
        # Search for header
        idx = self.buffer.find(b"\xff\xff")
        if idx == -1:
            # keep last byte just in case it is FF
            if self.buffer and self.buffer[-1] == 0xFF:
                self.buffer = self.buffer[-1:]
            else:
                self.buffer.clear()
            return False

        # trim garbage before header
        if idx > 0:
            self.buffer = self.buffer[idx:]

        if len(self.buffer) < 4:
            return False

        length = self.buffer[3]
        total_len = 4 + length

        return len(self.buffer) >= total_len

    def read_packet(self) -> Packet:
        idx = self.buffer.find(b"\xff\xff")
        if idx == -1:
            return None

        # Assumption: has_packet() was called and returned True,
        # so we have enough data starting at idx.
        # But for robustness, we re-parse.

        # trim
        self.buffer = self.buffer[idx:]

        if len(self.buffer) < 4:
            return None

        length = self.buffer[3]
        total_len = 4 + length

        if len(self.buffer) < total_len:
            return None

        packet_data = self.buffer[:total_len]
        try:
            pkt, _ = Packet.parse(packet_data)
            self.buffer = self.buffer[total_len:]
            return pkt
        except ValueError:
            # Corrupt packet, remove header and try again from next byte
            # Ideally we should remove only the first FF to see if next byte starts a header
            self.buffer = self.buffer[1:]
            # Recursion or return None and let loop handle it
            return self.scan_packet()

    def scan_packet(self) -> Packet:
        while True:
            idx = self.buffer.find(b"\xff\xff")
            if idx == -1:
                # preserve last byte if FF
                if self.buffer and self.buffer[-1] == 0xFF:
                    self.buffer = self.buffer[-1:]
                else:
                    self.buffer.clear()
                return None

            self.buffer = self.buffer[idx:]
            if len(self.buffer) < 4:
                return None

            length = self.buffer[3]
            total_len = 4 + length

            if len(self.buffer) < total_len:
                return None

            try:
                pkt, _ = Packet.parse(self.buffer[:total_len])
                self.buffer = self.buffer[total_len:]
                return pkt
            except ValueError:
                # Invalid packet found at header, skip first byte and search again
                self.buffer = self.buffer[1:]
                continue
