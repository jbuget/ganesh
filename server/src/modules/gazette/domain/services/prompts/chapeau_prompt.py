"""What is asked of the model, and the shape the facts are handed over in.

The instructions are in French because the chapeau is: asking in the language
one wants back is what makes getting it back reliable. They live in the domain
rather than beside the adapter because they are not a detail of how Gemini is
called — they are the rule, said out loud. The adapter may change; what the
model is forbidden to do may not.

The facts go over in the vocabulary the register uses, never in French. The
French of the gazette is written once, on the reading side, and a second copy
here would be a second thing to keep in step.
"""

from src.modules.gazette.domain.entities.brief import Brief
from src.modules.projects.domain.entities.project import ProjectStatus

#: Said twice on purpose — once as a rule, once as the reason. A model told
#: only « n'écris pas de chiffres » writes them out in letters instead.
INSTRUCTIONS = """Tu rédiges le chapeau d'un numéro de La Gazette, le journal
mensuel interne d'une équipe technique. Il est lu par l'équipe et par sa
direction.

Voici tous les faits du mois. Il n'y en a pas d'autres.

{facts}

Écris deux à trois phrases qui introduisent ce mois, en français.

Règles impératives :
- N'écris aucun chiffre, ni en chiffres ni en lettres. Ne compte rien, ne dis
  ni « trois projets » ni « plusieurs projets ». Les comptes sont affichés à
  côté de ton texte, par l'application : ce n'est pas ton travail.
- Nomme les projets et les personnes dont tu parles. Leurs noms sont dans les
  faits ci-dessus : « WAATcher est passé en exploitation » se lit, « un projet
  est passé en exploitation » ne dit rien que le tableau ne dise mieux.
- Ne récapitule pas tout. Retiens ce qui compte — une mise en service, un
  retour en arrière, une date dépassée — et laisse le reste au tableau.
- N'ajoute aucun fait absent de la liste. N'invente ni projet, ni date, ni
  cause, ni conséquence. Ne suppose pas pourquoi quelque chose est arrivé.
- Ne mets personne en cause, même implicitement.
- Ton sobre et factuel. Pas de jeu de mots, pas d'enthousiasme, pas de formule
  d'accroche, pas de conclusion qui encourage.
- Un seul paragraphe. Pas de titre, pas de liste, pas de markdown.
- Si la liste des faits est vide, écris simplement que le mois n'a rien laissé
  au registre.
"""

#: When nothing is handed over, say so rather than hand over a blank: a blank
#: is the one thing a model reliably fills in by itself.
_NOTHING = "(aucun fait enregistré ce mois-ci)"


def compose(brief: Brief) -> str:
    """The prompt for one month's chapeau."""
    return INSTRUCTIONS.format(facts=_facts(brief) or _NOTHING)


def _facts(brief: Brief) -> str:
    """The month's facts, one per line, in the register's own vocabulary."""
    lines = [
        f"- {movement.kind.value}: {movement.subject}"
        + _phases(movement.from_status, movement.to_status)
        for movement in brief.movements
    ]
    lines += [
        f"- {highlight.kind.value} ({highlight.tone.value}): {highlight.label}"
        for highlight in brief.highlights
    ]
    return "\n".join(lines)


def _phases(came_from: ProjectStatus | None, went_to: ProjectStatus | None) -> str:
    """Where a phase came from and went, when the fact is one of those."""
    if came_from is None and went_to is None:
        return ""
    return f" ({_phase(came_from)} -> {_phase(went_to)})"


def _phase(status: ProjectStatus | None) -> str:
    return status.value if status else "?"
