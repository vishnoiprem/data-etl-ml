import type { CoordinatesArray } from "./geometryVector";
import type { TopologyVector } from "./topologyVector";
export declare abstract class GpuVector implements Iterable<CoordinatesArray> {
    private readonly _triangleOffsets;
    private readonly _indexBuffer;
    private readonly _vertexBuffer;
    private readonly _topologyVector?;
    protected constructor(_triangleOffsets: Uint32Array, _indexBuffer: Uint32Array, _vertexBuffer: Int32Array | Uint32Array, _topologyVector?: TopologyVector);
    abstract geometryType(index: number): number;
    abstract get numGeometries(): number;
    abstract containsSingleGeometryType(): boolean;
    get triangleOffsets(): Uint32Array;
    get indexBuffer(): Uint32Array;
    get vertexBuffer(): Int32Array | Uint32Array;
    get topologyVector(): TopologyVector | undefined;
    getGeometries(): CoordinatesArray[];
    [Symbol.iterator](): Iterator<CoordinatesArray>;
}
