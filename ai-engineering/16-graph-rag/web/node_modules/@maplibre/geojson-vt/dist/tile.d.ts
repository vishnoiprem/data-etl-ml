import type { GeoJSONVTInternalFeature, GeoJSONVTInternalTile, GeoJSONVTOptions } from "./definitions";
export declare const GEOJSONVT_CLIP_START = "geojsonvt_clip_start";
export declare const GEOJSONVT_CLIP_END = "geojsonvt_clip_end";
/**
 * Creates a tile object from the given features
 * @param features - the features to include in the tile
 * @param z
 * @param tx
 * @param ty
 * @param options - the options object
 * @returns the created tile
 */
export declare function createTile(features: GeoJSONVTInternalFeature[], z: number, tx: number, ty: number, options: GeoJSONVTOptions): GeoJSONVTInternalTile;
//# sourceMappingURL=tile.d.ts.map