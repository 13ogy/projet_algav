#!/usr/bin/env python3
from __future__ import annotations
import sys
import time
import os
from aha import AHA
from bitio import BitWriter

def utf8_bytes_for_char(ch: str) -> bytes:
    return ch.encode("utf-8")

def os_path_size(path: str) -> int:
    return os.path.getsize(path)

def append_stats(filename: str, in_name: str, out_name: str, in_bytes: int, out_bytes: int, ratio: float, ms: int):
    line = f"{in_name};{out_name};{in_bytes};{out_bytes};{ratio:.5f};{ms}\n"
    with open(filename, "a", encoding="utf-8") as f:
        f.write(line)

def compresser(input_txt: str, output_bin: str):
    t0 = time.time()
    with open(input_txt, "r", encoding="utf-8") as f:
        text = f.read()

    bw = BitWriter(output_bin)
    # En-tête: nb total de caractères (64 bits, big-endian)
    # pour lever toute ambiguïté liée au padding
    bw.write_u64(len(text))

    aha = AHA()

    for ch in text:
        is_new, code = aha.encoder_symbole(ch)
        # écrire le code (de # si nouveau, ou code de ch sinon)
        bw.write_bits_from_str01(code)
        if is_new:
            # si nouveau: écrire ensuite l’UTF-8 du caractère
            bseq = utf8_bytes_for_char(ch)
            for byte_val in bseq:
                bw.write_byte(byte_val)
        # mise à jour de l’arbre
        aha.mise_a_jour(ch)

    bw.close()
    t1 = time.time()

    in_bytes = len(text.encode("utf-8"))
    out_bytes = os_path_size(output_bin)
    ratio = (out_bytes / in_bytes) if in_bytes > 0 else 1.0
    ms = int((t1 - t0) * 1000)
    append_stats("compression.txt", input_txt, output_bin, in_bytes, out_bytes, ratio, ms)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: compresser <fichier.txt> <fichier_compresse.huff>")
        sys.exit(1)
    compresser(sys.argv[1], sys.argv[2])
    