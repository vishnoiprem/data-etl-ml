import { GeometryVector, type MortonSettings } from "./geometryVector";
import { VertexBufferType } from "./vertexBufferType";
import type { TopologyVector } from "../../vector/geometry/topologyVector";
export declare function createConstGeometryVector(numGeometries: number, geometryType: number, topologyVector: TopologyVector, vertexOffsets: Uint32Array | undefined, vertexBuffer: Int32Array | Uint32Array): ConstGeometryVector;
export declare function createMortonEncodedConstGeometryVector(numGeometries: number, geometryType: number, topologyVector: TopologyVector, vertexOffsets: Uint32Array | undefined, vertexBuffer: Int32Array | Uint32Array, mortonInfo: MortonSettings): ConstGeometryVector;
export declare class ConstGeometryVector extends GeometryVector {
    private readonly _numGeometries;
    private readonly _geometryType;
    constructor(_numGeometries: number, _geometryType: number, vertexBufferType: VertexBufferType, topologyVector: TopologyVector, vertexOffsets: Uint32Array | undefined, vertexBuffer: Int32Array | Uint32Array, mortonSettings?: MortonSettings);
    geometryType(_index: number): number;
    get numGeometries(): number;
    containsPolygonGeometry(): boolean;
    containsSingleGeometryType(): boolean;
}
