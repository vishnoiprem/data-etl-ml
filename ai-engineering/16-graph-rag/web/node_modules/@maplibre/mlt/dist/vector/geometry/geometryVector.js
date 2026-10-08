import { convertGeometryVector } from "./geometryVectorConverter";
import { decodeZOrderCurve } from "./zOrderCurve";
export class GeometryVector {
    constructor(_vertexBufferType, _topologyVector, _vertexOffsets, _vertexBuffer, _mortonSettings) {
        this._vertexBufferType = _vertexBufferType;
        this._topologyVector = _topologyVector;
        this._vertexOffsets = _vertexOffsets;
        this._vertexBuffer = _vertexBuffer;
        this._mortonSettings = _mortonSettings;
    }
    get vertexBufferType() {
        return this._vertexBufferType;
    }
    get topologyVector() {
        return this._topologyVector;
    }
    get vertexOffsets() {
        return this._vertexOffsets;
    }
    get vertexBuffer() {
        return this._vertexBuffer;
    }
    /* Allows faster access to the vertices since morton encoding is currently not used in the POC. Morton encoding
       will be used after adapting the shader to decode the morton codes on the GPU. */
    getSimpleEncodedVertex(index) {
        const offset = this.vertexOffsets ? this.vertexOffsets[index] * 2 : index * 2;
        const x = this.vertexBuffer[offset];
        const y = this.vertexBuffer[offset + 1];
        return [x, y];
    }
    //TODO: add scaling information to the constructor
    getVertex(index) {
        if (this.vertexOffsets && this.mortonSettings) {
            //TODO: move decoding of the morton codes on the GPU in the vertex shader
            const vertexOffset = this.vertexOffsets[index];
            const mortonEncodedVertex = this.vertexBuffer[vertexOffset];
            //TODO: improve performance -> inline calculation and move to decoding of VertexBuffer
            const vertex = decodeZOrderCurve(mortonEncodedVertex, this.mortonSettings.numBits, this.mortonSettings.coordinateShift);
            return [vertex.x, vertex.y];
        }
        const offset = this.vertexOffsets ? this.vertexOffsets[index] * 2 : index * 2;
        const x = this.vertexBuffer[offset];
        const y = this.vertexBuffer[offset + 1];
        return [x, y];
    }
    getGeometries() {
        return convertGeometryVector(this);
    }
    get mortonSettings() {
        return this._mortonSettings;
    }
}
//# sourceMappingURL=geometryVector.js.map