#!/usr/bin/env python3
import os
from collections import deque


# Structure des nœuds de l'arbre AHA
class Noeud:
    def __init__(self, caractere):
        self.caractere = caractere  # Caractère
        self.poids = 1  # Poids
        self.parent = None  # Parent
        self.fg = None  # Fils gauche
        self.fd = None  # Fils droit


class AHA:
    def __init__(self):
        self.dieze = Noeud(
            "ᛃ"
        )  # Notre caractère spécial rune jera, car dièze n'est pas si rare dans les textes
        self.racine = self.dieze
        self.racine.parent = None
        self.dieze.poids = 0
        self.nodes = {"ᛃ": self.dieze} # Hashmap des feuilles, pour que contient() s'exécute en O(1)

    def est_vide(self):
        if self.racine == self.dieze:
            return True
        else:
            return False

    def insert_left(self, noeud_courant, caractere):
        noeud_courant.fg = Noeud(caractere)
        noeud_courant.fg.parent = noeud_courant
        return noeud_courant.fg

    def insert_right(self, noeud_courant, caractere):
        noeud_courant.fd = Noeud(caractere)
        noeud_courant.fd.parent = noeud_courant
        return noeud_courant.fd

    def parcours_largeur_inverse(self):
        """
        Renvoie une liste de nœuds représentant un parcours en largeur
        """
        file = deque([self.racine])
        liste_retour = []
        # La boucle s'exécute tant que la file contient des nœuds à traiter
        while file:
            # Récupération du nœud en tête de file
            defilage = file.popleft()

            liste_retour.append(defilage)
            fg = defilage.fg
            fd = defilage.fd

            if fg is None and fd is None:  # Nœud feuille
                continue
            else:
                # On explore le fils droit puis le fils gauche
                if fd is not None:
                    file.append(fd)
                if fg is not None:
                    file.append(fg)
        return liste_retour

    def parcours_gdbh(self):
        # Renvoie le parcours gdbh de l'AHA
        parcours_largeur = self.parcours_largeur_inverse()
        parcours_largeur.reverse()  # Comme gdbh est un parcours en largeur de droite a gauche inversé
        return parcours_largeur

    def fin_de_bloc(self, noeud):
        # Renvoie le nœud de fin de bloc
        # — le nœud avant le premier nœud avec un poids différent du nœud en argument
        gdbh = self.parcours_gdbh() # On récupère le parcours gdbh
        bloc = False
        for i in range(len(gdbh) - 1):
            if gdbh[i] == noeud:
                bloc = True # On a trouvé le bloc du meme poids
            if bloc:
                if gdbh[i].poids < gdbh[i + 1].poids:
                    return gdbh[i] # On a trouvé notre fin de bloc
        return gdbh[
            len(gdbh) - 1
        ]  # Cas où la racine serait le dernier élément de fin de bloc → c'est elle qu'on renvoie

    def chemin_jusqua_racine(self, noeud):
        """
        Renvoie la liste des nœuds du nœud donné jusqu'à la racine (inclus), dans l'ordre du nœud à la racine.
        """
        nouveau_noeud = noeud
        chemin = []
        continuer = True
        while continuer:
            chemin.append(nouveau_noeud)
            if nouveau_noeud.parent is None or nouveau_noeud == self.racine:
                continuer = False
            nouveau_noeud = nouveau_noeud.parent
        return chemin

    def contient(self, symbole):
        """
        Renvoie le nœud s'il existe dans l'arbre, None sinon.
        """
        return self.nodes.get(symbole, None)

    def modification(self, symbole):
        # Fonction du cours qui renvoie l'AHA avec le symbole incrémente
        noeud_correspondant = self.contient(symbole)
        est_dans_parcours = noeud_correspondant is not None

        if self.est_vide():  # Cas d'arbre vide
            self.racine = Noeud("vide")
            self.racine.poids = 1
            self.dieze.parent = self.racine
            self.racine.fg = self.dieze
            self.racine.fd = Noeud(symbole)
            self.racine.fd.parent = self.racine
            self.racine.parent = None
            self.nodes[symbole] = self.racine.fd
            return self

        elif not est_dans_parcours:
            Q = self.dieze.parent
            nouveau_noeud = Noeud("vide")
            nouveau_noeud.fg = self.insert_left(nouveau_noeud, "ᛃ")
            nouveau_noeud.fg.poids = 0
            nouveau_noeud.fd = self.insert_right(nouveau_noeud, symbole)
            nouveau_noeud.parent = Q
            self.dieze = nouveau_noeud.fg
            Q.fg = nouveau_noeud  # On sait que c'est fg puisqu'on met toujours le dièze à gauche
            self.nodes[symbole] = nouveau_noeud.fd
        else:
            Q = noeud_correspondant
            if Q.parent is not None and (Q.parent.fg.caractere == "ᛃ") and Q.parent == self.fin_de_bloc(Q):
                Q.poids += 1
                Q = Q.parent
        return self.Traitement(Q)

    def Traitement(self, Q):
        # Adaptation de la fonction du cours
        gamma = self.chemin_jusqua_racine(Q)
        gdbh = self.parcours_gdbh()
        successeur_direct_gamma_superieur = True
        for i in range(len(gdbh) - 1):  # On met -1 pour exclure la racine
            if gdbh[i] in gamma:
                if gdbh[i].poids >= gdbh[i + 1].poids:
                    successeur_direct_gamma_superieur = False

        if successeur_direct_gamma_superieur:  # Les poids sont incrémentables
            for i in gamma:
                i.poids += 1
            return self
        else:
            lgamma = len(gamma)
            m = 0
            for i in range(lgamma - 1):  # Cherche le nœud problématique
                if gamma[i].poids == gamma[i + 1].poids:
                    m = i
                    break
            gm = gamma[m]  # Nœud problématique
            b = self.fin_de_bloc(gm)
            for i in range(m + 1):
                gamma[i].poids += 1
            # Échange sous arbres
            parent_original_b = b.parent
            if parent_original_b is None:  # La racine est fin de bloc
                est_b_racine = True
            else:
                est_fgb = b.parent.fg == b
                est_b_racine = False
            if gm.parent is None:  # Cas de la racine
                self.racine = b
                b.parent = None
            else:
                est_fg = gm.parent.fg == gm
                if est_fg:
                    gm.parent.fg = b
                else:
                    gm.parent.fd = b
                b.parent = gm.parent
            gm.parent = parent_original_b
            if not est_b_racine:
                if est_fgb:
                    parent_original_b.fg = gm
                else:
                    parent_original_b.fd = gm
            else:
                self.racine = gm
                return self
        return self.Traitement(gm.parent)

    def encodage_caractere_arbre(self, caractere):
        """
        Le parcours qui traque le nœud dans l'arbre et
        renvoie son codage binaire sous forme d'une chaine de caractères
        """
        pile = [(self.racine, "")]
        while pile:
            noeud, chemin = pile.pop()
            fg = noeud.fg
            fd = noeud.fd
            if noeud.caractere == caractere:
                return chemin
            if fg is not None:
                pile.append((fg, chemin + "0"))
            if fd is not None:
                pile.append((fd, chemin + "1"))
        return None

