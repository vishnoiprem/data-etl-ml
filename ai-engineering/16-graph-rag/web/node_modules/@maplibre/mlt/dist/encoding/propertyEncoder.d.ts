/**
 * Encodes INT_32 values with NONE encoding (no delta, no RLE)
 */
export declare function encodeInt32NoneColumn(values: Int32Array): Uint8Array;
/**
 * Encodes INT_32 values with DELTA encoding
 */
export declare function encodeInt32DeltaColumn(values: Int32Array): Uint8Array;
/**
 * Encodes INT_32 values with RLE encoding
 * @param runs - Array of [runLength, value] pairs
 */
export declare function encodeInt32RleColumn(runs: Array<[number, number]>): Uint8Array;
/**
 * Encodes INT_32 values with DELTA+RLE encoding
 * @param runs - Array of [runLength, deltaValue] pairs, where first value is the base
 */
export declare function encodeInt32DeltaRleColumn(runs: Array<[number, number]>): Uint8Array;
/**
 * Encodes nullable INT_32 values
 */
export declare function encodeInt32NullableColumn(values: (number | null)[]): Uint8Array;
/**
 * Encodes UINT_32 values (no zigzag encoding)
 */
export declare function encodeUint32Column(values: Uint32Array): Uint8Array;
/**
 * Encodes INT_64 values with NONE encoding
 */
export declare function encodeInt64NoneColumn(values: BigInt64Array): Uint8Array;
/**
 * Encodes INT_64 values with DELTA encoding
 */
export declare function encodeInt64DeltaColumn(values: BigInt64Array): Uint8Array;
/**
 * Encodes INT_64 values with RLE encoding
 */
export declare function encodeInt64RleColumn(runs: Array<[number, bigint]>): Uint8Array;
/**
 * Encodes INT_64 values with DELTA+RLE encoding
 */
export declare function encodeInt64DeltaRleColumn(runs: Array<[number, bigint]>): Uint8Array;
/**
 * Encodes nullable INT_64 values
 */
export declare function encodeInt64NullableColumn(values: (bigint | null)[]): Uint8Array;
/**
 * Encodes UINT_64 values (no zigzag encoding)
 */
export declare function encodeUint64Column(values: BigUint64Array): Uint8Array;
/**
 * Encodes nullable UINT_64 values
 */
export declare function encodeUint64NullableColumn(values: (bigint | null)[]): Uint8Array;
/**
 * Encodes FLOAT values
 */
export declare function encodeFloatColumn(values: Float32Array): Uint8Array;
/**
 * Encodes nullable FLOAT values
 */
export declare function encodeFloatNullableColumn(values: (number | null)[]): Uint8Array;
/**
 * Encodes DOUBLE values
 */
export declare function encodeDoubleColumn(values: Float64Array): Uint8Array;
/**
 * Encodes nullable DOUBLE values
 */
export declare function encodeDoubleNullableColumn(values: (number | null)[]): Uint8Array;
/**
 * Encodes BOOLEAN values
 */
export declare function encodeBooleanColumn(values: boolean[]): Uint8Array;
/**
 * Encodes nullable BOOLEAN values
 */
export declare function encodeBooleanNullableColumn(values: (boolean | null)[]): Uint8Array;
