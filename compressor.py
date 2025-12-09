#!/usr/bin/env python3
import sys
import os
import time
import aha_et_utils
import texte_utils


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
        "bit_pos": 0,  # Nombre de bits actuellement dans current_byte (0..7)
        "nb_bits": 0,  # Nombre de bits UTILES écrits (sans le padding)
    }

    debut = time.perf_counter()

    bits = ""
    arbre = aha_et_utils.AHA()  # Initialise un arbre avec dièse / NYT

    # Initialise une table des caractères déjà vus avec leur codage de huffman correspondant
    table_correspondance = {"ᛃ": "0"}
    buffer = ""  # Se remplira petit à petit des bits

    # ---------------  BOUCLE PRINCIPALE ---------------
    # Lecture binaire, octet par octet, puis bit par bit ---
    try:
        while True:
            chunk = fin.read(1)  # <<< lecture octet par octet
            if not chunk:
                break

            byte = chunk[0]  # Entier 0–255

            # Pour chaque octet, on lit les 8 bits (MSB -> LSB)
            for bit_index in range(7, -1, -1):
                bit_val = (byte >> bit_index) & 1

                bit = "1" if bit_val == 1 else "0"  # Un bit en str
                buffer += bit
                if texte_utils.is_single_utf8_char(
                    buffer
                ):  # La suite de bits dans buffer représente un caractère utf 8
                    ch = texte_utils.bits_to_char(buffer)
                    buffer = ""

                    if ch in table_correspondance:  # On a déjà vu le caractère

                        bits += arbre.encodage_caractere_arbre(
                            ch
                        )  # On utilise son codage compressé

                    else:  # Caractère nouveau

                        bits += table_correspondance[
                            "ᛃ"
                        ]  # Transmet le caractère spécial

                        bits += texte_utils.char_to_bits(ch)  # Ajoute l'encodage utf 8

                    arbre.modification(ch)  # Actualise l'arbre

                    table_correspondance[ch] = arbre.encodage_caractere_arbre(
                        ch
                    )  # Actualise la table

                    table_correspondance["ᛃ"] = arbre.encodage_caractere_arbre(
                        "ᛃ"
                    )  # Actualise la table pour le caractère spécial

                    if bits:
                        texte_utils.ecrire_bits(
                            fout, bits, etat
                        )  # Écrits dans le fichier
                        bits = ""
    # --------------- FIN BOUCLE ---------------

    finally:
        fin.close()

    # --- Padding : compléter le dernier octet avec des '0' si besoin ---
    if etat["bit_pos"] > 0:
        # On décale les bits restants vers la gauche pour remplir l'octet
        etat["current_byte"] <<= 8 - etat["bit_pos"]
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

    # Mise à jour du registre comme avant
    aha_et_utils.mettre_a_jour_registre_compression(chemin_entree, chemin_sortie, duree)

    print(f"Compression terminée : '{chemin_entree}' → '{chemin_sortie}'")


def main():
    if len(sys.argv) != 3:  # Vérification de nb d'arguments
        print(f"Usage : {sys.argv[0]} <fichier_entree.txt> <fichier_sortie.huff>")
        sys.exit(1)

    # Récupération des arguments
    chemin_entree = sys.argv[1]
    chemin_sortie = sys.argv[2]

    compresser_fichier(chemin_entree, chemin_sortie)


if __name__ == "__main__":
    main()
