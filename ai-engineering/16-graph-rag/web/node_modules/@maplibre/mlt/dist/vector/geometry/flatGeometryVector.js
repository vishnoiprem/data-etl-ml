import { GeometryVector } from "./geometryVector";
import { GEOMETRY_TYPE } from "./geometryType";
import { VertexBufferType } from "./vertexBufferType";
export function createFlatGeometryVector(geometryTypes, topologyVector, vertexOffsets, vertexBuffer) {
    return new FlatGeometryVector(VertexBufferType.VEC_2, geometryTypes, topologyVector, vertexOffsets, vertexBuffer);
}
export function createFlatGeometryVectorMortonEncoded(geometryTypes, topologyVector, vertexOffsets, vertexBuffer, mortonInfo) {
    return new FlatGeometryVector(VertexBufferType.MORTON, geometryTypes, topologyVector, vertexOffsets, vertexBuffer, mortonInfo);
}
export class FlatGeometryVector extends GeometryVector {
    constructor(vertexBufferType, _geometryTypes, topologyVector, vertexOffsets, vertexBuffer, mortonSettings) {
        super(vertexBufferType, topologyVector, vertexOffsets, vertexBuffer, mortonSettings);
        this._geometryTypes = _geometryTypes;
    }
    geometryType(index) {
        return this._geometryTypes[index];
    }
    get numGeometries() {
        return this._geometryTypes.length;
    }
    containsPolygonGeometry() {
        for (let i = 0; i < this.numGeometries; i++) {
            if (this.geometryType(i) === GEOMETRY_TYPE.POLYGON || this.geometryType(i) === GEOMETRY_TYPE.MULTIPOLYGON) {
                return true;
            }
        }
        return false;
    }
    containsSingleGeometryType() {
        return false;
    }
}
//# sourceMappingURL=flatGeometryVector.js.map