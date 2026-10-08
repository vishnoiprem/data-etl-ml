import { FixedSizeVector } from "../fixedSizeVector";
export declare class Int64FlatVector extends FixedSizeVector<BigInt64Array | BigUint64Array, bigint> {
    protected getValueFromBuffer(index: number): bigint;
}
