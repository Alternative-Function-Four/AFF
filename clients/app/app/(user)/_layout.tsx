import { Redirect, Slot } from "expo-router";

import { isSessionExpired, useSessionStore } from "../../src/shared/state/session";

export default function UserLayout(): JSX.Element {
  const session = useSessionStore((state) => state.session);

  if (!session || isSessionExpired(session)) {
    return <Redirect href="/(public)/login" />;
  }

  return <Slot />;
}
