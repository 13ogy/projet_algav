#!/usr/bin/env python3
import os

# Structure des noeuds de l'arbre AHA
class Noeud: 
    def __init__(self, caractere):
        self.caractere = caractere  #caractère
        self.poids = 1
        self.parent = None
        self.fg = None #fils gauche
        self.fd = None #fils droit


class AHA:
    def __init__(self):
        
        self.dieze = Noeud('ᛃ') #notre caractère spécial rune jera, car dièze n'est pas si rare dans les textes
        self.racine = self.dieze
        self.racine.parent=None
        self.dieze.poids=0
    
    def est_vide(self):
        if self.racine==self.dieze:
            return True
        else : return False

    def insert_left(self, noeud_courant, caractere):
        noeud_courant.fg = Noeud(caractere)
        noeud_courant.fg.parent=noeud_courant
        return noeud_courant.fg

    def insert_right(self, noeud_courant, caractere):
        noeud_courant.fd = Noeud(caractere)
        noeud_courant.fd.parent=noeud_courant
        return noeud_courant.fd
    
    def parcours_largeur_inverse(self):
        #renvoie une liste de noeuds représentant un parcours en largeur où on explore d'abord le fils droit puis le gauche
        #liste.append((noeud_courant.caractere,noeud_courant.poids))
        file=[self.racine] #utilisations d'une list comme une file
        liste_retour=[]
        taille_file=1
        while taille_file>0 :
            defilage = file.pop(0)
            taille_file-=1
            liste_retour.append((defilage))
            fg=defilage.fg
            fd=defilage.fd
            if fg==None and fd==None:# on est sur une feuille
                continue
            else :              
                if fd!=None:
                    file.append(fd)
                    taille_file+=1
                if fg!=None:
                    taille_file+=1
                    file.append(fg)
        return liste_retour    
    
    
    
    def parcours_gdbh(self):#renvoie le parcours gdbh de l'AHA
        parcours_largeur=self.parcours_largeur_inverse()
        parcours_largeur.reverse() # comme gdbh est un parcours en largeur de droite a gauche inversé
        return parcours_largeur
    
    def afficher_parcours(self,liste): #fonction de debugage
        for i in liste:
            print(i.caractere,i.poids)

    def afficher_parcours_debug(self,liste):
        compteur=0
        print("\nDEBUG longueur liste: \n",len(liste))
        for i in liste:
            compteur+=1
            print("\nDEBUG , tour n°",compteur," :",i.caractere,i.poids)
            if (i.parent!=None):
                print("noeud parent:",i.parent.caractere,i.parent.poids)
            else : print("le parent est inexistant")
            if (i.fg!=None):
                print("fg:",i.fg.caractere,i.fg.poids)
            else : print("le fg est inexistant")
            if (i.fd!=None):
                print("fd:",i.fd.caractere,i.fd.poids)
            else : print("le fd est inexistant")
    
    def fin_de_bloc(self,noeud):#renvoie le noeud de fin de bloc (le premier avec un poids différent du noeud en argument) 
        gdbh=self.parcours_gdbh()
        bloc=False
        for i in range (len(gdbh)-1):
            if gdbh[i]==noeud:#on démarre le bloc
                bloc= True
            if bloc:
                if gdbh[i].poids<gdbh[(i+1)].poids:
                    return gdbh[i]
        return gdbh[len(gdbh)-1]#cas ou la racine serait le dernier élément de fin de bloc -> c'est elle qu'on renvoie 
    
    def chemin_jusqua_racine(self,noeud): #renvoie le chemin jusqu'à la racine
        nouveau_noeud=noeud
        chemin=[]
        continuer=True
        while continuer:
          
            chemin.append(nouveau_noeud)
            
            if (nouveau_noeud.parent==None or nouveau_noeud==self.racine):
                continuer = False
            nouveau_noeud=nouveau_noeud.parent
            
        return chemin

    def contient(self,symbole):
        
        #renvoie le noeud si l'arbre contient le noeud, None sinon
        #le parcours se fait en largeur
        file=[self.racine]
        taille_file=1
        while taille_file>0 :
            defilage = file.pop(0)
            if defilage.caractere==symbole:
                return defilage
            taille_file-=1       
            fg=defilage.fg
            fd=defilage.fd
            if fg==None and fd==None:# on est sur une feuille
                continue
            else :              
                if fd!=None:
                    file.append(fd)
                    taille_file+=1
                if fg!=None:
                    taille_file+=1
                    file.append(fg)
        return None

    def modification(self,symbole):
        #fonction du cours qui renvoie arbre huffman avec le symbole incrémente
        
        
        noeud_correspondant=self.contient(symbole)
        est_dans_parcours=(noeud_correspondant!=None)
        if self.est_vide(): #cas arbre vide
            self.racine = Noeud("vide")
            self.racine.poids=1
            self.dieze.parent=self.racine
            self.racine.fg=self.dieze
            self.racine.fd=Noeud(symbole)
            self.racine.parent=None
            
            return self
        

        elif (not est_dans_parcours):
            Q=self.dieze.parent
            
            nouveau_noeud=Noeud("vide")
            
            nouveau_noeud.fg=self.insert_left(nouveau_noeud,"ᛃ")
            nouveau_noeud.fg.poids=0

            nouveau_noeud.fd=self.insert_right(nouveau_noeud,symbole)
            nouveau_noeud.parent=Q
            nouveau_noeud.parent.fd.parent=Q
            self.dieze=nouveau_noeud.fg
            
            
            Q.fg=nouveau_noeud#on sait que c'est fg puisqu'on insere toujours dièze à gauche
        
        else:
            Q=noeud_correspondant

            if(Q.parent.fg.caractere=="ᛃ") and Q.parent==self.fin_de_bloc(Q): 
                Q.poids+=1
                Q=Q.parent

    
        return self.Traitement(Q)
    
    def Traitement(self,Q): #adaptation de la fonction du cours
        gamma=self.chemin_jusqua_racine(Q)
        
        gdbh=self.parcours_gdbh()
        successeur_direct_gamma_superieur=True
        for i in range(len(gdbh)-1): # on met -1 pour exclure la racine
            if gdbh[i] in gamma:
                
                if gdbh[i].poids>=gdbh[i+1].poids:
                    successeur_direct_gamma_superieur=False

        if successeur_direct_gamma_superieur:#les poids sonts incrémentables
            
            for i in gamma:
                i.poids+=1
            return self
        else:
            lgamma=len(gamma)
            m=0
            for i in range(lgamma-1) : #cherche le noeud problématique
                if gamma[i].poids==gamma[i+1].poids:
                    m=i
                    break
                
            
            gm=gamma[m]#noeud problématique
            b=self.fin_de_bloc(gm)
        
            
            for i in range(m+1):
                gamma[i].poids+=1
            #échange sous arbres
            parent_original_b=b.parent
            if parent_original_b==None:#la racine est fin de bloc
                est_b_racine=True
            else : 
                est_fgb=(b.parent.fg==b)
                est_b_racine=False
            if gm.parent==None: #cas de la racine
                self.racine=b
                b.parent=None
            else :

                est_fg=(gm.parent.fg==gm)
                if est_fg:
                    gm.parent.fg=b
                else :
                    gm.parent.fd=b
                b.parent=gm.parent
            gm.parent=parent_original_b
            if not est_b_racine:
                if est_fgb:
                    parent_original_b.fg=gm
                else :
                    parent_original_b.fd=gm 
            else : 
                self.racine = gm 
                return self
        return self.Traitement(gm.parent)

    def encodage_caractere_arbre(self,caractere):
        # Le parcours qui traque le noeud dans l'arbre et renvoie son codage binaire sous forme d'une chaine de caracteres
        pile=[(self.racine,"")]
        while pile!=[]:
            noeud,chemin=pile.pop()
            fg=noeud.fg
            fd=noeud.fd
            if noeud.caractere==caractere:
                return chemin
            if fg!=None:
                pile.append((fg,chemin+"0"))
            if fd!=None:
                pile.append((fd,chemin+"1"))
        return None        

