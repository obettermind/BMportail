"""Portail — démonstration publique de l'outil d'audit (format téléphone).

Lancer :  streamlit run app.py

Tout l'état du visiteur vit dans st.session_state : il est propre à sa visite
et disparaît à la fermeture de la page. Rien n'est écrit sur le disque.
"""
from urllib.parse import quote

import streamlit as st

import demo_portail as dp
import messages_portail as mp

import streamlit.components.v1 as components

# Votre numéro WhatsApp au format international, sans + ni espaces (ex. "2126XXXXXXXX").
# Tant qu'il est vide, le bouton « Essayer avec vos propres dossiers » n'est pas affiché.
NUMERO_WHATSAPP = ""

# Lien placé dans le message de bilan (ici, la démonstration elle-même).
LIEN_SUIVI = "https://bmportail.streamlit.app/"

# Marque et contact affichés sur l'accueil.
NOM_MARQUE = "Better Mind"
EMAIL_CONTACT = "obettermind@gmail.com"

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
    .marque {display: flex; align-items: center; gap: .6rem; margin-bottom: 1.2rem;}
    .marque span {font-size: 1.15rem; letter-spacing: .06em; font-weight: 600;}
    .contact {text-align: center; opacity: .75; font-size: .9rem; margin-top: 1.5rem;}
    .contact a {color: inherit;}
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
    st.session_state.navigation_version = (
        st.session_state.get("navigation_version", 0) + 1
    )
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
LOGO_SVG = (
    "<svg width='38' height='38' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'>"
    "<circle cx='20' cy='20' r='17' fill='none' stroke='#7FA8E8' stroke-width='2'/>"
    "<path d='M20 9 L23 17 L31 20 L23 23 L20 31 L17 23 L9 20 L17 17 Z' fill='#7FA8E8'/>"
    "<circle cx='33' cy='9' r='3' fill='#7FA8E8'/>"
    "</svg>"
)


def ecran_accueil():
    st.markdown(
        f"<div class='marque'>{LOGO_SVG}<span>{NOM_MARQUE}</span></div>",
        unsafe_allow_html=True,
    )

    st.title("Mieux comprendre. Mieux décider. Mieux agir.")

    st.write(
        "Chaque jour, les responsables doivent traiter des informations, "
        "suivre des dossiers, résoudre des difficultés et veiller à ce "
        "que le travail avance."
    )

    st.write(
        "Pourtant, disposer d’informations ne suffit pas toujours pour "
        "comprendre une situation, repérer ce qui bloque ou savoir "
        "quelle action entreprendre."
    )

    st.markdown(
        "**Better Mind vous aide à transformer les informations et les "
        "situations de travail en constats clairs, en pistes d’action "
        "et en un meilleur suivi.**"
    )

    st.divider()

    st.subheader("De quoi avez-vous besoin ?")

    with st.container(border=True):
        st.markdown("**Comprendre une situation**")
        st.caption(
            "Faire ressortir les constats, les liens et les risques "
            "utiles à la décision."
        )

    with st.container(border=True):
        st.markdown("**S’assurer qu’un dossier est complet**")
        st.caption(
            "Identifier les éléments manquants et faciliter le suivi."
        )

    with st.container(border=True):
        st.markdown("**Vérifier que le travail décidé est réalisé**")
        st.caption(
            "Suivre les actions attendues et vérifier leur réalisation."
        )

    st.markdown("*Le vrai luxe, c’est un travail sans accroc.*")

    st.button(
        "Essayer la démonstration de complétude",
        type="primary",
        use_container_width=True,
        on_click=aller,
        args=("retrouver",),
    )

    st.caption(
        "Démonstration : dossiers fictifs, rien n’est conservé. "
        "Chaque ouverture présente une situation différente."
    )

    st.markdown(
        f"<p class='contact'>{NOM_MARQUE} · "
        f"<a href='mailto:{EMAIL_CONTACT}'>{EMAIL_CONTACT}</a></p>",
        unsafe_allow_html=True,
    )
# ---------------------------------------------------------------------------
# Écran 2 — Retrouver
# ---------------------------------------------------------------------------

