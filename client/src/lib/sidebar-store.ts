"use client";

import { useSyncExternalStore } from "react";

const CLE = "timesheet.sidebar-repliee";

/**
 * Preference de repli de la barre laterale.
 *
 * Elle vit hors de React et se lit avec `useSyncExternalStore` : initialiser un
 * etat depuis `localStorage` au premier rendu ferait diverger le serveur et le
 * client, et le lire dans un effet imposerait un `setState` que React
 * deconseille.
 *
 * Aucune valeur n'est mise en cache : `localStorage` est la seule source, ce
 * qui laisse un autre onglet la modifier sans desynchroniser celui-ci.
 */
const subscribers = new Set<() => void>();

function read(): boolean {
  return typeof window !== "undefined" && window.localStorage.getItem(CLE) === "1";
}

function notify() {
  subscribers.forEach((callback) => callback());
}

function subscribe(callback: () => void) {
  subscribers.add(callback);
  window.addEventListener("storage", callback);

  // Le serveur rend toujours la barre depliee. Si la preference dit l'inverse,
  // personne ne previendrait React apres l'hydratation : on le fait ici, au
  // premier abonnement cote client.
  if (read()) queueMicrotask(callback);

  return () => {
    subscribers.delete(callback);
    window.removeEventListener("storage", callback);
  };
}

/** Cote serveur, la barre est toujours depliee : c'est l'etat par defaut. */
function surLeServeur() {
  return false;
}

export function basculerBarreLaterale() {
  window.localStorage.setItem(CLE, read() ? "0" : "1");
  notify();
}

export function useBarreLateraleRepliee(): boolean {
  return useSyncExternalStore(subscribe, read, surLeServeur);
}
