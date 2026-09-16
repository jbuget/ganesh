@AGENTS.md

# CLAUDE.md — Timesheet

Guide de développement pour Claude Code sur ce projet. Ces règles s'appliquent à toutes les contributions, sans exception.

Ce projet reprend délibérément les conventions de **WAATcher**. En cas de doute sur un point non couvert ici, se référer à l'existant WAATcher plutôt que d'inventer : **la cohérence prime sur la préférence personnelle**.

---

## Le produit

Timesheet permet à chaque développeur de déclarer, en journées ou demi-journées, le temps passé (ou prévu) sur chaque projet ou sous-projet, sous forme d'une matrice `jours du mois × missions`.

- **V1 : aucune intégration Monday.** Les projets sont créés dans l'application ou importés par CSV.
- **V1.1 :** bouton « Synchroniser vers Monday », réservé aux managers. Les colonnes `monday_item_id` / `monday_subitem_id` existent dès la V1, nullables.
- Monday ne sera **jamais** une source de saisie : la synchronisation est unidirectionnelle, Timesheet → Monday.

### Rôles

| Action | `TEAMMATE` | `MANAGER` |
|---|---|---|
| Saisir son mois, consulter et éditer le mois ouvert d'un collègue | ✅ | ✅ |
| Créer / modifier un projet, changer son statut | ✅ | ✅ |
| Valider son propre mois | ✅ | ✅ |
| Rouvrir un mois validé | ❌ | ✅ |
| Gestion des collaborateurs | ❌ | ✅ |
| Synchroniser vers Monday (V1.1) | ❌ | ✅ |

### Invariants métier

Ces règles sont testées **au niveau du domaine**, indépendamment de l'API et de l'UI :

- Une saisie vaut `0.5` ou `1.0`, jamais autre chose.
- **Aucune saisie n'est possible sur un jour non ouvré** (week-end ou jour férié
  français). La règle est portée par le domaine et refusée par l'API : le
  verrouillage de la cellule côté client n'en est que le reflet.
- La somme des saisies d'un utilisateur pour un jour donné ne doit pas dépasser `1` (alerte, pas blocage).
- Un mois validé est **immuable** : aucune écriture possible tant qu'un manager ne l'a pas rouvert.
- Chaque saisie mémorise le statut du projet au moment où elle est écrite (`statut_at_entry`), ce qui permet de mesurer le temps passé par phase.
- Les activités hors projet (absences, formation, interne) n'ont pas de statut et ne sont jamais synchronisées.
- Toute action significative est tracée dans `audit_log`.

---

## Philosophie

Ce projet suit les principes du **Software Craftsmanship** : code propre, testé, bien architecturé, livré en continu avec discipline. Chaque contribution doit laisser le code dans un meilleur état qu'elle ne l'a trouvé (règle du boy scout).

- **TDD** : écrire le test avant le code de production. Les tests documentent l'intention, pas l'implémentation.
- **Baby Steps** : avancer par petits incréments vérifiables. Chaque étape doit compiler, passer les tests, et laisser le code dans un état cohérent.
- **Clean Code** : noms explicites, fonctions courtes à responsabilité unique, pas de commentaires inutiles, pas de code mort.
- **Clean Architecture** (côté serveur) : respecter les couches — jamais de dépendance vers l'extérieur depuis le domaine.
- **DRY / SOLID** : une règle métier s'écrit à un seul endroit ; les types d'API ne s'écrivent jamais à la main.
- **YAGNI / KISS** : ne pas anticiper. Implémenter ce qui est demandé, rien de plus.

---

## Stack

| Couche | Technologie |
|--------|------------|
| Frontend | Next.js 16, TypeScript, React 19, Tailwind CSS 4 |
| BFF | Route Handlers Next.js (`client/src/app/api/`) |
| Backend | Python 3.12, FastAPI, SQLAlchemy async, Alembic |
| Base de données | PostgreSQL 16 |
| Authentification | Microsoft Entra ID |
| Tests front | Vitest + Testing Library |
| Tests back | pytest + pytest-asyncio |
| Client API | Orval (généré depuis OpenAPI) |

---

## Architecture serveur

Le backend suit une **Clean Architecture** stricte par module fonctionnel. Chaque module dans `server/src/modules/<nom>/` est organisé en 4 couches :

```
src/modules/<module>/
├── domain/           # Entités, value objects, interfaces de repositories (aucune dépendance externe)
├── application/      # Use cases, DTOs
├── infrastructure/   # Modèles SQLAlchemy, implémentations de repositories
└── presentation/     # Routes FastAPI, schémas Pydantic, dépendances
```

