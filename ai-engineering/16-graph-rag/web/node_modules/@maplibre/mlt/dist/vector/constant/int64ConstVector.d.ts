import type BitVector from "../flat/bitVector";
import Vector from "../vector";
export declare class Int64ConstVector extends Vector<BigInt64Array | BigUint64Array, bigint> {
    constructor(name: string, value: bigint, sizeOrNullabilityBuffer: number | BitVector, isSigned: boolean);
    protected getValueFromBuffer(_index: number): bigint;
}
