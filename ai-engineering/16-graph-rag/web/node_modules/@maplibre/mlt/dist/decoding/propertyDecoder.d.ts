import type IntWrapper from "./intWrapper";
import { type Column } from "../metadata/tileset/tilesetMetadata";
import type Vector from "../vector/vector";
export declare function decodePropertyColumn(data: Uint8Array, offset: IntWrapper, columnMetadata: Column, numStreams: number, numFeatures: number, propertyColumnNames?: Set<string>): Vector | Vector[] | null;
