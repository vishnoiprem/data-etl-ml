/**
 * Encodes a single typeCode as a varint.
 */
export declare function encodeTypeCode(typeCode: number): Uint8Array;
/**
 * Encodes a field name as a length-prefixed UTF-8 string.
 */
export declare function encodeFieldName(name: string): Uint8Array;
/**
 * Encodes a child count as a varint.
 */
export declare function encodeChildCount(count: number): Uint8Array;
/**
 * Computes typeCode for a scalar field.
 */
export declare function scalarTypeCode(scalarType: number, nullable: boolean): number;