Modules : `users`, `projects`, `entries`, `months`, `calendar`, `audit_logs`.

**Règles d'or :**
- Le domaine ne connaît ni SQLAlchemy, ni FastAPI, ni Pydantic, ni aucun framework. Les entités sont des `dataclass`.
- Les use cases orchestrent, ils ne font pas de logique métier directe.
- Les repositories sont des interfaces (ABC) dans le domaine, implémentées dans l'infrastructure.
- **Un use case ne peut jamais appeler un autre use case.** Extraire la logique partagée dans un service domaine.
- **Les routes FastAPI n'injectent jamais de repository directement** — uniquement des use cases.
- Toujours dépendre de l'interface, jamais de l'implémentation concrète.

**Ces règles ne sont pas déclaratives : elles sont vérifiées par `import-linter`** (`server/.importlinter`), exécuté par `make lint` et en CI. Une violation casse le build.

Le code partagé (exceptions, types génériques) vit dans `server/src/shared/`.

---

## Ports et URLs

Ports par défaut. WAATcher occupe `3001-3003` / `8001-8003` / `54321-54323`,
il n'y a donc pas de collision, mais tout autre service local écoutant sur `3000`
ou `5432` doit être arrêté au préalable. Les ports sont surchargeables via
`WEB_PORT`, `API_PORT` et `POSTGRES_PORT` dans le `.env` racine.

| | Port | URL |
|---|---|---|
| Client Next.js | `3000` | http://localhost:3000 |
| API FastAPI | `8000` | http://localhost:8000 |
| PostgreSQL | `5432` | — |

Conventions identiques à WAATcher : `API_PREFIX=/api/v1`, variables `AZURE_AD_*`,
callback `/api/auth/callback/azure-ad`.

**Le BFF expose exactement les mêmes chemins que l'API** : le navigateur appelle
`/api/v1/<ressource>`, le Route Handler relaie vers `${API_URL}/api/v1/<ressource>`.
Un seul vocabulaire d'URL dans tout le projet.

### Identifiants Entra

Timesheet réutilise **l'enregistrement d'application Entra de WAATcher**
(même `AZURE_AD_TENANT_ID` et `AZURE_AD_CLIENT_ID`). L'URI de redirection
`http://localhost:3000/api/auth/callback/azure-ad` doit donc être déclarée sur
cette app registration dans le portail Azure.

Le `AZURE_AD_CLIENT_SECRET` vit uniquement dans `client/.env.local` : c'est le BFF
qui porte le flow OAuth. Le serveur ne fait que valider les jetons et n'a besoin
que du tenant et du client id.

---

## Architecture client

- **BFF obligatoire** : le navigateur n'appelle jamais FastAPI directement. Il appelle les Route Handlers de `client/src/app/api/`, qui relaient vers l'API en injectant le token Entra. Le token reste côté serveur, dans une session `httpOnly`.
- **Hooks Orval uniquement** : les hooks de données viennent exclusivement du client généré (`client/src/lib/api/generated/`), dont la `baseUrl` pointe vers le BFF. Ne jamais créer d'instance fetch/axios custom pour appeler l'API.
- **Aucun type d'API écrit à la main** : ils sont générés depuis l'OpenAPI de FastAPI (`pnpm api:generate`).
> **Divergence assumée avec WAATcher.** WAATcher n'a pas de BFF : son navigateur
> appelle FastAPI directement via `NEXT_PUBLIC_API_URL`. Timesheet introduit
> délibérément un BFF, pour que le jeton Entra ne quitte jamais le serveur et que
> l'API ne soit pas exposée publiquement. C'est le seul écart structurel ; tout le
> reste suit WAATcher.

- **Atomic Design** : voir `AGENTS.md`. Les règles de composition sont vérifiées par `eslint-plugin-boundaries`. Une violation casse le lint.

---

## Git

### Branches

Modèle **Git Feature Branching** :

- `main` — production, protégée
- `feature/<description>` — nouvelle fonctionnalité
- `fix/<description>` — correction de bug
- `chore/<description>` — maintenance, tooling, dépendances
- `refactor/<description>` — refactoring sans changement fonctionnel

**Workflow :** créer une branche depuis `main`, ouvrir une PR vers `main`, merger après review.

**Règle stricte :** ne jamais pousser directement sur `main`.

### Commits

Format **Conventional Commits** obligatoire :

```
<type>(<scope optionnel>): <description courte en anglais>
```

Types : `feat`, `fix`, `chore`, `refactor`, `test`, `docs`, `perf`, `ci`

