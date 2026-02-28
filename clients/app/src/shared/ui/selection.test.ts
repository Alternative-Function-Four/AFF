import { describe, expect, it } from "vitest";

import { dedupeIds, setAllSelections, toggleSelection } from "./selection";

describe("selection helpers", () => {
  it("dedupes repeated ids", () => {
    expect(dedupeIds(["s-1", "s-2", "s-1"])).toEqual(["s-1", "s-2"]);
  });

  it("toggles a single id", () => {
    expect(toggleSelection(["s-1"], "s-2")).toEqual(["s-1", "s-2"]);
    expect(toggleSelection(["s-1", "s-2"], "s-2")).toEqual(["s-1"]);
  });

  it("selects and clears all ids", () => {
    const ids = ["s-1", "s-2", "s-2"];
    expect(setAllSelections(ids, true)).toEqual(["s-1", "s-2"]);
    expect(setAllSelections(ids, false)).toEqual([]);
  });
});
