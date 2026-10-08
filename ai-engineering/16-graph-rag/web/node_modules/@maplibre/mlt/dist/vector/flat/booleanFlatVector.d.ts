import type BitVector from "./bitVector";
import Vector from "../vector";
export declare class BooleanFlatVector extends Vector<Uint8Array, boolean> {
    private readonly dataVector;
    constructor(name: string, dataVector: BitVector, sizeOrNullabilityBuffer: number | BitVector);
    protected getValueFromBuffer(index: number): boolean;
}
