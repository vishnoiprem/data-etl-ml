import Vector from "../vector";
export declare abstract class SequenceVector<T extends ArrayBufferView, K> extends Vector<T, K> {
    protected readonly delta: K;
    protected constructor(name: string, baseValueBuffer: T, delta: K, size: number);
}
