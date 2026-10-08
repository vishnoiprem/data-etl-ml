import type { GeoJSONVTInternalFeature, GeoJSONVTOptions } from './definitions';
/**
 * converts GeoJSON to internal source features (an intermediate projected JSON vector format with simplification data)
 * @param data
 * @param options
 * @returns
 */
export declare function convertToInternal(data: GeoJSON.GeoJSON, options: GeoJSONVTOptions): GeoJSONVTInternalFeature[];
/**
 * Convert longitude to spherical mercator in [0..1] range
 */
export declare function projectX(x: number): number;
/**
 * Convert latitude to spherical mercator in [0..1] range
 */
export declare function projectY(y: number): number;
//# sourceMappingURL=convert.d.ts.map