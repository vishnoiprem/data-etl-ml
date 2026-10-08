import { type MapEncodingOptions, type MapValue } from "./mapPropertyEncoder";
/** A coordinate pair in tile-local units. */
export type Position = [number, number];
/**
 * The geometry of one feature, in the same nesting GeoJSON uses:
 * a point is a position, a line string a list of positions, a polygon a list of rings, and the
 * multi variants add one more level. Polygon rings are given without a repeated closing position.
 */
export type FeatureGeometry = {
    type: "Point";
    coordinates: Position;
} | {
    type: "MultiPoint";
    coordinates: Position[];
} | {
    type: "LineString";
    coordinates: Position[];
} | {
    type: "MultiLineString";
    coordinates: Position[][];
} | {
    type: "Polygon";
    coordinates: Position[][];
} | {
    type: "MultiPolygon";
    coordinates: Position[][][];
};
/**
 * A property value. Maps and lists of arbitrary depth are allowed and go out as a nested (MAP)
 * column; `null` means the property is absent for that feature.
 */
export type PropertyValue = MapValue | null;
export interface Feature {
    id?: number | bigint;
    geometry: FeatureGeometry;
    properties?: Record<string, PropertyValue>;
}
/** One feature table, the equivalent of a layer in the Java encoder's `LayerSource`. */
export interface Layer {
    name: string;
    features: Feature[];
    extent?: number;
}
/**
 * The physical type a property column is written as. Inferred per column when not given, which is
 * all the synthetic cases need; pass it explicitly to pin a width the values alone do not imply.
 *
 * `map` is the nested column, which holds maps, lists and scalars of any shape. It is inferred for
 * any column holding a map or a list, and can be pinned to keep a column nested even when the
 * values it happens to hold are all scalars.
 */
export type PropertyType = "boolean" | "int32" | "int64" | "uint64" | "float" | "double" | "string" | "map";
export interface EncodeOptions {
    /** Physical type per property name, for columns whose values do not imply one. */
    propertyTypes?: Record<string, PropertyType>;
    /** Dictionary widths for nested columns, which the values alone do not always imply. */
    mapOptions?: MapEncodingOptions;
}
/**
 * Encodes layers into an MLT tile, the inverse of `decodeTile`.
 *
 * This is the plainest encoding the format allows: values go out as varints and plain strings, with
 * no dictionaries, no RLE, no FastPFOR or FSST, no morton-coded or dictionary-encoded vertices and
 * no pre-tessellation. The result is larger than what the Java or Rust encoders produce but is
 * built only from the stream encoders already in this package, and decodes to the same features.
 *
 * Nested (MAP) columns are the one exception: the format stores them as dictionaries of scalars and
 * a stream of tokens, so there is no plainer form to write them in.
 */
export declare function encodeTile(layers: Layer[], options?: EncodeOptions): Uint8Array;
