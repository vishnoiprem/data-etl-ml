import { ObjectFlatVector } from "../vector/flat/objectFlatVector";
import { decodeStreamMetadata } from "../metadata/tile/streamMetadataDecoder";
import { PhysicalStreamType } from "../metadata/tile/physicalStreamType";
import { MapMask } from "../metadata/tile/mapMask";
import { MapControlValue } from "../metadata/tile/mapControlValue";
import { decodeBooleanRle, decodeDoublesLE, decodeFloatsLE } from "./decodingUtils";
import { decodeSignedInt32Stream, decodeSignedInt64Stream, decodeUnsignedInt32Stream, decodeUnsignedInt64Stream, } from "./integerStreamDecoder";
import { decodeString } from "./stringDecoder";
import BitVector from "../vector/flat/bitVector";
/**
 * Decodes a nested property (MAP) column into one vector per child column.
 *
 * The column is stored as a length stream (values per feature), a dictionary stream per value type
 * present, an optional presence stream, and a data stream of dictionary indices interleaved with
 * the control tokens that describe the map/list structure.
 *
 * Ported from the Java reference implementation (`MapPropertyDecoder`).
 */
export function decodeMapPropertyColumn(data, offset, columnMetadata, numStreams) {
    const columnNames = getMapColumnNames(columnMetadata);
    if (numStreams === 0) {
        return columnNames.map((name) => new ObjectFlatVector(name, []));
    }
    const streams = decodeMapStreams(data, offset, numStreams);
    const totalCounts = streams.presentStream ? streams.presentCount : streams.lengthStream.length;
    const featureCount = totalCounts / columnNames.length;
    const vectors = [];
    let countsCursor = 0;
    let valuesCursor = 0;
    for (let childIndex = 0; childIndex < columnNames.length; childIndex++) {
        const child = decodeChildColumn(streams, childIndex, featureCount, countsCursor, valuesCursor);
        vectors.push(new ObjectFlatVector(columnNames[childIndex], child.value, child.nullabilityBuffer));
        countsCursor = child.countsEnd;
        valuesCursor = child.valuesEnd;
    }
    return vectors;
}
/**
 * A single map column carries its own name. A shared column carries one child per sibling, whose
 * full name is the parent name followed by the child name.
 */
function getMapColumnNames(columnMetadata) {
    const children = columnMetadata.type === "complexType" ? columnMetadata.complexType.children : undefined;
    if (!children || children.length === 0) {
        return [columnMetadata.name];
    }
    return children.map((child) => columnMetadata.name + (child.name ?? ""));
}
/** Reads the stream mask and every stream it announces, in the order the encoder wrote them. */
function decodeMapStreams(data, offset, numStreams) {
    const dictionaryMask = data[offset.get()];
    offset.add(1);
    // The length stream is the only mandatory one.
    const lengthStream = decodeUnsignedInt32Stream(data, offset, decodeStreamMetadata(data, offset));
    let remainingStreams = numStreams - 1;
    const dictionary = [];
    if (dictionaryMask & MapMask.STRING) {
        remainingStreams -= decodeStringDictionary(data, offset, dictionary);
    }
    remainingStreams -= decodeIntegerDictionaries(data, offset, dictionaryMask, dictionary);
    remainingStreams -= decodeFloatingPointDictionaries(data, offset, dictionaryMask, dictionary);
    let presentStream;
    let presentCount = 0;
    if (dictionaryMask & MapMask.PRESENCE) {
        const presence = decodePresenceStream(data, offset);
        presentStream = presence.value;
        presentCount = presence.count;
        remainingStreams--;
    }
    let flattenedValues = new Uint32Array(0);
    if (remainingStreams > 0) {
        flattenedValues = decodeUnsignedInt32Stream(data, offset, decodeStreamMetadata(data, offset));
        remainingStreams--;
    }
    if (remainingStreams !== 0) {
        throw new Error(`Unexpected number of remaining streams while decoding map column: ${remainingStreams}`);
    }
    return { lengthStream, dictionary, presentStream, presentCount, flattenedValues };
}
/** @returns the number of streams consumed, which the string encoding decides for itself. */
function decodeStringDictionary(data, offset, dictionary) {
    const stringStreamCount = data[offset.get()];
    offset.add(1);
    const strings = decodeString("", data, offset, stringStreamCount);
    if (strings) {
        for (let i = 0; i < strings.size; i++) {
            dictionary.push(strings.getValue(i));
        }
    }
    return stringStreamCount;
}
/**
 * Signed and unsigned integers each get at most one stream, whose width the encoder chose to fit
 * the widest value.
 *
 * @returns the number of streams consumed.
 */