def ecran_retrouver():
    st.markdown(
        "<p class='scene'>Un mardi, à dix heures, un client appelle "
        "pour un dossier ouvert il y a trois ans. Vous saisissez les "
        "premiers chiffres de son identifiant : le dossier apparaît "
        "aussitôt dans la liste. Le client n’a pas eu le temps de "
        "sentir l’attente.</p>",
        unsafe_allow_html=True,
    )

    saisie = st.text_input(
        "Numéro ou nom du dossier",
        key="saisie",
        placeholder="Tapez 2 chiffres, puis Entrée",
    )

    st.caption(
        "Saisissez 44 ou 99, puis sélectionnez le dossier qui apparaît."
    )
    st.caption("Dossiers fictifs : 4402 et 9941.")

    suivi = st.session_state.suivi
    resultats = dp.rechercher(suivi, saisie)
    for id_dos in resultats:
        st.button(
            f"Dossier de démonstration {id_dos} · "
            f"{suivi[id_dos]['sujet']}",
            key=f"ouvrir_{id_dos}",
            use_container_width=True,
            on_click=aller,
            args=("fiche", id_dos),
        )
    if saisie.strip() and not resultats:
        st.info("Aucun dossier ne correspond. Essayez 44 ou 99.")

    st.button(
        "← Retour",
        key="retour_accueil",
        on_click=aller,
        args=("accueil",),
    )


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

    st.subheader("Vérifier le dossier")
    st.markdown(f"**{infos['sujet']}**")

    st.progress(
        r["pourcentage"] / 100,
        text=f"{len(r['validees'])} pièces sur {r['total']} · "
             f"{r['pourcentage']} %",
    )

    st.divider()
    st.markdown("**Pièces reçues**")
    recues = [p for p in r["pieces"] if p["ok"]]

    if recues:
        for p in recues:
            st.markdown(f"✓ &nbsp; {p['numero']}. {p['libelle']}")
    else:
        st.caption("Aucune pièce reçue pour le moment.")

    st.divider()
    st.markdown("**Pièces à fournir**")

    if r["manquantes"]:
        st.caption(
            "Sélectionnez une pièce lorsque vous souhaitez simuler son dépôt."
        )
        for p in r["manquantes"]:
            st.button(
                f"Déposer — {p['numero']}. {p['libelle']}",
                key=f"dep_{id_dos}_{p['code']}",
                use_container_width=True,
                on_click=deposer,
                args=(id_dos, code_obj, p["code"]),
            )
    else:
        st.success("Dossier complet. Rien ne manque.")

    st.divider()
    st.button(
        "Actions et contact client →",
        key="vers_actions",
        type="primary",
        use_container_width=True,
        on_click=aller,
        args=("actions",),
    )
    st.button(
        "← Autre dossier",
        key="retour_recherche",
        on_click=aller,
        args=("retrouver",),
    )
    st.button(
        "Recommencer la démonstration",
        key="reset",
        on_click=recommencer,
    )



# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------

