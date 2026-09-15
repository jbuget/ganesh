"""Configuration pytest racine : rend le package src importable.

`holidays` emet un avertissement informatif sur sa future strategie de version
au moment de son import. On l'importe ici une fois, silencieusement, pour garder
une sortie de tests propre sans masquer les avertissements du projet.
"""

import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import holidays  # noqa: F401