"""
Fonctions qui ajoutent des statistiques de compression/decompression
"""

NOM_REGISTRE_COMPR = "compression.txt"
NOM_REGISTRE_DECOMPR = "decompression.txt"

def mettre_a_jour_registre_compression(
    chemin_entree: str, chemin_sortie: str, duree: float
) -> None:
    """
    Ajoute une ligne des statistiques dans "compression.txt"
    """
    nom_entree = os.path.basename(chemin_entree)
    nom_sortie = os.path.basename(chemin_sortie)
    try:
        taille_entree = os.path.getsize(chemin_entree)
    except OSError:
        taille_entree = 0

    try:
        taille_sortie = os.path.getsize(chemin_sortie)
    except OSError:
        taille_sortie = 0

    if taille_entree > 0:
        taux = taille_sortie / taille_entree
    else:
        taux = 0.0

    with open(NOM_REGISTRE_COMPR, "a", encoding="utf-8") as registre:
        registre.write(
            f"{nom_entree};{nom_sortie};{taille_entree};{taille_sortie};{taux:.5f};{duree}\n"
        )

def mettre_a_jour_registre_decompression(
    chemin_entree: str, chemin_sortie: str, duree: float
) -> None:
    """
    Ajoute une ligne des statistiques dans "decompression.txt"
    """
    nom_entree = os.path.basename(chemin_entree)
    nom_sortie = os.path.basename(chemin_sortie)
    try:
        taille_entree = os.path.getsize(chemin_entree)
    except OSError:
        taille_entree = 0

    try:
        taille_sortie = os.path.getsize(chemin_sortie)
    except OSError:
        taille_sortie = 0

    if taille_entree > 0:
        taux = taille_entree / taille_sortie # Pour obténir le meme taux qu'a la compression
    else:
        taux = 0.0

    with open(NOM_REGISTRE_DECOMPR, "a", encoding="utf-8") as registre:
        registre.write(
            f"{nom_entree};{nom_sortie};{taille_entree};{taille_sortie};{taux:.5f};{duree}\n"
        )
