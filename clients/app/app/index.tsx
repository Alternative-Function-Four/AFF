import { Redirect } from "expo-router";

import { env } from "../src/shared/config/env";
import { isSessionExpired, useSessionStore } from "../src/shared/state/session";

export default function IndexRoute(): JSX.Element {
  const session = useSessionStore((state) => state.session);

  if (!session || isSessionExpired(session)) {
    return <Redirect href="/(public)/login" />;
  }

  if (env.enableAdmin && session.user.role === "admin") {
    return <Redirect href="/admin/sources" />;
  }

  return <Redirect href="/(user)/feed" />;
}
