import Vector from "./vector";
export class VariableSizeVector extends Vector {
    constructor(name, offsetBuffer, dataBuffer, sizeOrNullabilityBuffer) {
        super(name, dataBuffer, sizeOrNullabilityBuffer);
        this.offsetBuffer = offsetBuffer;
    }
}
//# sourceMappingURL=variableSizeVector.js.map