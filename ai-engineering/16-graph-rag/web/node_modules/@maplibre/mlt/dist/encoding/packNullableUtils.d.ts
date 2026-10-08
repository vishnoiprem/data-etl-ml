import type { TypedArrayInstance } from "../decoding/unpackNullableUtils";
import BitVector from "../vector/flat/bitVector";
export declare function packNullable<T extends TypedArrayInstance>(data: T, presentBits: BitVector | null): T;
export declare function packNullableBoolean(data: Uint8Array, dataSize: number, presentBits: BitVector | null): Uint8Array;
