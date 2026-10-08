import { type GeoJSONVTSourceDiff } from './difference';
import type { ClusterOrPointFeature, GeoJSONVTOptions, GeoJSONVTTile, SuperclusterOptions } from './definitions';
export declare const defaultOptions: GeoJSONVTOptions;
/**
 * Main class for creating and managing a vector tile index from GeoJSON data.
 */
export declare class GeoJSONVT {
    private options;
    private source?;
    private tileIndex;
    constructor(data: GeoJSON.GeoJSON, options?: GeoJSONVTOptions);
    private initializeIndex;
    /**
     * Given z, x, and y tile coordinates, returns the corresponding tile with geometries in tile coordinates, much like MVT data is stored.
     * @param z - tile zoom level
     * @param x - tile x coordinate
     * @param y - tile y coordinate
     * @returns the transformed tile or null if not found
     */
    getTile(z: number | string, x: number | string, y: number | string): GeoJSONVTTile | null;
    /**
     * Updates the source data feature set using a {@link GeoJSONVTSourceDiff}
     * @param diff - the source diff object
     */
    updateData(diff: GeoJSONVTSourceDiff, filter?: (feature: GeoJSON.Feature) => boolean): void;
    /**
     * Filter an update using a predicate function. Returns the affected and updated source features.
     */
    private filterUpdate;
    /**
     * Returns source data as GeoJSON - only available when `updateable` option is set to true.
     */
    getData(): GeoJSON.GeoJSON;
    /**
     * Update supercluster options and regenerate the index.
     * @param cluster - whether to enable clustering
     * @param clusterOptions - {@link SuperclusterOptions}
     */
    updateClusterOptions(cluster: boolean, clusterOptions: SuperclusterOptions): void;
    /**
     * Returns the zoom level at which a cluster expands into multiple children.
     * @param clusterId - The target cluster id.
     * @returns the expansion zoom or null in case of non-clustered source
     */
    getClusterExpansionZoom(clusterId: number): number | null;
    /**
     * Returns the immediate children (clusters or points) of a cluster as GeoJSON.
     * @param clusterId - The target cluster id.
     * @returns the immediate children or null in case of non-clustered source
     */
    getClusterChildren(clusterId: number): ClusterOrPointFeature[] | null;
    /**
     * Returns leaf point features under a cluster, paginated by `limit` and `offset`.
     * @param clusterId - The target cluster id.
     * @param limit - Maximum number of points to return (defaults to `10`).
     * @param offset - Number of points to skip before collecting results (defaults to `0`).
     * @returns leaf point features under a cluster or null in case of non-clustered source
     */
    getClusterLeaves(clusterId: number, limit: number, offset: number): GeoJSON.Feature<GeoJSON.Point>[] | null;
}
//# sourceMappingURL=geojsonvt.d.ts.map