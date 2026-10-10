"""What is asked of the model, and the shape the facts are handed over in.

The instructions are in French because the text is: asking in the language one
wants back is what makes getting it back reliable. They live in the domain
rather than beside the adapter because they are not a detail of how Gemini is
called — they are the rule, said out loud. The adapter may change; what the
model is forbidden to do may not.

The facts go over in the vocabulary the register uses, never in French. The
French of the gazette is written once, on the reading side, and a second copy
here would be a second thing to keep in step. The one exception is the tally,
whose labels are the reader's.
"""

from src.modules.gazette.domain.entities.brief import Brief
from src.modules.gazette.domain.entities.dossier import Dossier
from src.modules.gazette.domain.entities.focus import ProjectFocus
from src.modules.projects.domain.entities.project import ProjectStatus

#: Said twice on purpose — once as a rule, once as the reason. A model told
#: only « n'invente pas de chiffre » invents one that sounds right.
INSTRUCTIONS = """Tu rédiges le compte rendu mensuel de La Gazette, le journal \
d'une équipe d'ingénierie logicielle. Il est lu surtout par des personnes qui \
ne font PAS partie de l'équipe et ne connaissent pas le jargon technique : \
collaborateurs d'autres services concernés par les projets, sponsors, membres \
du COMEX et du COMOP, investisseurs, autres équipes de la DSI. Elles veulent \
comprendre ce que l'équipe a accompli, ce qui avance, ce qui coince et ce que \
cela change pour elles.

Voici tout ce que le registre sait du mois. Il n'y a rien d'autre.

## Faits du mois
{facts}

## Chiffres du mois
{figures}

## Projets sous le projecteur
{spotlights}

## Autres projets qui ont bougé ce mois-ci (contexte pour l'éditorial)
{background}

Réponds par un objet JSON de la forme :
{{"editorial": ["paragraphe", ...], "spotlights": [{{"project_id": 12, "text": \
"..."}}, ...]}}

« editorial » : trois à cinq paragraphes de trois à cinq phrases chacun, qui \
racontent le mois comme un journaliste le raconterait à un lecteur pressé : \
les grands mouvements, les mises en service, ce qui a ralenti ou reculé. \
Commence par l'essentiel. Appuie-toi sur le contenu des mises à jour des \
projets sous le projecteur ET des autres projets qui ont bougé : cite des \
projets précis et ce que leurs mises à jour disent concrètement, plutôt que \
de résumer le mois en généralités. Relie les faits entre eux quand le \
registre le permet. Les projets sous le projecteur ont leur propre encadré, lu juste après \
l'éditorial : n'en dis qu'une phrase pour situer, sans répéter leurs \
détails. Termine sur un fait, pas sur une tendance générale.

« spotlights » : un élément par projet listé sous « Projets sous le \
projecteur », avec son project_id exact. Chaque texte compte un à deux \
paragraphes séparés par une ligne vide. Explique d'abord, en une phrase \
simple, à quoi sert le projet et pour qui, comme à quelqu'un qui n'en a \
jamais entendu parler — mais SEULEMENT si la fiche de service ou les mises \
à jour le disent. Sinon ne devine pas : passe directement à ce que le mois \
lui a apporté. Raconte ensuite ce que le mois lui a apporté, en \
t'appuyant sur les mises à jour de l'équipe : où il en est, ce qui a été \
décidé ou livré, ce qui reste à faire. Les mises à jour sont le point de vue \
de leurs auteurs à leur date : rapporte-les comme tel, sans les présenter \
comme des vérités établies. Ne récite pas la liste des chiffres du projet : \
ils sont déjà affichés à côté du texte ; n'en reprends un que s'il aide à \
comprendre.

Règles impératives :
- Tu peux citer un chiffre UNIQUEMENT s'il figure dans « Chiffres du mois » \
ou dans les chiffres d'un projet, sous la même valeur. Tu peux écrire « 12 \
mises à jour » si le registre dit 12. Tout autre chiffre, en chiffres ou en \
lettres, est interdit : pas d'estimation, pas d'arrondi, pas de calcul, pas \
de pourcentage, pas de date, pas de durée. Si tu hésites, n'écris pas de \
chiffre. Un texte qui contient un chiffre non listé sera supprimé en entier.
- Nomme les projets tels qu'ils figurent dans les faits. Ne cite JAMAIS le \
prénom ou le nom d'une personne trouvée dans les mises à jour : écris \
« l'équipe », « un développeur », « le métier ». Seules les arrivées et \
départs d'équipe de la liste des faits peuvent nommer quelqu'un, et \
simplement.
- N'attribue jamais une intention, un objectif ou une cause qui n'est pas \
écrit dans une mise à jour : pas de « afin de », « visent à », « cherchent à », \
« dans le but de » pour expliquer ce que l'équipe a fait. Décris ce qui s'est \
passé, pas pourquoi. Pas non plus de « dynamique », de « recentrage » ou de \
« montée en puissance » que rien n'établit.
- Respecte l'accord en nombre et en genre autour des chiffres : « 1 personne \
», « 2 personnes ».
- Écris pour quelqu'un qui ne connaît pas le jargon : explique ou évite les \
sigles, les noms de technologies et les termes d'ingénierie. Dis ce que \
cela change plutôt que comment c'est fait.
- N'ajoute aucun fait absent de ce qui précède. N'invente ni projet, ni \
date, ni cause, ni conséquence, ni citation. Ne devine pas pourquoi quelque \
chose est arrivé : si les mises à jour ne le disent pas, ne le dis pas.
- Ne cite pas un projet uniquement parce qu'il figure dans les faits : \
ignore ceux qui ont à peine vécu ou dont aucune mise à jour ne montre \
qu'ils comptent. Mieux vaut peu de projets bien racontés qu'une \
énumération.
- Ne mets jamais une personne en cause, même implicitement. Un retard ou un \
recul est une affaire de projet, jamais de personne.
- Ton clair, posé et accessible. Pas de jeu de mots, pas d'enthousiasme \
forcé, pas de formule d'accroche, pas de conclusion qui encourage.
- Pas de titre, pas de liste, pas de markdown dans les textes.
- Si le registre est vide, un seul paragraphe dit que le mois n'a presque \
rien laissé au registre, et « spotlights » reste vide.
"""

