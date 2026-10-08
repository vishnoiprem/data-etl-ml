import { ConstGeometryVector } from "../vector/geometry/constGeometryVector";
import { GEOMETRY_TYPE } from "../vector/geometry/geometryType";
import { VertexBufferType } from "../vector/geometry/vertexBufferType";
import { encodeZOrderCurve } from "./zOrderCurveEncoder";
export const DEFAULT_MORTON_SETTINGS = { numBits: 16, coordinateShift: 0 };
export function encode(x, y) {
    return encodeZOrderCurve(x, y, DEFAULT_MORTON_SETTINGS.numBits, DEFAULT_MORTON_SETTINGS.coordinateShift);
}
export function encodePointGeometryVector(x, y) {
    return new ConstGeometryVector(1, GEOMETRY_TYPE.POINT, VertexBufferType.VEC_2, {
        geometryOffsets: new Uint32Array([0]),
        partOffsets: new Uint32Array([0]),
        ringOffsets: new Uint32Array([0]),
    }, undefined, new Int32Array([x, y]));
}
export function encodePointGeometryVectorWithOffset(x, y) {
    return new ConstGeometryVector(1, GEOMETRY_TYPE.POINT, VertexBufferType.VEC_2, {
        geometryOffsets: new Uint32Array([0]),
        partOffsets: new Uint32Array([0]),
        ringOffsets: new Uint32Array([0]),
    }, new Uint32Array([1]), new Int32Array([99, 99, x, y]));
}
export function encodePointGeometryVectorWithMortonEncoding(x, y) {
    const mortonEncoded = encode(x, y);
    return new ConstGeometryVector(1, GEOMETRY_TYPE.POINT, VertexBufferType.MORTON, {
        geometryOffsets: new Uint32Array([0]),
        partOffsets: new Uint32Array([0]),
        ringOffsets: new Uint32Array([0]),
    }, new Uint32Array([0]), new Int32Array([mortonEncoded]), DEFAULT_MORTON_SETTINGS);
}
export function encodePointsGeometryVector(points) {
    return new ConstGeometryVector(points.length / 2, GEOMETRY_TYPE.POINT, VertexBufferType.VEC_2, {
        geometryOffsets: new Uint32Array([0]),
        partOffsets: new Uint32Array([0]),
        ringOffsets: new Uint32Array([0]),
    }, undefined, new Int32Array(points));
}
export function encodeMultiPointGeometryVector(points) {
    const vertexBuffer = new Int32Array(points.flatMap((point) => [point[0], point[1]]));
    return new ConstGeometryVector(1, GEOMETRY_TYPE.MULTIPOINT, VertexBufferType.VEC_2, {
        geometryOffsets: new Uint32Array([0, points.length]),
        partOffsets: undefined,
        ringOffsets: undefined,
    }, undefined, vertexBuffer);
}
export function encodeLineStringGeometryVector(lines) {
    const vertexBuffer = new Int32Array(lines.flatMap((line) => [line[0], line[1]]));
    return new ConstGeometryVector(1, GEOMETRY_TYPE.LINESTRING, VertexBufferType.VEC_2, {
        geometryOffsets: undefined,
        partOffsets: new Uint32Array([0, vertexBuffer.length / 2]),
        ringOffsets: undefined,
    }, undefined, vertexBuffer);
}
export function encodeLineStringGeometryVectorWithMortonEncoding(line) {
    const numVertices = line.length;
    const vertexBuffer = new Int32Array(numVertices);
    const offsetBuffer = new Uint32Array(numVertices);
    for (let i = 0; i < numVertices; i++) {
        vertexBuffer[i] = encode(line[i][0], line[i][1]);
        offsetBuffer[i] = i;
    }
    return new ConstGeometryVector(1, GEOMETRY_TYPE.LINESTRING, VertexBufferType.MORTON, {
        geometryOffsets: undefined,
        partOffsets: new Uint32Array([0, numVertices]),
        ringOffsets: undefined,
    }, offsetBuffer, vertexBuffer, DEFAULT_MORTON_SETTINGS);
}
export function encodePolygonGeometryVector(polygon) {
    const vertexBuffer = new Int32Array(polygon.flatMap((ring) => ring.flatMap((point) => [point[0], point[1]])));
    const ringOffsets = new Uint32Array(polygon.length + 1);
    ringOffsets[0] = 0;
    let ringIndex = 1;
    for (const ring of polygon) {
        ringOffsets[ringIndex] = ringOffsets[ringIndex - 1] + ring.length;
        ringIndex++;
    }
    return new ConstGeometryVector(1, GEOMETRY_TYPE.POLYGON, VertexBufferType.VEC_2, {
        geometryOffsets: undefined,
        partOffsets: new Uint32Array([0, polygon.length]),
        ringOffsets,
    }, undefined, vertexBuffer);
}
export function encodePolygonGeometryVectorWithOffsets(polygon) {
    const vertexBuffer = new Int32Array(polygon.flatMap((ring) => ring.flatMap((point) => [point[0], point[1]])));
    const ringOffsets = new Uint32Array(polygon.length + 1);
    ringOffsets[0] = 0;
    let ringIndex = 1;
    for (const ring of polygon) {
        ringOffsets[ringIndex] = ringOffsets[ringIndex - 1] + ring.length;
        ringIndex++;
    }
    const offsetBuffer = new Uint32Array(vertexBuffer.length / 2);
    for (let i = 0; i < offsetBuffer.length; i++) {
        offsetBuffer[i] = i;
    }
    return new ConstGeometryVector(1, GEOMETRY_TYPE.POLYGON, VertexBufferType.VEC_2, {
        geometryOffsets: undefined,
        partOffsets: new Uint32Array([0, polygon.length]),
        ringOffsets,
    }, offsetBuffer, vertexBuffer);
}
export function encodePolygonGeometryVectorWithMortonOffsets(polygon) {
    const vertexBuffer = new Int32Array(polygon.flatMap((ring) => ring.flatMap((point) => encode(point[0], point[1]))));
    const ringOffsets = new Uint32Array(polygon.length + 1);
    ringOffsets[0] = 0;
    let ringIndex = 1;
    for (const ring of polygon) {
        ringOffsets[ringIndex] = ringOffsets[ringIndex - 1] + ring.length;
        ringIndex++;
    }
    const offsetBuffer = new Uint32Array(vertexBuffer.length);
    for (let i = 0; i < offsetBuffer.length; i++) {
        offsetBuffer[i] = i;
    }
    return new ConstGeometryVector(1, GEOMETRY_TYPE.POLYGON, VertexBufferType.MORTON, {
        geometryOffsets: undefined,
        partOffsets: new Uint32Array([0, polygon.length]),
        ringOffsets,
    }, offsetBuffer, vertexBuffer, DEFAULT_MORTON_SETTINGS);
}
export function encodeMultiLineStringGeometryVector(lines) {
    const vertexBuffer = new Int32Array(lines.flatMap((line) => line.flatMap((point) => [point[0], point[1]])));
    const partOffsets = new Uint32Array(lines.length + 1);
    partOffsets[0] = 0;
    let partIndex = 1;
    for (const line of lines) {
        partOffsets[partIndex] = partOffsets[partIndex - 1] + line.length;
        partIndex++;
    }
    return new ConstGeometryVector(1, GEOMETRY_TYPE.MULTILINESTRING, VertexBufferType.VEC_2, {
        geometryOffsets: new Uint32Array([0, lines.length]),
        partOffsets,
        ringOffsets: undefined,
    }, undefined, vertexBuffer);
}
export function encodeMultiLineStringGeometryVectorWithOffsets(lines) {
    const vertexBuffer = new Int32Array(lines.flatMap((line) => line.flatMap((point) => [point[0], point[1]])));
    const partOffsets = new Uint32Array(lines.length + 1);
    partOffsets[0] = 0;
    let partIndex = 1;
    for (const line of lines) {
        partOffsets[partIndex] = partOffsets[partIndex - 1] + line.length;
        partIndex++;
    }
    const offsetBuffer = new Uint32Array(vertexBuffer.length / 2);
    for (let i = 0; i < offsetBuffer.length; i++) {
        offsetBuffer[i] = i;
    }
    return new ConstGeometryVector(1, GEOMETRY_TYPE.MULTILINESTRING, VertexBufferType.VEC_2, {
        geometryOffsets: new Uint32Array([0, lines.length]),
        partOffsets,
        ringOffsets: undefined,
    }, offsetBuffer, vertexBuffer);
}
export function encodeMultiLineStringGeometryVectorWithMortonOffsets(lines) {
    const vertexBuffer = new Int32Array(lines.flatMap((line) => line.flatMap((point) => encode(point[0], point[1]))));
    const partOffsets = new Uint32Array(lines.length + 1);
    partOffsets[0] = 0;
    let partIndex = 1;
    for (const line of lines) {
        partOffsets[partIndex] = partOffsets[partIndex - 1] + line.length;
        partIndex++;
    }
    const offsetBuffer = new Uint32Array(vertexBuffer.length);
    for (let i = 0; i < offsetBuffer.length; i++) {
        offsetBuffer[i] = i;
    }
    return new ConstGeometryVector(1, GEOMETRY_TYPE.MULTILINESTRING, VertexBufferType.MORTON, {
        geometryOffsets: new Uint32Array([0, lines.length]),
        partOffsets,
        ringOffsets: undefined,
    }, offsetBuffer, vertexBuffer, DEFAULT_MORTON_SETTINGS);
}
export function encodeMultiPolygonGeometryVector(polygons) {
    const vertexBuffer = new Int32Array(polygons.flatMap((polygon) => polygon.flatMap((ring) => ring.flatMap((point) => [point[0], point[1]]))));
    const ringOffsets = new Uint32Array(polygons.reduce((sum, polygon) => sum + polygon.length, 0) + 1);
    const partOffsets = new Uint32Array(polygons.length + 1);
    ringOffsets[0] = 0;
    partOffsets[0] = 0;
    let ringIndex = 1;
    let partIndex = 1;
    for (const polygon of polygons) {
        for (const ring of polygon) {
            ringOffsets[ringIndex] = ringOffsets[ringIndex - 1] + ring.length;
            ringIndex++;
        }
        partOffsets[partIndex] = partOffsets[partIndex - 1] + polygon.length;
        partIndex++;
    }
    return new ConstGeometryVector(1, GEOMETRY_TYPE.MULTIPOLYGON, VertexBufferType.VEC_2, {
        geometryOffsets: new Uint32Array([0, polygons.length]),
        partOffsets,
        ringOffsets,
    }, undefined, vertexBuffer);
}
export function encodeMultiPolygonGeometryVectorWithOffsets(polygons) {
    const vertexBuffer = new Int32Array(polygons.flatMap((polygon) => polygon.flatMap((ring) => ring.flatMap((point) => [point[0], point[1]]))));
    const ringOffsets = new Uint32Array(polygons.reduce((sum, polygon) => sum + polygon.length, 0) + 1);
    const partOffsets = new Uint32Array(polygons.length + 1);
    ringOffsets[0] = 0;
    partOffsets[0] = 0;
    let ringIndex = 1;
    let partIndex = 1;
    for (const polygon of polygons) {
        for (const ring of polygon) {
            ringOffsets[ringIndex] = ringOffsets[ringIndex - 1] + ring.length;
            ringIndex++;
        }
        partOffsets[partIndex] = partOffsets[partIndex - 1] + polygon.length;
        partIndex++;
    }
    const offsetBuffer = new Uint32Array(vertexBuffer.length / 2);
    for (let i = 0; i < offsetBuffer.length; i++) {
        offsetBuffer[i] = i;
    }
    return new ConstGeometryVector(1, GEOMETRY_TYPE.MULTIPOLYGON, VertexBufferType.VEC_2, {
        geometryOffsets: new Uint32Array([0, polygons.length]),
        partOffsets,
        ringOffsets,
    }, offsetBuffer, vertexBuffer);
}
export function encodeMultiPolygonGeometryVectorWithMortonOffsets(polygons) {
    const vertexBuffer = new Int32Array(polygons.flatMap((polygon) => polygon.flatMap((ring) => ring.flatMap((point) => encode(point[0], point[1])))));
    const ringOffsets = new Uint32Array(polygons.reduce((sum, polygon) => sum + polygon.length, 0) + 1);
    const partOffsets = new Uint32Array(polygons.length + 1);
    ringOffsets[0] = 0;
    partOffsets[0] = 0;
    let ringIndex = 1;
    let partIndex = 1;
    for (const polygon of polygons) {
        for (const ring of polygon) {
            ringOffsets[ringIndex] = ringOffsets[ringIndex - 1] + ring.length;
            ringIndex++;
        }
        partOffsets[partIndex] = partOffsets[partIndex - 1] + polygon.length;
        partIndex++;
    }
    const offsetBuffer = new Uint32Array(vertexBuffer.length);
    for (let i = 0; i < offsetBuffer.length; i++) {
        offsetBuffer[i] = i;
    }
    return new ConstGeometryVector(1, GEOMETRY_TYPE.MULTIPOLYGON, VertexBufferType.MORTON, {
        geometryOffsets: new Uint32Array([0, polygons.length]),
        partOffsets,
        ringOffsets,
    }, offsetBuffer, vertexBuffer, DEFAULT_MORTON_SETTINGS);
}
//# sourceMappingURL=constGeometryVectorEncoder.js.map