def char_to_bits(ch: str) -> str:
    return ''.join(f"{byte:08b}" for byte in ch.encode("utf-8"))

def bits_to_char(bits: str) -> str:
    # Découper la chaîne en groupes de 8 bits
    bytes_list = [int(bits[i:i+8], 2) for i in range(0, len(bits), 8)]
    return bytes(bytes_list).decode("utf-8")

def is_single_utf8_char(bits: str) -> bool:
    """
    Fonction qui vérifie si la chaine de bits correspond a un code utf 8
    """
    # enlever les espaces éventuels
    bits = bits.replace(" ", "")
    
    # longueur 8, 16, 24 ou 32 bits
    if len(bits) == 0 or len(bits) % 8 != 0 or len(bits) > 32:
        return False

    # convertir en octets
    b = [int(bits[i:i+8], 2) for i in range(0, len(bits), 8)]
    first = b[0]

    # déterminer la longueur attendue et le début du point de code
    if first & 0b10000000 == 0:           # 0xxxxxxx
        expected = 1
        cp = first & 0b01111111
    elif first & 0b11100000 == 0b11000000: # 110xxxxx
        expected = 2
        cp = first & 0b00011111
    elif first & 0b11110000 == 0b11100000: # 1110xxxx
        expected = 3
        cp = first & 0b00001111
    elif first & 0b11111000 == 0b11110000: # 11110xxx
        expected = 4
        cp = first & 0b00000111
    else:
        return False

    # doit avoir exactement expected octets
    if len(b) != expected:
        return False

    # vérifier les octets de continuation et reconstruire le point de code
    for c in b[1:]:
        if c & 0b11000000 != 0b10000000:  # doit être 10xxxxxx
            return False
        cp = (cp << 6) | (c & 0b00111111)

    # vérification des bornes
    if expected == 1 and not (0x0 <= cp <= 0x7F):
        return False
    if expected == 2 and not (0x80 <= cp <= 0x7FF):
        return False
    if expected == 3 and not (0x800 <= cp <= 0xFFFF):
        return False
    if expected == 4 and not (0x10000 <= cp <= 0x10FFFF):
        return False

    # exclure les surrogates UTF-16
    if 0xD800 <= cp <= 0xDFFF:
        return False

    return True

"""
Fonctions qui ajoutent des statistiques de compression/decompression
"""

NOM_REGISTRE_COMPR = "compression.txt"
NOM_REGISTRE_DECOMPR = "decompression.txt"

def mettre_a_jour_registre_compression(
                           chemin_entree: str,
                           chemin_sortie: str,
                           duree: float) -> None:
    """
    Ajoute une ligne des statistiques dans compression.txt
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
                           chemin_entree: str,
                           chemin_sortie: str,
                           duree: float) -> None:
    """
    Ajoute une ligne es statistiques dans decompression.txt
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

    with open(NOM_REGISTRE_DECOMPR, "a", encoding="utf-8") as registre:
        registre.write(
            f"{nom_entree};{nom_sortie};{taille_entree};{taille_sortie};{taux:.5f};{duree}\n"
        )
