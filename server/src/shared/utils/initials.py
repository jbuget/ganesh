"""Initiales affichees en pastille."""


def initiales(nom: str) -> str:
    """Deux initiales au plus, tirees d'un nom affiche.

    Les noms de l'annuaire prennent la forme « L. Chen » : le point y separe
    autant que l'espace, faute de quoi « L. » donnerait une seule initiale.
    """
    mots = [mot for mot in nom.replace(".", " ").split() if mot]
    return "".join(mot[0].upper() for mot in mots[:2])
