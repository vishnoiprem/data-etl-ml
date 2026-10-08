import { GeometryVector } from "./geometryVector";
import { GEOMETRY_TYPE } from "./geometryType";
import { VertexBufferType } from "./vertexBufferType";
export function createConstGeometryVector(numGeometries, geometryType, topologyVector, vertexOffsets, vertexBuffer) {
    return new ConstGeometryVector(numGeometries, geometryType, VertexBufferType.VEC_2, topologyVector, vertexOffsets, vertexBuffer);
}
export function createMortonEncodedConstGeometryVector(numGeometries, geometryType, topologyVector, vertexOffsets, vertexBuffer, mortonInfo) {
    return new ConstGeometryVector(numGeometries, geometryType, VertexBufferType.MORTON, topologyVector, vertexOffsets, vertexBuffer, mortonInfo);
}
export class ConstGeometryVector extends GeometryVector {
    constructor(_numGeometries, _geometryType, vertexBufferType, topologyVector, vertexOffsets, vertexBuffer, mortonSettings) {
        super(vertexBufferType, topologyVector, vertexOffsets, vertexBuffer, mortonSettings);
        this._numGeometries = _numGeometries;
        this._geometryType = _geometryType;
    }
    geometryType(_index) {
        return this._geometryType;
    }
    get numGeometries() {
        return this._numGeometries;
    }
    containsPolygonGeometry() {
        return this._geometryType === GEOMETRY_TYPE.POLYGON || this._geometryType === GEOMETRY_TYPE.MULTIPOLYGON;
    }
    containsSingleGeometryType() {
        return true;
    }
}
//# sourceMappingURL=constGeometryVector.js.map