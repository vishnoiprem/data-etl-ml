/** A value that can appear inside a nested property column. `null` means the property is absent. */
export type MapValue = string | number | bigint | boolean | MapValue[] | {
    [key: string]: MapValue;
};
export interface MapEncodingOptions {
    /**
     * Route every integer value through the unsigned dictionary rather than the signed one.
     * The encoder cannot tell a signed from an unsigned source type by looking at a JS value, so by
     * default only values too large for a signed 64-bit stream go to the unsigned dictionary.
     */
    unsignedIntegers?: boolean;
    /** Encode non-integer numbers as 32-bit floats instead of doubles. */
    singlePrecisionFloats?: boolean;
}
/**
 * Encodes nested property (MAP) columns, the inverse of `decodeMapPropertyColumn`.
 *
 * Takes one array of per-feature values per child column - a single column for a standalone map,
 * several when the dictionaries are shared between sibling columns. A `null` entry marks the
 * property as absent for that feature, which is the only form of null the format can express;
 * nulls nested inside a map or list are rejected.
 *
 * Values are collected into one dictionary per type in first-seen order, and the structure is
 * flattened into a token stream of dictionary indices interleaved with control values. Booleans are
 * encoded directly as control values rather than being added to a dictionary.
 *
 * @returns the encoded column and the stream count the decoder must be given.
 */
export declare function encodeMapPropertyColumn(childColumns: (MapValue | null)[][], options?: MapEncodingOptions): {
    data: Uint8Array;
    numStreams: number;
};
