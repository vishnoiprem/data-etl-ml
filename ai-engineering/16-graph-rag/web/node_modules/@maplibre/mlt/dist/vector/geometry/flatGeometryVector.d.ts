import { GeometryVector, type MortonSettings } from "./geometryVector";
import { VertexBufferType } from "./vertexBufferType";
import type { TopologyVector } from "../../vector/geometry/topologyVector";
export declare function createFlatGeometryVector(geometryTypes: Uint32Array, topologyVector: TopologyVector, vertexOffsets: Uint32Array | undefined, vertexBuffer: Int32Array | Uint32Array): FlatGeometryVector;
export declare function createFlatGeometryVectorMortonEncoded(geometryTypes: Uint32Array, topologyVector: TopologyVector, vertexOffsets: Uint32Array | undefined, vertexBuffer: Int32Array | Uint32Array, mortonInfo: MortonSettings): FlatGeometryVector;
export declare class FlatGeometryVector extends GeometryVector {
    private readonly _geometryTypes;
    constructor(vertexBufferType: VertexBufferType, _geometryTypes: Uint32Array, topologyVector: TopologyVector, vertexOffsets: Uint32Array | undefined, vertexBuffer: Int32Array | Uint32Array, mortonSettings?: MortonSettings);
    geometryType(index: number): number;
    get numGeometries(): number;
    containsPolygonGeometry(): boolean;
    containsSingleGeometryType(): boolean;
}
