#!/usr/bin/env python3
from __future__ import annotations
import sys
import time
import os
from aha import AHA
from bitio import BitReader

# Constantes lisibles pour l’UTF-8 (premier octet)
UTF8_ONEBYTE_MAX = 0x7F
UTF8_TWO_BYTE_MIN = 0xC0
UTF8_TWO_BYTE_MAX = 0xDF
UTF8_THREE_BYTE_MIN = 0xE0
UTF8_THREE_BYTE_MAX = 0xEF
UTF8_FOUR_BYTE_MIN = 0xF0
UTF8_FOUR_BYTE_MAX = 0xF7

def read_utf8_char(br: BitReader) -> str:
    first = br.read_byte()
    if first is None:
        raise EOFError("Fin de flux pendant lecture UTF-8")
    val0 = first

    if val0 <= UTF8_ONEBYTE_MAX:
        seq = [val0]
    elif UTF8_TWO_BYTE_MIN <= val0 <= UTF8_TWO_BYTE_MAX:
        b1 = br.read_byte()
        if b1 is None:
            raise EOFError("UTF-8 tronqué (2 octets)")
        seq = [val0, b1]
    elif UTF8_THREE_BYTE_MIN <= val0 <= UTF8_THREE_BYTE_MAX:
        b1 = br.read_byte()
        b2 = br.read_byte()
        if b1 is None or b2 is None:
            raise EOFError("UTF-8 tronqué (3 octets)")
        seq = [val0, b1, b2]
    elif UTF8_FOUR_BYTE_MIN <= val0 <= UTF8_FOUR_BYTE_MAX:
        b1 = br.read_byte()
        b2 = br.read_byte()
        b3 = br.read_byte()
        if b1 is None or b2 is None or b3 is None:
            raise EOFError("UTF-8 tronqué (4 octets)")
        seq = [val0, b1, b2, b3]
    else:
        raise ValueError(f"Octet initial UTF-8 invalide: 0x{val0:02X}")

    return bytes(seq).decode("utf-8")

def os_path_size(path: str) -> int:
    return os.path.getsize(path)

def append_stats(filename: str, in_name: str, out_name: str, in_bytes: int, out_bytes: int, ratio: float, ms: int):
    line = f"{in_name};{out_name};{in_bytes};{out_bytes};{ratio:.5f};{ms}\n"
    with open(filename, "a", encoding="utf-8") as f:
        f.write(line)

def decompresser(input_bin: str, output_txt: str):
    t0 = time.time()
    br = BitReader(input_bin)
    aha = AHA()

    nsyms = br.read_u64()
    if nsyms is None:
        raise EOFError("Fichier compressé vide/corrompu (pas d’en-tête)")
    total = int(nsyms)

    out_chars: list[str] = []

    def lire_bit() -> int | None:
        return br.read_bit()

    for _ in range(total):
        ch, need_utf8 = aha.decoder_un_symbole(lire_bit)
        if need_utf8:
            new_char = read_utf8_char(br)
            out_chars.append(new_char)
            aha.mise_a_jour(new_char)
        else:
            assert ch is not None
            out_chars.append(ch)
            aha.mise_a_jour(ch)

    br.close()
    text = "".join(out_chars)

    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(text)

    t1 = time.time()
    in_bytes = os_path_size(input_bin)
    out_bytes = len(text.encode("utf-8"))
    ratio = (in_bytes / out_bytes) if out_bytes > 0 else 1.0
    ms = int((t1 - t0) * 1000)
    append_stats("decompression.txt", input_bin, output_txt, in_bytes, out_bytes, ratio, ms)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: decompresser <fichier_compresse.huff> <fichier.txt>")
        sys.exit(1)
    decompresser(sys.argv[1], sys.argv[2])
