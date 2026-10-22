"""Portail — démonstration publique de l'outil d'audit (format téléphone).

Lancer :  streamlit run app.py

Tout l'état du visiteur vit dans st.session_state : il est propre à sa visite
et disparaît à la fermeture de la page. Rien n'est écrit sur le disque.
"""
from urllib.parse import quote

import streamlit as st

import demo_portail as dp
import messages_portail as mp

# Votre numéro WhatsApp au format international, sans + ni espaces (ex. "2126XXXXXXXX").
# Tant qu'il est vide, le bouton « Essayer avec vos propres dossiers » n'est pas affiché.
NUMERO_WHATSAPP = ""

# Lien placé dans le message de bilan (ici, la démonstration elle-même).
LIEN_SUIVI = "https://bmportail.streamlit.app/"

st.set_page_config(
    page_title="Mieux communiquer, mieux avancer",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    #MainMenu, footer {visibility: hidden;}
    header[data-testid="stHeader"] {display: none;}
    .block-container {max-width: 560px; padding-top: 1.5rem; padding-bottom: 3rem;}
    .scene {font-style: italic; opacity: .8; line-height: 1.55; margin: .5rem 0 1rem 0;}
    .stButton > button, .stLinkButton > a {min-height: 3rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# État de la visite
# ---------------------------------------------------------------------------
def init():
    if "suivi" not in st.session_state:
        suivi, presentes = dp.nouvelle_session()  # état de départ aléatoire
        st.session_state.suivi = suivi
        st.session_state.presentes = presentes
        st.session_state.ecran = "accueil"
        st.session_state.dossier = None


def aller(ecran, dossier=None):
    st.session_state.ecran = ecran
    if dossier is not None:
        st.session_state.dossier = dossier


def deposer(id_dos, code_obj, piece):
    dp.deposer_piece(st.session_state.suivi, st.session_state.presentes, id_dos, code_obj, piece)
    st.toast("Pièce déposée.")


def recommencer():
    st.session_state.clear()  # init() recrée un jeu neuf, avec un nouveau tirage


# ---------------------------------------------------------------------------
# Bilan PDF (généré en mémoire, jamais écrit sur le disque)
# ---------------------------------------------------------------------------
def _latin(texte):
    """fpdf2 (polices de base) n'accepte que le latin-1 : on adoucit le reste."""
    texte = (
        str(texte)
        .replace("’", "'")
        .replace("‘", "'")
        .replace("–", "-")
        .replace("—", "-")
        .replace("·", "-")
        .replace("…", "...")
    )
    return texte.encode("latin-1", "replace").decode("latin-1")


def bilan_pdf(infos, r):
    """Retourne les octets du PDF de bilan, ou None si fpdf2 n'est pas installé."""
    try:
        from fpdf import FPDF
    except ImportError:
        return None

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _latin("Bilan du dossier"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, _latin(infos["sujet"]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.cell(
        0,
        8,
        _latin(f"{len(r['validees'])} pièces sur {r['total']} - {r['pourcentage']} %"),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, _latin("Pièces reçues"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    recues = [p for p in r["pieces"] if p["ok"]]
    if recues:
        for p in recues:
            pdf.cell(0, 7, _latin(f"- {p['numero']}. {p['libelle']}"), new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 7, _latin("Aucune pièce reçue pour l'instant."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, _latin("Pièces manquantes"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    if r["manquantes"]:
        for p in r["manquantes"]:
            pdf.cell(0, 7, _latin(f"- {p['numero']}. {p['libelle']}"), new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 7, _latin("Dossier complet. Rien ne manque."), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 6, _latin("Démonstration : dossier fictif, aucune donnée réelle."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# Écran 1 — Accueil
# ---------------------------------------------------------------------------
def ecran_accueil():
    st.title("Mieux communiquer, mieux avancer.")
    st.write(
        "Des outils simples, faits pour votre travail, par des gens qui parlent "
        "le langage des innovations les plus modernes, pour vous aider à y accéder aisément."
    )
    st.markdown("*Le vrai luxe, c’est un travail sans accroc.*")
    st.button("Essayer", type="primary", use_container_width=True, on_click=aller, args=("retrouver",))
    st.caption(
        "Démonstration : dossiers fictifs, rien n’est conservé. "
        "Chaque ouverture présente une situation différente."
    )


# ---------------------------------------------------------------------------
# Écran 2 — Retrouver
# ---------------------------------------------------------------------------
def ecran_retrouver():
    st.markdown(
        "<p class='scene'>Un mardi, dix heures. Un client appelle pour un dossier ouvert "
        "il y a trois ans. Vous tapez deux chiffres, et le dossier est là. Le client "
        "n’a pas eu le temps de sentir l’attente.</p>",
        unsafe_allow_html=True,
    )
    saisie = st.text_input(
        "Numéro ou nom du dossier",
        key="saisie",
        placeholder="Tapez 2 chiffres, puis Entrée",
    )
    st.caption("Tapez deux chiffres, puis cliquez sur « Dossier de démonstration ».")
    st.caption("Dossiers de démonstration : 4402 et 9941.")

    suivi = st.session_state.suivi
    resultats = dp.rechercher(suivi, saisie)
    for id_dos in resultats:
        st.button(
            f"Dossier de démonstration {id_dos} · {suivi[id_dos]['sujet']}",
            key=f"ouvrir_{id_dos}",
            use_container_width=True,
            on_click=aller,
            args=("fiche", id_dos),
        )
    if saisie.strip() and not resultats:
        st.info("Aucun dossier ne correspond. Essayez 44 ou 99.")

    st.button("← Retour", key="retour_accueil", on_click=aller, args=("accueil",))


# ---------------------------------------------------------------------------
# Écrans 3 et 4 — Fiche dossier, dépôt d'une pièce, relance
# ---------------------------------------------------------------------------
def ecran_fiche():
    suivi = st.session_state.suivi
    id_dos = st.session_state.dossier
    if id_dos not in suivi:
        aller("retrouver")
        st.rerun()

    infos = suivi[id_dos]
    code_obj = next(iter(infos["objectifs_actifs"]))
    r = dp.resume_dossier(suivi, id_dos, code_obj)

    st.subheader(infos["sujet"])
    st.progress(
        r["pourcentage"] / 100,
        text=f"{len(r['validees'])} pièces sur {r['total']} · {r['pourcentage']} %",
    )

    # Pièces : validées en lignes simples, manquantes en boutons « Déposer »
    for p in r["pieces"]:
        if p["ok"]:
            st.markdown(f"✓ &nbsp; {p['numero']}. {p['libelle']}")
    if r["manquantes"]:
        st.markdown("**Il manque :**")
        for p in r["manquantes"]:
            st.button(
                f"Déposer — {p['numero']}. {p['libelle']}",
                key=f"dep_{id_dos}_{p['code']}",
                use_container_width=True,
                on_click=deposer,
                args=(id_dos, code_obj, p["code"]),
            )
    else:
        st.success("Dossier complet. Rien ne manque, rien à relancer.")

    libelles_manquants = [p["libelle"] for p in r["manquantes"]]

    # Relance en un clic + phrase pour un message vocal
    if r["manquantes"]:
        st.divider()
        st.markdown("**Relancer le client**")
        message = st.text_area(
            "Message prêt à envoyer",
            value=mp.message_relance(infos["sujet"], libelles_manquants, r["pourcentage"]),
            height=260,
            key=f"msg_{id_dos}_{len(libelles_manquants)}",  # se rafraîchit quand l'état change
        )
        st.link_button("Envoyer par WhatsApp", mp.lien_whatsapp(message), use_container_width=True)

        st.markdown("**À dire dans un message vocal**")
        st.info(mp.phrase_vocale(libelles_manquants, r["pourcentage"]))

    st.divider()
    st.button(
        "Bilan et suivi client →",
        key="vers_bilan",
        type="primary",
        use_container_width=True,
        on_click=aller,
        args=("bilan",),
    )
    st.button("← Autre dossier", key="retour_recherche", on_click=aller, args=("retrouver",))
    st.button("Recommencer la démonstration", key="reset", on_click=recommencer)
    st.caption(
        "Chaque démonstration part de données différentes, pour montrer la variété des "
        "situations possibles : un dossier presque prêt un jour, à moitié rempli un autre."
    )


# ---------------------------------------------------------------------------
# Écran 5 — Bilan par WhatsApp, aperçu du suivi client, sortie vers WhatsApp
# ---------------------------------------------------------------------------
def ecran_bilan():
    suivi = st.session_state.suivi
    id_dos = st.session_state.dossier
    if id_dos not in suivi:
        aller("retrouver")
        st.rerun()

    infos = suivi[id_dos]
    code_obj = next(iter(infos["objectifs_actifs"]))
    r = dp.resume_dossier(suivi, id_dos, code_obj)
    libelles_manquants = [p["libelle"] for p in r["manquantes"]]

    st.subheader("Bilan et suivi")

    # --- 1. Le bilan envoyé par WhatsApp ------------------------------------
    st.markdown("**Envoyer le bilan par WhatsApp**")
    if r["manquantes"]:
        corps = (
            f"Bonjour, voici le point sur votre dossier « {infos['sujet']} » : "
            f"il est complet à {r['pourcentage']} %. "
            "Il nous manque : " + ", ".join(libelles_manquants) + ".\n\n"
        )
    else:
        corps = (
            f"Bonjour, bonne nouvelle : votre dossier « {infos['sujet']} » est complet. "
            "Rien ne manque.\n\n"
        )
    corps += f"Vous pouvez télécharger votre bilan en PDF ici : {LIEN_SUIVI}"
    message = st.text_area(
        "Message prêt à envoyer",
        value=corps,
        height=220,
        key=f"msg_bilan_{id_dos}_{len(libelles_manquants)}",
    )
    st.link_button("Envoyer par WhatsApp", mp.lien_whatsapp(message), use_container_width=True)
    st.caption("Dans l’usage réel, ce lien ouvre la page de suivi propre à votre client.")
    pdf = bilan_pdf(infos, r)
    if pdf:
        st.download_button(
            "Voir le bilan en PDF",
            data=pdf,
            file_name=f"bilan_{id_dos}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    # --- 2. Ce que voit le client final ------------------------------------
    st.divider()
    st.markdown("**Ce que voit votre client**")
    st.caption("Un lien de suivi, sur son téléphone, sans rien installer.")
    with st.container(border=True):
        st.markdown(f"**{infos['sujet']}**")
        st.progress(
            r["pourcentage"] / 100,
            text=f"Votre dossier est complet à {r['pourcentage']} %",
        )
        if r["manquantes"]:
            st.markdown("**Il reste à nous transmettre :**")
            for p in r["manquantes"]:
                st.markdown(f"○ &nbsp; {p['libelle']}")
        else:
            st.markdown("✓ &nbsp; Tout est reçu. Merci !")

    # --- 3. Sortie vers votre WhatsApp -------------------------------------
    if NUMERO_WHATSAPP:
        st.divider()
        texte = quote("Bonjour, j’aimerais essayer l’outil avec mes propres dossiers.")
        st.link_button(
            "Essayer avec vos propres dossiers",
            f"https://wa.me/{725633569}?text={texte}",
            type="primary",
            use_container_width=True,
        )

    st.divider()
    st.button("← Retour au dossier", key="retour_fiche", on_click=aller, args=("fiche",))
    st.button("Recommencer la démonstration", key="reset_bilan", on_click=recommencer)


# ---------------------------------------------------------------------------
init()
{
    "accueil": ecran_accueil,
    "retrouver": ecran_retrouver,
    "fiche": ecran_fiche,
    "bilan": ecran_bilan,
}[st.session_state.ecran]()
