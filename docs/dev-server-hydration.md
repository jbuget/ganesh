# Point ouvert : pas d'hydratation avec `next dev`

**Statut : non résolu.** L'application est pleinement fonctionnelle en production ;
seul le serveur de développement est affecté.

## Symptôme

Avec `pnpm dev`, la page est rendue côté serveur (le HTML est correct et complet)
mais React ne s'hydrate jamais :

- aucune clé `__reactFiber$…` sur les nœuds du DOM ;
- les boutons ne réagissent pas, aucun `useState` ne se met à jour ;
- aucune requête n'est émise vers le BFF, donc la matrice reste vide ;
- **aucune erreur** en console, et tous les chunks répondent `200`.

Avec `pnpm build && pnpm start`, tout fonctionne : matrice, saisie au clic,
totaux, navigation entre mois.

## Ce qui a été écarté

| Piste | Verdict |
|---|---|
| Code applicatif | Écarté : un `page.tsx` réduit à un compteur `useState` ne s'hydrate pas davantage |
| `QueryProvider` / React Query | Écarté : un layout minimal sans provider ne change rien |
| Turbopack | Écarté : `next dev --webpack` reproduit exactement le même symptôme |
| Chunk manquant ou 404 | Écarté : les 17 scripts répondent `200` |
| CSP bloquant les scripts inline | Écarté : aucun en-tête CSP, pas de `nonce` |
| Cache de build | Écarté : `rm -rf .next` et redémarrage ne changent rien |
| HTML invalide | Corrigé par ailleurs (voir plus bas), mais sans effet sur ce point |

## Piste restante

L'extension Chrome utilisée pour tester injecte un script dans la page
(`chrome-extension://…/injected.js`). En développement, Next charge en plus son
overlay `next-devtools`, absent en production — c'est la principale différence
entre les deux modes. Une interférence entre les deux est l'hypothèse la plus
plausible, mais elle n'a pas pu être confirmée faute de pouvoir tester dans un
navigateur sans extension.

**Premier test à faire :** ouvrir `http://localhost:3000` dans une fenêtre de
navigation privée, ou dans un navigateur sans extension. Si la page s'hydrate,
le problème vient de l'extension et non du projet.

## Note connexe, celle-ci corrigée

Un vrai défaut a été trouvé et corrigé pendant ce diagnostic : `DayCell` rendait
un `<button>` directement enfant de `<tr>`, ce qui est du HTML invalide et
casse l'hydratation React. Le composant rend désormais `<td><button/></td>`, et
un test verrouille la régression (`DayCell.test.tsx`, « est une cellule de
tableau, pas un bouton nu dans la ligne »).
