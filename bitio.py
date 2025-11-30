from __future__ import annotations
from typing import Optional, List


class BitWriter:
    def __init__(self, path: str):
        # Fichier en écriture binaire
        self._file = open(path, "wb")
        # Accumulateur de bits (0/1) avant de les empaqueter en octet
        self._bit_buffer: List[int] = []

    def write_bit(self, bit: int) -> None:
        """
        Ecrit un seul bit (0 ou 1) dans le tampon. Dès que 8 bits sont accumulés,
        on les convertit en un octet et on l’écrit dans le fichier.
        """
        self._bit_buffer.append(1 if bit else 0)
        if len(self._bit_buffer) == 8:
            value = 0
            for b in self._bit_buffer:
                value = (value * 2) + (1 if b == 1 else 0)
            self._file.write(bytes([value]))
            self._bit_buffer.clear()

    def write_bits_from_str01(self, bits: str) -> None:
        """
        Ecrit une suite de bits passée sous forme de chaîne de '0' et '1'.
        Exemple: bits="10110"
        """
        for ch in bits:
            self.write_bit(1 if ch == '1' else 0)

    def write_byte(self, value: int) -> None:
        """
        Ecrit un octet (0..255), en appelant 8 fois write_bit() dans l’ordre MSB -> LSB.
        """
        assert 0 <= value <= 255, "write_byte attend une valeur 0..255"
        for i in range(7, -1, -1):
            self.write_bit((value >> i) & 1)

    def write_u64(self, value: int) -> None:
        """
        Ecrit un entier non signé 64 bits en big-endian (octet 7 -> octet 0),
        c’est-à-dire octet de poids fort en premier, puis octet suivant, etc.
        """
        assert 0 <= value < (1 << 64), "write_u64 attend un entier non signé sur 64 bits"
        for i in range(7, -1, -1):
            self.write_byte((value >> (8 * i)) & 0xFF)

    def flush(self) -> None:
        """
        Ecrit le dernier octet si le tampon contient des bits (padding avec des 0).
        """
        if self._bit_buffer:
            while len(self._bit_buffer) < 8:
                self._bit_buffer.append(0)
            value = 0
            for b in self._bit_buffer:
                value = (value * 2) + (1 if b == 1 else 0)
            self._file.write(bytes([value]))
            self._bit_buffer.clear()

    def close(self) -> None:
        """
        Flush + fermeture du fichier.
        """
        self.flush()
        self._file.close()


class BitReader:
    def __init__(self, path: str):
        # Fichier en lecture binaire
        self._file = open(path, "rb")
        # Tampon du prochain octet “déplié” en bits, MSB -> LSB
        self._byte_buffer: List[int] = []

    def _fill_from_next_byte(self) -> bool:
        """
        Tente de lire 1 octet depuis le fichier, et prépare _byte_buffer
        comme la liste de ses 8 bits (MSB -> LSB).
        Retourne True si un octet a été lu, False sur fin de fichier.
        """
        b = self._file.read(1)
        if not b:
            return False
        v = b[0]
        bits: List[int] = []
        for i in range(7, -1, -1):
            bits.append((v >> i) & 1)
        self._byte_buffer = bits
        return True

    def read_bit(self) -> Optional[int]:
        """
        Renvoie le prochain bit (0/1), ou None si fin de fichier atteinte.
        """
        if not self._byte_buffer:
            if not self._fill_from_next_byte():
                return None
        bit = self._byte_buffer[0]
        self._byte_buffer = self._byte_buffer[1:]
        return bit

    def read_byte(self) -> Optional[int]:
        """
        Lit 8 bits pour construire un octet (0..255).
        Renvoie None si la fin de fichier est atteinte avant d’avoir lu 8 bits.
        """
        value = 0
        for _ in range(8):
            b = self.read_bit()
            if b is None:
                return None
            value = (value << 1) | b
        return value

    def read_u64(self) -> Optional[int]:
        """
        Lit un entier non signé 64 bits en big-endian.
        Renvoie None si la fin de fichier survient avant d’avoir lu 8 octets.
        """
        value = 0
        for _ in range(8):
            b = self.read_byte()
            if b is None:
                return None
            value = (value << 8) | b
        return value

    def close(self) -> None:
        """Ferme le fichier sous-jacent."""
        self._file.close()
