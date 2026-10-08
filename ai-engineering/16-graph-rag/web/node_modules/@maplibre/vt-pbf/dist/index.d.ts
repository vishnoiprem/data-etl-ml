import { type Feature, GEOJSON_TILE_LAYER_NAME, type GeoJSONOptions, GeoJSONWrapper } from "./lib/geojson_wrapper";
import type { GeoJSONVTTile } from '@maplibre/geojson-vt';
import type { VectorTileFeatureLike, VectorTileLike, VectorTileLayerLike } from './lib/types';
/**
 * Serialize a vector-tile-js-created tile to pbf
 *
 * @param tile - the tile to serialize
 * @param jsonPrefix - a string prefix to prepend to JSON-stringified non-primitive property values, used to distinguish them from regular string values when parsing the tile later. Default is "".
 * @return uncompressed, pbf-serialized tile data
 */
export declare function fromVectorTileJs(tile: VectorTileLike, jsonPrefix?: string): Uint8Array;
/**
 * Serialized a geojson-vt-created tile to pbf.
 *
 * @param layers - An object mapping layer names to geojson-vt-created vector tile objects
 * @param options - An object specifying the vector-tile specification version and extent that were used to create `layers`.
 * @return uncompressed, pbf-serialized tile data
 */
export declare function fromGeojsonVt(layers: Record<string, GeoJSONVTTile>, options?: GeoJSONOptions): Uint8Array;
export { GeoJSONWrapper, GeoJSONOptions, Feature, GEOJSON_TILE_LAYER_NAME, VectorTileFeatureLike, VectorTileLike, VectorTileLayerLike, };
