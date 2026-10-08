import { VariableSizeVector } from "../variableSizeVector";
import type BitVector from "./bitVector";
export declare class StringFlatVector extends VariableSizeVector<Uint8Array, string> {
    constructor(name: string, offsetBuffer: Uint32Array, dataBuffer: Uint8Array, nullabilityBuffer?: BitVector);
    protected getValueFromBuffer(index: number): string;
}
