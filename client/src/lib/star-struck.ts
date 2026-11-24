import { createLucideIcon } from "lucide-react";

/**
 * A grin with stars for eyes: the face of a day that stood out.
 *
 * Lucide draws no such face, and the top of the scale needs a mouth and eyes
 * of its own — the rung below already grins, and a scale read by shape must
 * not end on two faces that differ only by their shade. Drawn on Lucide's
 * grid, with its grin, so it sits among the others as one of them.
 */
export const StarStruck = createLucideIcon("star-struck", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "face" }],
  [
    "path",
    {
      d: "M7.084 14.302a5.12 5.12 0 009.833 0 .24.24 0 00-.235-.302H7.32a.24.24 0 00-.235.302",
      key: "grin",
    },
  ],
  [
    "path",
    {
      d: "M8.5 6.4 9.3 8.2 11.1 9 9.3 9.8 8.5 11.6 7.7 9.8 5.9 9 7.7 8.2Z",
      strokeWidth: "1.5",
      key: "left-eye",
    },
  ],
  [
    "path",
    {
      d: "M15.5 6.4 16.3 8.2 18.1 9 16.3 9.8 15.5 11.6 14.7 9.8 12.9 9 14.7 8.2Z",
      strokeWidth: "1.5",
      key: "right-eye",
    },
  ],
]);
