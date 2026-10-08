import type { GeoJSONVTInternalFeature, GeoJSONVTOptions } from './definitions';
export type GeoJSONVTSourceDiff = {
    /**
     * If true, clear all existing features
     */
    removeAll?: boolean;
    /**
     * Array of feature IDs to remove
     */
    remove?: (string | number)[];
    /**
     * Array of GeoJSON features to add
     */
    add?: GeoJSON.Feature[];
    /**
     * Array of per-feature updates
     */
    update?: GeoJSONVTFeatureDiff[];
};
export type GeoJSONVTFeatureDiff = {
    /**
     * ID of the feature being updated
     */
    id: string | number;
    /**
     * Optional new geometry
     */
    newGeometry?: GeoJSON.Geometry;
    /**
     * Remove all properties if true
     */
    removeAllProperties?: boolean;
    /**
     * Specific properties to delete
     */
    removeProperties?: string[];
    /**
     * Properties to add or update
     */
    addOrUpdateProperties?: {
        key: string;
        value: unknown;
    }[];
};
export type ApplySourceDiffResult = {
    /**
     * The features affected by this update, which should be used to invalidate tiles
     */
    affected: GeoJSONVTInternalFeature[];
    /**
     * The updated source data, which should replace the existing source data in the index
     */
    source: GeoJSONVTInternalFeature[];
};
type HashedGeoJSONVTSourceDiff = {
    removeAll?: boolean | undefined;
    remove: Set<string | number>;
    add: Map<string | number | undefined, GeoJSON.Feature>;
    update: Map<string | number, GeoJSONVTFeatureDiff>;
};
/**
 * Applies a GeoJSON Source Diff to an existing set of simplified features
 * @param source
 * @param dataDiff
 * @param options
 * @returns
 */
export declare function applySourceDiff(source: GeoJSONVTInternalFeature[], dataDiff: GeoJSONVTSourceDiff, options: GeoJSONVTOptions): ApplySourceDiffResult;
/**
 * Convert a GeoJSON Source Diff to an idempotent hashed representation using Sets and Maps
 */
export declare function diffToHashed(diff: GeoJSONVTSourceDiff, options: GeoJSONVTOptions): HashedGeoJSONVTSourceDiff;
export {};
//# sourceMappingURL=difference.d.ts.map