import { SequenceVector } from "./sequenceVector";
export declare class Int32SequenceVector extends SequenceVector<Int32Array | Uint32Array, number> {
    constructor(name: string, baseValue: number, delta: number, size: number, isSigned: boolean);
    protected getValueFromBuffer(index: number): number;
}
