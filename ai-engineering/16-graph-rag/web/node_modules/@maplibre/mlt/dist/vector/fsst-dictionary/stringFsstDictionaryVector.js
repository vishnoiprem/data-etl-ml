import { VariableSizeVector } from "../variableSizeVector";
import { decodeFsst } from "../../decoding/fsstDecoder";
import { decodeString } from "../../decoding/decodingUtils";
export class StringFsstDictionaryVector extends VariableSizeVector {
    constructor(name, indexBuffer, offsetBuffer, dictionaryBuffer, symbolOffsetBuffer, symbolTableBuffer, nullabilityBuffer, 
    /** Cache shared by the FSST child columns of one SharedDict. */
    sharedDictionaryCache) {
        super(name, offsetBuffer, dictionaryBuffer, nullabilityBuffer ?? indexBuffer.length);
        this.indexBuffer = indexBuffer;
        this.symbolOffsetBuffer = symbolOffsetBuffer;
        this.symbolTableBuffer = symbolTableBuffer;
        this.sharedDictionaryCache = sharedDictionaryCache;
    }
    getValueFromBuffer(index) {
        if (this.decodedDictionary == null) {
            this.decodedDictionary = this.sharedDictionaryCache?.decodedDictionary;
            if (this.decodedDictionary == null) {
                this.decodedDictionary = this.decodeDictionary();
                if (this.sharedDictionaryCache) {
                    this.sharedDictionaryCache.decodedDictionary = this.decodedDictionary;
                }
            }
        }
        const offset = this.indexBuffer[index];
        const start = this.offsetBuffer[offset];
        const end = this.offsetBuffer[offset + 1];
        return decodeString(this.decodedDictionary, start, end);
    }
    decodeDictionary() {
        if (this.symbolLengthBuffer == null) {
            this.symbolLengthBuffer = this.offsetToLengthBuffer(this.symbolOffsetBuffer);
        }
        return decodeFsst(this.symbolTableBuffer, this.symbolLengthBuffer, this.dataBuffer);
    }
    // TODO: get rid of that conversion
    offsetToLengthBuffer(offsetBuffer) {
        const lengthBuffer = new Uint32Array(offsetBuffer.length - 1);
        let previousOffset = offsetBuffer[0];
        for (let i = 1; i < offsetBuffer.length; i++) {
            const offset = offsetBuffer[i];
            lengthBuffer[i - 1] = offset - previousOffset;
            previousOffset = offset;
        }
        return lengthBuffer;
    }
}
//# sourceMappingURL=stringFsstDictionaryVector.js.map