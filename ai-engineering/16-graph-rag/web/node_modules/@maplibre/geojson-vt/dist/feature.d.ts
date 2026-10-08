import type { GeoJSONVTInternalFeature, GeoJSONVTInternalLineStringFeature, GeoJSONVTInternalMultiLineStringFeature, GeoJSONVTInternalMultiPointFeature, GeoJSONVTInternalMultiPolygonFeature, GeoJSONVTInternalPointFeature, GeoJSONVTInternalPolygonFeature, SliceArray } from "./definitions";
type FeatureTypeMap = {
    Point: GeoJSONVTInternalPointFeature["geometry"];
    MultiPoint: GeoJSONVTInternalMultiPointFeature["geometry"];
    LineString: GeoJSONVTInternalLineStringFeature["geometry"];
    MultiLineString: GeoJSONVTInternalMultiLineStringFeature["geometry"];
    Polygon: GeoJSONVTInternalPolygonFeature["geometry"];
    MultiPolygon: GeoJSONVTInternalMultiPolygonFeature["geometry"];
};
/**
 *
 * @param id - the feature's ID
 * @param type - the feature's type
 * @param geom - the feature's geometry
 * @param tags - the feature's properties
 * @returns the created feature
 */
export declare function createFeature<T extends GeoJSONVTInternalFeature["type"]>(id: number | string | undefined, type: T, geom: FeatureTypeMap[T], tags: GeoJSON.GeoJsonProperties): GeoJSONVTInternalFeature;
export declare function optimizeLineMemory(line: SliceArray): void;
export {};
//# sourceMappingURL=feature.d.ts.map