"""Données et logique de la démonstration publique (portail).

Principe : tout reste EN MÉMOIRE, propre à chaque visiteur.
  - aucun fichier n'est lu ni écrit ;
  - on n'appelle JAMAIS charger_referentiel() / charger_patients() de donnees.py
    (ces fonctions écrivent des JSON sur le disque, partagés entre tous les visiteurs) ;
  - on n'utilise de donnees.py que synchroniser_base_suivi(), qui ne touche pas au disque.

Dossiers et personnes : fictifs.
"""
import copy
import random

from donnees import synchroniser_base_suivi
from moteur_audit import appliquer_pieces_presentes

# ---------------------------------------------------------------------------
# Les deux protocoles de la démonstration (même structure que le référentiel)
# ---------------------------------------------------------------------------
REFERENTIEL_DEMO = {
    "IMMO": {
        "nom_objective": "Crédit immobilier",
        "conditions": [
            "cnie", "bulletins", "attestationtravail", "attestationsalaire", "releves",
            "promesse", "titrepropriete", "assuranceemprunteur", "justifdomicile", "simulation",
        ],
    },
    "CLIN": {
        "nom_objective": "Sortie de patient",
        "conditions": [
            "cnie", "priseencharge", "crhospit", "ordonnancesortie",
            "bonsortie", "facturefinale", "quitusfacturation", "consignessuivi",
        ],
    },
}

# Libellés lisibles affichés au visiteur (le numéro 1..N vient de l'ordre ci-dessus)
LIBELLES = {
    "IMMO": {
        "cnie": "Pièce d’identité",
        "bulletins": "3 derniers bulletins de salaire",
        "attestationtravail": "Attestation de travail",
        "attestationsalaire": "Attestation de salaire",
        "releves": "Relevés bancaires (3 mois)",
        "promesse": "Promesse de vente",
        "titrepropriete": "Titre de propriété du bien",
        "assuranceemprunteur": "Assurance emprunteur",
        "justifdomicile": "Justificatif de domicile",
        "simulation": "Simulation de financement signée",
    },
    "CLIN": {
        "cnie": "Pièce d’identité",
        "priseencharge": "Prise en charge / couverture",
        "crhospit": "Compte rendu d’hospitalisation",
        "ordonnancesortie": "Ordonnance de sortie",
        "bonsortie": "Bon de sortie signé par le médecin",
        "facturefinale": "Facture finale",
        "quitusfacturation": "Quitus de la facturation",
        "consignessuivi": "Consignes de suivi",
    },
}

# Les ids ne doivent pas contenir « _ » (voir decouper_nom_fichier).
# « contact » : mail du client / patient, vide au départ ; le visiteur peut y mettre
# le sien pour essayer la relance. Il ne vit que dans la session du visiteur.
DOSSIERS_DEMO = {
    "4402": {
        "sujet": "Courtois Marie — Crédit immobilier",
        "contact": "",
        "objectifs_actifs": {"IMMO": {}},
    },
    "9941": {
        "sujet": "Dupont Jean — Sortie de patient",
        "contact": "",
        "objectifs_actifs": {"CLIN": {}},
    },
}

# Part minimale de pièces présentes au départ (jamais un dossier vide)
PART_MINI_PRESENTES = 0.3


def nouvelle_session(graine=None):
    """Crée un jeu de démonstration neuf, avec un état de départ aléatoire.

    Pour chaque dossier : au moins 30 % des pièces présentes (arrondi, minimum 1)
    et toujours AU MOINS UNE pièce manquante, pour que la relance ait un sens.
    À chaque ouverture de la page, la barre de progression est donc différente.

    Renvoie (suivi, presentes) :
      suivi     : état de chaque pièce par dossier (comme suivi_dossiers de l'app bureau)
      presentes : ensemble de tuples (id_dossier, id_objectif, piece)
    """
    rng = random.Random(graine)  # graine=None -> tirage différent à chaque appel
    suivi = copy.deepcopy(DOSSIERS_DEMO)
    synchroniser_base_suivi(suivi, REFERENTIEL_DEMO)

    presentes = set()
    for id_dos, infos in suivi.items():
        for code_obj, pieces in infos["objectifs_actifs"].items():
            codes = list(pieces.keys())
            n = len(codes)
            mini = max(1, round(n * PART_MINI_PRESENTES))
            maxi = n - 1
            nb = rng.randint(mini, maxi)
            for piece in rng.sample(codes, nb):
                presentes.add((id_dos, code_obj, piece))

    appliquer_pieces_presentes(suivi, presentes)
    return suivi, presentes


def deposer_piece(suivi, presentes, id_dos, code_obj, piece):
    """Simule le dépôt d'une pièce (aucun contenu de fichier : seul l'identifiant compte)."""
    presentes.add((id_dos, code_obj, piece))
    appliquer_pieces_presentes(suivi, presentes)


def resume_dossier(suivi, id_dos, code_obj):
    """Tout ce dont l'écran « fiche dossier » a besoin."""
    pieces = suivi[id_dos]["objectifs_actifs"][code_obj]
    libelles = LIBELLES[code_obj]
    detail = [
        {"numero": i, "code": code, "libelle": libelles[code], "ok": ok}
        for i, (code, ok) in enumerate(pieces.items(), start=1)
    ]
    validees = [p for p in detail if p["ok"]]
    manquantes = [p for p in detail if not p["ok"]]
    total = len(detail)
    return {
        "total": total,
        "pieces": detail,
        "validees": validees,
        "manquantes": manquantes,
        "pourcentage": round(100 * len(validees) / total),
        "complet": not manquantes,
    }


def rechercher(suivi, saisie):
    """Écran « Retrouver » : quelques chiffres du numéro, ou une partie du nom."""
    saisie = saisie.strip().lower()
    if not saisie:
        return []
    return [
        id_dos for id_dos, infos in suivi.items()
        if saisie in id_dos.lower() or saisie in infos["sujet"].lower()
    ]
