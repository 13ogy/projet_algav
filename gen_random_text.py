from __future__ import annotations
import argparse
import random
from collections import Counter
from typing import List

"""
Fonctions pour générer des textes aléatoires avec des distributions 
de probabilité contrôlées (Uniforme, Zipf, Pondérée) pour les tests (Q9).
"""

def normalize(weights: List[float]) -> List[float]:
    """
    Normalise une liste de poids bruts pour obtenir une distribution de probabilité valide
    """
    s = sum(weights)
    if s <= 0:
        raise ValueError("La somme des poids doit être > 0")
    return [w / s for w in weights]

def categorical(choices: List[str], probs: List[float]) -> str:
    """
    Tirage catégoriel. Sélectionne un caractère selon la distribution 'probs'.
    """
    r = random.random()
    acc = 0.0 # Accumulateur de probabilité

    # Parcours des probabilités cumulées
    for ch, p in zip(choices, probs):
        acc += p
        if r <= acc:
            return ch

    return choices[-1]

def build_zipf_probs(k: int, s: float) -> List[float]:
    """
    Construit une distribution de type Zipf (loi de puissance).
    La probabilité est inversement proportionnelle au rang à la puissance 's'.
    """
    # Calcule les poids bruts (1/rang^s)
    raw = [1.0 / (i ** s) for i in range(1, k + 1)]

    # Normalise les poids pour obtenir des probabilités
    return normalize(raw)

def write_stats_csv(path: str, text: str) -> None:
    """
    Calcule et écrit les statistiques de fréquence
    des caractères observés dans le texte généré vers un fichier CSV.
    """
    counts = Counter(text)
    n = len(text)
    lines = ["char,count,rel_freq"]

    # Trie par fréquence décroissante
    for ch, c in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        rf = c / n if n > 0 else 0.0
        printable = ch.replace("\n", "\\n")
        lines.append(f"{printable},{c},{rf:.6f}")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def generate_text_by_mode(mode: str, N: int, alphabet: List[str], weights: List[float] = None, zipf_s: float = 1.0) -> str:
    """
    Fonction qui génère le texte selon le mode spécifié.
    Utilise categorical() pour la génération des caractères
    """
    k = len(alphabet)

    if mode == "uniform":
        # Tous les caractères ont une probabilité égale
        probs = [1.0 / k] * k
        text = "".join(categorical(alphabet, probs) for _ in range(N))

    elif mode == "weighted":
        # Utilise des poids fournis manuellement pour créer une asymétrie
        if weights is None or len(weights) != k:
            raise ValueError("Poids invalides ou manquants pour le mode pondéré.")
        probs = normalize(weights)
        text = "".join(categorical(alphabet, probs) for _ in range(N))

    elif mode == "zipf":
        # Distribution de type loi de puissance
        probs = build_zipf_probs(k, zipf_s)
        text = "".join(categorical(alphabet, probs) for _ in range(N))

    else:
        raise ValueError(f"Mode de génération inconnu ou non pris en charge: {mode}.")

    return text


# ------ Logique du main ----------
def main():
    parser = argparse.ArgumentParser(description="Générateur de texte aléatoire (UTF-8) à distribution contrôlée (Q9).")

    # Arguments nécessaires
    parser.add_argument("--output", "-o", required=True, help="Fichier texte de sortie (UTF-8)")
    parser.add_argument("--N", type=int, required=True, help="Nombre de caractères à générer")
    parser.add_argument("--alphabet", type=str, default="abcdefghijklmnopqrstuvwxyz ",
                        help="Alphabet à utiliser (chaîne UTF-8). Par défaut: lettres minuscules a-z + espace")
    parser.add_argument("--mode", choices=["uniform", "weighted", "zipf"], required=True,
                        help="Type de distribution")

    # Arguments optionnels pour la configuration
    parser.add_argument("--seed", type=int, default=42, help="Graine RNG pour reproductibilité (supprimé dans la version concise, restauré ici pour le parsing)")
    parser.add_argument("--stats", type=str, default="", help="Fichier CSV pour enregistrer les fréquences observées")
    parser.add_argument("--weights", type=str, default="",
                        help="[MODE weighted] Liste de poids séparés par des virgules (Longueur = |alphabet|)")
    parser.add_argument("--zipf_s", type=float, default=1.0,
                        help="[MODE zipf] Paramètre s de Zipf (s>0).")

    args = parser.parse_args()

    # Restauration de la graine aléatoire pour la reproductibilité
    random.seed(args.seed)

    alphabet = list(args.alphabet)
    k = len(alphabet)
    N = args.N
    text = ""

    # -------------------------------------------------------------------------
    # Logique de génération selon le mode
    # -------------------------------------------------------------------------
    if args.mode == "uniform":
        probs = [1.0 / k] * k
        text = "".join(categorical(alphabet, probs) for _ in range(N))

    elif args.mode == "weighted":
        if not args.weights:
            raise ValueError("--weights requis en mode weighted")
        try:
            w = [float(x) for x in args.weights.split(",")]
        except Exception as e:
            raise ValueError("--weights doit être une liste de nombres séparés par des virgules") from e

        if len(w) != k:
            raise ValueError("len(weights) doit être égal à |alphabet|")

        probs = normalize(w)
        text = "".join(categorical(alphabet, probs) for _ in range(N))

    elif args.mode == "zipf":
        if args.zipf_s <= 0:
            raise ValueError("--zipf_s doit être > 0")

        probs = build_zipf_probs(k, args.zipf_s)
        text = "".join(categorical(alphabet, probs) for _ in range(N))

    # -------------------------------------------------------------------------
    # Sortie
    # -------------------------------------------------------------------------
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(text)

    if args.stats:
        write_stats_csv(args.stats, text)
        print(f"Statistiques écrites dans {args.stats}")

    print(f"Texte généré dans {args.output} (N={N}, mode={args.mode})")

if __name__ == "__main__":
    main()
