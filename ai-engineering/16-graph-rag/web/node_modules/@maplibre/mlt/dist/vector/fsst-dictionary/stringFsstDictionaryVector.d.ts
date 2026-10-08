import { VariableSizeVector } from "../variableSizeVector";
import type BitVector from "../flat/bitVector";
/** Mutable cache shared by the FSST child columns of one SharedDict. */
export type FsstDictionaryCache = {
    /** Undefined until one member of the SharedDict group decodes the dictionary on first access. */
    decodedDictionary?: Uint8Array;
};
export declare class StringFsstDictionaryVector extends VariableSizeVector<Uint8Array, string> {
    private readonly indexBuffer;
    private readonly symbolOffsetBuffer;
    private readonly symbolTableBuffer;
    /** Cache shared by the FSST child columns of one SharedDict. */
    private readonly sharedDictionaryCache?;
    private symbolLengthBuffer?;
    private decodedDictionary?;
    constructor(name: string, indexBuffer: Uint32Array, offsetBuffer: Uint32Array, dictionaryBuffer: Uint8Array, symbolOffsetBuffer: Uint32Array, symbolTableBuffer: Uint8Array, nullabilityBuffer?: BitVector, 
    /** Cache shared by the FSST child columns of one SharedDict. */
    sharedDictionaryCache?: FsstDictionaryCache);
    protected getValueFromBuffer(index: number): string;
    private decodeDictionary;
    private offsetToLengthBuffer;
}
