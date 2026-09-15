"""Exceptions metier partagees par tous les modules.

Le domaine leve ces exceptions ; la couche presentation les traduit en
reponses HTTP. Aucune dependance vers un framework ici.
"""


class DomainError(Exception):
    """Erreur metier generique."""


class EntityNotFoundError(DomainError):
    """L'entite demandee n'existe pas."""


class ValidationError(DomainError):
    """Une invariante metier n'est pas respectee."""


class ForbiddenActionError(DomainError):
    """L'acteur n'a pas le droit d'effectuer cette action."""


class ConflictError(DomainError):
    """L'action entre en conflit avec l'etat courant."""
