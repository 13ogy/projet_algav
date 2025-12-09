#!/usr/bin/env python3
import sys
import os
import time
import aha_et_utils
import texte_utils


TAILLE_ENTETE_OCTETS = 8  # nombre de bits utiles stocké sur 8 octets


def decomprimer_fichier(chemin_entree: str, chemin_sortie: str) -> None:
    """
    Décompression en flux
    – Lit le .huff binaire
    - Récupère en-tête nb_bits_utiles
    - Lit les bits au fur et à mesure
    """
    if not os.path.exists(chemin_entree):
        print(f"Le fichier d'entrée '{chemin_entree}' n'existe pas.")
        sys.exit(1)

    debut = time.perf_counter()

    with open(chemin_entree, "rb") as fichier_entree:
        # Lecture de l'en-tête : nombre de bits utiles
        entete = fichier_entree.read(TAILLE_ENTETE_OCTETS)
        if len(entete) != TAILLE_ENTETE_OCTETS:
            print("Fichier compressé invalide : en-tête manquante ou incomplète.")
            sys.exit(1)

        nb_bits_utiles = int.from_bytes(entete, "big")
        lecteur_bits = texte_utils.LecteurBits(fichier_entree, nb_bits_utiles)

        # On écrase le fichier de sortie.
        with open(chemin_sortie, "w", encoding="utf-8") as fichier_sortie:
            arbre = aha_et_utils.AHA()  # Initialise un arbre avec dieze

            noeud = arbre.racine  # On commence le parcours depuis la racine
            texte_init = ""  # Sert quand on vient de rencontrer un dieze

            caracterecorrespondant = ""  # Quand on est sur une feuille
            test = (
                lecteur_bits.lire_bit()
            )  # Lit le premier bit qui est nécessairement un dièze donc 0
            post_dieze = True  # Cas du caractère succédant à #
            en_cours_de_parcours = False  # Indique dans la boucle si on doit rechercher dans l'arborescence
            caractere_trouve = (
                False  # Indique dans la boucle si on a trouvé un caractere dans l'arbre
            )
            if test != 0:
                print("Erreur ne commence pas par le caractère spécial")
            while True:
                bit = lecteur_bits.lire_bit()

                if en_cours_de_parcours:
                    # Recherche un caractere en suivant l'arbre selon le flux de bits
                    if noeud is None:
                        print("Erreur : on a pas une feuille")

                    if bit == 1:
                        if noeud.fd is None:  # On est au bout

                            en_cours_de_parcours = False
                            caractere_trouve = True
                        else:

                            noeud = noeud.fd
                            continue
                    elif bit == 0:
                        if noeud.fg is None:  # On est au bout
                            en_cours_de_parcours = False
                            caractere_trouve = True

                        else:
                            noeud = noeud.fg

                            continue

                    else:  # N'arrive qu'en fin de parcours
                        pass

                if (
                    caractere_trouve
                ):  # Peut s'effectuer juste après, toujours avec le même caractère que dans le elif ci dessus

                    caracterecorrespondant = (
                        noeud.caractere
                    )  # Lit a partir du curseur et renvoie un caractere, sa profondeur, et son chemin binaire

                    noeud = arbre.racine  # On recommence le parcours depuis la racine

                    if (
                        caracterecorrespondant == "ᛃ"
                    ):  # On ne vas pas écrire # dans le fichier

                        post_dieze = True  # Pour le prochain tour de boucle on ira chercher dans le codage utf8
                        en_cours_de_parcours = False

                    else:  # On écrit le caractere en utf8

                        fichier_sortie.write(
                            caracterecorrespondant
                        )  # Écrit dans le fichier
                        arbre.modification(
                            caracterecorrespondant
                        )  # On actualise l'arbre
                        caracterecorrespondant = ""
                        en_cours_de_parcours = True  # Indique dans la boucle si on doit rechercher dans l'arborescence
                        post_dieze = False  # Au cas ou

                        # On parcourt l'arbre avec le caractère courant
                        if noeud is None:
                            print("Erreur : on a pas une feuille")

                        if bit == 1:
                            noeud = noeud.fd  # On va à droite

                        elif bit == 0:
                            noeud = noeud.fg  # On va à gauche

                    caractere_trouve = False  # Indique qu'il faudra chercher un caractère dans la prochaine itération

                if post_dieze:  # Le caractère précédent était un dièze
                    texte_init += str(bit)  # "Enmagasine" les bits jusqu'à avoir un utf8

                    if texte_utils.is_single_utf8_char(
                        texte_init
                    ):  # La suite de bits dans le texte init représente un caractère utf 8

                        caracterecorrespondant = texte_utils.bits_to_char(texte_init)

                        fichier_sortie.write(
                            caracterecorrespondant
                        )  # Écrit dans le fichier
                        arbre.modification(
                            caracterecorrespondant
                        )  # On actualise l'arbre
                        caracterecorrespondant = ""
                        post_dieze = False
                        en_cours_de_parcours = True  # Indique dans la boucle si on doit rechercher dans l'arborescence
                        caractere_trouve = False  # Indique dans la boucle si on a trouvé un caractere dans l'arbre
                        noeud = arbre.racine  # On commence le parcours depuis la racine
                        texte_init = ""  # Vide pour la suite

                if bit is None:  # Il n'y a plus rien à lire
                    break

            caracterecorrespondant = noeud.caractere
            if caracterecorrespondant != "vide":  # Évite un bug
                fichier_sortie.write(
                    caracterecorrespondant
                )  # Écrit dans le fichier le dernier caractère stocké

    duree = int((time.perf_counter() - debut) * 1000)  # Pour le temps en ms

    aha_et_utils.mettre_a_jour_registre_decompression(chemin_entree, chemin_sortie, duree)
    print(f"Décompression terminée : '{chemin_entree}' → '{chemin_sortie}'")


def main():
    if len(sys.argv) != 3:
        print(f"Usage : {sys.argv[0]} <fichier_entree.huff> <fichier_sortie.txt>")
        sys.exit(1)

    chemin_entree = sys.argv[1]
    chemin_sortie = sys.argv[2]

    if os.path.exists(chemin_sortie):
        os.remove(chemin_sortie)

    decomprimer_fichier(chemin_entree, chemin_sortie)
    return "Terminé"


if __name__ == "__main__":
    main()
