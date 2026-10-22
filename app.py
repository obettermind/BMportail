"""Portail — démonstration publique de l'outil d'audit (format téléphone).

Lancer :  streamlit run app.py

Tout l'état du visiteur vit dans st.session_state : il est propre à sa visite
et disparaît à la fermeture de la page. Rien n'est écrit sur le disque.
"""
import streamlit as st

import demo_portail as dp
import messages_portail as mp

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
# Écran 1 — Accueil
# ---------------------------------------------------------------------------
def ecran_accueil():
    st.title("Mieux communiquer, mieux avancer.")
    st.write(
        "Des outils simples, faits pour votre travail, par des gens qui parlent "
        "le langage des innovations les plus modernes, pour que vous n’ayez pas à le parler."
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
    st.caption("Dossiers de démonstration : 4402 et 9941.")

    suivi = st.session_state.suivi
    resultats = dp.rechercher(suivi, saisie)
    for id_dos in resultats:
        st.button(
            f"{id_dos} · {suivi[id_dos]['sujet']}",
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
    st.button("← Autre dossier", key="retour_recherche", on_click=aller, args=("retrouver",))
    st.button("Recommencer la démonstration", key="reset", on_click=recommencer)
    st.caption(
        "Chaque démonstration part de données différentes, pour montrer la variété des "
        "situations possibles : un dossier presque prêt un jour, à moitié rempli un autre."
    )


# ---------------------------------------------------------------------------
init()
{"accueil": ecran_accueil, "retrouver": ecran_retrouver, "fiche": ecran_fiche}[
    st.session_state.ecran
]()
