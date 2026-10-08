import { FixedSizeVector } from "../fixedSizeVector";
export class Int64FlatVector extends FixedSizeVector {
    getValueFromBuffer(index) {
        return this.dataBuffer[index];
    }
}
//# sourceMappingURL=int64FlatVector.js.map