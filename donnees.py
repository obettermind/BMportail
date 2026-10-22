import os
import json
import time

# Les fichiers JSON sont toujours cherchés à côté de ce script,
# quel que soit le dossier depuis lequel le programme est lancé.
DOSSIER_PROJET = os.path.dirname(os.path.abspath(__file__))
PATH_REFERENTIEL = os.path.join(DOSSIER_PROJET, "referentiel.json")
PATH_PATIENTS = os.path.join(DOSSIER_PROJET, "patients.json")

REFERENTIEL_PAR_DEFAUT = {
    "A_AA": {
        "nom_objective": "Cas A: Adulte assuré (Chirurgie programmée)",
        "conditions": ["cnie", "carteamo", "accordpc", "consentement", "consultationanesthesie",
                       "bilanpreop", "checklistbloc", "croperatoire", "ordonnancesortie", "facturesoldee"]
    },
    "B_MA": {
        "nom_objective": "Cas B: Mineur (Chirurgie ambulatoire)",
        "conditions": ["livretfamille", "cnieparent", "autorisationparentale", "consentement",
                       "consultationanesthesie", "feuillesurveillance", "consignesparent", "ordonnancesortie"]
    },
    "C_UE": {
        "nom_objective": "Cas C: Urgence (Patient étranger sans assurance)",
        "conditions": ["ficheurgence", "passeport", "assurancevoyage", "acompte", "consentementurgence",
                       "bilanimagerie", "croperatoirehospit", "facturesoldee"]
    }
}

PATIENTS_PAR_DEFAUT = {
    "100": {"sujet": "Hassan B. (52 ans - Cholécystectomie)", "objectifs_actifs": {"A_AA": {}}},
    "200": {"sujet": "Yassine (8 ans - Amygdalectomie)", "objectifs_actifs": {"B_MA": {}}},
    "300": {"sujet": "Marc T. (45 ans - Appendicite aiguë)", "objectifs_actifs": {"C_UE": {}}}
}


def _ecrire_json(chemin, data):
    """Écriture sécurisée : on écrit dans un fichier temporaire puis on remplace l'original.
    Si le programme s'arrête en pleine écriture, l'ancien fichier reste intact."""
    temporaire = chemin + ".tmp"
    with open(temporaire, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    os.replace(temporaire, chemin)


def _lire_json(chemin):
    """Lit un JSON. S'il est illisible, il est mis de côté (jamais écrasé) et None est renvoyé."""
    if not os.path.exists(chemin):
        return None
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        copie = f"{chemin}.corrompu_{time.strftime('%Y%m%d_%H%M%S')}"
        try:
            os.replace(chemin, copie)
            print(f"Fichier illisible mis de côté : {copie}")
        except Exception as e:
            print(f"Impossible de mettre de côté {chemin} : {e}")
        return None


def sauvegarder_referentiel(data):
    try:
        _ecrire_json(PATH_REFERENTIEL, data)
    except Exception as e:
        print(f"Erreur sauvegarde référentiel : {e}")


def sauvegarder_patients(data):
    try:
        _ecrire_json(PATH_PATIENTS, data)
    except Exception as e:
        print(f"Erreur sauvegarde patients : {e}")


def charger_referentiel():
    data = _lire_json(PATH_REFERENTIEL)
    if data is not None:
        return data
    data = json.loads(json.dumps(REFERENTIEL_PAR_DEFAUT))
    sauvegarder_referentiel(data)
    return data


def charger_patients():
    data = _lire_json(PATH_PATIENTS)
    if data is not None:
        return data
    data = json.loads(json.dumps(PATIENTS_PAR_DEFAUT))
    sauvegarder_patients(data)
    return data


def synchroniser_base_suivi(suivi_dossiers, referentiel):
    """Prépare, pour chaque patient, la liste des pièces attendues selon son protocole."""
    for id_dos, infos in suivi_dossiers.items():
        for code_obj in list(infos["objectifs_actifs"].keys()):
            if code_obj in referentiel:
                pieces_attendues = referentiel[code_obj]["conditions"]
                ancien_etat = infos["objectifs_actifs"][code_obj]
                infos["objectifs_actifs"][code_obj] = {p: ancien_etat.get(p, False) for p in pieces_attendues}