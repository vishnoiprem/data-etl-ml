import type BitVector from "./flat/bitVector";
import Vector from "./vector";
export declare abstract class VariableSizeVector<T extends ArrayBufferView, K> extends Vector<T, K> {
    protected offsetBuffer: Uint32Array;
    protected constructor(name: string, offsetBuffer: Uint32Array, dataBuffer: T, sizeOrNullabilityBuffer: number | BitVector);
}
