import type { GeoJSONVTInternalFeature } from './definitions';
/**
 * Converts internal source features back to GeoJSON format.
 */
export declare function convertToGeoJSON(source: GeoJSONVTInternalFeature[]): GeoJSON.GeoJSON;
/**
 * Converts a single internal feature to GeoJSON format.
 */
export declare function featureToGeoJSON(feature: GeoJSONVTInternalFeature): GeoJSON.Feature;
export declare function unprojectPoints(coords: number[] | Float64Array): GeoJSON.Position[];
/**
 * Convert spherical mercator in [0..1] range to longitude
 */
export declare function unprojectX(x: number): number;
/**
 * Convert spherical mercator in [0..1] range to latitude
 */
export declare function unprojectY(y: number): number;
//# sourceMappingURL=deconvert.d.ts.map