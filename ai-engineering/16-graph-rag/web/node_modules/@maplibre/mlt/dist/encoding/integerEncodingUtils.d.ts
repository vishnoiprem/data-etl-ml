import IntWrapper from "../decoding/intWrapper";
export declare function encodeVarintInt32Value(value: number, dst: Uint8Array, offset: IntWrapper): void;
export declare function encodeVarintInt32(values: Uint32Array): Uint8Array;
export declare function encodeVarintInt64(values: BigUint64Array): Uint8Array;
export declare function encodeVarintFloat64(values: Float64Array): Uint8Array;
export declare function encodeFastPfor(values: Uint32Array): Uint8Array;
export declare function encodeZigZagInt32Value(value: number): number;
export declare function encodeZigZagInt64Value(value: bigint): bigint;
export declare function encodeZigZagFloat64Value(n: number): number;
export declare function encodeZigZagInt32(data: Int32Array): Uint32Array;
export declare function encodeZigZagInt64(data: BigInt64Array): BigUint64Array;
export declare function encodeZigZagFloat64(data: Float64Array): void;
export declare function encodeUnsignedRleInt32(input: Uint32Array): {
    data: Uint32Array;
    runs: number;
};
export declare function encodeUnsignedRleInt64(input: BigInt64Array): {
    data: BigUint64Array;
    runs: number;
};
export declare function encodeUnsignedRleFloat64(input: Float64Array): {
    data: Float64Array;
    runs: number;
};
export declare function encodeZigZagDeltaInt32(data: Int32Array): Uint32Array;
export declare function encodeZigZagDeltaInt64(data: BigInt64Array): BigUint64Array;
export declare function encodeZigZagDeltaFloat64(data: Float64Array): void;
export declare function encodeZigZagRleInt32(input: Int32Array): {
    data: Uint32Array;
    runs: number;
    numTotalValues: number;
};
export declare function encodeZigZagRleInt64(input: BigInt64Array): {
    data: BigUint64Array;
    runs: number;
    numTotalValues: number;
};
export declare function encodeZigZagRleFloat64(input: Float64Array): {
    data: Float64Array;
    runs: number;
    numTotalValues: number;
};
/**
 * This is not really a encode, but more of a decode method...
 */
export declare function encodeDeltaInt32(data: Int32Array | Uint32Array): void;
export declare function encodeComponentwiseDeltaVec2(data: Int32Array): Uint32Array;
export declare function encodeComponentwiseDeltaVec2Scaled(data: Int32Array, scale: number): Uint32Array;
export declare function encodeZigZagRleDeltaInt32(values: Int32Array | number[]): {
    data: Uint32Array;
    runs: number;
    numTotalValues: number;
};
export declare function encodeRleDeltaInt32(values: Uint32Array | number[]): {
    data: Uint32Array;
    runs: number;
    numTotalValues: number;
};
export declare function encodeDeltaRleInt32(input: Int32Array): {
    data: Uint32Array;
    runs: number;
    numValues: number;
};
export declare function encodeDeltaRleInt64(input: BigInt64Array): {
    data: BigUint64Array;
    runs: number;
    numValues: number;
};
