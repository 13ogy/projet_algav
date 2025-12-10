import os
import texte_utils


def lecture(fichier_bin: str) -> str:
    """
    Q3 — Lecture d’un fichier binaire en chaîne de bits.
    """
    with open(fichier_bin, "rb") as f:
        nb_bits_utiles = os.path.getsize(fichier_bin) * 8 # Fois huit pour passer de bytes en bits
        lecteur = texte_utils.LecteurBits(f, nb_bits_utiles)
        bits = []
        while True:
            b = lecteur.lire_bit()
            if b is None:
                break
            bits.append('1' if b == 1 else '0')
    chaine = "".join(bits)
    print(chaine)
    return chaine


def ecriture(fichier_chaine_txt: str, fichier_bin: str) -> None:
    """
    Q4 — Ecriture d’une chaîne de bits (“0”/“1”) vers un fichier binaire.
    """
    # Lit la chaîne de bits et retire les espaces éventuels
    with open(fichier_chaine_txt, "r", encoding="utf-8") as f:
        line = f.read().strip()

    # Uniquement '0' ou '1'
    for ch in line:
        if ch not in ("0", "1"):
            raise ValueError(
                "Le fichier texte pour Q4 doit contenir uniquement des caractères '0' et '1'."
            )

    # Écrit la suite de bits dans le binaire (MSB → LSB, octets complets, padding 0 à fin si besoin)
    with open(fichier_bin, "wb") as fout:
        etat = {
            "current_byte": 0,
            "bit_pos": 0,
            "nb_bits": 0,
        }
        texte_utils.ecrire_bits(fout, line, etat)

        # Padding
        if etat["bit_pos"] > 0:
            etat["current_byte"] <<= (8 - etat["bit_pos"])
            fout.write(bytes([etat["current_byte"]]))
