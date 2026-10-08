import { VariableSizeVector } from "../variableSizeVector";
import { decodeString } from "../../decoding/decodingUtils";
export class StringDictionaryVector extends VariableSizeVector {
    constructor(name, indexBuffer, offsetBuffer, dictionaryBuffer, nullabilityBuffer) {
        super(name, offsetBuffer, dictionaryBuffer, nullabilityBuffer ?? indexBuffer.length);
        this.indexBuffer = indexBuffer;
        this.indexBuffer = indexBuffer;
    }
    getValueFromBuffer(index) {
        const offset = this.indexBuffer[index];
        const start = this.offsetBuffer[offset];
        const end = this.offsetBuffer[offset + 1];
        return decodeString(this.dataBuffer, start, end);
    }
}
//# sourceMappingURL=stringDictionaryVector.js.map