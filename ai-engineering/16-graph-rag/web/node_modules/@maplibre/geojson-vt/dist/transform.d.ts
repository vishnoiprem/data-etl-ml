import type { GeoJSONVTInternalTile, GeoJSONVTTile } from "./definitions";
/**
 * Transforms the coordinates of each feature in the given tile from
 * mercator-projected space into (extent x extent) tile space.
 * @param tile - the tile to transform, this gets modified in place
 * @param extent - the tile extent (usually 4096)
 * @returns the transformed tile
 */
export declare function transformTile(tile: GeoJSONVTInternalTile, extent: number): GeoJSONVTTile;
//# sourceMappingURL=transform.d.ts.map