#: When nothing is handed over, say so rather than hand over a blank: a blank
#: is the one thing a model reliably fills in by itself.
_NOTHING = "(aucun)"


def compose(dossier: Dossier) -> str:
    """The prompt for one month's editorial and spotlights."""
    brief = dossier.brief
    return INSTRUCTIONS.format(
        facts=_facts(dossier) or _NOTHING,
        figures=_figures(brief),
        spotlights=_spotlights(dossier) or _NOTHING,
        background=_background(dossier) or _NOTHING,
    )


def _counted(count: int, one: str, many: str) -> str:
    """A figure with its noun, agreed: « 1 personne », « 2 personnes ».

    Handed over already agreed, because a model copying « 1 personnes » out of
    a list writes it that way in the sentence too.
    """
    return f"{count} {many if count > 1 else one}"


def _days(days: float) -> str:
    """« 7,75 jours déclarés », as French writes a fraction of a day."""
    text = f"{days:g}".replace(".", ",")
    return f"{text} {'jours déclarés' if days > 1 else 'jour déclaré'}"


def _facts(dossier: Dossier) -> str:
    """The month's facts, one per line, in the register's own vocabulary.

    What concerns a project opened and closed with nothing written on it is
    left out: it would only give the model a sentence to write about nothing.
    """
    brief = dossier.brief
    lines = [
        f"- {movement.kind.value}: {movement.subject}"
        + _phases(movement.from_status, movement.to_status)
        for movement in brief.movements
        if movement.project_id not in dossier.quiet
    ]
    lines += [
        f"- {highlight.kind.value} ({highlight.tone.value}): {highlight.label}"
        for highlight in brief.highlights
        if highlight.project_id not in dossier.quiet
    ]
    return "\n".join(lines)


def _figures(brief: Brief) -> str:
    tally = brief.tally
    return "\n".join(
        f"- {line}"
        for line in [
            _counted(tally.projects_created, "projet créé", "projets créés"),
            _counted(tally.projects_archived, "projet archivé", "projets archivés"),
            _counted(
                tally.phase_changes, "changement de phase", "changements de phase"
            ),
            _counted(tally.news_posted, "mise à jour publiée", "mises à jour publiées"),
            _counted(
                brief.went_live_count,
                "projet mis en exploitation",
                "projets mis en exploitation",
            ),
            _counted(tally.months_validated, "mois validé", "mois validés"),
            _counted(tally.requests_filed, "demande déposée", "demandes déposées"),
            _counted(
                tally.requests_converted,
                "demande devenue un projet",
                "demandes devenues un projet",
            ),
        ]
    )


def _spotlights(dossier: Dossier) -> str:
    """Each project of the month, its figures and what the team wrote on it."""
    blocks = []
    for focus in dossier.brief.focus:
        material = dossier.material.get(focus.project_id)
        lines = [
            f"### project_id {focus.project_id} : {focus.label}",
            _focus_figures(focus),
        ]
        if material is not None and material.summary:
            lines.append(f"Fiche de service : {material.summary}")
        else:
            lines.append("Fiche de service : (aucune)")
        if material is not None and material.excerpts:
            lines.append(
                "Mises à jour de l'équipe, de la plus ancienne à la plus récente :"
            )
            lines += [f"> {excerpt}" for excerpt in material.excerpts]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _focus_figures(focus: ProjectFocus) -> str:
    parts = [
        f"phase actuelle : {_phase(focus.status)}",
        _counted(focus.updates_posted, "mise à jour publiée", "mises à jour publiées"),
        _counted(focus.phase_moves, "changement de phase", "changements de phase"),
    ]
    if focus.contributors:
        parts.append(
            _counted(
                focus.contributors,
                "personne a déclaré du temps",
                "personnes ont déclaré du temps",
            )
        )
    if focus.days_declared:
        parts.append(_days(focus.days_declared))
    if focus.went_live:
        parts.append("mis en exploitation ce mois-ci")
    return "; ".join(parts)


def _background(dossier: Dossier) -> str:
    """The other projects that moved: what they are, and their last words.

    Handed over with no figure of their own. The editorial may name them and
    say what their updates say; counting them is not what they are here for.
    """
    blocks = []
    for other in dossier.background:
        lines = [f"### {other.label}"]
        if other.summary:
            lines.append(f"Fiche de service : {other.summary}")
        lines += [f"> {excerpt}" for excerpt in other.excerpts]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _phases(came_from: ProjectStatus | None, went_to: ProjectStatus | None) -> str:
    """Where a phase came from and went, when the fact is one of those."""
    if came_from is None and went_to is None:
        return ""
    return f" ({_phase(came_from)} -> {_phase(went_to)})"


def _phase(status: ProjectStatus | None) -> str:
    return status.value if status else "?"
