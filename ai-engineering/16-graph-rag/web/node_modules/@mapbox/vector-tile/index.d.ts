/** classifies an array of rings into polygons with outer rings and holes
 * @param {Point[][]} rings
 */
export function classifyRings(rings: Point[][]): Point[][][];
/** @import {PbfReader} from 'pbf' */
/** @import {Feature} from 'geojson' */
export class VectorTileFeature {
    /**
     * @param {PbfReader} pbf
     * @param {number} end
     * @param {number} extent
     * @param {string[]} keys
     * @param {(number | string | boolean)[]} values
     */
    constructor(pbf: PbfReader, end: number, extent: number, keys: string[], values: (number | string | boolean)[]);
    /** @type {Record<string, number | string | boolean>} */
    properties: Record<string, number | string | boolean>;
    extent: number;
    /** @type {0 | 1 | 2 | 3} */
    type: 0 | 1 | 2 | 3;
    /** @type {number | undefined} */
    id: number | undefined;
    /** @private */
    private _pbf;
    /** @private */
    private _geometry;
    /** @private */
    private _keys;
    /** @private */
    private _values;
    loadGeometry(): Point[][];
    bbox(): number[];
    /**
     * @param {number} x
     * @param {number} y
     * @param {number} z
     * @return {Feature}
     */
    toGeoJSON(x: number, y: number, z: number): Feature;
}
export namespace VectorTileFeature {
    let types: ["Unknown", "Point", "LineString", "Polygon"];
}
export class VectorTileLayer {
    /**
     * @param {PbfReader} pbf
     * @param {number} [end]
     */
    constructor(pbf: PbfReader, end?: number);
    version: number;
    name: string;
    extent: number;
    length: number;
    /** @private */
    private _pbf;
    /** @private
     * @type {string[]} */
    private _keys;
    /** @private
     * @type {(number | string | boolean)[]} */
    private _values;
    /** @private
     * @type {number[]} */
    private _features;
    /** return feature `i` from this layer as a `VectorTileFeature`
     * @param {number} i
     */
    feature(i: number): VectorTileFeature;
}
export class VectorTile {
    /**
     * @param {PbfReader} pbf
     * @param {number} [end]
     */
    constructor(pbf: PbfReader, end?: number);
    layers: Record<string, VectorTileLayer>;
}
import Point from '@mapbox/point-geometry';
import type { Feature } from 'geojson';
import type { PbfReader } from 'pbf';
