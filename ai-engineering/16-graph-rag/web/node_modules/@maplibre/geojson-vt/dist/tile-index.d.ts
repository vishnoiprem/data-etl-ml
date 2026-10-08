import type { GeoJSONVTInternalFeature, GeoJSONVTOptions, ClusterOrPointFeature, GeoJSONVTTileIndex, GeoJSONVTInternalTile, GeoJSONVTTile } from "./definitions";
export declare class TileIndex implements GeoJSONVTTileIndex {
    private options;
    private tileCoords;
    private total;
    /** @internal */
    tiles: {
        [key: string]: GeoJSONVTInternalTile;
    };
    /** @internal */
    stats: {
        [key: string]: number;
    };
    constructor(options: GeoJSONVTOptions);
    initialize(features: GeoJSONVTInternalFeature[]): void;
    /** {@inheritdoc} */
    updateIndex(source: GeoJSONVTInternalFeature[], affected: GeoJSONVTInternalFeature[], options: GeoJSONVTOptions): void;
    /** {@inheritdoc} */
    getClusterExpansionZoom(_clusterId: number): number | null;
    /** {@inheritdoc} */
    getChildren(_clusterId: number): ClusterOrPointFeature[] | null;
    /** {@inheritdoc} */
    getLeaves(_clusterId: number, _limit?: number, _offset?: number): GeoJSON.Feature<GeoJSON.Point>[] | null;
    /** {@inheritdoc} */
    getTile(z: number, x: number, y: number): GeoJSONVTTile | null;
    /**
     * splits features from a parent tile to sub-tiles.
     * z, x, and y are the coordinates of the parent tile
     * cz, cx, and cy are the coordinates of the target tile
     *
     * If no target tile is specified, splitting stops when we reach the maximum
     * zoom or the number of points is low as specified in the options.
     * @internal
     * @param features - features to split
     * @param z - tile zoom level
     * @param x - tile x coordinate
     * @param y - tile y coordinate
     * @param cz - target tile zoom level
     * @param cx - target tile x coordinate
     * @param cy - target tile y coordinate
     */
    private splitTile;
    /**
     * Invalidates (removes) tiles affected by the provided features
     * @internal
     * @param features
     */
    private invalidateTiles;
}
//# sourceMappingURL=tile-index.d.ts.map