function decodeIntegerDictionaries(data, offset, dictionaryMask, dictionary) {
    let consumed = 0;
    if (dictionaryMask & MapMask.INT32) {
        pushAll(dictionary, decodeSignedInt32Stream(data, offset, decodeStreamMetadata(data, offset)));
        consumed++;
    }
    else if (dictionaryMask & MapMask.INT64) {
        pushAll(dictionary, decodeSignedInt64Stream(data, offset, decodeStreamMetadata(data, offset)));
        consumed++;
    }
    if (dictionaryMask & MapMask.UINT32) {
        pushAll(dictionary, decodeUnsignedInt32Stream(data, offset, decodeStreamMetadata(data, offset)));
        consumed++;
    }
    else if (dictionaryMask & MapMask.UINT64) {
        pushAll(dictionary, decodeUnsignedInt64Stream(data, offset, decodeStreamMetadata(data, offset)));
        consumed++;
    }
    return consumed;
}
/** @returns the number of streams consumed. */
function decodeFloatingPointDictionaries(data, offset, dictionaryMask, dictionary) {
    let consumed = 0;
    if (dictionaryMask & MapMask.FLOAT) {
        const streamMetadata = decodeStreamMetadata(data, offset);
        pushAll(dictionary, decodeFloatsLE(data, offset, streamMetadata.numValues));
        consumed++;
    }
    if (dictionaryMask & MapMask.DOUBLE) {
        const streamMetadata = decodeStreamMetadata(data, offset);
        pushAll(dictionary, decodeDoublesLE(data, offset, streamMetadata.numValues));
        consumed++;
    }
    return consumed;
}
function decodePresenceStream(data, offset) {
    const streamMetadata = decodeStreamMetadata(data, offset);
    if (streamMetadata.physicalStreamType !== PhysicalStreamType.PRESENT) {
        throw new Error(`Expected PRESENT stream for map column but found: ${streamMetadata.physicalStreamType}`);
    }
    const count = streamMetadata.numValues;
    const streamDataStart = offset.get();
    const value = new BitVector(decodeBooleanRle(data, count, streamMetadata.byteLength, offset), count);
    offset.set(streamDataStart + streamMetadata.byteLength);
    return { value, count };
}
/**
 * Decodes one child column's per-feature values.
 *
 * Lengths, presence bits and tokens are all laid out child-major, so each child picks up where the
 * previous one left off.
 */
function decodeChildColumn(streams, childIndex, featureCount, countsCursor, valuesCursor) {
    const { lengthStream, flattenedValues, presentStream, dictionary } = streams;
    const presentOffset = childIndex * featureCount;
    let presentInChild = featureCount;
    let nullabilityBuffer;
    if (presentStream) {
        nullabilityBuffer = new BitVector(new Uint8Array(Math.ceil(featureCount / 8)), featureCount);
        presentInChild = 0;
        for (let i = 0; i < featureCount; i++) {
            if (presentStream.get(presentOffset + i)) {
                nullabilityBuffer.set(i, true);
                presentInChild++;
            }
        }
    }
    const countsEnd = countsCursor + presentInChild;
    if (countsEnd > lengthStream.length) {
        throw new Error("Merged map counts underflow while decoding child streams");
    }
    const value = new Array(featureCount);
    let countCursor = countsCursor;
    let flattenedIndex = valuesCursor;
    for (let featureIndex = 0; featureIndex < featureCount; featureIndex++) {
        if (presentStream && !presentStream.get(presentOffset + featureIndex)) {
            value[featureIndex] = null;
            continue;
        }
        const endIndex = flattenedIndex + lengthStream[countCursor++];
        if (endIndex > flattenedValues.length) {
            throw new Error("Map value stream underflow while decoding feature payload");
        }
        const decoded = decodeFeatureValue(flattenedValues, flattenedIndex, endIndex, dictionary);
        value[featureIndex] = decoded.value;
        flattenedIndex = decoded.nextIndex;
    }
    let childValueCount = 0;
    for (let i = countsCursor; i < countsEnd; i++)
        childValueCount += lengthStream[i];
    const valuesEnd = valuesCursor + childValueCount;
    if (flattenedIndex !== valuesEnd) {
        throw new Error("Unused flattened map values remain after decode");
    }
    return { value, nullabilityBuffer, countsEnd, valuesEnd };
}
/**
 * A feature's payload is a bare sequence of map entries, unless it is a single token - a root-level
 * scalar - or opens with a list token. Those two shapes are what distinguish it from map entries.
 */
