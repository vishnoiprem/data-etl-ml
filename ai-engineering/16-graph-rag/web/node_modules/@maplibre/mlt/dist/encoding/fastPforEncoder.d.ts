/**
 * Internal workspace for the FastPFOR encoder.
 * Exposed so callers can avoid allocations.
 * Use one workspace per concurrent encode call.
 */
export type FastPforEncoderWorkspace = {
    dataToBePacked: Array<Uint32Array | undefined>;
    dataPointers: Int32Array;
    byteContainer: Uint8Array;
    bitWidthFrequencies: Int32Array;
    bestBitWidthPlan: Int32Array;
};
export declare function fastPack32(inValues: Uint32Array, inPos: number, out: Uint32Array, outPos: number, bitWidth: number): void;
export declare function createFastPforEncoderWorkspace(): FastPforEncoderWorkspace;
/**
 * Encodes an int32 stream using the FastPFOR wire format (pages + VByte tail).
 */
export declare function encodeFastPforInt32WithWorkspace(values: Uint32Array, workspace: FastPforEncoderWorkspace): Uint32Array;
