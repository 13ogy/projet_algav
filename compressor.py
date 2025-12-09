#!/usr/bin/env python3
from __future__ import annotations
import sys
import time
import os
from aha_fgk_oh import AHA
from bitio import BitWriter


def utf8_bytes_for_char(ch: str) -> bytes:
    """
    Convertit un caractère Python (Unicode) en sa séquence d’octets UTF-8.
    """
    return ch.encode("utf-8")


def os_path_size(path: str) -> int:
    """
    Retourne la taille d’un fichier en octets.
    """
    return os.path.getsize(path)


def append_stats(
        filename: str,
        in_name: str,
        out_name: str,
        in_bytes: int,
        out_bytes: int,
        ratio: float,
        ms: int
) -> None:
    """
    Ajoute une ligne de statistiques dans 'filename' (mode append):
      in_name;out_name;in_bytes;out_bytes;ratio;ms
    """
    line = f"{in_name};{out_name};{in_bytes};{out_bytes};{ratio:.5f};{ms}\n"
    with open(filename, "a", encoding="utf-8") as f:
        f.write(line)


def compresser(input_txt: str, output_bin: str) -> None:
    """
    Lit 'input_txt' (UTF-8), compresse le contenu en utilisant l’AHA et écrit le résultat binaire
    dans 'output_bin'. Un en-tête 64 bits (big-endian) stocke le nombre total de caractères
    afin de désambiguïser le padding en fin de flux.

    Le code de chaque caractère est écrit sous forme de bits (via BitWriter.write_bits_from_str01),
    et, pour les premières occurrences, la séquence d’octets UTF-8 du caractère est écrite.
    """
    # Début du chronométrage
    t0 = time.time()

    # Lecture du texte source
    with open(input_txt, "r", encoding="utf-8") as f:
        text = f.read()

    # Ouverture du fichier binaire de sortie + en-tête (nombre total de caractères)
    bit_writer = BitWriter(output_bin)
    bit_writer.write_u64(len(text))

    # Initialisation de l’arbre Huffman adaptatif
    aha = AHA()

    # Parcours du texte, compression symbole par symbole
    for ch in text:
        # Obtenir le code courant pour ce symbole
        is_new, code_bits = aha.encoder_symbole(ch)

        # 1) Ecrire les bits du code (si nouveau => code de NYT)
        bit_writer.write_bits_from_str01(code_bits)

        # 2) Si première occurrence, écrire ensuite les octets UTF-8 du caractère
        if is_new:
            for byte_val in utf8_bytes_for_char(ch):
                bit_writer.write_byte(byte_val)

        # 3) Mettre à jour l’arbre (adaptation)
        aha.mise_a_jour(ch)

    # Fermer le flux binaire (flush des bits restants + fermeture)
    bit_writer.close()

    # Fin chronométrage
    t1 = time.time()

    # Statistiques de compression
    input_bytes = len(text.encode("utf-8"))
    output_bytes = os_path_size(output_bin)
    ratio = (output_bytes / input_bytes) if input_bytes > 0 else 1.0
    elapsed_ms = int((t1 - t0) * 1000)

    append_stats("compression.txt", input_txt, output_bin, input_bytes, output_bytes, ratio, elapsed_ms)


if __name__ == "__main__":
    # Usage simple: compresser <fichier.txt> <fichier_compresse.huff>
    if len(sys.argv) != 3:
        print("Usage: compresser <fichier.txt> <fichier_compresse.huff>")
        sys.exit(1)
    compresser(sys.argv[1], sys.argv[2])
