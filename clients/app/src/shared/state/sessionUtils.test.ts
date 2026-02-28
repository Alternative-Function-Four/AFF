import { describe, expect, it } from "vitest";

import { isSessionExpired, mapAuthSession } from "./sessionUtils";

describe("session utils", () => {
  it("maps admin role from auth response", () => {
    const mapped = mapAuthSession({
      access_token: "tok",
      token_type: "bearer",
      expires_at: "2099-01-01T00:00:00+08:00",
      user: {
        id: "u-1",
        display_name: "Admin",
        role: "admin"
      }
    });

    expect(mapped.user.role).toBe("admin");
  });

  it("falls back to member role when backend role is missing", () => {
    const mapped = mapAuthSession({
      access_token: "tok",
      token_type: "bearer",
      expires_at: "2099-01-01T00:00:00+08:00",
      user: {
        id: "u-2",
        display_name: "Member"
      }
    });

    expect(mapped.user.role).toBe("member");
  });

  it("detects expiration with custom clock", () => {
    const now = new Date("2026-02-28T10:00:00.000Z").getTime();

    expect(
      isSessionExpired(
        {
          accessToken: "tok",
          expiresAt: "2026-02-28T09:59:59.000Z",
          user: {
            id: "u-3",
            displayName: "Ari",
            role: "member"
          }
        },
        now
      )
    ).toBe(true);

    expect(
      isSessionExpired(
        {
          accessToken: "tok",
          expiresAt: "2026-02-28T10:30:00.000Z",
          user: {
            id: "u-3",
            displayName: "Ari",
            role: "member"
          }
        },
        now
      )
    ).toBe(false);
  });
});
