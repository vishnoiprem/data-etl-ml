import type BitVector from "./flat/bitVector";
export default abstract class Vector<T extends ArrayBufferView = ArrayBufferView, K = unknown> {
    private readonly _name;
    protected readonly dataBuffer: T;
    protected nullabilityBuffer: BitVector | null;
    protected _size: number;
    constructor(_name: string, dataBuffer: T, sizeOrNullabilityBuffer: number | BitVector);
    getValue(index: number): K | null;
    has(index: number): boolean;
    get name(): string;
    get size(): number;
    protected abstract getValueFromBuffer(index: number): K;
}
