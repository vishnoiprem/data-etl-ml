/**
 * Splits the flat ring list of a multi-polygon into its polygons by winding order, following the
 * same rule as `classifyRings` in the style-spec: a ring wound like the current polygon's exterior
 * starts a new polygon, a ring wound the other way is one of its holes.
 *
 * It differs from the style-spec version in how it treats degenerate rings. That one skips any ring
 * whose signed area is zero, which silently drops rings the decoder returned correctly. Several
 * synthetic fixtures are deliberately degenerate - self-intersecting "bow-ties" with zero area - so
 * a heuristic that discards them hides real regressions. Here a degenerate ring starts a new
 * polygon instead, and no ring is ever dropped.
 *
 * Note that a degenerate exterior has no winding to compare against, so the rings that follow it
 * are treated as its holes. Grouping is a property of the topology vector (partOffsets), not of the
 * coordinates, so for such rings this is a convention rather than something the geometry implies.
 */
export declare function classifyRings(rings: number[][][]): number[][][][];
