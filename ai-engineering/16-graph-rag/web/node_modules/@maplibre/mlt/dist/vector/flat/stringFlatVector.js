import { VariableSizeVector } from "../variableSizeVector";
import { decodeString } from "../../decoding/decodingUtils";
export class StringFlatVector extends VariableSizeVector {
    constructor(name, offsetBuffer, dataBuffer, nullabilityBuffer) {
        super(name, offsetBuffer, dataBuffer, nullabilityBuffer ?? offsetBuffer.length - 1);
    }
    getValueFromBuffer(index) {
        const start = this.offsetBuffer[index];
        const end = this.offsetBuffer[index + 1];
        return decodeString(this.dataBuffer, start, end);
    }
}
//# sourceMappingURL=stringFlatVector.js.map