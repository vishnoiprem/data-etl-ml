import type IntWrapper from "./intWrapper";
import type { GeometryVector } from "../vector/geometry/geometryVector";
import type { GpuVector } from "../vector/geometry/gpuVector";
import type GeometryScaling from "./geometryScaling";
export declare function decodeGeometryColumn(tile: Uint8Array, numStreams: number, offset: IntWrapper, numFeatures: number, scalingData?: GeometryScaling): GeometryVector | GpuVector;
