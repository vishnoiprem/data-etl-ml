import type IntWrapper from "./intWrapper";
import BitVector from "../vector/flat/bitVector";
import type Vector from "../vector/vector";
import { type Column } from "../metadata/tileset/tilesetMetadata";
export declare function decodeString(name: string, data: Uint8Array, offset: IntWrapper, numStreams: number, bitVector?: BitVector): Vector | undefined;
export declare function decodeSharedDictionary(data: Uint8Array, offset: IntWrapper, column: Column, propertyColumnNames?: Set<string>): Vector[];
