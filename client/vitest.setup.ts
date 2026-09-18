import "@testing-library/jest-dom/vitest";

/**
 * Radix, which the shadcn components rest on, leans on APIs jsdom does not
 * implement. Without these stubs, opening a `Select` or a `Dialog` raises an
 * error in the tests.
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
