from bitio import BitReader, BitWriter

def lecture(fichier_bin: str) -> str:
    """
    Q3 — Lit fichier_bin et renvoie/affiche son contenu sous forme d'une chaîne de bits.
    Conventions: lecture MSB→LSB, regroupée par octets (cf. BitReader).
    """
    br = BitReader(fichier_bin)
    bits = []
    while True:
        b = br.read_bit()
        if b is None:
            break
        bits.append('1' if b == 1 else '0')
    br.close()
    chaine = "".join(bits)
    print(chaine)
    return chaine

def ecriture(fichier_chaine_txt: str, fichier_bin: str) -> None:
    """
    Q4 — Lit une suite de bits ('0'/'1') dans fichier_chaine.txt (une seule ligne),
    et écrit le binaire correspondant dans fichier_bin (lisible par lecture()).
    Conventions: écriture MSB→LSB, regroupée par octets, padding 0 si nécessaire.
    Remarque: ce fichier est lisible par lecture(), conformément à l'énoncé.
    """
    with open(fichier_chaine_txt, "r", encoding="utf-8") as f:
        line = f.read().strip()

    # Validation simple: uniquement 0/1
    for ch in line:
        if ch not in ("0", "1"):
            raise ValueError("Le fichier texte ne doit contenir que des bits '0' et '1' sur une seule ligne.")

    bw = BitWriter(fichier_bin)
    bw.write_bits_from_str01(line)
    bw.close()
