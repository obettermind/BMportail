import os
from donnees import synchroniser_base_suivi


def decouper_nom_fichier(nom):
    """
    Convention : idDossier_codeObjectif_piece.pdf
    Exemple    : 100_A_AA_cnie.pdf  ->  ("100", "A_AA", "cnie")
    Le code objectif peut contenir un « _ » (A_AA, B_MA, C_UE), donc on découpe
    au premier « _ » pour l'id dossier et au dernier « _ » pour la pièce.
    """
    if "_" not in nom:
        return None
    id_dossier, reste = nom.split("_", 1)
    if "_" not in reste:
        return None
    id_objectif, id_tache = reste.rsplit("_", 1)
    if not id_dossier or not id_objectif or not id_tache:
        return None
    return id_dossier, id_objectif.upper(), id_tache.lower()


def appliquer_pieces_presentes(suivi_dossiers, pieces_presentes):
    """Recalcule l'état de chaque pièce à partir d'un ensemble de pièces présentes.

    pieces_presentes : ensemble de tuples (id_dossier, id_objectif, piece).
    Une pièce est validée si et seulement si son tuple figure dans cet ensemble.
    Une pièce absente de l'ensemble repasse donc à « manquante ».

    Cette fonction ne touche à aucun fichier : elle sert à la fois à l'audit d'un
    dossier surveillé (executer_audit) et à la démonstration web, sans fichiers.
    """
    for id_dossier, infos in suivi_dossiers.items():
        for id_objectif, objectif in infos["objectifs_actifs"].items():
            for piece in objectif:
                objectif[piece] = (id_dossier, id_objectif, piece) in pieces_presentes


def executer_audit(dossier_surveille, suivi_dossiers, referentiel_objectifs):
    """Analyse les fichiers PDF présents dans le dossier pour valider les conditions"""
    if not dossier_surveille or not os.path.exists(dossier_surveille):
        return

    # Prépare la liste des pièces attendues de chaque patient (sans effacer les états)
    synchroniser_base_suivi(suivi_dossiers, referentiel_objectifs)

    try:
        fichiers = os.listdir(dossier_surveille)
    except Exception:
        return

    # 1) On repère d'abord toutes les pièces présentes dans le dossier
    pieces_presentes = set()
    for fichier in fichiers:
        if not fichier.lower().endswith('.pdf'):
            continue

        nom_sans_extension = fichier
        while nom_sans_extension.lower().endswith('.pdf'):
            nom_sans_extension = nom_sans_extension[:-4]

        decoupe = decouper_nom_fichier(nom_sans_extension)
        if decoupe is not None:
            pieces_presentes.add(decoupe)

    # 2) Puis on recalcule l'état de chaque pièce en une seule passe :
    #    une pièce est validée si et seulement si son fichier est présent.
    #    Un fichier supprimé ou renommé fait donc repasser la pièce à « manquante ».
    appliquer_pieces_presentes(suivi_dossiers, pieces_presentes)
