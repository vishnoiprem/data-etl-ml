import KDBush from 'kdbush';
import type { ClusterOrPointFeature, GeoJSONVTTileIndex, GeoJSONVTInternalFeature, GeoJSONVTInternalPointFeature, GeoJSONVTOptions, GeoJSONVTTile, SuperclusterOptions } from './definitions';
/** @internal */
export type KDBushWithData = KDBush & {
    flatData: number[];
};
export declare const defaultClusterOptions: Required<SuperclusterOptions>;
/**
 * This class allow clustering of geojson points.
 */
export declare class ClusterTileIndex implements GeoJSONVTTileIndex {
    options: Required<SuperclusterOptions>;
    trees: KDBushWithData[];
    stride: number;
    clusterProps: Record<string, unknown>[];
    points: GeoJSONVTInternalPointFeature[];
    constructor(options?: SuperclusterOptions);
    /**
     * Loads GeoJSON point features and builds the internal clustering index.
     * @param points - GeoJSON point features to cluster.
     */
    load(points: GeoJSON.Feature<GeoJSON.Point>[]): void;
    /**
     * @internal
     * Loads internal GeoJSONVT point features from a data source and builds the clustering index.
     * @param features - {@link GeoJSONVTInternalFeature} data source features to filter and cluster.
     */
    initialize(features: GeoJSONVTInternalFeature[]): void;
    /**
     * @internal
     * Updates the cluster data by rebuilding.
     * @param features
     */
    updateIndex(features: GeoJSONVTInternalFeature[], _affected: GeoJSONVTInternalFeature[], options: GeoJSONVTOptions): void;
    private createIndex;
    /**
     * Returns clusters and/or points within a bounding box at a given zoom level.
     * @param bbox - Bounding box in `[westLng, southLat, eastLng, northLat]` order.
     * @param zoom - Zoom level to query.
     */
    getClusters(bbox: [number, number, number, number], zoom: number): ClusterOrPointFeature[];
    private getClustersInternal;
    /**
     * Returns the immediate children (clusters or points) of a cluster as GeoJSON.
     * @param clusterId - The target cluster id.
     */
    getChildren(clusterId: number): ClusterOrPointFeature[];
    /**
     * Returns leaf point features under a cluster, paginated by `limit` and `offset`.
     * @param clusterId - The target cluster id.
     * @param limit - Maximum number of points to return (defaults to `10`).
     * @param offset - Number of points to skip before collecting results (defaults to `0`).
     */
    getLeaves(clusterId: number, limit?: number, offset?: number): GeoJSON.Feature<GeoJSON.Point>[];
    /**
     * Generates a vector-tile-like representation of a single tile.
     * @param z - Tile zoom.
     * @param x - Tile x coordinate.
     * @param y - Tile y coordinate.
     */
    getTile(z: number, x: number, y: number): GeoJSONVTTile | null;
    /**
     * Returns the zoom level at which a cluster expands into multiple children.
     * @param clusterId - The target cluster id.
     */
    getClusterExpansionZoom(clusterId: number): number;
    private appendLeaves;
    private createTree;
    private addTileFeatures;
    private limitZoom;
    private cluster;
    private getOriginId;
    private getOriginZoom;
    private map;
}
//# sourceMappingURL=cluster-tile-index.d.ts.map