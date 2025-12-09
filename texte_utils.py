class LecteurBits:
    """
    Lit des bits (0/1) à partir d'un flux binaire.
    On limite à nb_bits_utiles pour ignorer le padding final.
    """

    def __init__(self, fichier_binaire, nb_bits_utiles: int):
        self.fichier = fichier_binaire
        self.nb_bits_restants = nb_bits_utiles
        self.tampon = 0
        self.nb_bits_tampon = 0

    def lire_bit(self):
        """
        Retourne 0 ou 1, ou None si tous les bits utiles ont été lus.
        """
        if self.nb_bits_restants <= 0:
            return None

        if self.nb_bits_tampon == 0:
            octet = self.fichier.read(1)
            if not octet:
                # Fichier tronqué par rapport au nombre de bits annoncés
                return None
            self.tampon = octet[0]
            self.nb_bits_tampon = 8

        bit = (self.tampon >> 7) & 1
        self.tampon = (self.tampon << 1) & 0xFF
        self.nb_bits_tampon -= 1
        self.nb_bits_restants -= 1
        return bit

    def lire_n_bits(self, n: int) -> str:
        """
        Lit n bits et les renvoie sous forme de chaîne '0'/'1'.
        Peut renvoyer moins de n bits si la fin est atteinte.
        Utile si tu veux lire un octet complet après un NYT par exemple.
        """
        bits = []
        for _ in range(n):
            b = self.lire_bit()
            if b is None:
                break
            bits.append("1" if b else "0")
        return "".join(bits)


def char_to_bits(ch: str) -> str:
    """
    Convertit un caractère UTF-8 en chaîne de bits.
    """
    return "".join(f"{byte:08b}" for byte in ch.encode("utf-8"))


def bits_to_char(bits: str) -> str:
    """
    Convertit une chaîne de bits en caractère UTF-8.
    """
    # Découper la chaîne en groupes de 8 bits
    bytes_list = [int(bits[i : i + 8], 2) for i in range(0, len(bits), 8)]
    return bytes(bytes_list).decode("utf-8")


def is_single_utf8_char(bits: str) -> bool:
    """
    Vérifie si la chaîne de bits correspond à un code UTF-8 valide.
    """
    # Enlever les espaces éventuels
    bits = bits.replace(" ", "")

    # Longueur 8, 16, 24 ou 32 bits
    if len(bits) == 0 or len(bits) % 8 != 0 or len(bits) > 32:
        return False

    # Convertir en octets
    b = [int(bits[i : i + 8], 2) for i in range(0, len(bits), 8)]
    first = b[0]

    # Déterminer la longueur attendue et le début du point de code
    if first & 0b10000000 == 0:  # 0xxxxxxx
        expected = 1
        cp = first & 0b01111111
    elif first & 0b11100000 == 0b11000000:  # 110xxxxx
        expected = 2
        cp = first & 0b00011111
    elif first & 0b11110000 == 0b11100000:  # 1110xxxx
        expected = 3
        cp = first & 0b00001111
    elif first & 0b11111000 == 0b11110000:  # 11110xxx
        expected = 4
        cp = first & 0b00000111
    else:
        return False

    # Doit avoir exactement expected octets
    if len(b) != expected:
        return False

    # Vérifier les octets de continuation et reconstruire le point de code
    for c in b[1:]:
        if c & 0b11000000 != 0b10000000:  # Doit être 10xxxxxx
            return False
        cp = (cp << 6) | (c & 0b00111111)

    # Vérification des bornes
    if expected == 1 and not (0x0 <= cp <= 0x7F):
        return False
    if expected == 2 and not (0x80 <= cp <= 0x7FF):
        return False
    if expected == 3 and not (0x800 <= cp <= 0xFFFF):
        return False
    if expected == 4 and not (0x10000 <= cp <= 0x10FFFF):
        return False

    # Exclure les surrogates UTF-16
    if 0xD800 <= cp <= 0xDFFF:
        return False

    return True


def ecrire_bits(fout, bits: str, etat):
    """
    Écrit une chaîne de bits '0'/'1' dans le fichier binaire fout,
    en utilisant un petit état pour le byte en cours.
    'etat' est un dict contenant
        — current_byte : entier [0..255]
        – bit_pos      : nombre de bits déjà remplis dans current_byte (0..7)
        - nb_bits      : nombre total de bits UTILES écrits (sans padding)
    """
    for b in bits:
        if b not in ("0", "1"):
            raise ValueError(f"Bit invalide : {b!r}")

        bit = 1 if b == "1" else 0

        # On pousse le bit en mode MSB-first
        etat["current_byte"] = (etat["current_byte"] << 1) | bit
        etat["bit_pos"] += 1
        etat["nb_bits"] += 1

        # Quand on a 8 bits, on écrit un octet
        if etat["bit_pos"] == 8:
            fout.write(bytes([etat["current_byte"]]))
            etat["current_byte"] = 0
            etat["bit_pos"] = 0
