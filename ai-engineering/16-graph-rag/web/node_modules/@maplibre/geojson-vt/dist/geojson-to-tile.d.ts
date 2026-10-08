import type { GeoJSONToTileOptions, GeoJSONVTTile } from './definitions';
/**
 * Converts GeoJSON data directly to a single vector tile without building a tile index.
 *
 * Unlike the {@link GeoJSONVT} class which builds a hierarchical tile index for efficient
 * repeated tile access, this function generates a single tile on-demand. This is useful when:
 * - You only need one specific tile and don't need to query multiple tiles
 * - The source data is already spatially filtered to the tile's bounding box
 * - You want to avoid the overhead of building a full tile index
 *
 * @example
 * ```ts
 * import {geoJSONToTile} from '@maplibre/geojson-vt';
 *
 * const geojson = {
 *   type: 'FeatureCollection',
 *   features: [{
 *     type: 'Feature',
 *     geometry: { type: 'Point', coordinates: [-77.03, 38.90] },
 *     properties: { name: 'Washington, D.C.' }
 *   }]
 * };
 *
 * const tile = geoJSONToTile(geojson, 10, 292, 391, { extent: 4096 });
 * ```
 *
 * @param data - GeoJSON data (Feature, FeatureCollection, or Geometry)
 * @param z - Tile zoom level
 * @param x - Tile x coordinate
 * @param y - Tile y coordinate
 * @param options - Optional configuration for tile generation
 * @returns The generated tile with geometries in tile coordinates, or null if no features
 */
export declare function geoJSONToTile(data: GeoJSON.GeoJSON, z: number, x: number, y: number, options?: GeoJSONToTileOptions): GeoJSONVTTile;
//# sourceMappingURL=geojson-to-tile.d.ts.map