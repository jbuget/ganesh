import "@testing-library/jest-dom/vitest";

/**
 * Radix, sur lequel reposent les composants shadcn, s'appuie sur des API que
 * jsdom n'implemente pas. Sans ces bouchons, ouvrir un `Select` ou un `Dialog`
 * leve une erreur dans les tests.
 */
if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = () => false;
  Element.prototype.setPointerCapture = () => {};
  Element.prototype.releasePointerCapture = () => {};
}

if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {};
}

globalThis.ResizeObserver ??= class {
  observe() {}
  unobserve() {}
  disconnect() {}
};
