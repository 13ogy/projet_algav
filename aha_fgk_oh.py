from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Tuple, Callable, List


@dataclass(eq=False)
class Node:
    """
    Noeud d’un arbre de Huffman adaptatif (FGK/Vitter).

    - symbol:
        None  -> noeud interne
        "#"   -> feuille spéciale NYT (Not Yet Transmitted)
        "a", "b", ... -> feuille pour un caractère déjà vu
    - weight: poids (fréquence cumulée) du noeud
    - parent, left, right: liens structuraux dans l’arbre
    - num: numéro hiérarchique (plus grand => plus “tard” dans l’ordre global FGK)
    - prev_in_w, next_in_w: chainage double dans le bloc de noeuds de même poids
    """
    symbol: Optional[str]
    weight: int
    parent: Optional["Node"] = None
    left: Optional["Node"] = None
    right: Optional["Node"] = None
    num: int = 0
    prev_in_w: Optional["Node"] = None
    next_in_w: Optional["Node"] = None

    def is_leaf(self) -> bool:
        """True si feuille (pas d’enfants)."""
        return self.left is None and self.right is None


class AHA:
    """
    Huffman adaptatif (FGK/Vitter) avec une mise à jour “slide-and-increment”.

    Principes et invariants clés:
    - On maintient des blocs par poids (weight -> (head, tail)) via une liste doublement chaînée.
    - tail(weight) doit pointer vers le noeud de poids “weight” qui a le num maximal (leader du bloc).
    - A chaque symbole traité, pour chaque noeud “n” du chemin jusqu’à la racine:
        1) Slide: on cherche un leader dans le bloc de même poids en partant de tail et en remontant prev_in_w,
           tel que le leader ne soit ni le noeud courant n, ni un ancêtre de n, ni un descendant de n.
           Si trouvé, on procède à un échange STRUCTUREL (réécritures parent/enfants) + échange des num.
           On corrige tail(weight) si besoin (si les deux étaient dans le même bloc).
        2) Increment: on retire n du bloc weight, on passe n.weight à weight+1, on insère n dans le bloc weight+1,
           et on corrige tail(weight+1) si le num de n devient le plus grand.
    - Insertion d’un nouveau symbole:
        * On remplace la feuille NYT par un noeud interne dont left=NYT et right=nouvelle feuille.
        * On attribue deux num (en fin d’ordre), puis on met à jour d’abord depuis la nouvelle feuille,
          puis depuis l’interne, pour stabiliser la structure.
    """

    def __init__(self, debug: bool = False, log_every: int = 0):
        # Arbre initial : racine = NYT (“#”) de poids 0
        self.root = Node(symbol="#", weight=0)
        self.root.num = 1
        self.nyt = self.root

        # Index pratique pour retrouver les feuilles et par numéro hiérarchique
        self.leaves: Dict[str, Node] = {"#": self.nyt}   # symbole -> feuille
        self.by_num: Dict[int, Node] = {1: self.root}    # num -> noeud
        self.max_num = 1

        # Blocs de poids: weight -> (head, tail)
        self.blocks: Dict[int, Tuple[Optional[Node], Optional[Node]]] = {}
        self._block_insert(self.root)  # NYT appartient au bloc weight=0

        # Debug (optionnel)
        self.debug = debug
        self.log_every = log_every
        self.update_count = 0
        self.swap_count = 0

    # -------------------------------------------------------------------------
    # Outils pour blocs par poids (chaînage double) — O(1)
    # -------------------------------------------------------------------------

    def _block_head_tail(self, weight_value: int) -> Tuple[Optional[Node], Optional[Node]]:
        """Renvoie (head, tail) pour le bloc de poids weight_value."""
        return self.blocks.get(weight_value, (None, None))

    def _block_set(self, weight_value: int, head: Optional[Node], tail: Optional[Node]):
        """Met à jour la table des blocs (ajoute ou supprime si vide)."""
        if head is None and tail is None:
            if weight_value in self.blocks:
                del self.blocks[weight_value]
        else:
            self.blocks[weight_value] = (head, tail)

    def _block_insert(self, node: Node):
        """Insère node en queue (tail) du bloc node.weight."""
        w = node.weight
        head, tail = self._block_head_tail(w)
        node.prev_in_w = tail
        node.next_in_w = None
        if tail is not None:
            tail.next_in_w = node
        tail = node
        if head is None:
            head = node
        self._block_set(w, head, tail)

    def _block_remove(self, node: Node):
        """Retire node de son bloc de poids actuel."""
        w = node.weight
        head, tail = self._block_head_tail(w)
        prevn, nextn = node.prev_in_w, node.next_in_w
        if prevn is not None:
            prevn.next_in_w = nextn
        if nextn is not None:
            nextn.prev_in_w = prevn
        if head is node:
            head = nextn
        if tail is node:
            tail = prevn
        node.prev_in_w = node.next_in_w = None
        self._block_set(w, head, tail)

    def _tail(self, w: int) -> Optional[Node]:
        """Renvoie tail(w), c.-à-d. le leader du bloc weight=w."""
        return self._block_head_tail(w)[1]

    # -------------------------------------------------------------------------
    # Numérotation hiérarchique et relation d’ascendance
    # -------------------------------------------------------------------------

    def _swap_in_by_num(self, a: Node, b: Node):
        """Echange en O(1) les num d’a et b, en maintenant by_num."""
        self.by_num[a.num], self.by_num[b.num] = b, a
        a.num, b.num = b.num, a.num

    def _is_ancestor(self, ancestor_candidate: Node, node: Node) -> bool:
        """True si ancestor_candidate est un ancêtre de node (par remontée parent -> racine)."""
        cur = node.parent
        while cur is not None:
            if cur is ancestor_candidate:
                return True
            cur = cur.parent
        return False

    # -------------------------------------------------------------------------
    # Sélection d’un leader non ancêtre/descendant dans le bloc
    # -------------------------------------------------------------------------

    def _find_leader_for(self, node: Node) -> Optional[Node]:
        """
        Remonte depuis tail(weight(node)) jusqu’à trouver un leader qui:
          - n’est pas node lui-même,
          - n’est pas un ancêtre de node,
          - n’est pas un descendant de node.
        Cette restriction (ni ancêtre ni descendant) évite les cycles et garantit
        un vrai rééquilibrage structurel par un swap “sécurisé”.
        """
        w = node.weight
        cur = self._tail(w)
        while cur is not None:
            if cur is not node and not self._is_ancestor(cur, node) and not self._is_ancestor(node, cur):
                return cur
            cur = cur.prev_in_w
        return None

    # -------------------------------------------------------------------------
    # Echange STRUCTUREL de deux noeuds (réécriture parent/enfants) + échange num
    # -------------------------------------------------------------------------

    def _swap_structure(self, a: Node, b: Node):
        """
        Echange STRUCTUREL des positions de a et b (parents/enfants), puis echange des num.
        A n’appeler que si a et b ne sont ni ancêtre ni descendant l’un de l’autre.
        Corrige tail(w) si a et b ont le même poids.
        """
        if a is b:
            return
        pa, pb = a.parent, b.parent
        if pa is None or pb is None:
            return  # ne pas échanger la racine

        # Remplacer a par b dans pa
        if pa.left is a:
            pa.left = b
        else:
            pa.right = b
        b.parent = pa

        # Remplacer b par a dans pb
        if pb.left is b:
            pb.left = a
        else:
            pb.right = a
        a.parent = pb

        # Echanger les num
        self._swap_in_by_num(a, b)

        # Corriger tail(w) si a et b sont dans le même bloc
        if a.weight == b.weight:
            w = a.weight
            head, tail = self._block_head_tail(w)
            new_tail = tail
            for cand in (a, b):
                if cand.weight == w and (new_tail is None or cand.num > new_tail.num):
                    new_tail = cand
            if new_tail is not tail:
                self._block_set(w, head, new_tail)

        self.swap_count += 1

    # -------------------------------------------------------------------------
    # Etape locale “slide-and-increment” pour un noeud n
    # -------------------------------------------------------------------------

    def _slide_and_increment(self, node: Node):
        """
        1) Slide: trouver un leader non ancêtre/descendant dans le bloc node.weight et échanger structurellement.
        2) Increment: retirer node du bloc w, passer node.weight à w+1, insérer dans bloc w+1, et corriger tail(w+1).
        """
        w = node.weight
        leader = self._find_leader_for(node)
        if leader is not None:
            self._swap_structure(node, leader)

        # Increment
        self._block_remove(node)
        node.weight = w + 1
        self._block_insert(node)

        # tail(w+1) doit pointer vers le noeud au num maximal
        head2, tail2 = self._block_head_tail(node.weight)
        if tail2 is None or node.num > tail2.num:
            self._block_set(node.weight, head2, node)

    def _update(self, start: Node):
        """
        Met à jour en remontant depuis start jusqu’à la racine, en appliquant _slide_and_increment.
        """
        steps = 0
        n = start
        while n is not None:
            self._slide_and_increment(n)
            n = n.parent
            steps += 1
            if steps > 200000:
                raise RuntimeError("Boucle suspecte dans _update (trop d’étapes).")
        self.update_count += 1
        if self.debug and self.log_every > 0 and (self.update_count % self.log_every == 0):
            print(f"[AHA FGK OH] updates={self.update_count} swaps={self.swap_count}")

    # -------------------------------------------------------------------------
    # Insertion d’un nouveau symbole ch (NYT -> interne + feuille)
    # -------------------------------------------------------------------------

    def _insert_new_symbol(self, ch: str) -> Node:
        """
        Remplace la feuille NYT par un noeud interne:
           internal.left  = NYT
           internal.right = new_leaf(ch)
        Assigne deux nouveaux num (new_leaf puis internal), insère les deux dans le bloc 0,
        fixe tail(0) sur l’interne (num maximal).
        """
        internal = Node(symbol=None, weight=0, parent=self.nyt.parent)
        new_leaf = Node(symbol=ch, weight=0, parent=internal)

        # Rebrancher l’arbre
        if self.nyt.parent is None:
            self.root = internal
        else:
            if self.nyt.parent.left is self.nyt:
                self.nyt.parent.left = internal
            else:
                self.nyt.parent.right = internal

        internal.left = self.nyt
        internal.right = new_leaf
        self.nyt.parent = internal

        # Numérotation hiérarchique (en fin d’ordre)
        self.max_num += 1
        new_leaf.num = self.max_num
        self.by_num[new_leaf.num] = new_leaf

        self.max_num += 1
        internal.num = self.max_num
        self.by_num[internal.num] = internal

        # Index et blocs
        self.leaves[ch] = new_leaf
        self.leaves["#"] = self.nyt

        self._block_insert(new_leaf)   # poids 0
        self._block_insert(internal)   # poids 0

        # tail(0) = internal (num maximal)
        head0, _ = self._block_head_tail(0)
        self._block_set(0, head0, internal)

        return internal

    # -------------------------------------------------------------------------
    # API publique: encodage/décodage logique
    # -------------------------------------------------------------------------

    def code_for(self, ch: str) -> Tuple[bool, str]:
        """
        Renvoie (is_new, code_binaire) pour le caractère ch:
        - is_new = True -> renvoyer le code de NYT (chemin de la racine à NYT),
        - is_new = False -> renvoyer le code de la feuille de ch.
        """
        if ch in self.leaves and ch != "#":
            target = self.leaves[ch]
            is_new = False
        else:
            target = self.nyt
            is_new = True

        bits: List[str] = []
        cur = target
        while cur.parent is not None:
            bits.append('0' if cur.parent.left is cur else '1')
            cur = cur.parent
        bits.reverse()
        return is_new, ''.join(bits)

    def update_with(self, ch: str):
        """
        Mise à jour adaptative (après avoir “émis” les bits correspondants):
        - Si ch est un nouveau symbole: insertion NYT->(interne+feuille),
          puis mise à jour d’abord depuis la nouvelle feuille, puis depuis l’interne.
        - Sinon: mise à jour depuis la feuille de ch.
        """
        if ch not in self.leaves:
            internal = self._insert_new_symbol(ch)
            new_leaf = self.leaves[ch]
            # Double passage pour stabiliser la forme au début.
            self._update(new_leaf)
            self._update(internal)
        else:
            self._update(self.leaves[ch])

    def decode_one(self, read_bit: Callable[[], Optional[int]]) -> Tuple[Optional[str], bool]:
        """
        Descend l’arbre en lisant des bits (0 = gauche, 1 = droite) jusqu’à une feuille.
        - Si la feuille est NYT: (None, True) -> l’appelant doit lire le caractère UTF-8 brut
          et appeler update_with(ch).
        - Sinon: (symbole, False).
        """
        n = self.root
        while not n.is_leaf():
            b = read_bit()
            if b is None:
                raise EOFError("Fin de flux inattendue.")
            n = n.left if b == 0 else n.right
        if n.symbol == "#":
            return None, True
        return n.symbol, False

    # Aliases compatibles avec vos scripts
    def encoder_symbole(self, ch: str) -> Tuple[bool, str]:
        return self.code_for(ch)

    def mise_a_jour(self, ch: str) -> None:
        self.update_with(ch)