function decodeFeatureValue(flattenedValues, startIndex, endIndex, dictionary) {
    if (endIndex - startIndex === 1 || flattenedValues[startIndex] === MapControlValue.START_LIST) {
        return decodeValue(flattenedValues, startIndex, endIndex, dictionary);
    }
    return decodeMapEntries(flattenedValues, startIndex, endIndex, dictionary);
}
function decodeMapEntries(flattenedValues, startIndex, endIndex, dictionary) {
    // Keys come off the wire, so the object is created without a prototype: a `__proto__` key would
    // otherwise reassign the prototype instead of being stored as an entry.
    const value = Object.create(null);
    let index = startIndex;
    while (index < endIndex) {
        const key = decodeScalarByIndex(flattenedValues[index++], dictionary);
        if (typeof key !== "string") {
            throw new Error(`Map key dictionary index does not resolve to a string: ${key}`);
        }
        const decoded = decodeValue(flattenedValues, index, endIndex, dictionary);
        value[key] = decoded.value;
        index = decoded.nextIndex;
    }
    return { value, nextIndex: index };
}
function decodeValue(flattenedValues, startIndex, endIndex, dictionary) {
    if (startIndex >= endIndex) {
        throw new Error("Unexpected end of map value stream");
    }
    const token = flattenedValues[startIndex];
    if (token === MapControlValue.FALSE)
        return { value: false, nextIndex: startIndex + 1 };
    if (token === MapControlValue.TRUE)
        return { value: true, nextIndex: startIndex + 1 };
    if (token === MapControlValue.START_MAP) {
        const valueEndIndex = decodeNestedPayloadEnd(flattenedValues, startIndex, endIndex);
        const nested = decodeMapEntries(flattenedValues, startIndex + 2, valueEndIndex, dictionary);
        return { value: nested.value, nextIndex: valueEndIndex };
    }
    if (token === MapControlValue.START_LIST) {
        const valueEndIndex = decodeNestedPayloadEnd(flattenedValues, startIndex, endIndex);
        const value = [];
        let index = startIndex + 2;
        while (index < valueEndIndex) {
            const nested = decodeValue(flattenedValues, index, valueEndIndex, dictionary);
            value.push(nested.value);
            index = nested.nextIndex;
        }
        return { value, nextIndex: valueEndIndex };
    }
    return { value: decodeScalarByIndex(token, dictionary), nextIndex: startIndex + 1 };
}
/**
 * Reads the length prefix of a nested payload and returns where it ends, the counterpart of
 * `encodeNestedPayloadLength`. The length covers the two header tokens as well.
 */
function decodeNestedPayloadEnd(flattenedValues, startIndex, endIndex) {
    if (startIndex + 1 >= endIndex) {
        throw new Error("Missing length for nested map/list payload");
    }
    const encodedLength = flattenedValues[startIndex + 1];
    if (encodedLength < 2) {
        throw new Error(`Invalid nested payload length: ${encodedLength}`);
    }
    const valueEndIndex = startIndex + encodedLength;
    if (valueEndIndex > endIndex) {
        throw new Error("Nested payload exceeds containing payload bounds");
    }
    return valueEndIndex;
}
function decodeScalarByIndex(token, dictionary) {
    const dictionaryIndex = token - MapControlValue.COUNT;
    if (dictionaryIndex < 0 || dictionaryIndex >= dictionary.length) {
        throw new Error(`Scalar dictionary index out of range: ${token}`);
    }
    return dictionary[dictionaryIndex];
}
function pushAll(dictionary, values) {
    for (const value of values)
        dictionary.push(value);
}
//# sourceMappingURL=mapPropertyDecoder.js.map