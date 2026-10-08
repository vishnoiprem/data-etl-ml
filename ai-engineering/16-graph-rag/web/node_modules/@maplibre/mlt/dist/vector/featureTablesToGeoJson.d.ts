import type { Geometry } from "./geometry/geometryVector";
import type FeatureTable from "./featureTable";
/**
 * Converts decoded feature tables into the GeoJSON shape the synthetic fixtures are written in.
 *
 * Shared by the decoder's synthetic tests and the encoder's round trip, so both compare against the
 * fixtures in exactly the same way. The layer name and extent are carried in the properties, since
 * GeoJSON has nowhere else to put them.
 */
export declare function featureTablesToFeatureCollection(featureTables: FeatureTable[]): GeoJSON.FeatureCollection;
/**
 * Converts one decoded geometry to GeoJSON. Multi-polygons need their flat ring list grouped back
 * into polygons, which {@link classifyRings} does from the winding order.
 */
export declare function getGeometry(geometry: Geometry): GeoJSON.Geometry;
