import type { GeoJSONVTFeature } from '@maplibre/geojson-vt';
import type { VectorTileFeatureLike, VectorTileLayerLike, VectorTileLike } from "./types";
export { VectorTileFeatureLike, VectorTileLayerLike, VectorTileLike };
export type Feature = GeoJSONVTFeature;
export interface GeoJSONOptions {
    version: number;
    extent: number;
}
export declare const GEOJSON_TILE_LAYER_NAME = "_geojsonTileLayer";
export declare class GeoJSONWrapper implements VectorTileLayerLike {
    layers: Record<string, VectorTileLayerLike>;
    features: Feature[];
    version: VectorTileLayerLike['version'];
    name: VectorTileLayerLike['name'];
    extent: VectorTileLayerLike['extent'];
    length: VectorTileLayerLike['length'];
    constructor(features: Feature[], options?: GeoJSONOptions);
    feature(i: number): VectorTileFeatureLike;
}
