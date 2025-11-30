#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import math
import random
from collections import Counter
from typing import List, Dict, Tuple, Optional

def normalize(weights: List[float]) -> List[float]:
    s = sum(weights)
    if s <= 0:
        raise ValueError("La somme des poids doit être > 0")
    return [w / s for w in weights]

def categorical(choices: List[str], probs: List[float]) -> str:
    # tirage discret selon probs (déjà normalisées)
    r = random.random()
    acc = 0.0
    for ch, p in zip(choices, probs):
        acc += p
        if r <= acc:
            return ch
    return choices[-1]

def build_zipf_probs(k: int, s: float) -> List[float]:
    # Proba ∝ 1/(rank^s), rank = 1..k
    raw = [1.0 / (i ** s) for i in range(1, k + 1)]
    return normalize(raw)

def sample_bigram(
        N: int,
        alphabet: List[str],
        init_probs: List[float],
        trans: Dict[str, List[float]],
) -> str:
    # génération Markov 1-ordre: P(X_0), P(X_t | X_{t-1})
    out = []
    cur = categorical(alphabet, init_probs)
    out.append(cur)
    for _ in range(N - 1):
        next_probs = trans[cur]
        nxt = categorical(alphabet, next_probs)
        out.append(nxt)
        cur = nxt
    return "".join(out)

def write_stats_csv(path: str, text: str) -> None:
    counts = Counter(text)
    n = len(text)
    lines = ["char,count,rel_freq"]
    for ch, c in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        rf = c / n if n > 0 else 0.0
        printable = ch.replace("\n", "\\n")
        lines.append(f"{printable},{c},{rf:.6f}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main():
    parser = argparse.ArgumentParser(description="Générateur de texte aléatoire (UTF-8) à distribution contrôlée (Q9).")
    parser.add_argument("--output", "-o", required=True, help="Fichier texte de sortie (UTF-8)")
    parser.add_argument("--N", type=int, required=True, help="Nombre de caractères à générer")
    parser.add_argument("--alphabet", type=str, default="abcdefghijklmnopqrstuvwxyz",
                        help="Alphabet à utiliser (chaîne UTF-8). Par défaut: lettres minuscules a-z")
    parser.add_argument("--mode", choices=["uniform", "weighted", "zipf", "bigram"], required=True,
                        help="Type de distribution")
    parser.add_argument("--seed", type=int, default=42, help="Graine RNG pour reproductibilité")
    parser.add_argument("--stats", type=str, default="", help="Fichier CSV pour enregistrer les fréquences observées")
    # weighted
    parser.add_argument("--weights", type=str, default="",
                        help="Liste de poids séparés par des virgules (ex: 10,1,1,...). Longueur = |alphabet|")
    # zipf
    parser.add_argument("--zipf_s", type=float, default=1.0,
                        help="Paramètre s de Zipf (s>0); plus grand s => distribution plus concentrée")
    # bigram
    parser.add_argument("--bigram_init", type=str, default="",
                        help='Probas initiales, liste de poids séparés par virgules (longueur = |alphabet|)')
    parser.add_argument("--bigram_trans", type=str, default="",
                        help='JSON: dictionnaire état->liste de poids (longueur = |alphabet|), ex: {"a":[...],"b":[...],...}')

    args = parser.parse_args()
    random.seed(args.seed)

    alphabet = list(args.alphabet)
    k = len(alphabet)
    N = args.N

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
        # ordre naturel de l'alphabet = rang 1..k
        probs = build_zipf_probs(k, args.zipf_s)
        text = "".join(categorical(alphabet, probs) for _ in range(N))

    elif args.mode == "bigram":
        if not args.bigram_init or not args.bigram_trans:
            raise ValueError("--bigram_init et --bigram_trans requis en mode bigram")
        init_raw = [float(x) for x in args.bigram_init.split(",")]
        if len(init_raw) != k:
            raise ValueError("len(bigram_init) doit être égal à |alphabet|")
        init_probs = normalize(init_raw)
        trans_raw = json.loads(args.bigram_trans)
        # valider toutes les clés et longueurs
        trans: Dict[str, List[float]] = {}
        for ch in alphabet:
            if ch not in trans_raw:
                raise ValueError(f"Transition manquante pour état '{ch}'")
            row = [float(x) for x in trans_raw[ch]]
            if len(row) != k:
                raise ValueError(f"len(transition['{ch}']) doit être égal à |alphabet|")
            trans[ch] = normalize(row)
        text = sample_bigram(N, alphabet, init_probs, trans)

    else:
        raise ValueError("Mode inconnu")

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(text)

    if args.stats:
        write_stats_csv(args.stats, text)
        print(f"Statistiques écrites dans {args.stats}")

    print(f"Texte généré dans {args.output} (N={N}, mode={args.mode})")

if __name__ == "__main__":
    main()
