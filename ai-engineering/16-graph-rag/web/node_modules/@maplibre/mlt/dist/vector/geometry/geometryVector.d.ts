import type Point from "@mapbox/point-geometry";
import type { GEOMETRY_TYPE } from "./geometryType";
import type { VertexBufferType } from "./vertexBufferType";
import type { TopologyVector } from "../../vector/geometry/topologyVector";
export type CoordinatesArray = Array<Array<Point>>;
export type Geometry = {
    coordinates: CoordinatesArray;
    type: GEOMETRY_TYPE;
};
export interface MortonSettings {
    numBits: number;
    coordinateShift: number;
}
export declare abstract class GeometryVector {
    private readonly _vertexBufferType;
    private readonly _topologyVector;
    private readonly _vertexOffsets;
    private readonly _vertexBuffer;
    private readonly _mortonSettings?;
    protected constructor(_vertexBufferType: VertexBufferType, _topologyVector: TopologyVector, _vertexOffsets: Uint32Array | undefined, _vertexBuffer: Int32Array | Uint32Array, _mortonSettings?: MortonSettings);
    get vertexBufferType(): VertexBufferType;
    get topologyVector(): TopologyVector;
    get vertexOffsets(): Uint32Array | undefined;
    get vertexBuffer(): Int32Array | Uint32Array;
    getSimpleEncodedVertex(index: number): [number, number];
    getVertex(index: number): [number, number];
    getGeometries(): CoordinatesArray[];
    get mortonSettings(): MortonSettings | undefined;
    abstract containsPolygonGeometry(): boolean;
    abstract geometryType(index: number): number;
    abstract get numGeometries(): number;
    abstract containsSingleGeometryType(): boolean;
}
