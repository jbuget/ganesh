# Correspondance Monday ↔ Timesheet (préparation V1.1)

> La V1 ne communique **pas** avec Monday. Ce document prépare la V1.1 :
> bouton « Synchroniser vers Monday », réservé aux managers, en écriture seule.

## Source

- Compte : `waat-global`, plan Pro
- Board **Projets Dev & Automatisation** : `5091544837`
  ([lien](https://waat-global.monday.com/boards/5091544837))
- Workspace : « Chantiers UC IA & Dev » (`4420418`)
- Board des sous-éléments (lots) : `5091588527`
- Groupes : `topics` (« Backlog »), `group_mm0fqn9k` (« Hors pipe »)

## Colonnes

### Niveau projet (item du board `5091544837`)

| Colonne | ID | Type | Usage |
|---|---|---|---|
| Tps estimé dev (j) | `numeric_mm0e80ek` | numbers | lecture → `projects.estime_j` |
| **Tps passé (j)** | `numeric_mm1zyga2` | numbers | **écriture** ← somme du réalisé |
| Statut d'avancement | `color_mm0e7asn` | status | filtre des projets synchronisables |
| Développeur(s) | `text_mm0f5bwg` | text | ⚠️ texte libre, non exploitable comme clé |
| Subitems | `subtasks_mm0ej7ty` | subtasks | accès aux lots |

### Niveau lot (subitem, board `5091588527`)

| Colonne | ID | Type | Usage |
|---|---|---|---|
| Tps estimé dev | `numeric_mm6afd76` | numbers | lecture → `projects.estime_j` |
| **Tps passé dev** | `numeric_mm6av3hh` | numbers | **écriture** ← somme du réalisé |
| Owner | `person` | people | indicatif |
| Statut | `status` | status | indicatif |

## Règles de synchronisation

1. **Unidirectionnelle** : Timesheet → Monday. Une valeur saisie dans Monday est
   écrasée, jamais relue. Monday n'est pas une source de saisie.
2. **Réalisé uniquement** : ne sommer que les saisies dont `jour <= aujourd'hui`.
   Le prévisionnel ne doit jamais apparaître comme du temps passé.
3. **Clés de rattachement** : `projects.monday_item_id` (projet) et
   `projects.monday_subitem_id` (lot). Les IDs Monday sont stables.
4. **Total projet** = somme des lots rattachés + saisies imputées directement au
   projet.
5. **Jamais synchronisé** : les activités `hors_projet` (absences, formation,
   interne) n'ont pas d'ID Monday.
6. **Périmètre** : uniquement les projets du groupe « Backlog » dont le statut
   d'avancement est actif (En cours, Prêt à démarrer en dev, POC, Étude).

## Point d'attention

Les statuts de phase de Timesheet (`exploration`, `cadrage`, `réalisation`,
`validation`, `exploitation`) sont **distincts** du « Statut d'avancement »
Monday. Aucun des deux ne doit écraser l'autre : ils répondent à des questions
différentes.
