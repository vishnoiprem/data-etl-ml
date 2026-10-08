import { VariableSizeVector } from "../variableSizeVector";
import type BitVector from "../flat/bitVector";
export declare class StringDictionaryVector extends VariableSizeVector<Uint8Array, string> {
    private readonly indexBuffer;
    constructor(name: string, indexBuffer: Uint32Array, offsetBuffer: Uint32Array, dictionaryBuffer: Uint8Array, nullabilityBuffer?: BitVector);
    protected getValueFromBuffer(index: number): string;
}
