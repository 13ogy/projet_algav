from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Callable


@dataclass
class Noeud:
    """Noeud binaire pour Huffman adaptatif.
    - caractere: str pour une feuille, '#' pour NYT, None pour un nœud interne
    - poids: entier (0 au départ pour NYT)
    """
    caractere: Optional[str]
    poids: int = 0
    parent: Optional["Noeud"] = None
    fg: Optional["Noeud"] = None
    fd: Optional["Noeud"] = None

    def est_feuille(self) -> bool:
        return self.fg is None and self.fd is None


class AHA:
    """Arbre de Huffman Adaptatif (NYT, fin de bloc, échanges sans ancêtre).
    Référence: cours Huffman dynamique (propriété P, finBloc, traitement) [1][4][5].
    """

    def __init__(self) -> None:
        self.dieze: Noeud = Noeud(caractere="#", poids=0)
        self.racine: Noeud = self.dieze
        self._feuilles: Dict[str, Noeud] = {"#": self.dieze}

    # --------- Utilitaires structurels ---------

    def _est_ancetre(self, ancetre: Noeud, n: Noeud) -> bool:
        cur = n.parent
        while cur is not None:
            if cur is ancetre:
                return True
            cur = cur.parent
        return False

    def _parcours_gdbh(self) -> List[Noeud]:
        """Vue GDBH (préfixe gauche/droite) pour repérer les blocs de poids."""
        ordre: List[Noeud] = []

        def dfs(x: Optional[Noeud]) -> None:
            if x is None:
                return
            ordre.append(x)
            dfs(x.fg)
            dfs(x.fd)

        dfs(self.racine)
        return ordre

    def _fin_de_bloc(self, noeud: Noeud) -> Noeud:
        """Leader de bloc (dernier nœud de même poids, non-ancêtre du noeud)."""
        gdbh = self._parcours_gdbh()
        # position du noeud
        idx = -1
        for i, n in enumerate(gdbh):
            if n is noeud:
                idx = i
                break
        if idx == -1:
            return noeud

        w = noeud.poids
        end = idx
        for j in range(idx, len(gdbh)):
            if gdbh[j].poids == w:
                end = j
            else:
                break

        # dernier élément du bloc qui n'est pas ancêtre
        for k in range(end, idx - 1, -1):
            cand = gdbh[k]
            if cand is noeud:
                continue
            if not self._est_ancetre(cand, noeud):
                return cand
        return noeud

    def _echanger_sous_arbres(self, a: Noeud, b: Noeud) -> None:
        """Échange les sous-arbres enracinés en a et b (pas d’ancêtre)."""
        pa = a.parent
        pb = b.parent
        if pa is None or pb is None:
            return

        # Remplacer a par b dans pa
        if pa.fg is a:
            pa.fg = b
        else:
            pa.fd = b
        b.parent = pa

        # Remplacer b par a dans pb
        if pb.fg is b:
            pb.fg = a
        else:
            pb.fd = a
        a.parent = pb

    def _recalculer_poids(self, n: Optional[Noeud]) -> int:
        """Recalcule récursivement le poids d’un sous-arbre."""
        if n is None:
            return 0
        if n.est_feuille():
            return n.poids
        n.poids = self._recalculer_poids(n.fg) + self._recalculer_poids(n.fd)
        return n.poids

    # --------- API encodage/décodage logique ---------

    def code_pour(self, caractere: str) -> Tuple[bool, str]:
        """(is_new, code) pour un symbole.
        - si nouveau: (True, code(NYT))
        - sinon: (False, code(feuille(caractere)))
        """
        cible: Noeud
        if caractere in self._feuilles and caractere != "#":
            cible = self._feuilles[caractere]
        else:
            cible = self.dieze

        bits: List[str] = []
        cur = cible
        while cur.parent is not None:
            if cur.parent.fg is cur:
                bits.append('0')
            else:
                bits.append('1')
            cur = cur.parent
        bits.reverse()
        return (cible is self.dieze, "".join(bits))

    def inserer_nouveau_symbole(self, caractere: str) -> None:
        """Remplace NYT par un nœud interne (fg: nouveau NYT, fd: nouvelle feuille)."""
        if self.dieze.parent is None:
            # Racine = NYT
            interne = Noeud(caractere=None, poids=1, parent=None)
            nouveau_nyt = Noeud(caractere="#", poids=0, parent=interne)
            feuille = Noeud(caractere=caractere, poids=1, parent=interne)
            interne.fg = nouveau_nyt
            interne.fd = feuille
            self.racine = interne
            self.dieze = nouveau_nyt
            self._feuilles["#"] = self.dieze
            self._feuilles[caractere] = feuille
            self._recalculer_poids(self.racine)
            return

        p = self.dieze.parent
        interne = Noeud(caractere=None, poids=1, parent=p)
        nouveau_nyt = Noeud(caractere="#", poids=0, parent=interne)
        feuille = Noeud(caractere=caractere, poids=1, parent=interne)
        interne.fg = nouveau_nyt
        interne.fd = feuille

        if p.fg is self.dieze:
            p.fg = interne
        else:
            p.fd = interne

        self.dieze = nouveau_nyt
        self._feuilles["#"] = self.dieze
        self._feuilles[caractere] = feuille
        self._recalculer_poids(self.racine)

    def _traitement_depuis(self, noeud: Noeud) -> None:
        """Traitement: fin de bloc → échanges (sans ancêtre) → incrément → remonter."""
        cur = noeud
        while cur is not None:
            leader = self._fin_de_bloc(cur)
            if (leader is not cur) and (not self._est_ancetre(leader, cur)) and (not self._est_ancetre(cur, leader)):
                self._echanger_sous_arbres(cur, leader)
            cur.poids = cur.poids + 1
            cur = cur.parent
        self._recalculer_poids(self.racine)

    def mise_a_jour(self, caractere: str) -> None:
        """Modification(H, s): insertion si nouveau, puis traitement (ou traitement direct)."""
        if caractere not in self._feuilles:
            anc = self.dieze.parent
            self.inserer_nouveau_symbole(caractere)
            if anc is not None:
                self._traitement_depuis(anc)
        else:
            self._traitement_depuis(self._feuilles[caractere])

    def decoder_un_symbole(self, lire_bit: Callable[[], Optional[int]]) -> Tuple[Optional[str], bool]:
        """Parcours des bits jusqu’à une feuille.
        - Si feuille == '#': (None, True) → lire UTF-8 brut ensuite et mise_a_jour
        - Sinon: (char, False) → mise_a_jour
        """
        n = self.racine
        while not n.est_feuille():
            b = lire_bit()
            if b is None:
                raise EOFError("Flux de bits terminé pendant le décodage.")
            if b == 0:
                if n.fg is None:
                    raise ValueError("Arbre invalide (fils gauche manquant).")
                n = n.fg
            else:
                if n.fd is None:
                    raise ValueError("Arbre invalide (fils droit manquant).")
                n = n.fd

        if n.caractere == "#":
            return (None, True)
        else:
            return (n.caractere, False)

    def encoder_symbole(self, caractere: str) -> Tuple[bool, str]:
        """Raccourci: (is_new, code) du symbole courant."""
        return self.code_pour(caractere)
