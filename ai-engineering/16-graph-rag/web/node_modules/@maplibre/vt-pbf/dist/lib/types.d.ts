import type Point from '@mapbox/point-geometry';
export interface VectorTileFeatureLike {
    type: 0 | 1 | 2 | 3;
    properties: Record<string, number | string | boolean>;
    id: number | undefined;
    extent: number;
    loadGeometry(): Point[][];
}
export interface VectorTileLayerLike {
    version: number;
    name: string;
    extent: number;
    length: number;
    feature(i: number): VectorTileFeatureLike;
}
export interface VectorTileLike {
    layers: Record<string, VectorTileLayerLike>;
}
