#!/usr/bin/env python3
import sys
import os
import time
import aha_et_utils as projet


def ecrire_bits(fout, bits: str, etat):
    """
    Écrit une chaîne de bits '0'/'1' dans le fichier binaire fout,
    en utilisant un petit état pour le byte en cours.
    'etat' est un dict contenant :
        - current_byte : entier [0..255]
        - bit_pos      : nombre de bits déjà remplis dans current_byte (0..7)
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

        # Quand on a 8 bits, on écrit l'octet
        if etat["bit_pos"] == 8:
            fout.write(bytes([etat["current_byte"]]))
            etat["current_byte"] = 0
            etat["bit_pos"] = 0


def compresser_fichier(chemin_entree: str, chemin_sortie: str) -> None:
    """
    Lit 'chemin_entree' en binaire, octet par octet, puis bit par bit,
    compresse en bits (algo de compression dans la boucle centrale)
    et écrit dans 'chemin_sortie' un fichier binaire .huff avec :

        [8 octets en-tête = nb_bits utiles (entier 64 bits, big-endian)]
        [flux de bits compressés, complété par du padding de 0 jusqu'à l'octet]
    """
    # Vérifier que le fichier d'entrée existe
    if not os.path.exists(chemin_entree):
        print(f"Erreur : le fichier d'entrée '{chemin_entree}' n'existe pas.")
        sys.exit(1)

    # Ouvrir le fichier d'entrée en lecture binaire
    try:
        fin = open(chemin_entree, "rb")
    except OSError as e:
        print(f"Erreur à l'ouverture de '{chemin_entree}' en lecture : {e}")
        sys.exit(1)

    # Ouvrir le fichier de sortie en binaire, en l'écrasant
    try:
        fout = open(chemin_sortie, "wb")
    except OSError as e:
        fin.close()
        print(f"Erreur à l'ouverture de '{chemin_sortie}' en écriture binaire : {e}")
        sys.exit(1)

    # On réserve huit octets pour l'en-tête (nb_bits). On met 0 pour l'instant.
    fout.write(b"\x00" * 8)

    # État pour l'écriture bit par bit
    etat = {
        "current_byte": 0,
        "bit_pos": 0,   # nombre de bits actuellement dans current_byte (0..7)
        "nb_bits": 0,   # nombre de bits UTILES écrits (sans le padding)
    }

    debut = time.perf_counter()

    bits = ""
    arbre = projet.AHA()  # initialise un arbre avec dièse / NYT

    # initialise une table des caractères déjà vus avec leur codage de huffman correspondant
    table_correspondance = {"ᛃ": "0"}
    buffer="" #se remplira petit à petit des bits

    # ---------------  BOUCLE PRINCIPALE ---------------
    # Lecture binaire, octet par octet, puis bit par bit ---
    try:
        while True:
            chunk = fin.read(1)       # <<< lecture octet par octet
            if not chunk:
                break

            byte = chunk[0]           # entier 0–255

            # pour chaque octet, on lit les 8 bits (MSB -> LSB)
            for bit_index in range(7, -1, -1):
                bit_val = (byte >> bit_index) & 1

                # on crée un "pseudo-caractère" à partir du bit (tu adapteras)
                bit = "1" if bit_val == 1 else "0" #un bit en str
                buffer+=bit
                if projet.is_single_utf8_char(buffer): #la suite de bits dans texte init représente un caractère utf 8
                    ch=projet.bits_to_char(buffer)
                    buffer=""
                    

                    if ch in table_correspondance.keys():  # on a déjà vu le caractère

                        bits += arbre.encodage_caractere_arbre(ch)  # on utilise son codage compressé

                    else:  # caractère nouveau

                        bits += table_correspondance["ᛃ"]  # transmet le caractère spécial

                        bits += projet.char_to_bits(ch)  # ajoute l'encodage utf 8 (à toi d'adapter)

                    arbre.modification(ch)  # actualise l'arbre

                    table_correspondance[ch] = arbre.encodage_caractere_arbre(ch)  # actualise la table

                    table_correspondance["ᛃ"] = arbre.encodage_caractere_arbre("ᛃ")  # actualise la table pour le caractère spécial
                    # arbre.afficher_parcours_debug(arbre.parcours_gdbh())

                    if bits:
                        ecrire_bits(fout, bits, etat)  # écrits dans le fichier
                        bits = ""
    # --------------- FIN BOUCLE ---------------

    finally:
        fin.close()

    # --- Padding : compléter le dernier octet avec des '0' si besoin ---
    if etat["bit_pos"] > 0:
        # On décale les bits restants vers la gauche pour remplir l'octet
        etat["current_byte"] <<= (8 - etat["bit_pos"])
        fout.write(bytes([etat["current_byte"]]))
        # nb_bits NE CHANGE PAS : on ne compte pas le padding dans nb_bits

    # --- Écriture réelle de l'en-tête avec nb_bits ---
    nb_bits = etat["nb_bits"]
    # On revient au début du fichier
    fout.seek(0)
    # Écrit nb_bits sur 8 octets (entier 64 bits, big-endian)
    fout.write(nb_bits.to_bytes(8, byteorder="big"))

    fout.close()
    duree = int((time.perf_counter() - debut) * 1000)  # * 1000 pour les millisecondes

    # mise à jour du registre comme avant
    projet.mettre_a_jour_registre_compression(chemin_entree, chemin_sortie, duree)

    print(f"Compression terminée : '{chemin_entree}' → '{chemin_sortie}'")


def main():
    if len(sys.argv) != 3:  # vérification de nb d'arguments
        print(f"Usage : {sys.argv[0]} <fichier_entree.txt> <fichier_sortie.huff>")
        sys.exit(1)

    # Récupération des arguments
    chemin_entree = sys.argv[1]
    chemin_sortie = sys.argv[2]

    compresser_fichier(chemin_entree, chemin_sortie)


if __name__ == "__main__":
    main()
