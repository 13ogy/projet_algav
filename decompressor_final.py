#!/usr/bin/env python3
import sys
import os
import time
import aha_et_utils as projet


TAILLE_ENTETE_OCTETS = 8  # nombre de bits utiles stocké sur 8 octets


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
        """Retourne 0 ou 1, ou None si tous les bits utiles ont été lus."""
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


def decomprimer_fichier(chemin_entree: str, chemin_sortie: str) -> None:
    """
    Décompression en flux :
    - lit le .huff binaire
    - récupère en-tête nb_bits_utiles
    - lit les bits au fur et à mesure
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
        lecteur_bits = LecteurBits(fichier_entree, nb_bits_utiles)

        # On écrase le fichier de sortie.
        with open(chemin_sortie, "w", encoding="utf-8") as fichier_sortie:
            arbre = projet.AHA() # Initialise un arbre avec dieze

            noeud = arbre.racine # On commence le parcours depuis la racine
            texte_init = "" # Sert quand on vient de rencontrer un dieze

            caracterecorrespondant = "" # quand on est sur une feuille
            test=lecteur_bits.lire_bit()#lit le premier bit qui est nécessairement un dièze donc 0
            post_dieze=True#cas du caractère succédant à #
            en_cours_de_parcours=False #indique dans la boucle si on dois rechercher dans l'arborescnece
            caractere_trouve=False #indique dans la boucle si on a trouvé un caractere dans l'arbre
            if test!=0:
                print("erreur ne commence pas par le caractère spécial")
            while True:
                bit = lecteur_bits.lire_bit()
        
                if en_cours_de_parcours:
                #recherche un caractere en suivant l'arbre selon le flux de bits                   
                #print("debug c : ",c)
                    if noeud==None:
                        print("erreur : on a pas une feuille")   
                        
                    if bit==1:
                        if noeud.fd is None: # On est au bout
                            
                            en_cours_de_parcours=False
                            caractere_trouve=True
                        else :
                            
                            noeud=noeud.fd
                            continue
                    elif bit==0:
                        if noeud.fg==None:#on est au bout
                            en_cours_de_parcours=False
                            caractere_trouve=True
                            
                        else :
                            noeud=noeud.fg
                            
                            continue
                    
                    else:# n'arrive qu'en fin de parcours
                        pass
                    
                if (caractere_trouve):#peut s'effectuer juste après, toujours avec le même caractère que dans le elif ci dessus
                    
                    caracterecorrespondant=noeud.caractere #lit a partir du curseur et renvoie un caractere,sa profondeur, et son chemin binaire
                    
                    noeud=arbre.racine#on recommence le parcours depuis la racine
                    
                    if caracterecorrespondant=="ᛃ":#on ne vas pas écrire # dans le fichier
                        
                        post_dieze=True #pour le prochain tour de boucle on ira chercher dans le codage utf8
                        en_cours_de_parcours=False
                         
                        
                        
                    else:#on écrtit le caractere en utf8
                        
                        fichier_sortie.write(caracterecorrespondant) # écrit dans le fichier
                        arbre.modification(caracterecorrespondant) # on actualise l'arbre
                        caracterecorrespondant = ""
                        en_cours_de_parcours=True #indique dans la boucle si on dois rechercher dans l'arborescnece
                        post_dieze=False #au cas ou

                        #on parcours l'arbre avec la carctère courant
                        if noeud==None:
                            print("erreur : on a pas une feuille")   
                        
                        if bit==1:
                            noeud=noeud.fd #on va à droie
                                                   
                        elif bit==0:
                            noeud=noeud.fg #on va à gauche
                    
                    caractere_trouve=False #indique qu'il faudra chercher un caractère dans la prochaine itération
                    

                if post_dieze : #le carctère précednet était un dièze
                    texte_init+=str(bit) #enmmagasine les bits jusqu'à avoir un utf8

                    if projet.is_single_utf8_char(texte_init): #la suite de bits dans texte init représente un caractère utf 8
                        
                        caracterecorrespondant=projet.bits_to_char(texte_init)

                        fichier_sortie.write(caracterecorrespondant)#écrit dans le fichier
                        arbre.modification(caracterecorrespondant)#on actualise l'arbre
                        caracterecorrespondant=""
                        post_dieze=False
                        en_cours_de_parcours=True #indique dans la boucle si on dois rechercher dans l'arborescnece
                        caractere_trouve=False #indique dans la boucle si on a trouvé un caractere dans l'arbre
                        noeud=arbre.racine#on commence le parcours depuis la racine
                        texte_init=""#vide pour la suite

                if bit is None:#il n'y a plus rien à lire
                    break
            
            caracterecorrespondant=noeud.caractere
            if caracterecorrespondant!="vide":#évite un bug
                fichier_sortie.write(caracterecorrespondant)#écrit dans le fichier le dernier caractère stocké

    duree = int ((time.perf_counter() - debut)* 1000) #pour le temps en ms
   
    projet.mettre_a_jour_registre_decompression(chemin_entree, chemin_sortie, duree)
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