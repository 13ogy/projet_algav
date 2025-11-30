from __future__ import annotations
from dataclasses import dataclass
from collections import deque
from typing import Optional, List, Tuple, Dict, Callable


@dataclass(eq=False)
class Noeud:
    """
    Représentation d’un nœud dans l’arbre de Huffman adaptatif (version O(n) du cours).

    - caractere:
        None  -> nœud interne
        "#"   -> feuille NYT (Not Yet Transmitted)
        "a", "b", ... -> feuille pour un caractère déjà vu
    - poids: fréquence cumulée associée à ce nœud (entier)
    - parent, fg, fd: liens structuraux (respectivement parent, fils gauche, fils droit)
    """
    caractere: Optional[str]
    poids: int = 0
    parent: Optional["Noeud"] = None
    fg: Optional["Noeud"] = None
    fd: Optional["Noeud"] = None

    def est_feuille(self) -> bool:
        """Retourne True si le nœud n’a pas d’enfants (fg=fd=None)."""
        return self.fg is None and self.fd is None


class AHA:
    """
    Arbre de Huffman Adaptatif — Version O(n) fidèle au cours.

    Idée principale:
    - A chaque mise à jour (après lecture/écriture d’un symbole), on reconstruit un ordre “GDBH”
      correct en triant les nœuds par (poids, index de parcours BFS gauche→droite). Cet ordre impose
      des poids non décroissants et des “blocs de même poids” contigus, ce qui permet d’appliquer
      correctement:
        * la Propriété P (chemin incrémentable)
        * fin de bloc (dernier nœud du bloc de même poids)
        * l’échange intra-bloc (jamais avec un ancêtre/descendant)
      puis on remonte.

    Complexité:
    - O(n) par mise à jour (on reconstruit l’ordre et on scanne des listes), ce qui est acceptable
      et robuste sur du texte, et surtout bien aligné avec les transparents “traitement/modification”.
    """

    def __init__(self):
        # Arbre initial = feuille NYT seule (poids 0)
        self.dieze = Noeud(caractere="#", poids=0)
        self.racine = self.dieze

        # Accès direct “symbole -> feuille”, pour retrouver rapidement la feuille d’un caractère
        self._feuilles: Dict[str, Noeud] = {"#": self.dieze}

    # -------------------------------------------------------------------------
    # Utilitaires de parcours et construction d’un ordre GDBH “correct” en O(n)
    # -------------------------------------------------------------------------

    def _collecter_tous_les_noeuds(self) -> List[Noeud]:
        """Collecte tous les nœuds de l’arbre (DFS préfixe)."""
        resultat: List[Noeud] = []

        def dfs(noeud: Optional[Noeud]):
            if noeud is None:
                return
            resultat.append(noeud)
            dfs(noeud.fg)
            dfs(noeud.fd)

        dfs(self.racine)
        return resultat

    def _index_bfs_gauche_droite(self) -> Dict[Noeud, int]:
        """
        Associe à chaque nœud un index donné par un parcours en largeur (BFS) gauche→droite.
        Cet index est utilisé comme second critère de tri au sein des blocs de même poids
        pour stabiliser l’ordre (GDBH “correct”).
        """
        file_bfs: deque[Noeud] = deque([self.racine])
        index_map: Dict[Noeud, int] = {}
        compteur = 0

        while file_bfs:
            courant = file_bfs.popleft()
            index_map[courant] = compteur
            compteur += 1
            if courant.fg is not None:
                file_bfs.append(courant.fg)
            if courant.fd is not None:
                file_bfs.append(courant.fd)

        return index_map

    def _ordre_gdbh(self) -> List[Noeud]:
        """
        Retourne la liste des nœuds triés par (poids, index BFS). Cet ordre garantit des poids
        non décroissants, donc des blocs de même poids contigus, ce qui permet d’appliquer
        fidèlement la Propriété P et fin de bloc.
        """
        tous = self._collecter_tous_les_noeuds()
        index_bfs = self._index_bfs_gauche_droite()
        tous.sort(key=lambda nd: (nd.poids, index_bfs.get(nd, 0)))
        return tous

    # -------------------------------------------------------------------------
    # Tests d’ascendance/descendance
    # -------------------------------------------------------------------------

    def _est_ancetre(self, ancetre: Noeud, noeud: Noeud) -> bool:
        """Retourne True si ‘ancetre’ est un ancêtre de ‘noeud’ (remontée parent→racine)."""
        courant = noeud.parent
        while courant is not None:
            if courant is ancetre:
                return True
            courant = courant.parent
        return False

    # -------------------------------------------------------------------------
    # Opérations sur l’ordre GDBH et les blocs
    # -------------------------------------------------------------------------

    def _successeur_dans_ordre(self, noeud: Noeud, ordre: List[Noeud]) -> Optional[Noeud]:
        """Renvoie le successeur de ‘noeud’ dans ‘ordre’ (ou None s’il n’y en a pas)."""
        for i, nd in enumerate(ordre):
            if nd is noeud:
                return ordre[i + 1] if i + 1 < len(ordre) else None
        return None

    def _fin_de_bloc(self, debut_bloc: Noeud, ordre: List[Noeud]) -> Noeud:
        """
        Renvoie la fin du bloc de même poids que ‘debut_bloc’, en évitant tout échange
        ancêtre/descendant. On parcourt le bloc de la fin vers le début pour choisir un
        candidat “sûr” (ni ancêtre ni descendant).
        """
        poids_cible = debut_bloc.poids

        # Localiser [start, end] = limites du bloc de même poids dans l’ordre
        debut_index = fin_index = None
        for i, nd in enumerate(ordre):
            if nd.poids == poids_cible:
                if debut_index is None:
                    debut_index = i
                fin_index = i
            elif debut_index is not None:
                # On a quitté le bloc
                break

        if debut_index is None:
            return debut_bloc  # sécurité : cas inattendu

        # Rechercher un candidat “sûr” en partant de la fin du bloc
        for k in range(fin_index, debut_index - 1, -1):
            candidat = ordre[k]
            if candidat is debut_bloc:
                continue
            # Pas d’échange si ancêtre/descendant (par prudence)
            if self._est_ancetre(candidat, debut_bloc):
                continue
            if self._est_ancetre(debut_bloc, candidat):
                continue
            return candidat

        # Si tout est interdit, on ne fait pas d’échange (rare)
        return debut_bloc

    # -------------------------------------------------------------------------
    # Échange structurel (réécriture des pointeurs parent/enfant) — O(1)
    # -------------------------------------------------------------------------

    def _echanger_sous_arbres(self, a: Noeud, b: Noeud) -> None:
        """
        Échange les positions de ‘a’ et ‘b’ dans l’arbre :
          - réécrit les pointeurs parent->enfant,
          - met à jour les parents des nœuds échangés.
        Attention: n’appeler que si a et b ne sont ni ancêtre ni descendant l’un de l’autre.
        """
        pa, pb = a.parent, b.parent
        if pa is None or pb is None:
            # Ne pas échanger avec la racine
            return

        # Remplacer ‘a’ par ‘b’ dans pa
        if pa.fg is a:
            pa.fg = b
        else:
            pa.fd = b
        b.parent = pa

        # Remplacer ‘b’ par ‘a’ dans pb
        if pb.fg is b:
            pb.fg = a
        else:
            pb.fd = a
        a.parent = pb

    def _recalculer_poids(self, noeud: Optional[Noeud]) -> int:
        """Recalcul bottom-up des poids, à partir de ‘noeud’ (O(n))."""
        if noeud is None:
            return 0
        if noeud.est_feuille():
            return noeud.poids
        noeud.poids = self._recalculer_poids(noeud.fg) + self._recalculer_poids(noeud.fd)
        return noeud.poids

    # -------------------------------------------------------------------------
    # Traitement (version itérative, fidèle au cours) — O(n) par mise à jour
    # -------------------------------------------------------------------------

    def _traitement_iteratif(self, point_depart: Noeud) -> None:
        """
        Applique le traitement du cours à partir de ‘point_depart’, en mode itératif:
          - construit Gamma (chemin point_depart -> racine),
          - teste la Propriété P,
          - sinon, trouve m où cela coince, applique finDeBloc, incrémente et échange,
          - remonte jusqu’à la racine.
        """
        Q = point_depart
        while Q is not None:
            ordre = self._ordre_gdbh()  # ordre GDBH “correct” (poids non décroissants)

            # Construire Gamma = chemin de Q à la racine (dans l’ordre racine … Q)
            gamma: List[Noeud] = []
            courant = Q
            while courant is not None:
                gamma.append(courant)
                courant = courant.parent
            gamma.reverse()

            # Test Propriété P: pour chaque ‘nd’ dans Gamma,
            # poids(nd) < poids(successeur_GDBH(nd)) (si un successeur existe)
            incrementable = True
            for nd in gamma:
                succ = self._successeur_dans_ordre(nd, ordre)
                if succ is None:
                    continue
                if nd.poids >= succ.poids:
                    incrementable = False
                    break

            if incrementable:
                # Incrémenter tous les nœuds de Gamma
                for nd in gamma:
                    nd.poids += 1
                self._recalculer_poids(self.racine)
                return  # traitement terminé

            # Sinon: trouver m (premier nd dans Gamma où poids(nd) == poids(successeur(nd)))
            index_m = 0
            for i in range(len(gamma) - 1):
                nd = gamma[i]
                succ = self._successeur_dans_ordre(nd, ordre)
                if succ is not None and nd.poids == succ.poids:
                    index_m = i
                    break

            noeud_m = gamma[index_m]
            fin_bloc = self._fin_de_bloc(noeud_m, ordre)  # fin de bloc (pas d’ancêtre/descendant)

            # Incrémenter de la racine jusqu’à ‘noeud_m’ (inclus)
            for i in range(index_m + 1):
                gamma[i].poids += 1

            # Échanger structurellement ‘noeud_m’ et ‘fin_bloc’ si autorisé
            if (not self._est_ancetre(fin_bloc, noeud_m)) and (not self._est_ancetre(noeud_m, fin_bloc)):
                self._echanger_sous_arbres(noeud_m, fin_bloc)

            # On remonte au parent de m et on continue
            Q = noeud_m.parent

        # Sécurité: recalcul global
        self._recalculer_poids(self.racine)

    # -------------------------------------------------------------------------
    # Modification (cours): insertion et traitement
    # -------------------------------------------------------------------------

    def mise_a_jour(self, symbole: str) -> None:
        """
        Modification(H, s) du cours:
          - Cas initial: arbre = NYT seul -> créer interne (fg=NYT, fd=feuille(symbole)).
          - Si ‘symbole’ déjà vu: traitement à partir de sa feuille.
          - Sinon: remplacer NYT par (interne: fg=NYT, fd=feuille(symbole)), puis traitement
            à partir du parent (ou de l’interne si c’est la racine).
        """
        # Cas initial: la racine est une feuille NYT
        if self.racine.est_feuille() and self.racine.caractere == "#":
            noeud_interne = Noeud(caractere=None, poids=1)
            nouveau_dieze = Noeud(caractere="#", poids=0, parent=noeud_interne)
            nouvelle_feuille = Noeud(caractere=symbole, poids=1, parent=noeud_interne)
            noeud_interne.fg, noeud_interne.fd = nouveau_dieze, nouvelle_feuille
            self.racine = noeud_interne
            self.dieze = nouveau_dieze
            self._feuilles["#"] = nouveau_dieze
            self._feuilles[symbole] = nouvelle_feuille
            self._recalculer_poids(self.racine)
            return

        # Symbole déjà vu ?
        feuille_symbole = self._feuilles.get(symbole)
        if feuille_symbole is not None:
            # Traitement à partir de sa feuille
            self._traitement_iteratif(feuille_symbole)
            return

        # Nouveau symbole: remplacer la feuille NYT par (interne + nouvelle feuille)
        parent_dieze = self.dieze.parent
        noeud_interne = Noeud(caractere=None, poids=1, parent=parent_dieze)
        nouveau_dieze = Noeud(caractere="#", poids=0, parent=noeud_interne)
        nouvelle_feuille = Noeud(caractere=symbole, poids=1, parent=noeud_interne)
        noeud_interne.fg, noeud_interne.fd = nouveau_dieze, nouvelle_feuille

        if parent_dieze is None:
            # on remplace la racine
            self.racine = noeud_interne
        else:
            if parent_dieze.fg is self.dieze:
                parent_dieze.fg = noeud_interne
            else:
                parent_dieze.fd = noeud_interne

        # Mise à jour des accès directs
        self.dieze = nouveau_dieze
        self._feuilles["#"] = nouveau_dieze
        self._feuilles[symbole] = nouvelle_feuille

        # Recalcul des poids
        self._recalculer_poids(self.racine)

        # Lancer le traitement à partir du parent inséré (cours)
        self._traitement_iteratif(noeud_interne if parent_dieze is None else parent_dieze)

    # -------------------------------------------------------------------------
    # Codage (code préfixe du symbole) et décodage logique
    # -------------------------------------------------------------------------

    def code_pour(self, symbole: str) -> Tuple[bool, str]:
        """
        Renvoie (is_new, code_binaire) pour ‘symbole’:
          - Si symbole nouveau: code pour NYT (0/1 depuis la racine vers NYT).
          - Sinon: code pour la feuille du symbole.
        """
        cible = self._feuilles.get(symbole, self.dieze)
        is_new = (cible is self.dieze)

        bits: List[str] = []
        courant = cible
        while courant.parent is not None:
            bits.append('0' if courant.parent.fg is courant else '1')
            courant = courant.parent
        bits.reverse()
        return is_new, ''.join(bits)

    def decoder_un_symbole(self, lire_bit: Callable[[], Optional[int]]) -> Tuple[Optional[str], bool]:
        """
        Descend dans l’arbre en lisant des bits (0 = aller à gauche, 1 = aller à droite)
        jusqu’à atteindre une feuille.
          - Si c’est NYT (“#”) -> (None, True) : l’appelant doit lire l’UTF-8 brut ensuite.
          - Sinon -> (symbole, False).
        """
        courant = self.racine
        while not courant.est_feuille():
            bit = lire_bit()
            if bit is None:
                raise EOFError("Fin de flux inattendue pendant le décodage.")
            courant = courant.fg if bit == 0 else courant.fd

        if courant.caractere == "#":
            return None, True
        return courant.caractere, False

    # Alias pour compatibilité avec vos scripts
    def encoder_symbole(self, symbole: str) -> Tuple[bool, str]:
        return self.code_pour(symbole)

