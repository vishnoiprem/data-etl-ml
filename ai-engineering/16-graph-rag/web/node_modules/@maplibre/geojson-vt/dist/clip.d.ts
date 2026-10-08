import type { GeoJSONVTInternalFeature, GeoJSONVTOptions } from './definitions';
export declare const enum AxisType {
    X = 0,
    Y = 1
}
/**
 * clip features between two vertical or horizontal axis-parallel lines:
 *     |        |
 *  ___|___     |     /
 * /   |   \____|____/
 *     |        |
 *
 * @param features - the features to clip
 * @param scale - the scale to divide start and end inputs
 * @param start - the start of the clip range
 * @param end - the end of the clip range
 * @param axis - which axis to clip against
 * @param minAll - the minimum for all features in the relevant axis
 * @param maxAll - the maximum for all features in the relevant axis
 */
export declare function clip(features: GeoJSONVTInternalFeature[], scale: number, start: number, end: number, axis: AxisType, minAll: number, maxAll: number, options: GeoJSONVTOptions): GeoJSONVTInternalFeature[] | null;
//# sourceMappingURL=clip.d.ts.map