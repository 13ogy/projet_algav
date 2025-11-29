from __future__ import annotations
from typing import Optional, List

class BitWriter:
    """Ecrit des bits (MSB->LSB) regroupés en octets; padding 0 à droite si besoin.
    """
    def __init__(self, path: str):
        self.path = path
        self.f = open(path, "wb")
        self.bit_buffer: List[int] = []  # accumulateur de bits (0/1)

    def write_bit(self, bit: int):
        if bit == 0:
            self.bit_buffer.append(0)
        else:
            self.bit_buffer.append(1)
        if len(self.bit_buffer) == 8:
            value = 0
            for b in self.bit_buffer:
                if b == 0:
                    value = (value * 2) + 0
                else:
                    value = (value * 2) + 1
            self.f.write(bytes([value]))
            self.bit_buffer.clear()

    def write_bits_from_str01(self, bits: str):
        for ch in bits:
            if ch == '0':
                self.write_bit(0)
            else:
                self.write_bit(1)

    def write_byte(self, value: int):
        # Ecrire un octet via 8 bits MSB -> LSB
        remaining = value
        out_bits: List[int] = []
        for i in range(8):
            # calcule chaque bit par comparaison, pas de masques opaques
            power = 7 - i
            threshold = 1 << power
            if remaining >= threshold:
                out_bits.append(1)
                remaining = remaining - threshold
            else:
                out_bits.append(0)
        for b in out_bits:
            self.write_bit(b)

    def write_u64(self, value: int):
        # Big-endian: 8 octets
        remaining = value
        bytes_out: List[int] = []
        for i in range(8):
            power = 7 - i
            mask = 1 << (power * 8)
            byte_val = (remaining // mask) % 256
            bytes_out.append(byte_val)
        for b in bytes_out:
            self.write_byte(b)

    def flush(self):
        if len(self.bit_buffer) > 0:
            while len(self.bit_buffer) < 8:
                self.bit_buffer.append(0)
            value = 0
            for b in self.bit_buffer:
                if b == 0:
                    value = (value * 2) + 0
                else:
                    value = (value * 2) + 1
            self.f.write(bytes([value]))
            self.bit_buffer.clear()

    def close(self):
        self.flush()
        self.f.close()


class BitReader:
    """Lit des bits (MSB->LSB) depuis un fichier binaire, octet par octet.
    """
    def __init__(self, path: str):
        self.path = path
        self.f = open(path, "rb")
        self.byte_buffer: List[int] = []  # bits restants du prochain octet

    def _fill_from_next_byte(self) -> bool:
        b = self.f.read(1)
        if not b:
            return False
        value = b[0]
        bits: List[int] = []
        remaining = value
        for i in range(8):
            power = 7 - i
            threshold = 1 << power
            if remaining >= threshold:
                bits.append(1)
                remaining = remaining - threshold
            else:
                bits.append(0)
        self.byte_buffer = bits
        return True

    def read_bit(self) -> Optional[int]:
        if len(self.byte_buffer) == 0:
            ok = self._fill_from_next_byte()
            if not ok:
                return None
        bit = self.byte_buffer[0]
        self.byte_buffer = self.byte_buffer[1:]
        return bit

    def read_byte(self) -> Optional[int]:
        bits: List[int] = []
        for _ in range(8):
            b = self.read_bit()
            if b is None:
                return None
            bits.append(b)
        value = 0
        for bit in bits:
            if bit == 0:
                value = (value * 2) + 0
            else:
                value = (value * 2) + 1
        return value

    def read_u64(self) -> Optional[int]:
        total = 0
        for _ in range(8):
            b = self.read_byte()
            if b is None:
                return None
            total = (total * 256) + b
        return total

    def close(self):
        self.f.close()
