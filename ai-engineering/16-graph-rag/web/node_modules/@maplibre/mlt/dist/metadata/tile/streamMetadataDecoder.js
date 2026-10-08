import { LogicalLevelTechnique } from "./logicalLevelTechnique";
import { PhysicalLevelTechnique } from "./physicalLevelTechnique";
import { decodeVarintInt32 } from "../../decoding/integerDecodingUtils";
import { PhysicalStreamType } from "./physicalStreamType";
import { DictionaryType } from "./dictionaryType";
import { OffsetType } from "./offsetType";
import { LengthType } from "./lengthType";
const PHYSICAL_STREAM_TYPE_BY_ID = [
    PhysicalStreamType.PRESENT,
    PhysicalStreamType.DATA,
    PhysicalStreamType.OFFSET,
    PhysicalStreamType.LENGTH,
];
const LOGICAL_LEVEL_TECHNIQUE_BY_ID = [
    LogicalLevelTechnique.NONE,
    LogicalLevelTechnique.DELTA,
    LogicalLevelTechnique.COMPONENTWISE_DELTA,
    LogicalLevelTechnique.RLE,
    LogicalLevelTechnique.MORTON,
];
const PHYSICAL_LEVEL_TECHNIQUE_BY_ID = [
    PhysicalLevelTechnique.NONE,
    PhysicalLevelTechnique.FAST_PFOR,
    PhysicalLevelTechnique.VARINT,
];
const DICTIONARY_TYPE_BY_ID = [
    DictionaryType.NONE,
    DictionaryType.SINGLE,
    DictionaryType.SHARED,
    DictionaryType.VERTEX,
    DictionaryType.MORTON,
    DictionaryType.FSST,
];
const OFFSET_TYPE_BY_ID = [
    OffsetType.VERTEX,
    OffsetType.INDEX,
    OffsetType.STRING,
    OffsetType.KEY,
];
const LENGTH_TYPE_BY_ID = [
    LengthType.VAR_BINARY,
    LengthType.GEOMETRIES,
    LengthType.PARTS,
    LengthType.RINGS,
    LengthType.TRIANGLES,
    LengthType.SYMBOL,
    LengthType.DICTIONARY,
];
export function decodeStreamMetadata(tile, offset) {
    const streamMetadata = decodeStreamMetadataInternal(tile, offset);
    if (streamMetadata.logicalLevelTechnique1 === LogicalLevelTechnique.MORTON) {
        return decodePartialMortonEncodedStreamMetadata(streamMetadata, tile, offset);
    }
    if ((LogicalLevelTechnique.RLE === streamMetadata.logicalLevelTechnique1 ||
        LogicalLevelTechnique.RLE === streamMetadata.logicalLevelTechnique2) &&
        PhysicalLevelTechnique.NONE !== streamMetadata.physicalLevelTechnique) {
        return decodePartialRleEncodedStreamMetadata(streamMetadata, tile, offset);
    }
    return streamMetadata;
}
function decodePartialMortonEncodedStreamMetadata(streamMetadata, tile, offset) {
    const mortonInfo = decodeVarintInt32(tile, offset, 2);
    return {
        physicalStreamType: streamMetadata.physicalStreamType,
        logicalStreamType: streamMetadata.logicalStreamType,
        logicalLevelTechnique1: streamMetadata.logicalLevelTechnique1,
        logicalLevelTechnique2: streamMetadata.logicalLevelTechnique2,
        physicalLevelTechnique: streamMetadata.physicalLevelTechnique,
        numValues: streamMetadata.numValues,
        byteLength: streamMetadata.byteLength,
        decompressedCount: streamMetadata.decompressedCount,
        numBits: mortonInfo[0],
        coordinateShift: mortonInfo[1],
    };
}
function decodePartialRleEncodedStreamMetadata(streamMetadata, tile, offset) {
    const rleInfo = decodeVarintInt32(tile, offset, 2);
    return {
        physicalStreamType: streamMetadata.physicalStreamType,
        logicalStreamType: streamMetadata.logicalStreamType,
        logicalLevelTechnique1: streamMetadata.logicalLevelTechnique1,
        logicalLevelTechnique2: streamMetadata.logicalLevelTechnique2,
        physicalLevelTechnique: streamMetadata.physicalLevelTechnique,
        numValues: streamMetadata.numValues,
        byteLength: streamMetadata.byteLength,
        decompressedCount: rleInfo[1],
        runs: rleInfo[0],
        numRleValues: rleInfo[1],
    };
}
function decodeStreamMetadataInternal(tile, offset) {
    const stream_type = tile[offset.get()];
    const physicalStreamType = PHYSICAL_STREAM_TYPE_BY_ID[stream_type >> 4];
    let logicalStreamType = {};
    switch (physicalStreamType) {
        case PhysicalStreamType.DATA:
            logicalStreamType = {
                dictionaryType: DICTIONARY_TYPE_BY_ID[stream_type & 0xf],
            };
            break;
        case PhysicalStreamType.OFFSET:
            logicalStreamType = {
                offsetType: OFFSET_TYPE_BY_ID[stream_type & 0xf],
            };
            break;
        case PhysicalStreamType.LENGTH:
            logicalStreamType = {
                lengthType: LENGTH_TYPE_BY_ID[stream_type & 0xf],
            };
            break;
    }
    offset.increment();
    const encodings_header = tile[offset.get()];
    const llt1 = LOGICAL_LEVEL_TECHNIQUE_BY_ID[encodings_header >> 5];
    const llt2 = LOGICAL_LEVEL_TECHNIQUE_BY_ID[(encodings_header >> 2) & 0x7];
    const plt = PHYSICAL_LEVEL_TECHNIQUE_BY_ID[encodings_header & 0x3];
    offset.increment();
    const sizeInfo = decodeVarintInt32(tile, offset, 2);
    const numValues = sizeInfo[0];
    const byteLength = sizeInfo[1];
    return {
        physicalStreamType,
        logicalStreamType,
        logicalLevelTechnique1: llt1,
        logicalLevelTechnique2: llt2,
        physicalLevelTechnique: plt,
        numValues,
        byteLength,
        decompressedCount: numValues,
    };
}
//# sourceMappingURL=streamMetadataDecoder.js.map