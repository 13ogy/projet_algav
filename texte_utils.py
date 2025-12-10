class LecteurBits:
    """
    Lit des bits (0/1) à partir d'un flux binaire.
    On utilise nb_bits_utiles pour ignorer le padding final.
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
    # Découpe la chaîne en groupes de 8 bits
    bytes_list = [int(bits[i : i + 8], 2) for i in range(0, len(bits), 8)]
    return bytes(bytes_list).decode("utf-8")


def is_single_utf8_char(bits: str) -> bool:
    """
    Vérifie si la chaîne de bits correspond à un code UTF-8 valide.
    """
    bits_str = bits.replace(" ", "") # On se débarrasse des espaces
    if len(bits_str) == 0 or len(bits_str) % 8 != 0 or len(bits_str) > 32: # Doit être un multiple d'octets, max 4 octets pour UTF-8
        return False
    try:
        # On découpe la chaîne en blocs de 8 bits et on les convertit en octets
        octets_list = [int(bits_str[i:i+8], 2) for i in range(0, len(bits_str), 8)]

        # On transforme la liste d'octets en objet 'bytes'
        byte_sequence = bytes(octets_list)
    except ValueError: # Conversion échouée
        return False

    try:
        # Décode l'objet 'bytes'
        caractere = byte_sequence.decode("utf-8", errors="strict")

        if len(caractere) == 1: # On valide qu'il s'agit d'un seul caractère
            return True
        else:
            return False
    except UnicodeDecodeError: # Erreur levée par Python si le binaire n'est pas un UTF-8 valide
        return False
    except Exception: # Capture d'autres erreurs possibles
        return False


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