def ecran_actions():
    suivi = st.session_state.suivi
    id_dos = st.session_state.dossier

    if id_dos not in suivi:
        aller("retrouver")
        st.rerun()

    infos = suivi[id_dos]
    code_obj = next(iter(infos["objectifs_actifs"]))
    r = dp.resume_dossier(suivi, id_dos, code_obj)
    libelles_manquants = [p["libelle"] for p in r["manquantes"]]

    st.subheader("Actions et contact client")
    st.markdown(f"**{infos['sujet']}**")

    if not r["manquantes"]:
        st.success(
            "Le dossier est complet. Aucune relance n'est nécessaire."
        )
    else:
        st.write(
            f"Le dossier est complet à {r['pourcentage']} %. "
            f"Il reste {len(r['manquantes'])} pièce(s) à recevoir."
        )

        st.divider()
        st.markdown("**Option 1 — Envoyer un message écrit**")
        st.caption(
            "Pour préciser les pièces manquantes et transmettre "
            "une demande claire au client."
        )

        message = st.text_area(
            "Message prêt à envoyer",
            value=mp.message_relance(
                infos["sujet"],
                libelles_manquants,
                r["pourcentage"],
            ),
            height=220,
            key=f"msg_actions_{id_dos}_{len(libelles_manquants)}",
        )

        st.link_button(
            "Ouvrir WhatsApp avec ce message",
            mp.lien_whatsapp(message),
            use_container_width=True,
        )

        st.divider()
        st.markdown("**Option 2 — Préparer une relance vocale**")
        st.caption(
            "Pour privilégier un contact plus personnel, "
            "ou relancer après l'absence de réponse."
        )
        st.info(
            mp.phrase_vocale(
                libelles_manquants,
                r["pourcentage"],
            )
        )
        st.caption(
            "Cette formulation est destinée à être prononcée "
            "dans un audio WhatsApp. L'enregistrement et l'envoi "
            "de l'audio se font dans WhatsApp."
        )

    st.divider()
    st.button(
        "Préparer le bilan et le suivi →",
        key="vers_bilan",
        type="primary",
        use_container_width=True,
        on_click=aller,
        args=("bilan",),
    )
    st.button(
        "← Retour à l'état du dossier",
        key="retour_fiche_actions",
        on_click=aller,
        args=("fiche",),
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
            f"https://wa.me/{NUMERO_WHATSAPP}?text={texte}",
            type="primary",
            use_container_width=True,
        )


    st.divider()
    st.button(
        "Terminer la démonstration →",
        key="vers_conclusion",
        type="primary",
        use_container_width=True,
        on_click=aller,
        args=("conclusion",),
    )
    st.button(
        "← Retour aux actions",
        key="retour_actions_bilan",
        on_click=aller,
        args=("actions",),
    )



# ---------------------------------------------------------------------------


def ecran_conclusion():
    st.subheader("Ce que cette démonstration vous apporte")

    st.write(
        "Un dossier mieux suivi, c'est moins de temps passé à rechercher "
        "les pièces, une meilleure visibilité sur ce qui manque et des "
        "relances plus faciles à préparer."
    )

    st.divider()

    st.markdown("**En pratique, l'outil permet de :**")
    st.markdown(
        "- repérer les pièces présentes et celles qui manquent ;\n"
        "- visualiser rapidement l'état d'avancement du dossier ;\n"
        "- préparer le contact avec le client ;\n"
        "- produire un bilan pour faciliter le suivi."
    )

    st.caption(
        "Vous venez d'explorer une démonstration avec des données fictives. "
        "Le fonctionnement réel doit être adapté aux dossiers et aux "
        "règles de votre organisation."
    )

    st.divider()
    st.markdown("**Vous souhaitez étudier une utilisation dans votre activité ?**")
    st.write(
        "Contactez Better Mind pour échanger sur vos besoins et "
        "les possibilités d'adaptation."
    )
    st.markdown(f"**Contact :** {EMAIL_CONTACT}")

    st.button(
        "Recommencer la démonstration",
        type="primary",
        use_container_width=True,
        on_click=recommencer,
    )
    st.button(
        "Retour à l'accueil",
        on_click=aller,
        args=("accueil",),
        use_container_width=True,
    )


# ---------------------------------------------------------------------------


def remonter_en_haut():
    version = st.session_state.get("navigation_version", 0)

    components.html(
        f"""
        <script>
        const version = "{version}";
        window.parent.document.documentElement.scrollTop = 0;
        window.parent.document.body.scrollTop = 0;

        const main = window.parent.document.querySelector(
            '[data-testid="stMain"]'
        );
        if (main) {{
            main.scrollTop = 0;
        }}

        window.parent.requestAnimationFrame(() => {{
            window.parent.document.documentElement.scrollTop = 0;
            if (main) {{
                main.scrollTop = 0;
            }}
        }});
        </script>
        """,
        height=0,
        key=f"remonter_{version}",
    )


# ---------------------------------------------------------------------------



init()
{
    "accueil": ecran_accueil,
    "retrouver": ecran_retrouver,
    "fiche": ecran_fiche,
    "actions": ecran_actions,
    "bilan": ecran_bilan,
    "conclusion": ecran_conclusion,
}[st.session_state.ecran]()




# ---------------------------------------------------------------------------



init()
remonter_en_haut()

{
    "accueil": ecran_accueil,
    "retrouver": ecran_retrouver,
    "fiche": ecran_fiche,
    "actions": ecran_actions,
    "bilan": ecran_bilan,
    "conclusion": ecran_conclusion,
}[st.session_state.ecran]()
