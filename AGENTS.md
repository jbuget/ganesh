<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `client/node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# Conventions UI

## Architecture des composants — Atomic Design

Les composants front sont organisés en niveaux stricts dans `client/src/components/` :

```
ui/          Primitives externes (shadcn/ui). Traitées comme des dépendances,
             non modifiées à la main.
atoms/       Blocs de base, aucune dépendance vers un autre composant local.
             Ex : DayCell, DayHeader, DayTotalCell, TotalCell, MissionLabel,
             MissionSelector
molecules/   Assemblage d'atoms formant une unité fonctionnelle.
             (vide pour l'instant : aucun composant n'assemble encore d'atoms)
organisms/   Sections complexes composées de molecules et d'atoms. Un organism
             peut en composer un autre : une page assemble des sections.
             Ex : TimesheetGrid, TimesheetPage
             (templates = layout.tsx Next.js / pages = app/)
```

**Règles :**
- Un atom n'importe jamais un autre composant local (hors `ui/` et `lib/`).
  C'est la dépendance qui classe un composant, pas sa complexité apparente.
- Une molecule n'importe que des atoms.
- Un organism peut importer des atoms, des molecules et d'autres organisms.
- Les pages (`app/`) n'importent que des organisms.
- La logique d'un écran (état, données, écritures) vit dans un hook de
  `src/lib/`, pas dans le composant : celui-ci ne porte que le rendu.
- Tout nouveau composant doit être placé au bon niveau avant d'être utilisé.
- Ne jamais créer de dossier `shared/`, `common/`, `features/` ou autre hors de cette structure.

Ces règles sont **vérifiées par `eslint-plugin-boundaries`** (`client/eslint.config.mjs`) : une violation est une erreur de lint, pas une remarque de review. Les fichiers de test colocalisés sont exemptés.

## Composants et fichiers

- Un composant par fichier, nommé en `PascalCase.tsx`, identique au nom du composant.
- Test colocalisé : `MonComposant.test.tsx` à côté de `MonComposant.tsx`.

## Curseur

Tous les éléments cliquables (`<button>`, `<a>`, éléments avec `onClick`) doivent avoir la classe `cursor-pointer`.

## Matrice de saisie

- Les jours non ouvrés (week-ends et jours fériés) sont visuellement distincts et identifiables au premier coup d'œil.
- Les jours futurs sont affichés en style atténué : ils relèvent du prévisionnel, pas du réalisé.
- Les totaux distinguent toujours **réalisé** et **prévu**.
- Un mois validé est affiché en lecture seule, avec la mention de qui l'a validé et quand.
