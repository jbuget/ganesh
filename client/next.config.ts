import type { NextConfig } from "next";

import { LEGACY_ROUTES } from "./src/lib/legacy-routes";

const nextConfig: NextConfig = {
  /**
   * Renamed screens keep answering on the address they were published at.
   *
   * These run before the proxy, so a bookmark reaches its screen whether or
   * not there is a session: what follows is the ordinary sign-in, on the new
   * address. Query strings are carried over by Next.
   *
   * Permanent, because the rename is: an address listed here is spent and is
   * never handed to another screen, so there is nothing for a browser to
   * unlearn.
   */
  async redirects() {
    return LEGACY_ROUTES.map((route) => ({ ...route, permanent: true }));
  },
};

export default nextConfig;
