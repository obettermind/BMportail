"""Textes de communication de la démonstration : relance d'une pièce manquante,
phrase pour un message vocal, lien WhatsApp.

Aucun envoi ici : ce module ne fait que fabriquer du texte.
"""
from urllib.parse import quote


def _minuscule(texte):
    return texte[:1].lower() + texte[1:]


def enumerer(libelles):
    """['A', 'B', 'C'] -> 'a, b et c' (première lettre passée en minuscule)."""
    libelles = [_minuscule(x) for x in libelles]
    if len(libelles) <= 1:
        return "".join(libelles)
    return ", ".join(libelles[:-1]) + " et " + libelles[-1]


def decouper_sujet(sujet):
    """'Courtois Marie — Crédit immobilier' -> ('Courtois Marie', 'Crédit immobilier')."""
    if " — " in sujet:
        nom, objet = sujet.split(" — ", 1)
        return nom, objet
    return sujet, ""


def message_relance(sujet, libelles_manquants, pourcentage, demo=True):
    """Message courtois à envoyer au client / patient pour les pièces manquantes."""
    _, objet = decouper_sujet(sujet)
    lignes = [
        "Bonjour,",
        "",
        f"Votre dossier « {objet} » est complet à {pourcentage} %." if objet
        else f"Votre dossier est complet à {pourcentage} %.",
        "Pour avancer sans attendre, il nous manque encore :",
    ]
    lignes += [f"- {x}" for x in libelles_manquants]
    lignes += [
        "",
        "Dès réception, nous le validons aussitôt. Merci d’avance !",
        "",
        "Cordialement,",
    ]
    if demo:
        lignes += ["", "(Message de démonstration)"]
    return "\n".join(lignes)


def phrase_vocale(libelles_manquants, pourcentage):
    """Quelques mots à enregistrer en message vocal (WhatsApp), sans avoir à appeler."""
    n = len(libelles_manquants)
    if n == 0:
        return "Bonjour, votre dossier est complet. Il n’y a rien d’autre à fournir."
    mot = "une pièce" if n == 1 else f"{n} pièces"
    return (
        f"Bonjour, votre dossier est complet à {pourcentage} %. "
        f"Il manque {mot} : {enumerer(libelles_manquants)}. "
        "Dès réception, c’est validé. Merci !"
    )


def lien_whatsapp(texte):
    """Ouvre WhatsApp avec le message déjà rédigé (l'utilisateur choisit le contact
    et appuie lui-même sur « envoyer »)."""
    return "https://wa.me/?text=" + quote(texte)
