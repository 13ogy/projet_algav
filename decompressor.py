#!/usr/bin/env python3
from __future__ import annotations
import sys
import time
import os
from typing import Optional, List

from aha_fgk_oh import AHA

from bitio import BitReader

# Détection de la longueur UTF-8 à partir du 1er octet
UTF8_ONEBYTE_MAX = 0x7F          # 0xxxxxxx
UTF8_TWO_BYTE_MIN = 0xC0         # 110xxxxx
UTF8_TWO_BYTE_MAX = 0xDF
UTF8_THREE_BYTE_MIN = 0xE0       # 1110xxxx
UTF8_THREE_BYTE_MAX = 0xEF
UTF8_FOUR_BYTE_MIN = 0xF0        # 11110xxx
UTF8_FOUR_BYTE_MAX = 0xF7


def read_utf8_char(bit_reader: BitReader) -> str:
    """
    Lit un caractère UTF-8 brut depuis bit_reader (1 à 4 octets) selon l’octet initial.
    Renvoie le caractère (str de longueur 1) ou lève une erreur en cas d’UTF-8 tronqué/invalide.
    """
    first = bit_reader.read_byte()
    if first is None:
        raise EOFError("Fin de flux pendant la lecture d’un caractère UTF-8.")

    v0 = first

    # Longueur 1 (ASCII)
    if v0 <= UTF8_ONEBYTE_MAX:
        seq = [v0]

    # Longueur 2
    elif UTF8_TWO_BYTE_MIN <= v0 <= UTF8_TWO_BYTE_MAX:
        b1 = bit_reader.read_byte()
        if b1 is None:
            raise EOFError("UTF-8 tronqué: attendu 2 octets.")
        seq = [v0, b1]

    # Longueur 3
    elif UTF8_THREE_BYTE_MIN <= v0 <= UTF8_THREE_BYTE_MAX:
        b1 = bit_reader.read_byte()
        b2 = bit_reader.read_byte()
        if b1 is None or b2 is None:
            raise EOFError("UTF-8 tronqué: attendu 3 octets.")
        seq = [v0, b1, b2]

    # Longueur 4
    elif UTF8_FOUR_BYTE_MIN <= v0 <= UTF8_FOUR_BYTE_MAX:
        b1 = bit_reader.read_byte()
        b2 = bit_reader.read_byte()
        b3 = bit_reader.read_byte()
        if b1 is None or b2 is None or b3 is None:
            raise EOFError("UTF-8 tronqué: attendu 4 octets.")
        seq = [v0, b1, b2, b3]

    else:
        raise ValueError(f"Octet initial UTF-8 invalide: 0x{v0:02X}")

    return bytes(seq).decode("utf-8")


def os_path_size(path: str) -> int:
    """Taille d’un fichier (octets)."""
    return os.path.getsize(path)


def append_stats(
        filename: str,
        input_name: str,
        output_name: str,
        in_bytes: int,
        out_bytes: int,
        ratio: float,
        elapsed_ms: int
) -> None:
    """
    Ajoute les stats dans filename (append):
      input_name;output_name;in_bytes;out_bytes;ratio;elapsed_ms
    """
    line = f"{input_name};{output_name};{in_bytes};{out_bytes};{ratio:.5f};{elapsed_ms}\n"
    with open(filename, "a", encoding="utf-8") as f:
        f.write(line)


def decompresser(input_huff_path: str, output_txt_path: str) -> None:
    """
    Décompresse un .huff AHA vers un .txt UTF-8:
    - Lit l’en-tête 64 bits (nb de symboles),
    - Décode N symboles en utilisant l’AHA,
    - Ecrit le résultat dans output_txt_path,
    - Journalise des stats (taille binaire/texte, ratio, temps).
    """
    start_time = time.time()

    # Ouvrir le flux binaire
    bit_reader = BitReader(input_huff_path)

    # Créer l’arbre adaptatif
    aha = AHA()

    # Lire le nombre total de symboles (en-tête)
    n_symbols = bit_reader.read_u64()
    if n_symbols is None:
        raise EOFError("Fichier compressé vide ou en-tête manquant.")
    total_symbols = int(n_symbols)

    # Accumulateur des caractères décodés
    output_chars: List[str] = []

    # Adaptateur pour fournir des bits à decoder_un_symbole
    def lire_bit() -> Optional[int]:
        return bit_reader.read_bit()

    # Décoder N symboles
    for _ in range(total_symbols):
        char_or_none, need_utf8 = aha.decode_one(lire_bit)
        if need_utf8:
            # Feuille NYT: lire le caractère brut (UTF-8) qui suit dans le flux
            new_char = read_utf8_char(bit_reader)
            output_chars.append(new_char)
            aha.mise_a_jour(new_char)
        else:
            # Feuille connue: produire et mettre à jour
            assert char_or_none is not None, "Décodage incohérent: feuille connue sans caractère."
            output_chars.append(char_or_none)
            aha.mise_a_jour(char_or_none)

    # Fermer le flux binaire
    bit_reader.close()

    # Écrire le texte reconstruit
    text = "".join(output_chars)
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    # Stats et log
    end_time = time.time()
    compressed_bytes = os_path_size(input_huff_path)
    decompressed_bytes = len(text.encode("utf-8"))
    ratio = (compressed_bytes / decompressed_bytes) if decompressed_bytes > 0 else 1.0
    elapsed_ms = int((end_time - start_time) * 1000)

    append_stats(
        "decompression.txt",
        input_huff_path,
        output_txt_path,
        compressed_bytes,
        decompressed_bytes,
        ratio,
        elapsed_ms
    )


if __name__ == "__main__":
    # Usage: decompresser <fichier_compresse.huff> <fichier.txt>
    if len(sys.argv) != 3:
        print("Usage: decompresser <fichier_compresse.huff> <fichier.txt>")
        sys.exit(1)
    decompresser(sys.argv[1], sys.argv[2])
