/**
 * FastPFOR decoding implementation.
 *
 * @remarks
 * Terminology note: "exceptions" in FastPFOR refer to **outlier values** within a block that do not fit in the
 * chosen base bit-width for that block. These are stored in separate "exception streams" and later applied back
 * to the unpacked base values. This is unrelated to JavaScript/TypeScript runtime exceptions.
 */
/**
 * Workspace for the FastPFOR decoder.
 */
export type FastPforDecoderWorkspace = {
    dataToBePacked: Array<Uint32Array>;
    dataPointers: Int32Array;
    byteContainer: Uint8Array;
    byteContainerI32?: Int32Array;
    exceptionSizes: Int32Array;
};
/**
 * Workspace for decoding the FastPFOR *wire format* (big-endian int32 words).
 *
 * @remarks
 * This workspace owns:
 * - a scratch `encodedWords` buffer to materialize big-endian words
 * - the reusable `FastPforDecoderWorkspace` used by `decodeFastPforInt32`
 *
 * The caller is responsible for creating and reusing this object.
 */
export type FastPforWireDecodeWorkspace = {
    encodedWords: Uint32Array;
    decoderWorkspace: FastPforDecoderWorkspace;
};
/**
 * Creates an isolated workspace for decoding.
 * Reusing a workspace across calls avoids repeated allocations.
 */
export declare function createDecoderWorkspace(): FastPforDecoderWorkspace;
export declare function createFastPforWireDecodeWorkspace(initialEncodedWordCapacity?: number): FastPforWireDecodeWorkspace;
export declare function ensureFastPforWireEncodedWordsCapacity(workspace: FastPforWireDecodeWorkspace, requiredWordCount: number): Uint32Array;
/**
 * Decodes a sequence of FastPFOR-encoded integers.
 *
 * @param encoded The input buffer containing FastPFOR encoded data.
 * @param numValues The number of integers expected to be decoded.
 * @param workspace Optional workspace for reuse across calls. If omitted, a new workspace is created per call.
 */
export declare function decodeFastPforInt32(encoded: Uint32Array, numValues: number, workspace?: FastPforDecoderWorkspace): Uint32Array;
