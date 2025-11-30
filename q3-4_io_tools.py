from bitio import BitReader, BitWriter


def lecture(fichier_bin: str) -> str:
    """
    Q3 — Lecture d’un fichier binaire en chaîne de bits.
    """
    br = BitReader(fichier_bin)
    bits: list[str] = []
    try:
        while True:
            b = br.read_bit()
            if b is None:
                break
            bits.append('1' if b == 1 else '0')
    finally:
        br.close()

    chaine = "".join(bits)
    print(chaine)
    return chaine


def ecriture(fichier_chaine_txt: str, fichier_bin: str) -> None:
    """
    Q4 — Ecriture d’une chaîne de bits (“0”/“1”) vers un fichier binaire.
    """
    # Lire la chaîne de bits (une seule ligne) et retirer espaces/retours
    with open(fichier_chaine_txt, "r", encoding="utf-8") as f:
        line = f.read().strip()

    # Validation stricte: uniquement '0' ou '1'
    for ch in line:
        if ch not in ("0", "1"):
            raise ValueError(
                "Le fichier texte pour Q4 doit contenir uniquement des caractères '0' et '1'."
            )

    # Ecrire la suite de bits dans le binaire
    # (MSB->LSB, octets complets, padding 0 à droite si besoin)
    bw = BitWriter(fichier_bin)
    try:
        bw.write_bits_from_str01(line)
    finally:
        bw.close()