```
feat(entries): capture project status on each timesheet entry
fix(months): prevent writing to a validated month
test(projects): cover status transition rules
```

- Description en anglais, minuscule, sans point final
- Un commit = une intention claire
- Pas de `WIP`, pas de `fix fix`, pas de `misc`

N'applique jamais la mention "Co-authored by Claude".

### Pull Requests

Titre et description en français, template obligatoire :

```markdown
### Problème

### Solution

### Implémentation

### Recette
```

---

## Qualité — checks obligatoires avant tout push

### Backend (`server/`)

```bash
make lint    # isort + black + ruff + flake8 + import-linter
make test    # pytest avec couverture
make format  # corrige isort + black + ruff
```

### Frontend (`client/`)

```bash
pnpm lint          # ESLint (dont les règles Atomic Design)
pnpm format:check  # Prettier
pnpm type-check    # tsc --noEmit
pnpm test          # Vitest
```

Depuis la racine : `make check` lance l'ensemble.

**Le lint doit passer à zéro erreur à la fin de chaque tâche**, sans exception.

---

## Tests

### Principes

- **TDD** : red → green → refactor.
- Un test = un comportement, pas une implémentation.
- Pas de test qui teste un mock qui teste un mock.
- Les use cases se testent avec des **repositories en mémoire**, pas des mocks.
- Les tests d'intégration touchent une vraie base de données, pas une base mockée.
- Nommage backend : `test_<quoi>_<dans quel contexte>_<résultat attendu>`.

### Backend — structure

```
server/tests/
├── conftest.py
├── modules/<module>/
│   ├── domain/           # Entités et services domaine
│   ├── application/      # Use cases (repositories en mémoire)
│   ├── infrastructure/   # Intégration, vraie DB
│   └── presentation/     # Routes FastAPI
└── shared/
```

### Frontend — structure

Tests Vitest colocalisés avec le source (`*.test.ts` / `*.test.tsx`).

---

## Migrations de base de données

- Les colonnes `Enum` sont déclarées `native_enum=False` : SQLAlchemy y stocke le
  **nom** du membre Python, pas sa valeur. En base on lit donc `LOT`, `HORS_PROJET`
  ou `CADRAGE`, jamais `lot` ni `cadrage`. L'ORM traduit dans les deux sens, mais
  toute requête SQL écrite à la main doit employer les noms en majuscules.
- Les migrations Alembic sont **immuables** une fois appliquées en production.
- Ne jamais modifier une migration existante sans accord explicite : créer une nouvelle migration.
- Nommage automatique : `YYYY_MM_DD_<rev>_<slug>.py`
- Tout nouveau modèle doit être importé dans `server/alembic/env.py`, sinon l'autogenerate ne le voit pas.

```bash
make migration   # demande un message
make migrate     # alembic upgrade head
```

---

## Conventions de code

### Python (backend)

- Typage strict partout — pas de `Any` sans justification.
- **Syntaxe de typage 3.10+ obligatoire** — builtins natifs, jamais les alias `typing` :

  | Interdit | Obligatoire |
  |-------------|----------------|
  | `Optional[X]` | `X \| None` |
  | `Union[X, Y]` | `X \| Y` |
  | `List[X]` | `list[X]` |
  | `Dict[X, Y]` | `dict[X, Y]` |
  | `Tuple[X, ...]` | `tuple[X, ...]` |
  | `Set[X]` | `set[X]` |
  | `Type[X]` | `type[X]` |

- Pas de logique métier dans les routes FastAPI.
- Les exceptions métier héritent de `src/shared/exceptions/domain_exceptions.py`.
- `async/await` partout sur les I/O — pas de blocking calls.
- Pas de `print()` en production — utiliser `logging`.

### TypeScript (frontend)

- Pas de `any` — typer explicitement ou utiliser les types générés par Orval.
- Server components par défaut, `"use client"` seulement si nécessaire.
- Un composant = une responsabilité. Extraire les hooks complexes dans `src/lib/`.
- Tous les éléments cliquables portent la classe `cursor-pointer`.

---

## Ce qu'il ne faut jamais faire

- Commiter des fichiers `.env`, secrets, clés API.
- Bypasser les hooks de commit (`--no-verify`).
- Pousser directement sur `main`.
- Désactiver un test qui échoue sans le corriger.
- Contourner un contrat `import-linter` ou une règle `boundaries` au lieu de corriger la conception.
- Appeler FastAPI directement depuis le navigateur, en contournant le BFF.
- Écrire un type d'API à la main plutôt que de régénérer le client Orval.
- Laisser du code commenté ou des `TODO` sans ticket associé.
